import json
from pathlib import Path

from bandit.rehab_adapter import adapt
from bandit.schema import validate_checkin


def _era3_record(**overrides):
    """A complete frontend v1 record (post-2026-04-29 era)."""
    base = {
        "date": "2026-04-30",
        "schemaVersion": 1,
        "streak": 9,
        "checkin_time": "2026-05-01T01:00:00Z",
        "modules": ["ankle"],
        "exercises": [
            {"id": "ankle-1", "plannedSets": 3, "completedSets": 3, "completed": True},
            {"id": "ankle-5", "plannedSets": 2, "completedSets": 1, "completed": False},
        ],
        "template_id": "ankle_only",
        "suggested_template_id": "ankle_only",
        "travel_mode": False,
        "feedback_score": 4,
    }
    base.update(overrides)
    return base


def test_era3_record_adapts_and_passes_v2_validator():
    out = adapt(_era3_record())
    assert out is not None
    validate_checkin(out)
    assert out["template_id"] == "ankle_only"
    assert out["daily_score"] == 4
    assert out["schema_version"] == 2


def test_era1_record_rejected_no_schema_version():
    raw = {"date": "2026-04-21", "exercises": []}
    assert adapt(raw) is None


def test_era2_record_rejected_no_feedback_score():
    raw = _era3_record(feedback_score=None)
    raw.pop("template_id", None)
    raw.pop("suggested_template_id", None)
    assert adapt(raw) is None


def test_no_template_id_rejected():
    raw = _era3_record()
    raw["template_id"] = None
    assert adapt(raw) is None


def test_override_detected():
    raw = _era3_record(template_id="ankle_only", suggested_template_id="lower_ankle")
    out = adapt(raw)
    assert out["was_override"] is True
    assert out["overridden_from"] == "lower_ankle"


def test_no_override_when_template_matches_suggestion():
    raw = _era3_record(template_id="ankle_only", suggested_template_id="ankle_only")
    out = adapt(raw)
    assert out["was_override"] is False
    assert out["overridden_from"] is None


def test_no_override_when_no_suggestion():
    raw = _era3_record(template_id="ankle_only", suggested_template_id=None)
    out = adapt(raw)
    assert out["was_override"] is False
    assert out["overridden_from"] is None


def test_completion_ratio_full():
    raw = _era3_record(exercises=[
        {"plannedSets": 3, "completedSets": 3},
        {"plannedSets": 2, "completedSets": 2},
    ])
    out = adapt(raw)
    assert out["completion_ratio"] == 1.0


def test_completion_ratio_partial():
    raw = _era3_record(exercises=[
        {"plannedSets": 4, "completedSets": 2},
        {"plannedSets": 2, "completedSets": 1},
    ])
    # (2 + 1) / (4 + 2) = 0.5
    assert adapt(raw)["completion_ratio"] == 0.5


def test_completion_ratio_capped_at_one():
    raw = _era3_record(exercises=[
        {"plannedSets": 2, "completedSets": 5},  # over-performed
    ])
    assert adapt(raw)["completion_ratio"] == 1.0


def test_completion_ratio_empty_exercises():
    raw = _era3_record(exercises=[])
    assert adapt(raw)["completion_ratio"] == 0.0


def test_completion_ratio_zero_planned_no_div_by_zero():
    raw = _era3_record(exercises=[{"plannedSets": 0, "completedSets": 0}])
    assert adapt(raw)["completion_ratio"] == 0.0


def test_real_rehab_file_e2e():
    """Sanity check against a real frontend file, if present."""
    p = Path("/Users/zhong/Documents/rehab/data/sessions/2026-05-01.json")
    if not p.exists():
        return  # frontend repo absent on this machine; skip
    raw = json.loads(p.read_text())
    out = adapt(raw)
    if raw.get("feedback_score") is not None and raw.get("template_id"):
        assert out is not None
        validate_checkin(out)
