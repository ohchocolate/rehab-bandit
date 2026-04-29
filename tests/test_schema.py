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
