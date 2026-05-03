# AGENTS.md

> Shared source of truth for AI assistants (Claude Code, Codex, etc.) collaborating on this repo.
> **Read order on every new session**: this file → `docs/decisions.md` → `docs/checkpoint.md` (last entry) → `docs/plan.md` (next unchecked task).

## Repos in play

- **`rehab-bandit/`** (this repo) — Python bandit service. Reads check-ins, recommends a daily template.
- **`rehab/`** (sibling, separate repo at `../rehab`) — Vanilla JS frontend. Author logs daily check-ins. Writes JSON files to `rehab/data/sessions/<date>.json`.

The bandit reads frontend output **through `bandit/rehab_adapter.py`** (see DEC-001). It does NOT write to the frontend repo.

## Hard Gate (do NOT implement)

Reserved for the human author. Assistants may write pseudocode, explain concepts, generate tests, or review the author's code — **but must not write runnable implementations** of these:

- `bandit/linucb.py` — `select_arm()`, `update()`
- `bandit/reward.py` — reward formula
- `bandit/context.py` — final context-vector assembly

If a task lands in one of these files: stop, log a checkpoint note `"paused: hard gate on <file>"`, exit. Wait for the author to push their implementation.

Author's rule: **"If you can't explain why a line is there, don't write it for them."**

## Soft Gate (assistants OK)

- Adapters, loaders, validators, schema definitions
- Tests (incl. tests for Hard Gate files — assistant can write tests, author writes the implementation under test)
- CLI, Flask routes, JSON IO, persistence helpers
- Concept explanations (UCB, confidence interval, off-policy, etc.)
- Code review of author's work

## Coordination protocol

1. **Before starting**: read `docs/checkpoint.md` (last line tells you what was last done and what's next), `docs/decisions.md` (any new DEC- entries since last session), then the next task in `docs/plan.md`.
2. **One task at a time**: finish, run tests, commit, append one line to `docs/checkpoint.md`, **stop**. Do not chain multiple tasks unsupervised.
3. **Commit message convention**: `<type>(<scope>): <summary>`. If the change implements a recorded decision, reference it: `feat(adapter): rehab v1 → v2 (DEC-001)`.
4. **New architectural decisions**: append to `docs/decisions.md` *before or alongside* the code change. Reference the DEC ID in the commit message.
5. **File ownership conflict** (two agents editing the same file across sessions): later agent must `git pull && git log` to see what landed before re-editing. If the prior commit is wrong (e.g. wrong field name), document the supersession in the new DEC entry.

## Hard Gate violations: how to recover

If you accidentally wrote runnable code in a Hard Gate file (or get caught about to):
1. `git restore <file>` — discard the change.
2. Append a checkpoint note: `paused: attempted hard-gate write on <file>, reverted`.
3. Reply to the user with pseudocode + an explanation of what they need to write themselves.

## Source-of-truth pointers

- **What to do next** → `docs/plan.md` first unchecked `- [ ]` after the last completed task in `docs/checkpoint.md`
- **Why it's designed this way** → `docs/spec.md` (high-level), `docs/decisions.md` (specific tradeoffs)
- **What's been done** → `git log --oneline` + `docs/checkpoint.md`
- **Personal style/tone for one specific assistant** → `CLAUDE.md` (Claude Code only) or equivalent per-agent file
