# Rehab Bandit

A contextual-bandit service for personal rehab plan recommendations.

This project learns from real daily check-in data produced by the sibling [`rehab`](../rehab) app. The goal is to recommend one of a small set of rehab/training templates each day, using lightweight reinforcement-learning ideas without turning the project into a heavyweight ML system.

## Why This Exists

The frontend rehab app already records what happened each day: which template was trained, whether the user was traveling, how much was completed, and how the session felt.

`rehab-bandit` turns that history into a recommendation loop:

```text
history + context -> recommended template -> check-in -> reward -> updated model
```

The project is also a learning track: the core LinUCB algorithm and reward formula are intentionally reserved for the author to implement by hand.

## Current Status

Completed:

- Project scaffolding
- Six daily-plan arms
- v2 check-in schema validation
- Local history loader
- Phase-1 rule-based recommender
- CLI recommendation smoke test
- Flask `/health` service skeleton

Next:

- Context feature extraction
- LinUCB skeleton and tests
- Reward computation
- Offline replay training
- `/recommend` observer mode

See `docs/checkpoint.md` for the task log and `docs/plan.md` for the full implementation plan.

## Recommendation Arms

The bandit chooses among six daily templates:

- `upper_ankle` - upper body + ankle rehab
- `lower_ankle` - lower body + ankle rehab
- `stretch_ankle` - mobility/stretch + ankle rehab
- `travel_minimal` - hotel/floor-friendly minimal plan
- `ankle_only` - ankle PT only
- `rest` - rest day

The bandit does not invent exercises. It chooses a template; the frontend app owns the actual exercise content.

## Learning Plan

The rollout is intentionally staged:

1. **Phase 1: Rules only**
   - Use simple rules to recommend templates.
   - Collect real check-in data.

2. **Phase 1.5: Observer mode**
   - Rules still decide.
   - Bandit trains in the background and logs what it would have picked.

3. **Phase 2: Bandit mode with safety rail**
   - LinUCB recommends.
   - Hard constraints still override unsafe picks, such as travel-mode restrictions.

4. **Phase 3: Stats and tuning**
   - Inspect per-arm reward, override rate, and learning behavior.

## Hard Gate

This is a learning project. AI assistants may scaffold, test, review, and debug, but must not directly implement the core learning code.

Reserved for the author:

- `bandit/linucb.py`: `select_arm()` and `update()`
- `bandit/reward.py`: reward formula
- `bandit/context.py`: final context-vector assembly

Assistants may write tests, Flask routes, JSON IO, persistence helpers, and review feedback.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## CLI Smoke Test

```bash
python -m bandit today --history data/sample_checkins.json --date 2026-04-28
```

Travel mode:

```bash
python -m bandit today --history data/sample_checkins.json --travel
```

## Server Smoke Test

```bash
python -m bandit.server
curl http://127.0.0.1:5000/health
```

Expected:

```json
{"status": "ok"}
```

## Project Docs

- `docs/spec.md` - system design and RL plan
- `docs/plan.md` - task-by-task implementation plan
- `docs/checkpoint.md` - progress log
- `CLAUDE.md` - AI assistant collaboration rules
