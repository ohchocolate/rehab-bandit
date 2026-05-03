# Decisions Log

ADR-style records of non-obvious architectural decisions. Newest first. Each entry: 1–3 short paragraphs. Reference the ID in commit messages (`feat(x): ... (DEC-001)`).

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
