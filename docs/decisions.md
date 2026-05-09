# Decisions Log

ADR-style records of non-obvious architectural decisions. Newest first. Each entry: 1–3 short paragraphs. Reference the ID in commit messages (`feat(x): ... (DEC-001)`).

---

## DEC-003 — Keep arms stable; reduce initial context vector

**Date**: 2026-05-09
**Status**: accepted

**Problem**: The 2026-05-09 return-to-training session suggests the user's body state is shifting from ankle-primary rehab toward shoulder rehab and broader strength return. This raises a real question about whether the original six arms are still the right taxonomy. At the same time, the project is currently paused at the Task 11 hard gate (`build_context_vector`), before any LinUCB model has run.

**Decision**: do not rename or replace the six arms yet. First get a minimal LinUCB path working with the existing arms. Reduce the initial context vector by excluding `weekday` from `build_context_vector()`, while leaving `weekday` available in `build_context_dict()` for future use.

**Why**: changing arms before the first working model would move the learning target again and increase the chance of another design loop. Removing `weekday` lowers dimensionality and removes one encoding decision. If a weekday pattern appears after 3+ weeks of data, it can be added back.

---

## DEC-002 — Treat return-test and transition sessions as out-of-distribution

**Date**: 2026-05-09
**Status**: accepted

**Problem**: Some real sessions, including the 2026-05-09 return-to-training / power-test session, do not fit the six normal daily rehab arms. Forcing these records into bandit training would create noisy samples: the session is valuable body history, but not evidence that one of the normal arms succeeded or failed.

**Decision**: add the concept of optional `session_type` labels. If a future frontend record has a `session_type` beginning with `ood_` (for example `ood_power_test`, `ood_shoulder_pt`, `ood_agility`), the bandit adapter/training path should skip it. The record should remain in the frontend history for retrospective analysis.

**Migration trigger**: if one OOD category reaches 5+ records and persists for 2+ weeks, review whether the six-arm taxonomy or schema should change. Until then, collect the data without teaching LinUCB from it.

---

## DEC-001 — rehab data ingested via adapter, not direct schema match

**Date**: 2026-05-02
**Status**: accepted

**Problem**: `rehab/` (frontend) writes check-in JSON with field names that diverge from `bandit/schema.py`'s internal v2 schema:

| bandit v2 (this repo) | rehab v1 (frontend) |
|---|---|
| `schema_version` (snake) = `2` | `schemaVersion` (camel) = `1` |
| `daily_score` | `feedback_score` |
| `was_override` (bool) | (absent — derivable from `template_id !== suggested_template_id`) |
| `completion_ratio` (float) | (absent — derivable from `exercises[].completedSets / plannedSets`) |

A previous fix (commit `98182fe`) tried to filter records by `"schema_version" in r`, but rehab uses the camelCase `schemaVersion`, so that filter dropped *every* real frontend record. Also: rehab's records went through three schema eras; only Era 3 (post-04-29, with `feedback_score`+`template_id`) carries enough signal to be a bandit training sample.

**Decision**: introduce `bandit/rehab_adapter.py`. It converts a rehab v1 raw dict → a bandit v2 dict, or returns `None` when the record is not bandit-ready (no `schemaVersion`, no `feedback_score`, or no `template_id`). `bandit/schema.py` remains the canonical contract for what bandit consumes downstream. The frontend repo is **not** modified.

**Why not match rehab's schema directly**: the frontend will keep evolving. If bandit's schema is whatever rehab happens to write, every frontend tweak ripples into bandit code and tests. The adapter is the seam — frontend changes touch only the adapter.

**Why drop Era 1/2 records instead of backfilling**: records without `feedback_score` carry no reward signal (the formula's 0.3 weight on subjective rating). Synthesizing a placeholder rating to make them pass validation would feed garbage to LinUCB. Records without `template_id` can't even contribute to context features (`days_since_<arm>`). Dropping is honest.

**Consequence**:
- New entry point: `bandit/history.load_from_rehab_dir(path)` — reads `rehab/data/sessions/*.json`, calls adapter per file, validates v2 output, sorts by date.
- `bandit/history.load_from_file(path)` retains v2-only semantics for `data/sample_checkins.json`.
- The misnamed filter from `98182fe` is reverted in this same change.

**Author manual work removed**: previously the author was going to backfill `was_override` and `schema_version` into rehab records by hand. That is no longer necessary — the adapter computes those fields from data the frontend already writes.
