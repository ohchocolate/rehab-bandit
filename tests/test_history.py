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
