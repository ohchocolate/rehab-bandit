# Rehab Bandit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **CRITICAL — Read `CLAUDE.md` first for Hard Gate / Soft Gate rules.** Some tasks have `🚨 HARD GATE` marker — agent must NOT write implementation for those; wait for author.

**Goal:** Build a contextual bandit (LinUCB) service that recommends daily rehab training templates for the author's personal rehab app, learning from real check-in data.

**Architecture:** Standalone Python service (this repo) reads check-in JSON from the rehab app's GitHub repo via API, runs LinUCB over 6 day-template arms with 8 context features, exposes `/recommend` and `/feedback` HTTP endpoints. Frontend (separate repo) adds UI to show recommendations, collect ratings, toggle travel mode.

**Tech Stack:** Python 3.10+, numpy, Flask, pytest, GitHub REST API (via `requests`)

---

## Week 1 — Day 0 Kickoff + Rules + Frontend Prep

### Task 1: Repo scaffolding + dependencies

**Files:**
- Create: `README.md`
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `pyproject.toml`

- [ ] **Step 1: Initialize git**

```bash
cd rehab-bandit
git init
git branch -M main
```

- [ ] **Step 2: Write `requirements.txt`**

```
numpy>=1.26
flask>=3.0
requests>=2.31
pytest>=8.0
python-dotenv>=1.0
```

- [ ] **Step 3: Write `.gitignore`**

```
__pycache__/
*.pyc
.venv/
venv/
.env
.pytest_cache/
*.egg-info/
*.log
# data/ is gitignored BY FILE below — sample_checkins.json is tracked (see Task 3),
# but generated artifacts (observations.jsonl, feedback.jsonl, bandit_state.npz) are not
data/observations.jsonl
data/feedback.jsonl
data/bandit_state.npz
```

- [ ] **Step 4: Write minimal `README.md`**

```markdown
# Rehab Bandit

Contextual bandit (LinUCB) for personal rehab daily plan recommendations.

See `docs/spec.md` for design, `docs/plan.md` for implementation steps.

## Setup

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

- [ ] **Step 5: Write `pyproject.toml`** (for pytest config)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
```

- [ ] **Step 6: Create venv and install**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Expected: no errors, pytest installed.

- [ ] **Step 7: Commit**

```bash
git add README.md requirements.txt .gitignore pyproject.toml
git commit -m "chore: repo scaffolding"
```

---

### Task 2: Define arms constant + template metadata

**Files:**
- Create: `bandit/__init__.py` (empty)
- Create: `bandit/arms.py`
- Create: `tests/__init__.py` (empty)
- Test: `tests/test_arms.py`

- [ ] **Step 1: Write failing test `tests/test_arms.py`**

```python
from bandit.arms import ARMS, ARM_IDS, get_arm

def test_six_arms_defined():
    assert len(ARMS) == 6

def test_arm_ids_unique():
    assert len(ARM_IDS) == len(set(ARM_IDS))

def test_expected_arm_ids_present():
    expected = {"upper_ankle", "lower_ankle", "stretch_ankle",
                "travel_minimal", "ankle_only", "rest"}
    assert set(ARM_IDS) == expected

def test_get_arm_returns_metadata():
    arm = get_arm("lower_ankle")
    assert arm["id"] == "lower_ankle"
    assert "description" in arm
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_arms.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'bandit.arms'`

- [ ] **Step 3: Create `bandit/__init__.py` (empty file) and `tests/__init__.py` (empty file)**

```bash
touch bandit/__init__.py tests/__init__.py
```

- [ ] **Step 4: Implement `bandit/arms.py`**

```python
"""Daily plan templates ("arms" in bandit terminology)."""

ARMS = [
    {"id": "upper_ankle",    "description": "上肢日 + 踝 PT + 胸腰椎拉伸"},
    {"id": "lower_ankle",    "description": "下肢日 + 踝 PT + 胸腰椎拉伸"},
    {"id": "stretch_ankle",  "description": "拉伸 + 踝 PT（轻量）"},
    {"id": "travel_minimal", "description": "旅行最小化：单腿平衡 + 徒手踝"},
    {"id": "ankle_only",     "description": "只做踝 PT"},
    {"id": "rest",           "description": "休息日"},
]

ARM_IDS = [a["id"] for a in ARMS]
_BY_ID = {a["id"]: a for a in ARMS}


def get_arm(arm_id: str) -> dict:
    return _BY_ID[arm_id]
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_arms.py -v
```

Expected: 4 PASSED.

- [ ] **Step 6: Commit**

```bash
git add bandit/__init__.py bandit/arms.py tests/__init__.py tests/test_arms.py
git commit -m "feat(arms): define 6 daily plan templates"
```

---

### Task 3: JSON schema types + sample data

**Files:**
- Create: `bandit/schema.py`
- Create: `data/sample_checkins.json` (fake data for local testing)
- Test: `tests/test_schema.py`

- [ ] **Step 1: Write failing test `tests/test_schema.py`**

```python
import json
from pathlib import Path
from bandit.schema import validate_checkin, CURRENT_SCHEMA_VERSION

def test_current_schema_version_is_2():
    assert CURRENT_SCHEMA_VERSION == 2

def test_valid_checkin_passes():
    record = {
        "date": "2026-04-28",
        "template_id": "lower_ankle",
        "exercises": [],
        "completion_ratio": 0.8,
        "daily_score": 4,
        "was_override": False,
        "overridden_from": None,
        "override_reason": None,
        "schema_version": 2,
    }
    validate_checkin(record)  # should not raise

def test_missing_field_raises():
    import pytest
    with pytest.raises(ValueError, match="missing required field"):
        validate_checkin({"date": "2026-04-28"})

def test_sample_data_loads_and_validates():
    path = Path(__file__).parent.parent / "data" / "sample_checkins.json"
    data = json.loads(path.read_text())
    assert len(data) >= 3
    for r in data:
        validate_checkin(r)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_schema.py -v
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement `bandit/schema.py`**

```python
"""JSON schema for daily check-in records."""

CURRENT_SCHEMA_VERSION = 2

REQUIRED_FIELDS = [
    "date", "template_id", "exercises", "completion_ratio",
    "daily_score", "was_override", "schema_version",
]


def validate_checkin(record: dict) -> None:
    for f in REQUIRED_FIELDS:
        if f not in record:
            raise ValueError(f"missing required field: {f}")
    if record["schema_version"] != CURRENT_SCHEMA_VERSION:
        raise ValueError(
            f"schema_version mismatch: got {record['schema_version']}, "
            f"expected {CURRENT_SCHEMA_VERSION}"
        )
    if not 0.0 <= record["completion_ratio"] <= 1.0:
        raise ValueError("completion_ratio must be in [0, 1]")
    if record["daily_score"] is not None and not 1 <= record["daily_score"] <= 5:
        raise ValueError("daily_score must be in [1, 5]")
```

- [ ] **Step 4: Create `data/sample_checkins.json`** (for local testing without GitHub access)

```json
[
  {
    "date": "2026-04-21",
    "template_id": "upper_ankle",
    "exercises": [],
    "completion_ratio": 1.0,
    "daily_score": 4,
    "was_override": false,
    "overridden_from": null,
    "override_reason": null,
    "schema_version": 2
  },
  {
    "date": "2026-04-22",
    "template_id": "stretch_ankle",
    "exercises": [],
    "completion_ratio": 0.67,
    "daily_score": 3,
    "was_override": false,
    "overridden_from": null,
    "override_reason": null,
    "schema_version": 2
  },
  {
    "date": "2026-04-23",
    "template_id": "travel_minimal",
    "exercises": [],
    "completion_ratio": 1.0,
    "daily_score": 5,
    "was_override": true,
    "overridden_from": "lower_ankle",
    "override_reason": "旅行",
    "schema_version": 2
  }
]
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_schema.py -v
```

Expected: 4 PASSED.

- [ ] **Step 6: Commit**

```bash
git add bandit/schema.py tests/test_schema.py data/sample_checkins.json
git commit -m "feat(schema): v2 checkin validation + sample data"
```

Note: `.gitignore` ignores only generated `data/*.jsonl` and `data/*.npz`, so `sample_checkins.json` commits normally.

---

### Task 4: History loader (local file + stub for GitHub)

**Files:**
- Create: `bandit/history.py`
- Test: `tests/test_history.py`

- [ ] **Step 1: Write failing test `tests/test_history.py`**

```python
from pathlib import Path
from bandit.history import load_from_file, History

def test_load_sample_file():
    path = Path(__file__).parent.parent / "data" / "sample_checkins.json"
    history = load_from_file(path)
    assert isinstance(history, History)
    assert len(history.records) == 3

def test_history_sorted_by_date():
    path = Path(__file__).parent.parent / "data" / "sample_checkins.json"
    history = load_from_file(path)
    dates = [r["date"] for r in history.records]
    assert dates == sorted(dates)

def test_history_last_of_arm():
    path = Path(__file__).parent.parent / "data" / "sample_checkins.json"
    history = load_from_file(path)
    last_upper = history.last_of_arm("upper_ankle")
    assert last_upper["date"] == "2026-04-21"
    assert history.last_of_arm("rest") is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_history.py -v
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement `bandit/history.py`**

```python
"""Check-in history loading and queries."""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from bandit.schema import validate_checkin


@dataclass
class History:
    records: list = field(default_factory=list)

    def last_of_arm(self, arm_id: str) -> Optional[dict]:
        matches = [r for r in self.records if r["template_id"] == arm_id]
        return matches[-1] if matches else None

    def days_in_current_week(self, today: str) -> int:
        """Count distinct check-in dates in the ISO week of `today`."""
        from datetime import date
        tgt = date.fromisoformat(today)
        year, week, _ = tgt.isocalendar()
        count = 0
        for r in self.records:
            d = date.fromisoformat(r["date"])
            y, w, _ = d.isocalendar()
            if y == year and w == week:
                count += 1
        return count


def load_from_file(path: Path) -> History:
    data = json.loads(Path(path).read_text())
    for r in data:
        validate_checkin(r)
    records = sorted(data, key=lambda r: r["date"])
    return History(records=records)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_history.py -v
```

Expected: 3 PASSED.

- [ ] **Step 5: Commit**

```bash
git add bandit/history.py tests/test_history.py
git commit -m "feat(history): load and query check-in records"
```

---

### Task 5: Rules-based recommender (Day 0 deliverable)

**Files:**
- Create: `bandit/rules.py`
- Test: `tests/test_rules.py`

- [ ] **Step 1: Write failing test `tests/test_rules.py`**

```python
from bandit.rules import rule_recommend


def _ctx(**overrides):
    base = {
        "travel_mode": False,
        "yesterday_score": 3,
        "days_since_upper_ankle": 99,
        "days_since_lower_ankle": 99,
        "days_since_stretch_ankle": 99,
        "week_checkin_count": 0,
        "weekday": 1,
        "last_same_arm_completion": 1.0,
    }
    base.update(overrides)
    return base


def test_travel_mode_always_returns_travel_minimal():
    assert rule_recommend(_ctx(travel_mode=True)) == "travel_minimal"

def test_low_yesterday_score_returns_stretch():
    assert rule_recommend(_ctx(yesterday_score=2)) == "stretch_ankle"
    assert rule_recommend(_ctx(yesterday_score=1)) == "stretch_ankle"

def test_default_picks_longest_gap_split():
    ctx = _ctx(days_since_upper_ankle=5, days_since_lower_ankle=2, days_since_stretch_ankle=3)
    assert rule_recommend(ctx) == "upper_ankle"

    ctx = _ctx(days_since_upper_ankle=1, days_since_lower_ankle=7, days_since_stretch_ankle=3)
    assert rule_recommend(ctx) == "lower_ankle"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_rules.py -v
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement `bandit/rules.py`**

```python
"""Phase 1 rule-based recommender. Used before bandit takes over."""


def rule_recommend(ctx: dict) -> str:
    if ctx["travel_mode"]:
        return "travel_minimal"
    if ctx["yesterday_score"] is not None and ctx["yesterday_score"] <= 2:
        return "stretch_ankle"
    gaps = {
        "upper_ankle": ctx["days_since_upper_ankle"],
        "lower_ankle": ctx["days_since_lower_ankle"],
        "stretch_ankle": ctx["days_since_stretch_ankle"],
    }
    return max(gaps, key=gaps.get)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_rules.py -v
```

Expected: 3 PASSED.

- [ ] **Step 5: Commit**

```bash
git add bandit/rules.py tests/test_rules.py
git commit -m "feat(rules): phase-1 rule-based recommender (Day 0)"
```

---

### Task 6: CLI entry — `python -m bandit.cli today`

**Files:**
- Create: `bandit/cli.py`
- Create: `bandit/__main__.py`
- Test: manual only (print-based CLI)

- [ ] **Step 1: Create `bandit/__main__.py`**

```python
from bandit.cli import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Create `bandit/cli.py`**

```python
"""CLI for Day 0 smoke-testing the rule recommender."""
import argparse
import json
from datetime import date
from pathlib import Path

from bandit.history import load_from_file
from bandit.rules import rule_recommend
from bandit.arms import get_arm


def _build_context(history, today_str: str, travel_mode: bool) -> dict:
    from datetime import date as _date
    today = _date.fromisoformat(today_str)

    def days_since(arm_id):
        last = history.last_of_arm(arm_id)
        if last is None:
            return 999
        return (today - _date.fromisoformat(last["date"])).days

    yesterday = sorted(history.records, key=lambda r: r["date"])
    yesterday_score = yesterday[-1]["daily_score"] if yesterday else None

    return {
        "travel_mode": travel_mode,
        "yesterday_score": yesterday_score,
        "days_since_upper_ankle": days_since("upper_ankle"),
        "days_since_lower_ankle": days_since("lower_ankle"),
        "days_since_stretch_ankle": days_since("stretch_ankle"),
        "week_checkin_count": history.days_in_current_week(today_str),
        "weekday": today.weekday(),
        "last_same_arm_completion": 1.0,  # filled once bandit knows what arm it will pick
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["today"])
    parser.add_argument("--history", default="data/sample_checkins.json")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--travel", action="store_true")
    args = parser.parse_args()

    history = load_from_file(Path(args.history))
    ctx = _build_context(history, args.date, args.travel)
    arm_id = rule_recommend(ctx)
    arm = get_arm(arm_id)

    print(f"📅 {args.date}")
    print(f"💡 推荐: {arm_id} — {arm['description']}")
    print(f"依据: {json.dumps(ctx, ensure_ascii=False, indent=2)}")
```

- [ ] **Step 3: Run CLI manually**

```bash
python -m bandit today --history data/sample_checkins.json --date 2026-04-28
```

Expected output: prints "📅 2026-04-28" + recommendation + context dict. Arm should be `rest` or one of the splits based on gaps (check: last upper_ankle = 2026-04-21, 7 days gap, should win).

Also try travel mode:

```bash
python -m bandit today --history data/sample_checkins.json --travel
```

Expected: `travel_minimal`.

- [ ] **Step 4: Commit**

```bash
git add bandit/cli.py bandit/__main__.py
git commit -m "feat(cli): Day 0 rule-based recommender CLI"
```

**🎉 Day 0 milestone**: you have a working recommender, first line of RL code written.

---

### Task 7: Write first real check-in by hand (Day 0 night)

**This is a manual task for the author**, no code. Agent: skip if not author.

- [ ] **Step 1**: Open the rehab app's GitHub repo, find today's check-in JSON file
- [ ] **Step 2**: Add these fields manually:
  - `"template_id": "<whatever you did today>"`
  - `"daily_score": <1-5>`
  - `"was_override": false`
  - `"schema_version": 2`
- [ ] **Step 3**: Commit to the rehab app repo with message `feat(schema): upgrade to v2 for bandit`

**Day 0 complete when**: this commit is pushed. First training sample in the books.

---

### Task 8: Frontend — "今日建议" card (rehab app repo, not this repo)

**This task is in the rehab app repo, not here.** Agent operating in `rehab-bandit` repo: output instructions as a markdown snippet for the author to copy-paste into the other repo.

**Files (in rehab app repo):**
- Modify: `index.html` — add card markup at top of main section
- Modify: `app.js` — add `fetchRecommendation()` and `renderCard()`

- [ ] **Step 1: Add HTML markup at top of main**

```html
<section id="today-card" class="recommendation-card">
  <div class="card-date" id="card-date">📅</div>
  <div class="card-title">💡 今日建议</div>
  <div class="card-arm" id="card-arm">加载中...</div>
  <div class="card-reason" id="card-reason"></div>
  <div class="card-actions">
    <button id="accept-btn">接受 →</button>
    <button id="override-btn">我想做别的 ▼</button>
  </div>
</section>
```

- [ ] **Step 2: Add CSS (inline or in stylesheet)**

```css
.recommendation-card {
  border: 2px solid #4a90e2;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
  background: #f0f7ff;
}
.card-arm { font-size: 1.4em; font-weight: bold; margin: 8px 0; }
.card-reason { color: #666; font-size: 0.9em; }
.card-actions { margin-top: 12px; display: flex; gap: 8px; }
```

- [ ] **Step 3: Add JS to fetch recommendation from local bandit service**

```javascript
async function fetchRecommendation() {
  const today = new Date().toISOString().split('T')[0];
  const travelMode = localStorage.getItem('travel_mode') === 'true';
  try {
    const res = await fetch(`http://localhost:5000/recommend?date=${today}&travel=${travelMode}`);
    if (!res.ok) throw new Error('bandit offline');
    return await res.json();
  } catch (e) {
    return { arm_id: 'ankle_only', description: '踝 PT（bandit 离线回退）', reason: 'offline' };
  }
}

function renderCard(rec) {
  document.getElementById('card-date').textContent = `📅 ${new Date().toLocaleDateString('zh-CN')}`;
  document.getElementById('card-arm').textContent = rec.description || rec.arm_id;
  document.getElementById('card-reason').textContent = `依据: ${rec.reason || ''}`;
}

window.addEventListener('DOMContentLoaded', async () => {
  renderCard(await fetchRecommendation());
});
```

- [ ] **Step 4: Test locally**

Start bandit service (Task 13) on port 5000 first, then open the rehab app. Card should render today's recommendation.

- [ ] **Step 5: Commit in rehab app repo**

```bash
git add index.html app.js style.css
git commit -m "feat: add today's recommendation card"
```

---

### Task 9: Frontend — Travel mode toggle + daily_score modal

**Again in rehab app repo.** Keep all UI changes in one commit sequence.

- [ ] **Step 1: Add travel toggle to settings or header**

```html
<label class="travel-toggle">
  <input type="checkbox" id="travel-mode-input">
  <span>✈️ 旅行模式</span>
</label>
```

- [ ] **Step 2: JS persistence**

```javascript
const travelInput = document.getElementById('travel-mode-input');
travelInput.checked = localStorage.getItem('travel_mode') === 'true';
travelInput.addEventListener('change', (e) => {
  localStorage.setItem('travel_mode', e.target.checked);
  fetchRecommendation().then(renderCard);
});
```

- [ ] **Step 3: Daily score modal on check-in complete**

```html
<div id="score-modal" class="modal hidden">
  <h3>今天的训练感觉怎么样？</h3>
  <div class="score-buttons">
    <button data-score="1">😫 1</button>
    <button data-score="2">😕 2</button>
    <button data-score="3">😐 3</button>
    <button data-score="4">🙂 4</button>
    <button data-score="5">🔥 5</button>
  </div>
</div>
```

- [ ] **Step 4: Hook modal to check-in complete + write to JSON**

```javascript
function showScoreModal(checkinRecord) {
  const modal = document.getElementById('score-modal');
  modal.classList.remove('hidden');
  modal.querySelectorAll('button').forEach(btn => {
    btn.onclick = async () => {
      checkinRecord.daily_score = parseInt(btn.dataset.score);
      checkinRecord.schema_version = 2;
      await writeCheckin(checkinRecord);  // existing GitHub PAT writer
      modal.classList.add('hidden');
    };
  });
}
```

- [ ] **Step 5: Commit in rehab app repo**

```bash
git add index.html app.js style.css
git commit -m "feat: travel toggle + daily score modal"
```

---

## Week 2 — Bandit Service + LinUCB Core

### Task 10: Flask service skeleton — `/health` endpoint

**Files:**
- Create: `bandit/server.py`
- Test: `tests/test_server.py`

- [ ] **Step 1: Write failing test `tests/test_server.py`**

```python
from bandit.server import create_app


def test_health_endpoint():
    app = create_app()
    client = app.test_client()
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json == {"status": "ok"}
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_server.py -v
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement `bandit/server.py`**

```python
"""Flask HTTP service for bandit recommendations."""
from flask import Flask, jsonify


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    return app


if __name__ == "__main__":
    create_app().run(port=5000, debug=True)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_server.py -v
```

Expected: 1 PASSED.

- [ ] **Step 5: Smoke test manually**

```bash
python -m bandit.server &
sleep 1
curl http://localhost:5000/health
kill %1
```

Expected: `{"status":"ok"}`

- [ ] **Step 6: Commit**

```bash
git add bandit/server.py tests/test_server.py
git commit -m "feat(server): flask skeleton with /health"
```

---

### Task 11: Context feature extraction

**Files:**
- Create: `bandit/context.py`  ⚠️ **🚨 HARD GATE for `build_context_vector()` only**
- Test: `tests/test_context.py`

> **Agent note**: Helper functions (`days_since`, `weekday_one_hot`) can be implemented by agent. The **final feature vector assembly** function `build_context_vector(ctx_dict) -> np.ndarray` — the actual decision of "which features in what order, how encoded" — must be written by the author.

- [ ] **Step 1: Write failing test `tests/test_context.py`**

```python
import numpy as np
from bandit.context import (
    days_since_arm, weekday_one_hot, last_same_arm_completion,
    build_context_dict,
)
from bandit.history import History


def _hist(*records):
    return History(records=list(records))


def test_days_since_none_returns_large_sentinel():
    h = _hist()
    assert days_since_arm(h, "upper_ankle", "2026-04-28") >= 999


def test_days_since_counts_correctly():
    h = _hist({"date": "2026-04-20", "template_id": "upper_ankle",
               "exercises": [], "completion_ratio": 1.0, "daily_score": 4,
               "was_override": False, "schema_version": 2})
    assert days_since_arm(h, "upper_ankle", "2026-04-28") == 8


def test_weekday_one_hot_is_length_7():
    v = weekday_one_hot(3)
    assert len(v) == 7
    assert v[3] == 1 and sum(v) == 1


def test_last_same_arm_completion_default_1():
    h = _hist()
    assert last_same_arm_completion(h, "upper_ankle") == 1.0


def test_build_context_dict_has_all_keys():
    h = _hist()
    ctx = build_context_dict(h, today="2026-04-28", travel_mode=False)
    required = {"travel_mode", "yesterday_score",
                "days_since_upper_ankle", "days_since_lower_ankle",
                "days_since_stretch_ankle", "week_checkin_count",
                "weekday", "last_same_arm_completion"}
    assert set(ctx.keys()) >= required
```

- [ ] **Step 2: Run to verify fail**

```bash
pytest tests/test_context.py -v
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement helpers in `bandit/context.py`** (agent can write these)

```python
"""Context feature extraction from check-in history."""
from datetime import date
from typing import Optional

import numpy as np

from bandit.history import History


def days_since_arm(history: History, arm_id: str, today: str) -> int:
    last = history.last_of_arm(arm_id)
    if last is None:
        return 999
    return (date.fromisoformat(today) - date.fromisoformat(last["date"])).days


def weekday_one_hot(weekday: int) -> list:
    v = [0] * 7
    v[weekday] = 1
    return v


def last_same_arm_completion(history: History, arm_id: str) -> float:
    last = history.last_of_arm(arm_id)
    return last["completion_ratio"] if last else 1.0


def build_context_dict(history: History, today: str, travel_mode: bool) -> dict:
    latest = history.records[-1] if history.records else None
    yesterday_score = latest["daily_score"] if latest else None
    today_d = date.fromisoformat(today)
    return {
        "travel_mode": travel_mode,
        "yesterday_score": yesterday_score,
        "days_since_upper_ankle": days_since_arm(history, "upper_ankle", today),
        "days_since_lower_ankle": days_since_arm(history, "lower_ankle", today),
        "days_since_stretch_ankle": days_since_arm(history, "stretch_ankle", today),
        "week_checkin_count": history.days_in_current_week(today),
        "weekday": today_d.weekday(),
        "last_same_arm_completion": last_same_arm_completion(history, "upper_ankle"),
    }
```

- [ ] **Step 4: Run test to verify helpers pass**

```bash
pytest tests/test_context.py -v
```

Expected: 5 PASSED.

- [ ] **Step 5: 🚨 HARD GATE — Author writes `build_context_vector`**

**Agent: STOP here. Write a note in `docs/checkpoint.md`:**
```
YYYY-MM-DD HH:MM | Task 11 paused | reason: hard gate on build_context_vector | next: author implements feature vector assembly
```

**Author task**: design and implement `build_context_vector(ctx_dict) -> np.ndarray` in `bandit/context.py`. Decisions to make:
- Normalize `days_since_*` (divide by 30? cap at 14?)
- Scale `yesterday_score` from 1-5 to 0-1?
- Include bias term (constant 1)?

**2026-05-09 amendment (DEC-003)**: initial v1 context vector should be small and explainable. Keep `weekday` in `build_context_dict()` for future use, but do **not** include it in `build_context_vector()` yet.

Suggested initial vector shape: `(8,)`

| Index | Feature | Suggested scaling |
|---:|---|---|
| 0 | bias term | `1.0` |
| 1 | `travel_mode` | `1.0` if true else `0.0` |
| 2 | `yesterday_score` | `(score - 1) / 4`, or `0.5` if missing |
| 3 | `days_since_upper_ankle` | cap at 14, divide by 14 |
| 4 | `days_since_lower_ankle` | cap at 14, divide by 14 |
| 5 | `days_since_stretch_ankle` | cap at 14, divide by 14 |
| 6 | `week_checkin_count` | cap at 7, divide by 7 |
| 7 | `last_same_arm_completion` | already 0-1 |

Write a test `test_build_context_vector_dimensions()` that asserts `vec.shape == (8,)`. Keep `d` consistent — Task 12 depends on it.

- [ ] **Step 6: Author commits**

```bash
git add bandit/context.py tests/test_context.py
git commit -m "feat(context): feature vector assembly"
```

---

### Task 12: LinUCB core algorithm — stepped implementation

**Files:**
- Create: `bandit/linucb.py` ⚠️ **🚨 HARD GATE — author writes `select_arm` and `update`**
- Test: `tests/test_linucb.py`

> **Agent**: Do NOT write runnable implementations for the math functions in this section. Write tests, class skeletons, docstrings, and pseudocode only. The author fills in the numpy math.

**2026-05-09 amendment (DEC-003)**: split LinUCB into five author-owned microtasks. Each step should be small enough for the author to explain why every line exists.

#### Task 12.0: LinUCB skeleton

**Files:**
- Create: `bandit/linucb.py`
- Test: `tests/test_linucb.py`

- [ ] **Step 1: Agent writes test skeleton `tests/test_linucb.py`** (agent can write tests)

```python
import numpy as np
from bandit.linucb import LinUCB


def test_initial_state_exploration_dominates():
    """With no data, UCB bonus should push it to pick each arm once."""
    model = LinUCB(arms=["a", "b", "c"], d=4, alpha=1.0)
    ctx = np.array([1.0, 0.5, 0.0, 1.0])
    picks = {model.select_arm(ctx) for _ in range(3)}  # deterministic before updates
    # All arms have equal UCB initially, so any arm is valid — just check it returns a known arm.
    assert model.select_arm(ctx) in {"a", "b", "c"}


def test_update_changes_state():
    model = LinUCB(arms=["a", "b"], d=3, alpha=1.0)
    ctx = np.array([1.0, 0.5, 0.2])
    A_before = model.A["a"].copy()
    model.update("a", ctx, reward=1.0)
    assert not np.array_equal(model.A["a"], A_before)


def test_converges_on_synthetic_good_arm():
    """If arm 'good' always yields reward 1.0 and 'bad' always 0.0, after many updates,
    select_arm should pick 'good' with high probability."""
    rng = np.random.default_rng(42)
    model = LinUCB(arms=["good", "bad"], d=3, alpha=0.5)
    for _ in range(100):
        ctx = rng.random(3)
        model.update("good", ctx, reward=1.0)
        model.update("bad", ctx, reward=0.0)
    # After learning, for random contexts, 'good' should dominate
    picks = [model.select_arm(rng.random(3)) for _ in range(20)]
    assert picks.count("good") >= 16  # 80%
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_linucb.py -v
```

Expected: FAIL — module not found.

- [ ] **Step 3: Agent writes class skeleton in `bandit/linucb.py`** (structure only, NOT method bodies)

```python
"""LinUCB contextual bandit.

⚠️  HARD GATE: select_arm and update bodies must be written by the author.
The skeleton below is a template; author fills in the numpy math.
"""
import numpy as np


class LinUCB:
    def __init__(self, arms: list, d: int, alpha: float = 1.0):
        self.arms = list(arms)
        self.d = d
        self.alpha = alpha
        # Per-arm state: A (d×d), b (d,)
        self.A = {a: np.eye(d) for a in self.arms}
        self.b = {a: np.zeros(d) for a in self.arms}

    def select_arm(self, context_vec: np.ndarray) -> str:
        """TODO (author): compute UCB = theta^T x + alpha * sqrt(x^T A^-1 x) for each arm.
        Return arm with highest UCB.
        """
        raise NotImplementedError("Hard gate: author must implement select_arm")

    def update(self, arm: str, context_vec: np.ndarray, reward: float) -> None:
        """TODO (author): rank-1 update A[arm] += x x^T; b[arm] += reward * x."""
        raise NotImplementedError("Hard gate: author must implement update")
```

- [ ] **Step 4: Run test to verify skeleton raises NotImplementedError**

```bash
pytest tests/test_linucb.py -v
```

Expected: FAIL — `NotImplementedError`. This confirms the skeleton exists.

Commit skeleton:

```bash
git add bandit/linucb.py tests/test_linucb.py
git commit -m "test(linucb): scaffold stepped LinUCB hard gate"
```

#### Task 12.1: `compute_theta(A, b)`

**Hard Gate**: author writes implementation.

Purpose: solve the per-arm linear reward model. In plain language: `theta` is the vector of learned feature weights for one arm.

Formula:

```python
theta = inv(A) @ b
```

Expected author explanation:

> A theta = b is the ridge/least-squares normal-equation form for one arm, so theta = A^-1 b.

Agent may write tests that check:
- with `A = I`, `theta == b`
- returned shape is `(d,)`

Commit:

```bash
git add bandit/linucb.py tests/test_linucb.py
git commit -m "feat(linucb): compute theta weights (self-written)"
```

#### Task 12.2: `predict_mean(theta, x)`

**Hard Gate**: author writes implementation.

Purpose: predict expected reward from context using the learned linear model.

Formula:

```python
mean = theta @ x
```

Expected author explanation:

> Linear prediction is a dot product: each feature contributes weight_i * x_i.

Agent may write tests that check a simple dot-product example.

Commit:

```bash
git add bandit/linucb.py tests/test_linucb.py
git commit -m "feat(linucb): predict mean reward (self-written)"
```

#### Task 12.3: `compute_bonus(A, x, alpha)`

**Hard Gate**: author writes implementation.

Purpose: compute uncertainty for this arm/context pair.

Formula:

```python
bonus = alpha * sqrt(x.T @ inv(A) @ x)
```

Expected author explanation:

> The bonus is larger when the model is less certain for this context. Alpha controls exploration strength.

Agent may write tests that check:
- bonus is non-negative
- higher `alpha` increases bonus
- with `A = I`, bonus equals `alpha * ||x||`

Commit:

```bash
git add bandit/linucb.py tests/test_linucb.py
git commit -m "feat(linucb): compute uncertainty bonus (self-written)"
```

#### Task 12.4: `select_arm(context_vec)`

**Hard Gate**: author writes implementation.

Purpose: compute `mean + bonus` for each arm and return the max.

Expected author explanation:

> LinUCB picks the arm with the highest optimistic reward estimate: predicted mean plus uncertainty bonus.

Agent may write tests using deterministic synthetic state.

Commit:

```bash
git add bandit/linucb.py tests/test_linucb.py
git commit -m "feat(linucb): select arm by UCB score (self-written)"
```

#### Task 12.5: `update(arm, x, reward)`

**Hard Gate**: author writes implementation.

Purpose: update the selected arm after observing reward.

Formula:

```python
A[arm] += outer(x, x)
b[arm] += reward * x
```

Expected author explanation:

> The arm gets more evidence for this context. A tracks feature covariance; b tracks reward-weighted features.

Agent may write tests that check `A` and `b` change for only the selected arm.

Commit:

```bash
git add bandit/linucb.py tests/test_linucb.py
git commit -m "feat(linucb): update selected arm state (self-written)"
```

- [ ] **Final Task 12 validation**

```bash
pytest tests/test_linucb.py -v
```

Expected: all LinUCB tests pass, including synthetic convergence.

- [ ] **Checkpoint**

When skeleton/tests are ready and before author implementation:
```
YYYY-MM-DD HH:MM | Task 12 paused | reason: hard gate — author must implement LinUCB select_arm / update
```

**Author reading material (before implementing):**
- Li et al. 2010 "A Contextual-Bandit Approach to Personalized News Article Recommendation" §3.1 (the LinUCB algorithm box)
- Optional: https://banditalgs.com/2016/09/18/the-upper-confidence-bound-algorithm/

After author completes all five microtasks, append:
```
YYYY-MM-DD HH:MM | Task 12 done | commit <sha> | next: Task 13
```

---

### Task 13: Reward computation

**Files:**
- Create: `bandit/reward.py` ⚠️ **🚨 HARD GATE — author writes the formula**
- Test: `tests/test_reward.py`

- [ ] **Step 1: Agent writes test `tests/test_reward.py`**

```python
from bandit.reward import compute_reward


def test_not_done_is_zero():
    r = compute_reward(done=False, completion=0.0, score=None)
    assert r == 0.0


def test_done_full_high_score_near_one():
    r = compute_reward(done=True, completion=1.0, score=5)
    assert r > 0.95


def test_done_half_mid_score_middle():
    r = compute_reward(done=True, completion=0.5, score=3)
    assert 0.4 < r < 0.8


def test_completion_clamped_to_1():
    r1 = compute_reward(done=True, completion=1.5, score=5)
    r2 = compute_reward(done=True, completion=1.0, score=5)
    assert r1 == r2
```

- [ ] **Step 2: Run to verify fails**

```bash
pytest tests/test_reward.py -v
```

Expected: FAIL.

- [ ] **Step 3: Agent writes skeleton `bandit/reward.py`** (signature only)

```python
"""Reward computation for check-in records.

⚠️  HARD GATE: formula body must be written by the author.
Reference: docs/spec.md §2.3.
"""
from typing import Optional


def compute_reward(done: bool, completion: float, score: Optional[int]) -> float:
    """TODO (author): implement reward formula per spec §2.3.

    reward = 0.4 * done + 0.3 * min(completion, 1.0) + 0.3 * score_normalized
    where score_normalized = (score - 1) / 4 if score else 0.
    """
    raise NotImplementedError("Hard gate: author must implement compute_reward")
```

- [ ] **Step 4: 🚨 HARD GATE — Author implements formula**

**Agent: STOP. Write checkpoint.**

Author implements per spec §2.3. Question author might ask themselves: should I normalize `score` differently? Should I clamp `completion`? Use the test cases as correctness oracle.

- [ ] **Step 5: Author runs test**

```bash
pytest tests/test_reward.py -v
```

Expected: 4 PASSED.

- [ ] **Step 6: Author commits**

```bash
git add bandit/reward.py tests/test_reward.py
git commit -m "feat(reward): implement reward formula (self-written)"
```

---

### Task 14: Persistence — save/load bandit state

**Files:**
- Modify: `bandit/linucb.py` (add `save` / `load` methods)
- Test: `tests/test_linucb.py` (append)

- [ ] **Step 1: Append failing test to `tests/test_linucb.py`**

```python
def test_save_load_roundtrip(tmp_path):
    import numpy as np
    from bandit.linucb import LinUCB
    model = LinUCB(arms=["a", "b"], d=3, alpha=0.5)
    ctx = np.array([1.0, 0.5, 0.2])
    model.update("a", ctx, reward=0.7)
    path = tmp_path / "state.npz"
    model.save(path)

    reloaded = LinUCB.load(path)
    assert reloaded.arms == model.arms
    assert reloaded.d == model.d
    assert reloaded.alpha == model.alpha
    assert np.allclose(reloaded.A["a"], model.A["a"])
    assert np.allclose(reloaded.b["a"], model.b["a"])
```

- [ ] **Step 2: Run to verify fails**

```bash
pytest tests/test_linucb.py::test_save_load_roundtrip -v
```

Expected: FAIL — no `save` method.

- [ ] **Step 3: Agent adds `save` / `load` to `bandit/linucb.py`** (NOT core algorithm — these are IO, soft gate)

```python
# Append to LinUCB class:

    def save(self, path) -> None:
        import numpy as np
        np.savez(path,
                 arms=np.array(self.arms),
                 d=np.array(self.d),
                 alpha=np.array(self.alpha),
                 **{f"A_{a}": self.A[a] for a in self.arms},
                 **{f"b_{a}": self.b[a] for a in self.arms})

    @classmethod
    def load(cls, path) -> "LinUCB":
        import numpy as np
        data = np.load(path, allow_pickle=False)
        arms = list(data["arms"])
        d = int(data["d"])
        alpha = float(data["alpha"])
        model = cls(arms=arms, d=d, alpha=alpha)
        for a in arms:
            model.A[a] = data[f"A_{a}"]
            model.b[a] = data[f"b_{a}"]
        return model
```

- [ ] **Step 4: Run test**

```bash
pytest tests/test_linucb.py -v
```

Expected: all passing.

- [ ] **Step 5: Commit**

```bash
git add bandit/linucb.py tests/test_linucb.py
git commit -m "feat(linucb): save/load state via npz"
```

---

### Task 15: Offline replay training on historical data

**Files:**
- Create: `bandit/train.py`
- Test: `tests/test_train.py`

- [ ] **Step 1: Write failing test `tests/test_train.py`**

```python
from pathlib import Path
from bandit.train import replay_train
from bandit.linucb import LinUCB


def test_replay_updates_model_from_sample_data(tmp_path):
    sample = Path(__file__).parent.parent / "data" / "sample_checkins.json"
    model = replay_train(history_path=sample, alpha=1.0)
    assert isinstance(model, LinUCB)
    # After training, all 6 arms exist in state
    assert set(model.arms) == {"upper_ankle", "lower_ankle", "stretch_ankle",
                               "travel_minimal", "ankle_only", "rest"}
```

- [ ] **Step 2: Run fail**

```bash
pytest tests/test_train.py -v
```

- [ ] **Step 3: Implement `bandit/train.py`** (agent writes — uses author's LinUCB and reward)

```python
"""Offline replay training: iterate historical records and update LinUCB."""
from pathlib import Path

import numpy as np

from bandit.arms import ARM_IDS
from bandit.context import build_context_dict, build_context_vector
from bandit.history import load_from_file, History
from bandit.linucb import LinUCB
from bandit.reward import compute_reward


def replay_train(history_path: Path, alpha: float = 1.0) -> LinUCB:
    history = load_from_file(history_path)
    # Peek at vector dim by building one context
    if not history.records:
        raise ValueError("empty history, cannot train")
    sample_ctx = build_context_dict(history, history.records[0]["date"], travel_mode=False)
    d = build_context_vector(sample_ctx).shape[0]
    model = LinUCB(arms=ARM_IDS, d=d, alpha=alpha)

    # Rebuild a growing history; for each record, compute ctx as-if that day,
    # then update with (arm, reward).
    sub = History(records=[])
    for record in history.records:
        ctx_dict = build_context_dict(sub, record["date"], travel_mode=False)
        vec = build_context_vector(ctx_dict)
        reward = compute_reward(
            done=(record["completion_ratio"] > 0),
            completion=record["completion_ratio"],
            score=record["daily_score"],
        )
        model.update(record["template_id"], vec, reward)
        sub.records.append(record)

    return model
```

- [ ] **Step 4: Run test pass**

```bash
pytest tests/test_train.py -v
```

- [ ] **Step 5: Commit**

```bash
git add bandit/train.py tests/test_train.py
git commit -m "feat(train): offline replay training from check-in history"
```

---

### Task 16: Observer mode — bandit logs predictions but rules decide

**Files:**
- Modify: `bandit/server.py` — add `/recommend` endpoint (rule-based output, bandit logs)
- Create: `bandit/observer.py`
- Test: `tests/test_server.py` (append)

- [ ] **Step 1: Append test to `tests/test_server.py`**

```python
def test_recommend_endpoint_returns_rule_in_observer_mode(tmp_path, monkeypatch):
    import os
    # Point at sample data
    sample = os.path.abspath("data/sample_checkins.json")
    monkeypatch.setenv("BANDIT_HISTORY_PATH", sample)
    monkeypatch.setenv("BANDIT_MODE", "observer")

    from bandit.server import create_app
    app = create_app()
    client = app.test_client()

    r = client.get("/recommend?date=2026-04-28&travel=false")
    assert r.status_code == 200
    assert "arm_id" in r.json
    assert r.json["source"] == "rule"
```

- [ ] **Step 2: Implement `bandit/observer.py`**

```python
"""Bandit observer logger — records what bandit WOULD have picked, for offline analysis."""
import json
from datetime import datetime
from pathlib import Path


def log_observation(path: Path, date: str, rule_pick: str, bandit_pick: str,
                    ctx: dict, ucb_scores: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "logged_at": datetime.utcnow().isoformat(),
        "date": date,
        "rule_pick": rule_pick,
        "bandit_pick": bandit_pick,
        "agreement": rule_pick == bandit_pick,
        "context": ctx,
        "ucb_scores": ucb_scores,
    }
    with path.open("a") as f:
        f.write(json.dumps(entry) + "\n")
```

- [ ] **Step 3: Update `bandit/server.py` to add `/recommend`**

```python
import os
from pathlib import Path

from flask import Flask, jsonify, request

from bandit.arms import get_arm
from bandit.context import build_context_dict, build_context_vector
from bandit.history import load_from_file
from bandit.observer import log_observation
from bandit.rules import rule_recommend
from bandit.train import replay_train


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/recommend")
    def recommend():
        history_path = Path(os.environ.get("BANDIT_HISTORY_PATH", "data/sample_checkins.json"))
        mode = os.environ.get("BANDIT_MODE", "observer")

        date = request.args.get("date")
        travel = request.args.get("travel", "false").lower() == "true"

        history = load_from_file(history_path)
        ctx_dict = build_context_dict(history, date, travel_mode=travel)
        rule_pick = rule_recommend(ctx_dict)

        # Bandit computes its own pick for logging (observer mode)
        try:
            model = replay_train(history_path)
            vec = build_context_vector(ctx_dict)
            bandit_pick = model.select_arm(vec)
            ucb_scores = {}  # optional: expose scores for transparency
        except Exception as e:
            bandit_pick = None
            ucb_scores = {"error": str(e)}

        # Log
        log_path = Path("data/observations.jsonl")
        if bandit_pick is not None:
            log_observation(log_path, date, rule_pick, bandit_pick, ctx_dict, ucb_scores)

        source = "rule" if mode == "observer" else "bandit"
        chosen = rule_pick if source == "rule" else bandit_pick
        arm = get_arm(chosen)

        return jsonify({
            "arm_id": chosen,
            "description": arm["description"],
            "source": source,
            "rule_pick": rule_pick,
            "bandit_pick": bandit_pick,
            "reason": f"distance-based rule (observer mode)" if source == "rule" else "bandit UCB",
        })

    return app


if __name__ == "__main__":
    create_app().run(port=5000, debug=True)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_server.py -v
```

Expected: 2 PASSED.

- [ ] **Step 5: Smoke test with curl**

```bash
BANDIT_HISTORY_PATH=data/sample_checkins.json BANDIT_MODE=observer python -m bandit.server &
sleep 1
curl "http://localhost:5000/recommend?date=2026-04-28&travel=false"
kill %1
cat data/observations.jsonl
```

Expected: JSON with `source: "rule"` and an observation logged.

- [ ] **Step 6: Commit**

```bash
git add bandit/server.py bandit/observer.py tests/test_server.py
git commit -m "feat(server): /recommend in observer mode (rule decides, bandit logs)"
```

---

## Week 3 — Bandit Takes Over + Safety Rail + Override Loop

### Task 17: Safety rail — hard constraints

**Files:**
- Create: `bandit/safety.py`
- Test: `tests/test_safety.py`

- [ ] **Step 1: Write failing test**

```python
from bandit.safety import apply_safety_rail


def test_travel_forces_allowed_set():
    ctx = {"travel_mode": True, "yesterday_score": 4}
    assert apply_safety_rail("lower_ankle", ctx) in {"travel_minimal", "ankle_only"}


def test_travel_passes_through_allowed():
    ctx = {"travel_mode": True, "yesterday_score": 4}
    assert apply_safety_rail("travel_minimal", ctx) == "travel_minimal"


def test_non_travel_passes_through():
    ctx = {"travel_mode": False, "yesterday_score": 4}
    assert apply_safety_rail("lower_ankle", ctx) == "lower_ankle"
```

- [ ] **Step 2: Run fail**

```bash
pytest tests/test_safety.py -v
```

- [ ] **Step 3: Implement `bandit/safety.py`**

```python
"""Safety rail: override bandit picks that violate hard constraints."""

TRAVEL_ALLOWED = {"travel_minimal", "ankle_only", "rest"}


def apply_safety_rail(bandit_pick: str, ctx: dict) -> str:
    if ctx.get("travel_mode") and bandit_pick not in TRAVEL_ALLOWED:
        return "travel_minimal"
    return bandit_pick
```

- [ ] **Step 4: Run pass**

```bash
pytest tests/test_safety.py -v
```

- [ ] **Step 5: Commit**

```bash
git add bandit/safety.py tests/test_safety.py
git commit -m "feat(safety): hard constraint rail (travel mode forces allowed arms)"
```

---

### Task 18: Switch `/recommend` to bandit mode + safety rail

**Files:**
- Modify: `bandit/server.py`

- [ ] **Step 1: Update `/recommend` in `bandit/server.py`**

Replace the `source` / `chosen` logic block with:

```python
        from bandit.safety import apply_safety_rail

        if mode == "bandit" and bandit_pick is not None:
            chosen = apply_safety_rail(bandit_pick, ctx_dict)
            source = "bandit" if chosen == bandit_pick else "safety_rail"
        else:
            chosen = rule_pick
            source = "rule"

        arm = get_arm(chosen)
        return jsonify({
            "arm_id": chosen,
            "description": arm["description"],
            "source": source,
            "rule_pick": rule_pick,
            "bandit_pick": bandit_pick,
            "reason": _explain(source, chosen, rule_pick, bandit_pick, ctx_dict),
        })
```

- [ ] **Step 2: Add `_explain` helper at bottom of `bandit/server.py`**

```python
def _explain(source: str, chosen: str, rule_pick: str, bandit_pick: str, ctx: dict) -> str:
    if source == "bandit":
        return f"bandit UCB (context: travel={ctx['travel_mode']}, score={ctx['yesterday_score']})"
    if source == "safety_rail":
        return f"safety rail overrode bandit→{bandit_pick} (reason: travel mode)"
    return f"rule fallback"
```

- [ ] **Step 3: Add test for bandit mode**

Append to `tests/test_server.py`:

```python
def test_recommend_bandit_mode_returns_bandit_pick(monkeypatch):
    import os
    monkeypatch.setenv("BANDIT_HISTORY_PATH", os.path.abspath("data/sample_checkins.json"))
    monkeypatch.setenv("BANDIT_MODE", "bandit")

    from bandit.server import create_app
    app = create_app()
    r = app.test_client().get("/recommend?date=2026-04-28&travel=false")
    assert r.status_code == 200
    assert r.json["source"] in {"bandit", "safety_rail"}


def test_recommend_travel_forces_safe_arm(monkeypatch):
    import os
    monkeypatch.setenv("BANDIT_HISTORY_PATH", os.path.abspath("data/sample_checkins.json"))
    monkeypatch.setenv("BANDIT_MODE", "bandit")
    from bandit.server import create_app
    r = create_app().test_client().get("/recommend?date=2026-04-28&travel=true")
    assert r.json["arm_id"] in {"travel_minimal", "ankle_only", "rest"}
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_server.py -v
```

Expected: 4 PASSED.

- [ ] **Step 5: Commit**

```bash
git add bandit/server.py tests/test_server.py
git commit -m "feat(server): bandit mode + safety rail integration"
```

---

### Task 19: `/feedback` endpoint — collect override + completion reward

**Files:**
- Modify: `bandit/server.py`
- Test: `tests/test_server.py`

- [ ] **Step 1: Append test**

```python
def test_feedback_endpoint_stores_record(tmp_path, monkeypatch):
    import os
    monkeypatch.setenv("BANDIT_FEEDBACK_LOG", str(tmp_path / "feedback.jsonl"))
    from bandit.server import create_app
    app = create_app()
    payload = {
        "date": "2026-04-28",
        "recommended_arm": "lower_ankle",
        "chosen_arm": "stretch_ankle",
        "was_override": True,
        "override_reason": "太累",
        "completion_ratio": 0.67,
        "daily_score": 3,
    }
    r = app.test_client().post("/feedback", json=payload)
    assert r.status_code == 200
    # Verify written
    content = (tmp_path / "feedback.jsonl").read_text()
    assert "太累" in content
```

- [ ] **Step 2: Add `/feedback` route in `bandit/server.py`**

```python
    @app.route("/feedback", methods=["POST"])
    def feedback():
        import json
        from datetime import datetime
        payload = request.get_json()
        required = {"date", "recommended_arm", "chosen_arm",
                    "was_override", "completion_ratio", "daily_score"}
        missing = required - set(payload.keys())
        if missing:
            return jsonify({"error": f"missing fields: {missing}"}), 400

        log_path = Path(os.environ.get("BANDIT_FEEDBACK_LOG", "data/feedback.jsonl"))
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {"logged_at": datetime.utcnow().isoformat(), **payload}
        with log_path.open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return jsonify({"status": "logged"})
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_server.py -v
```

Expected: 5 PASSED.

- [ ] **Step 4: Commit**

```bash
git add bandit/server.py tests/test_server.py
git commit -m "feat(server): /feedback endpoint for override + completion logging"
```

---

### Task 20: Frontend — override modal + call /feedback

**In rehab app repo, not here.** Copy-paste task for author.

- [ ] **Step 1: Override button handler**

```javascript
document.getElementById('override-btn').onclick = () => {
  const modal = document.getElementById('override-modal');
  modal.classList.remove('hidden');
};
```

- [ ] **Step 2: Override modal HTML**

```html
<div id="override-modal" class="modal hidden">
  <h3>换一个？</h3>
  <select id="override-arm">
    <option value="upper_ankle">上肢日+踝</option>
    <option value="lower_ankle">下肢日+踝</option>
    <option value="stretch_ankle">拉伸+踝</option>
    <option value="travel_minimal">旅行最小化</option>
    <option value="ankle_only">只做踝</option>
    <option value="rest">休息</option>
  </select>
  <h4>原因</h4>
  <div class="reasons">
    <button data-reason="太累">太累</button>
    <button data-reason="想换口味">想换口味</button>
    <button data-reason="没时间">没时间</button>
    <button data-reason="身体不适">身体不适</button>
    <button data-reason="旅行">旅行</button>
    <button data-reason="其他">其他</button>
  </div>
</div>
```

- [ ] **Step 3: Submit override + build check-in with override metadata**

```javascript
document.querySelectorAll('#override-modal .reasons button').forEach(btn => {
  btn.onclick = async () => {
    const chosenArm = document.getElementById('override-arm').value;
    const reason = btn.dataset.reason;
    window.currentCheckin = {
      ...window.currentCheckin,
      template_id: chosenArm,
      was_override: true,
      overridden_from: window.currentRecommendation.arm_id,
      override_reason: reason,
    };
    document.getElementById('override-modal').classList.add('hidden');
    // Proceed to exercise list for chosenArm
  };
});
```

- [ ] **Step 4: Post /feedback when check-in completes**

```javascript
async function submitFeedback(checkin) {
  await fetch('http://localhost:5000/feedback', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      date: checkin.date,
      recommended_arm: window.currentRecommendation.arm_id,
      chosen_arm: checkin.template_id,
      was_override: checkin.was_override,
      override_reason: checkin.override_reason || null,
      completion_ratio: checkin.completion_ratio,
      daily_score: checkin.daily_score,
    }),
  });
}
```

- [ ] **Step 5: Commit in rehab app repo**

```bash
git add index.html app.js style.css
git commit -m "feat: override modal + bandit feedback"
```

---

### Task 21: Smoke test — end-to-end replay from real history

**Files:**
- Create: `scripts/simulate_replay.py`

- [ ] **Step 1: Write `scripts/simulate_replay.py`**

```python
"""Replay historical records: show what bandit WOULD have picked each day."""
import argparse
from pathlib import Path

from bandit.arms import ARM_IDS
from bandit.context import build_context_dict, build_context_vector
from bandit.history import load_from_file, History
from bandit.linucb import LinUCB
from bandit.reward import compute_reward


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", default="data/sample_checkins.json")
    parser.add_argument("--alpha", type=float, default=1.0)
    args = parser.parse_args()

    history = load_from_file(Path(args.history))
    sub = History(records=[])

    # Determine d
    sample = build_context_dict(history, history.records[0]["date"], travel_mode=False)
    d = build_context_vector(sample).shape[0]
    model = LinUCB(arms=ARM_IDS, d=d, alpha=args.alpha)

    print(f"{'date':<12}{'actual':<18}{'bandit would pick':<22}{'agree':<8}{'reward':<8}")
    print("-" * 70)
    agreements = 0
    total = 0
    for record in history.records:
        ctx = build_context_dict(sub, record["date"], travel_mode=False)
        vec = build_context_vector(ctx)
        bandit_pick = model.select_arm(vec)
        reward = compute_reward(
            done=record["completion_ratio"] > 0,
            completion=record["completion_ratio"],
            score=record["daily_score"],
        )
        actual = record["template_id"]
        agree = "✓" if bandit_pick == actual else "✗"
        agreements += int(bandit_pick == actual)
        total += 1
        print(f"{record['date']:<12}{actual:<18}{bandit_pick:<22}{agree:<8}{reward:.2f}")
        model.update(actual, vec, reward)
    print("-" * 70)
    if total:
        print(f"agreement rate: {agreements/total:.1%} ({agreements}/{total})")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

```bash
python scripts/simulate_replay.py --history data/sample_checkins.json
```

Expected: table of date / actual / bandit pick / agreement. Low agreement early (high exploration), should trend up with more data.

- [ ] **Step 3: Commit**

```bash
git add scripts/simulate_replay.py
git commit -m "feat(scripts): historical replay simulation"
```

---

## Week 4 — Stats, Tuning, Retrospective

### Task 22: Stats endpoint — per-arm metrics

**Files:**
- Modify: `bandit/server.py` — add `/stats`
- Test: `tests/test_server.py` (append)

- [ ] **Step 1: Append test**

```python
def test_stats_endpoint(monkeypatch):
    import os
    monkeypatch.setenv("BANDIT_HISTORY_PATH", os.path.abspath("data/sample_checkins.json"))
    from bandit.server import create_app
    r = create_app().test_client().get("/stats")
    assert r.status_code == 200
    assert "per_arm" in r.json
    assert "override_rate" in r.json
```

- [ ] **Step 2: Add route**

```python
    @app.route("/stats")
    def stats():
        history_path = Path(os.environ.get("BANDIT_HISTORY_PATH", "data/sample_checkins.json"))
        history = load_from_file(history_path)

        per_arm = {}
        for arm_id in ARM_IDS:
            records = [r for r in history.records if r["template_id"] == arm_id]
            if not records:
                per_arm[arm_id] = {"count": 0, "avg_reward": None, "avg_score": None}
                continue
            from bandit.reward import compute_reward
            rewards = [compute_reward(r["completion_ratio"] > 0,
                                      r["completion_ratio"],
                                      r["daily_score"]) for r in records]
            scores = [r["daily_score"] for r in records if r["daily_score"] is not None]
            per_arm[arm_id] = {
                "count": len(records),
                "avg_reward": sum(rewards) / len(rewards),
                "avg_score": sum(scores) / len(scores) if scores else None,
            }

        overrides = sum(1 for r in history.records if r.get("was_override"))
        override_rate = overrides / len(history.records) if history.records else 0.0

        return jsonify({"per_arm": per_arm, "override_rate": override_rate,
                        "total_checkins": len(history.records)})
```

- [ ] **Step 3: Import `ARM_IDS` at top of `bandit/server.py`**

```python
from bandit.arms import ARM_IDS, get_arm
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_server.py -v
```

- [ ] **Step 5: Commit**

```bash
git add bandit/server.py tests/test_server.py
git commit -m "feat(server): /stats endpoint with per-arm metrics"
```

---

### Task 23: Frontend — `/stats` page (rehab app repo)

**In rehab app repo.** Simple HTML + fetch.

- [ ] **Step 1: Create `stats.html` in rehab app repo**

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Bandit Stats</title></head>
<body>
  <h1>Bandit Learning Stats</h1>
  <div id="summary"></div>
  <table id="arms-table">
    <thead><tr><th>Arm</th><th>Count</th><th>Avg Reward</th><th>Avg Score</th></tr></thead>
    <tbody></tbody>
  </table>
  <script>
  (async () => {
    const res = await fetch('http://localhost:5000/stats');
    const s = await res.json();
    document.getElementById('summary').textContent =
      `Total check-ins: ${s.total_checkins} | Override rate: ${(s.override_rate*100).toFixed(1)}%`;
    const tbody = document.querySelector('#arms-table tbody');
    for (const [arm, v] of Object.entries(s.per_arm)) {
      const row = tbody.insertRow();
      row.innerHTML = `<td>${arm}</td><td>${v.count}</td><td>${v.avg_reward?.toFixed(2) ?? '-'}</td><td>${v.avg_score?.toFixed(1) ?? '-'}</td>`;
    }
  })();
  </script>
</body>
</html>
```

- [ ] **Step 2: Commit in rehab app repo**

```bash
git add stats.html
git commit -m "feat: bandit stats dashboard"
```

---

### Task 24: Reward tuning script

**Files:**
- Create: `scripts/tune_reward.py`

- [ ] **Step 1: Write `scripts/tune_reward.py`**

```python
"""Experiment with reward weights without modifying production code.

Usage: python scripts/tune_reward.py --w_done 0.5 --w_completion 0.3 --w_score 0.2
"""
import argparse
from pathlib import Path

from bandit.history import load_from_file
from bandit.arms import ARM_IDS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", default="data/sample_checkins.json")
    parser.add_argument("--w_done", type=float, default=0.4)
    parser.add_argument("--w_completion", type=float, default=0.3)
    parser.add_argument("--w_score", type=float, default=0.3)
    args = parser.parse_args()

    assert abs(args.w_done + args.w_completion + args.w_score - 1.0) < 0.01, \
        "weights must sum to 1"

    def custom_reward(done, completion, score):
        s_norm = (score - 1) / 4 if score else 0
        return args.w_done * (1 if done else 0) \
             + args.w_completion * min(completion, 1.0) \
             + args.w_score * s_norm

    history = load_from_file(Path(args.history))
    per_arm = {a: [] for a in ARM_IDS}
    for r in history.records:
        reward = custom_reward(r["completion_ratio"] > 0, r["completion_ratio"], r["daily_score"])
        per_arm[r["template_id"]].append(reward)

    print(f"Weights: done={args.w_done}, completion={args.w_completion}, score={args.w_score}")
    for arm, rewards in per_arm.items():
        if rewards:
            print(f"  {arm:<18} n={len(rewards)} avg_reward={sum(rewards)/len(rewards):.3f}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run tuning experiment**

```bash
python scripts/tune_reward.py --w_done 0.4 --w_completion 0.3 --w_score 0.3
python scripts/tune_reward.py --w_done 0.5 --w_completion 0.3 --w_score 0.2
python scripts/tune_reward.py --w_done 0.6 --w_completion 0.2 --w_score 0.2
```

Compare avg rewards across weightings. Commit the findings in a new file `docs/reward_tuning_notes.md`.

- [ ] **Step 3: Commit**

```bash
git add scripts/tune_reward.py docs/reward_tuning_notes.md
git commit -m "feat(scripts): reward weight tuning experiment"
```

---

### Task 25: Checkpoint log format + status script

**Files:**
- Create: `docs/checkpoint.md` (template)
- Create: `scripts/status.py`

- [ ] **Step 1: Create `docs/checkpoint.md`**

```markdown
# Work Checkpoint Log

One line per session. Append to bottom.

## Format
`YYYY-MM-DD HH:MM | Task N done|paused | <commit sha or reason> | next: Task M`

## Log

(entries appended below)
```

- [ ] **Step 2: Create `scripts/status.py`**

```python
"""Quick status check — run when resuming after a break."""
from pathlib import Path


def main():
    print("=== Rehab Bandit Project Status ===\n")

    ckpt = Path("docs/checkpoint.md")
    if ckpt.exists():
        lines = [l for l in ckpt.read_text().splitlines() if l.startswith("20")]
        if lines:
            print(f"Last checkpoint: {lines[-1]}\n")

    sample = Path("data/sample_checkins.json")
    if sample.exists():
        import json
        data = json.loads(sample.read_text())
        print(f"Check-in records: {len(data)}")
        if data:
            print(f"  date range: {data[0]['date']} → {data[-1]['date']}")

    state = Path("data/bandit_state.npz")
    print(f"\nBandit state file: {'exists' if state.exists() else 'not yet saved'}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run it**

```bash
python scripts/status.py
```

- [ ] **Step 4: Commit**

```bash
git add docs/checkpoint.md scripts/status.py
git commit -m "chore: checkpoint log + resume-status script"
```

---

### Task 26: Retrospective write-up

**Files:**
- Create: `docs/retro.md`

- [ ] **Step 1: Write `docs/retro.md` — free-form**

Template:

```markdown
# 4-Week Retro: Rehab Bandit

## What shipped
- ...

## What I learned about RL
- LinUCB vs Epsilon-greedy: [in my own words]
- Exploration bonus as confidence interval: [my understanding]
- Off-policy learning in Phase 1.5: [my understanding]

## What surprised me
- ...

## What I'd do differently
- ...

## Success criteria check
- [ ] Can explain LinUCB vs Epsilon-greedy in 3 min? (try it into a voice memo)
- [ ] Debugged a "bad recommendation" case? Write it up below
- [ ] Tuned reward and observed behavior change? Link to `reward_tuning_notes.md`
- [ ] Agreement rate > 60% after 4 weeks? (check /stats)

## What's next
- Route A / B / C from spec §11, or something else?
```

- [ ] **Step 2: Fill it in honestly after 4 weeks of running.**

- [ ] **Step 3: Commit**

```bash
git add docs/retro.md
git commit -m "docs: 4-week retrospective"
```

---

## Appendix A: Suggested Learning Resources (before W2)

- **LinUCB paper §3.1**: Li et al. 2010 "A Contextual-Bandit Approach to Personalized News Article Recommendation" (search on arxiv)
- **Bandit algorithms blog**: https://banditalgs.com/2016/09/18/the-upper-confidence-bound-algorithm/
- **Sutton & Barto Ch 2** (for general bandit intuition)

## Appendix B: Common Bugs in LinUCB (heads-up for author)

1. **Matrix orientation**: `np.outer(x, x)` not `x @ x.T` if `x` is 1-D
2. **`alpha` too high**: pure exploration forever; start at 1.0, lower to 0.5 if picks look random
3. **Forgetting to normalize features**: if `days_since` can be 999 and `travel_mode` is 0/1, the large feature dominates. Normalize features roughly to similar scale.

## Appendix C: Running the Stack Locally

```bash
# 1. Start bandit service
source .venv/bin/activate
BANDIT_MODE=bandit BANDIT_HISTORY_PATH=data/sample_checkins.json python -m bandit.server

# 2. Open rehab app (in another terminal / browser)
# The app will call http://localhost:5000/recommend on load
```

---

**End of implementation plan.**
