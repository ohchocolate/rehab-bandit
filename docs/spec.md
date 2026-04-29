# Rehab Bandit: 用 Contextual Bandit 做个人康复训练的每日推荐

**Date**: 2026-04-28
**Author**: xiaoyaoe
**Status**: Draft, pending review
**Learning track**: Builder (light) — agents + RL
**Timebox**: 4 weeks, ~4-5h/week, total 16-20h

---

## 0. 背景与动机

作者是 Amazon infra 工程师，兴趣驱动想跟上 agent + RL 浪潮，选择 **Builder 轻量路线**：每周 3-5 小时、目标是「好玩 + 能 demo」。经过一轮 brainstorming 后确定载体为**已有的个人康复打卡 web app**（vibe coded, GitHub PAT 鉴权, JSON 存在 GitHub repo 里），在其上增加一个 contextual bandit 服务做每日训练计划推荐。

**为什么选这个项目而不是玩具 RL 项目**:
- 个人真实数据 = 稀缺 RL 燃料
- 有真实使用动力（作者要做康复）
- 已有 app + 数据管道，不用重建基础设施
- 反馈闭环短（每天一条样本）
- 涵盖 agent 浪潮核心概念：off-policy learning、reward shaping、exploration/exploitation

**非目标（明确排除）**:
- 不做视频/抖音集成（单独项目）
- 不做 AI 生成动作描述（属于「路线 1 教练 agent」）
- 不改现有打卡/编辑/手动 +1 组逻辑
- 不追求通用推荐框架（个人项目，不做多用户）

---

## 1. 系统架构

```
┌─────────────────────────────────┐
│ 康复 app (现有, 前端)              │
│  - 动作库、打卡、手动编辑           │
│  - 新增 5 处 UI 元素（§4）         │
└───────────┬─────────────────────┘
            │ HTTP (或直接读 GitHub JSON)
            ▼
┌─────────────────────────────────┐
│ Bandit 服务 (新增, ~300 行 Python) │
│  POST /recommend → 今日 arm       │
│  POST /feedback  → 收 reward 更新  │
│  读同一个 GitHub JSON 作历史        │
└─────────────────────────────────┘
```

**架构要点**:
1. **解耦**: bandit 服务独立，可 curl 测试后再接前端
2. **单一真相源**: 打卡历史 = GitHub repo 里的 JSON。bandit 只读不写。
3. **部署**: 第一阶段本地 `python bandit.py`，不上云。
4. **语言**: Python（numpy 足够，不需 PyTorch）。
5. **并发安全**: 所有写操作走前端；bandit 只读历史。架构上消除冲突。

---

## 2. Bandit 核心设计

### 2.1 Arms（6 个日计划模板）

| ID | 模板 | 内容 | 适用场景 |
|----|------|------|---------|
| `upper_ankle` | 上肢日 + 踝 | 踝 PT 全套 + 上肢激活 + 胸腰椎拉伸 | 常规 |
| `lower_ankle` | 下肢日 + 踝 | 踝 PT 全套 + 下肢力量 + 胸腰椎拉伸 | 常规 |
| `stretch_ankle` | 拉伸 + 踝 | 踝 PT 全套 + 胸腰椎拉伸（轻量） | 累 / 时间少 |
| `travel_minimal` | 旅行最小化 | 单腿平衡 + 徒手踝动作 | 旅行模式 ON |
| `ankle_only` | 只做踝 | 踝 PT 全套 | 很忙 / 很累 |
| `rest` | 休息日 | 无动作 | 身体需恢复 |

**为什么不是 30 个 arm**: 30 个 arm 需要 30×样本量才能学好；每天 1 条打卡学不完。6 个 arm 几周可收敛。Bandit 不「发明」计划，只在这 6 个里挑。具体动作由现有 app 模板定义。

### 2.2 Context（8 个特征）

| 特征 | 类型 | 来源 |
|------|------|-----|
| 距上次 `upper_ankle` 天数 | 数值 | 算打卡历史 |
| 距上次 `lower_ankle` 天数 | 数值 | 算打卡历史 |
| 距上次 `stretch_ankle` 天数 | 数值 | 算打卡历史 |
| 本周已打卡天数 | 数值 | 算打卡历史 |
| 昨日主观评分 (1-5) | 数值 | 新增字段（§4） |
| 旅行模式 | 布尔 | 新增字段（§4） |
| 星期几 (0-6) | 类别 | 系统时间 |
| 上次同 arm 完成度 (0-1) | 数值 | 算打卡历史 |

**Deferred features**（不加，未来触发条件达到再加）:
- 经期 / 天气 / 睡眠时长
- **触发条件**：跑 ≥4 周 **且** 在某场景 bandit 明显持续失效

### 2.3 Reward

```
reward = 0.4 × 做了吗 (0/1)
       + 0.3 × 完成度 (完成组数 / 规定组数, 封顶 1.0)
       + 0.3 × 主观评分 (1-5 线性映射到 0-1)
```

- 没做 = 0（最强负信号）
- 做了一半 ≈ 0.6
- 做完 + 5 星 = 1.0
- 手动 +1 组计入完成度（体现实际努力）
- **Override 双向信号**: bandit 推 X 你换 Y:
  - X 得到的 reward 与「你没做 X」场景一致：`做了吗=0, 完成度=0, 评分不适用`，按公式 reward = 0
  - Y 得到的 reward 按 Y 实际执行结果照公式算
  - 这样 override 不需要特殊 reward 规则，天然由公式处理（X 没做所以低分，Y 做了所以有正常 reward）

---

## 3. 算法与冷启动

### 3.1 算法: LinUCB

**候选对比**:

| 算法 | 选 arm 方式 | 优点 | 缺点 |
|------|-----------|------|------|
| Epsilon-greedy | 90% 最优 + 10% 随机 | 5 行代码 | **不看 context**，旅行 / 累日不区分 |
| **LinUCB** ⭐ | 线性模型预测每 arm reward，优先「既可能好又不确定」 | 看 context、可解释、~80 行 | 需懂小矩阵运算 |
| Thompson Sampling | 贝叶斯采样 | 理论最优 | 前期不稳、难 debug |

**选 LinUCB 理由**:
- 需要利用 context，Epsilon-greedy 出局
- LinUCB 可解释（能打印「今天推 X 因为 feature Y + confidence Z」），对 debug 友好
- 核心代码量 ~80 行，Builder 路线甜点

**伪代码**（作者将亲手实现）:
```python
# 初始化: 每个 arm a 有 A_a (d×d matrix) = I_d, b_a (d vector) = 0

def select_arm(context_vec, alpha=1.0):
    ucb = {}
    for a in arms:
        theta_a = np.linalg.inv(A[a]) @ b[a]
        mean = theta_a @ context_vec
        bonus = alpha * np.sqrt(context_vec @ np.linalg.inv(A[a]) @ context_vec)
        ucb[a] = mean + bonus
    return max(ucb, key=ucb.get)  # arm with highest UCB score

def update(arm, context_vec, reward):
    A[arm] += np.outer(context_vec, context_vec)
    b[arm] += reward * context_vec
```

### 3.2 冷启动三阶段

**Phase 1（W1）: 纯规则 + 数据收集（Bandit 未上线）**
- UI 显示规则推荐
- 规则逻辑:
  1. 旅行模式 → `travel_minimal`
  2. 昨日评分 ≤2 → `stretch_ankle`
  3. 否则 → 距上次最久的 split
- 每天打卡记录 (context, chosen_arm, reward) 的元组到 JSON（为 W2 bandit 旁观学习准备燃料）

**Phase 1.5（W2）: 规则主导 + Bandit 旁观学习**
- UI 仍显示规则推荐
- Bandit 上线但**不做决策**，读 W1 积累的历史 + 每天新数据做增量 update
- 这段数据是 **off-policy**（bandit 从规则的决策学），和 RLHF 核心思想同构

**Phase 2（W3）: Bandit 主导 + Safety Rail**
- UI 显示 bandit 推荐 + 透明度标签（"依据：距上次下肢 5 天 + 预期 reward 0.68"）
- Safety rail: bandit 推违反硬约束时强制覆盖
  - 硬约束: 旅行模式 ON 时不推非 `travel_minimal` 或 `ankle_only` 的 arm
- 添加 override 反馈闭环

**Phase 3（W4 起）: Bandit 完全掌权**
- Safety rail 保留但很少触发
- Stats 页上线（P2，作者的 Builder 仪表盘）

---

## 4. 前端改动清单

### 4.1 新增 UI（按优先级）

**P0（不加 bandit 跑不起来）**:

1. **今日建议卡片**（首页顶部）
   ```
   📅 2026-04-28 周二
   💡 建议：下肢日 + 踝
   [接受 →] [我想做别的 ▼]
   ```
   - Phase 1 显示规则推荐；Phase 2 切 bandit
   - 「我想做别的」弹 6 个 arm 选单

2. **旅行模式 toggle**（设置页 or 首页角落）
   - 开启后持续到手动关闭
   - 存 `settings.json` 的 `travel_mode` 字段

3. **每日事后评分 modal**（打卡完成后弹出）
   ```
   今天的训练感觉怎么样？
   [😫 1] [😕 2] [😐 3] [🙂 4] [🔥 5]
   ```
   - 写入当天记录 `daily_score: 1-5`

**P1（不加也能跑，bandit 学得慢）**:

4. **Override 原因标签**（「我想做别的」弹窗内）
   - 预设: `太累` / `想换口味` / `没时间` / `身体不适` / `旅行` / `其他`
   - 写入 `override_reason: string`

**P2（可延后）**:

5. **Bandit 进步报告页** `/stats`
   - 每 arm 平均 reward、探索次数、override 率、reward 趋势

### 4.2 JSON Schema 变更

```json
// 每日打卡记录（现有结构 + 新字段）
{
  "date": "2026-04-28",
  "template_id": "lower_ankle",        // P0 新增
  "exercises": [...],                   // 现有
  "completion_ratio": 0.83,             // 算出来（完成组 / 规定组）
  "daily_score": 4,                     // P0 新增
  "was_override": false,                // P1 新增
  "overridden_from": null,              // P1 新增
  "override_reason": null,              // P1 新增
  "schema_version": 2                   // 新增（风险防护）
}

// 全局设置
{
  "travel_mode": false                  // P0 新增
}
```

### 4.3 前端工时预估
- P0 三项：~2-3h（vibe coding）
- P1 override 标签：~30min
- P2 stats 页：W4 做，1-2h

---

## 5. 项目节奏：4 周 + Day 0 今晚启动

### Day 0: 今晚

**健身前（~30 min）**
- 建 `bandit/` 目录，`pip install numpy`
- 写 `rules.py`（~20 行），输入 context dict 输出 arm id
- CLI 跑通：`python rules.py --today` → 打印推荐 + 依据

**健身后（~30 min）**
- 手动往今天打卡 JSON 加 `daily_score` 和 `template_id`
- Commit 到 app repo
- 第一条训练样本落地

**Day 0 成功标准**: 睡前能说「写了第一行 RL 项目代码 + 收集了第一条样本」。

### 4 周节奏

| 周 | 预算 | 任务 | 可见产出 | RL 概念 |
|----|------|------|---------|---------|
| **W1** | 4-5h | Day 0 + 前端 P0（今日建议卡片、旅行 toggle、评分 modal） | Web app 首页卡片亮，规则跑，评分和 template_id 开始自动存 | off-policy 数据收集 |
| **W2** | 5-6h | Python bandit 服务骨架 + 读 GitHub JSON 历史 + LinUCB 核心 + 单元测试 | Bandit 后台旁观学习，日志显示参数更新，UI 仍规则 | LinUCB、confidence interval |
| **W3** | 4-5h | Phase 2 切换：Bandit 接管 + safety rail + Override 反馈（P1） | 首页是 bandit 推，override 带原因，bandit 下次调整 | contextual bandit 决策、reward shaping |
| **W4** | 3-4h | Reward 调优 + Stats 页（P2）+ 复盘 blog | 可演示项目：stats 页看每 arm 学习曲线 | off-policy evaluation、A/B 思维 |

**总计**: 16-20h / 4 周。

### 破线允许
- 某周忙到碰不了: OK，4 → 5 周
- W2 LinUCB 卡住: 降级 Epsilon-greedy 先上线，下轮再补 LinUCB
- 玩嗨提前做 Stats 页: OK，但先保主线通

---

## 6. 成功标准 & 失败退出线

### 成功标准

**硬性**:
- 能用自己话讲 LinUCB vs Epsilon-greedy（3 min）
- 能 debug 一次"推荐错了"案例
- 能调 reward 公式并观察行为变化
- 4 周后 bandit 推荐 vs 手动选择 agreement > 60%

**软性**:
- 作者仍在用 app（不是为了项目）
- 能看懂一篇 LinUCB / Thompson Sampling 教学文
- 对 DeepSeek R1 / GRPO 论文不再恐惧

### 失败退出线
- W2 结束 LinUCB 单元测试没过 → 降级 Epsilon-greedy
- W3-W4 推荐明显变坏找不到原因 → 退回规则 + bandit 旁观，exploration 调低
- 连续两周没碰 → **暂停不是失败**；spec §10 有恢复协议

---

## 7. 测试策略

### 7.1 单元测试（~20 个，必做）
- `test_reward_computation`: reward 公式边界条件
- `test_context_extraction`: 距上次天数、本周已打卡天数等算法
- `test_linucb_converges_on_synthetic_data`: 造 100 条假数据 "下肢日 reward 总高"，LinUCB 应 >80% 选下肢日

### 7.2 Bandit 冒烟测试（W3 接管前跑一次）
- `simulate.py` 拿前 14 天真实历史，模拟 bandit 从 Day 1 重新决策
- 检查: 是否有明显蠢推荐（旅行日推 `lower_ankle`）
- 不是 unit test，是 sanity check

### 7.3 生产监控（Phase 3 起）
- Stats 页显示每 arm 平均 reward、override 率、reward 趋势
- **告警规则**: 连续 5 天 override 率 >50% → UI 显示 "bandit 可能退化"

---

## 8. 风险登记

| 风险 | 概率 | 影响 | 对策 |
|------|------|------|------|
| 数据太少 bandit 学不动 | 高 | 推荐差，用户失望 | Phase 1 + 1.5 规则兜底，bandit 仅旁观学。失败场景 = W4 后仍 60% override → 降级算法 |
| Reward 设计不对，学到"推最容易做的" | 中 | 核心康复被忽视 | Reward 权重保留"踝 PT 完成度"；W3 结束做一次调参 review |
| GitHub JSON 读写并发冲突 | 低 | 数据不一致 | bandit 只读；所有写走前端。架构消除 |
| 打卡格式变动 bandit 读不了 | 中 | 隐性 bug | `schema_version` 字段 + bandit 启动 validate 直接报错 |
| 4 周后失去兴趣 | 中 | 项目烂尾 | 不是 bug 是 feature；spec §10 恢复协议；学到就值 |

---

## 9. Claude 协作协议（Hard Gate / Soft Gate）

**作者选择自己写 RL 核心**，为防 vibe coding 惯性吞噬学习，明确边界。

### Hard Gate（必须自己写）
- LinUCB 的 `select_arm` 和 `update` 函数
- Reward 公式
- Context feature 提取

### Soft Gate（可让 Claude 做）
- 解释概念（UCB、confidence interval 是什么）
- Review 已写代码找 bug
- Debug numpy 语法错误
- 生成测试用例
- 前端 UI（P0 5 处改动）
- Boilerplate（GitHub API 调用、JSON IO、日志格式）

**黄金原则**: **If you can't explain why you wrote this line, don't write it.** 凡解释不清的代码，不留在 RL 核心。

---

## 10. 中断恢复协议

**定义**: 连续 ≥7 天没动这个项目，视为中断。

**恢复步骤**:
1. 打开这份 spec，读 §5 节奏表，定位自己当时在哪周
2. 打开 `bandit/CHECKPOINT.md`（W2 起维护），读最后一条进度
3. 跑 `python bandit/status.py` 看当前参数 + 数据量
4. 决定: 继续原计划 / 降级 / 暂停

**Checkpoint 内容**（W2 起每次收工写一行）:
```
2026-05-14: 完成 LinUCB select_arm，update 还没测。下次: 写 test_linucb_converges。
```

---

## 11. 下一步展望（不在本 spec 范围）

本项目 4 周完成后的可能延伸:

- **A. Bandit → 真 RL**: 每周规划序列（Q-learning / DQN），数据需求 10×
- **B. Bandit + LLM agent**: Claude 每晚读 bandit 日志，生成训练心得（过渡到路线 D: GRPO 微调小模型）
- **C. 开源模板**: 抽象为"用 RL 帮你坚持任何日常习惯"通用框架

---

## 12. Appendix: 学习资源清单（W2 提供）

**在 W2 开始前会补**:
- 1 篇最短清楚的 LinUCB 介绍（~10 min 读完）
- 1 个 YouTube 讲解视频（~30 min）
- 常见新手坑清单（3 条，具体到代码层面）
- LinUCB 伪代码（§3.1 已内嵌）

---

**End of design spec.**
