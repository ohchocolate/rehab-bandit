# CLAUDE.md — Rehab Bandit Project Instructions

> **Agents reading this: read this file first, then follow `docs/plan.md` task by task.**

## Project Goal

用 contextual bandit (LinUCB) 给我的**个人康复打卡 app** 做每日训练计划推荐。详细设计见 `docs/spec.md`。

- **Learning track**: Builder light — 作者在学 agent + RL，项目载体是真实康复场景
- **Timebox**: 4 weeks, 16-20h total
- **Tech stack**: Python 3.10+ / numpy / Flask / pytest. 前端 vanilla JS（另一个 repo）

## 🚨 CRITICAL: Hard Gate / Soft Gate Rules

**作者正在学 RL，必须亲手写核心算法**。Agent 协作时严格遵守：

### ❌ HARD GATE — Agent 绝对不能直接写完整实现
作者必须自己敲以下代码：
- `bandit/linucb.py` 的 `select_arm()` 和 `update()` 函数
- `bandit/reward.py` 的 reward 公式
- `bandit/context.py` 的 feature 提取逻辑

**如果 plan 某个任务进入这些文件，agent 的工作是**：
1. 贴出伪代码 / 概念解释给作者看
2. **等作者自己写完 push 过来**
3. 然后 review 作者的实现，指出 bug

**不许直接在 `select_arm`、`update`、reward 公式里写可运行代码**。

### ✅ SOFT GATE — Agent 可以自由帮忙
- 解释 RL 概念（UCB、confidence interval）
- Debug 作者写的代码
- 生成测试用例（测试代码可以 agent 写）
- GitHub API 调用、JSON IO、Flask 路由、日志格式等 boilerplate
- 写所有非核心算法文件

### 判断边界的一句话
**"If the user can't explain why a line is there, don't write it for them."**

凡属核心 RL 算法的代码，agent 只提供骨架/伪代码/review，**实现必须等作者**。

## Execution Protocol

按 `docs/plan.md` 从上往下一个任务一个任务做：

1. **一次做一个任务**：看 `## Task N`，按步骤执行，勾 checkbox
2. **每任务结束 commit**：任务最后一步都是 `git commit`，不跳过
3. **遇到 Hard Gate 文件**：停下，留一条 `docs/checkpoint.md` 说明「等作者写 `select_arm`」，退出
4. **任务之间可以停下**：不连续跑整个 plan，一次做一个任务然后让作者 review

## Checkpoint Logging

每完成一个任务、或者遇到 Hard Gate 停下时，往 `docs/checkpoint.md` 追加一行：
```
YYYY-MM-DD HH:MM  | Task N done  | commit <sha>  | next: Task N+1
YYYY-MM-DD HH:MM  | Task N paused | reason: hard gate on linucb.select_arm
```

恢复工作时读最后一条就知道从哪继续。

## Key Files Reference

- `docs/spec.md` — 完整设计规范（arms、context、reward 公式、4 周节奏）
- `docs/plan.md` — 实施计划（任务列表，你主要执行这个）
- `docs/checkpoint.md` — 进度日志（自动更新）
- `bandit/` — Python bandit 服务代码
- `tests/` — pytest 测试

## What to do RIGHT NOW

1. Read `docs/spec.md` §1-3（架构、arms、reward、algorithm）
2. Open `docs/plan.md`
3. Find the first unchecked task (search `- [ ]`)
4. Execute it step by step
5. Respect Hard Gate — 核心算法停下让作者写
