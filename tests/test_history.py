import json
from pathlib import Path

from bandit.history import History, load_from_file, load_from_rehab_dir


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


def test_load_from_rehab_dir_filters_and_sorts(tmp_path):
    """Mixed-era directory: only Era 3 records survive, sorted by date."""
    # Era 3 — full v1 record, will adapt
    (tmp_path / "2026-04-30.json").write_text(json.dumps({
        "date": "2026-04-30",
        "schemaVersion": 1,
        "exercises": [{"plannedSets": 2, "completedSets": 2}],
        "template_id": "ankle_only",
        "suggested_template_id": "ankle_only",
        "travel_mode": False,
        "feedback_score": 4,
    }))
    # Era 3 — earlier date, also valid
    (tmp_path / "2026-04-29.json").write_text(json.dumps({
        "date": "2026-04-29",
        "schemaVersion": 1,
        "exercises": [{"plannedSets": 3, "completedSets": 3}],
        "template_id": "lower_ankle",
        "suggested_template_id": "upper_ankle",
        "travel_mode": False,
        "feedback_score": 3,
    }))
    # Era 2 — schemaVersion=1 but no feedback_score → dropped
    (tmp_path / "2026-04-25.json").write_text(json.dumps({
        "date": "2026-04-25",
        "schemaVersion": 1,
        "exercises": [],
    }))
    # Era 1 — no schemaVersion → dropped
    (tmp_path / "2026-04-21.json").write_text(json.dumps({
        "date": "2026-04-21",
        "exercises": [],
    }))

    history = load_from_rehab_dir(tmp_path)
    dates = [r["date"] for r in history.records]
    assert dates == ["2026-04-29", "2026-04-30"]
    # override correctly carried through adapter
    assert history.records[0]["was_override"] is True
    assert history.records[0]["overridden_from"] == "upper_ankle"
