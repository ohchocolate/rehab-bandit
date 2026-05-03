"""Translate rehab frontend v1 raw JSON to bandit-internal v2 schema.

See docs/decisions.md DEC-001 for rationale.
"""
from typing import Optional

REHAB_SCHEMA_VERSION = 1


def adapt(raw: dict) -> Optional[dict]:
    """rehab v1 record → bandit v2 dict, or None if not bandit-ready.

    Rejected:
      - records without `schemaVersion` (Era 1 — pre-v1 frontend)
      - records without `feedback_score` (no reward signal, Era 2)
      - records without `template_id` (can't contribute to features)
    """
    if raw.get("schemaVersion") != REHAB_SCHEMA_VERSION:
        return None
    if raw.get("feedback_score") is None:
        return None
    template = raw.get("template_id")
    if not template:
        return None

    suggested = raw.get("suggested_template_id")
    was_override = bool(suggested) and suggested != template

    return {
        "date": raw["date"],
        "template_id": template,
        "exercises": raw.get("exercises", []),
        "completion_ratio": _completion_ratio(raw.get("exercises", [])),
        "daily_score": raw["feedback_score"],
        "was_override": was_override,
        "overridden_from": suggested if was_override else None,
        "override_reason": None,
        "schema_version": 2,
    }


def _completion_ratio(exercises: list) -> float:
    if not exercises:
        return 0.0
    planned = sum(e.get("plannedSets", 0) for e in exercises)
    if planned == 0:
        return 0.0
    completed = sum(e.get("completedSets", 0) for e in exercises)
    return min(completed / planned, 1.0)
