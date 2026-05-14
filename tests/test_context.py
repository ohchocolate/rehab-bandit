from bandit.context import (
    build_context_dict,
    build_context_vector,
    days_since_arm,
    last_same_arm_completion,
    weekday_one_hot,
)
from bandit.history import History


def _hist(*records):
    return History(records=list(records))


def _record(date, template_id, **overrides):
    base = {
        "date": date,
        "template_id": template_id,
        "exercises": [],
        "completion_ratio": 1.0,
        "daily_score": 4,
        "was_override": False,
        "overridden_from": None,
        "override_reason": None,
        "schema_version": 2,
    }
    base.update(overrides)
    return base


def test_days_since_none_returns_large_sentinel():
    h = _hist()
    assert days_since_arm(h, "upper_ankle", "2026-04-28") >= 999


def test_days_since_counts_correctly():
    h = _hist(_record("2026-04-20", "upper_ankle"))
    assert days_since_arm(h, "upper_ankle", "2026-04-28") == 8


def test_weekday_one_hot_is_length_7():
    v = weekday_one_hot(3)
    assert len(v) == 7
    assert v[3] == 1 and sum(v) == 1


def test_last_same_arm_completion_default_1():
    h = _hist()
    assert last_same_arm_completion(h, "upper_ankle") == 1.0


def test_last_same_arm_completion_uses_record():
    h = _hist(_record("2026-04-20", "upper_ankle", completion_ratio=0.6))
    assert last_same_arm_completion(h, "upper_ankle") == 0.6


def test_build_context_dict_has_all_keys():
    h = _hist()
    ctx = build_context_dict(h, today="2026-04-28", travel_mode=False)
    required = {
        "travel_mode", "yesterday_score",
        "days_since_upper_ankle", "days_since_lower_ankle",
        "days_since_stretch_ankle", "week_checkin_count",
        "weekday", "last_same_arm_completion",
    }
    assert set(ctx.keys()) >= required


def test_build_context_dict_yesterday_score_from_latest_record():
    h = _hist(
        _record("2026-04-26", "upper_ankle", daily_score=3),
        _record("2026-04-27", "lower_ankle", daily_score=5),
    )
    ctx = build_context_dict(h, today="2026-04-28", travel_mode=False)
    assert ctx["yesterday_score"] == 5


def test_build_context_dict_weekday_matches_calendar():
    # 2026-04-28 is a Tuesday → weekday() == 1 (Mon=0)
    ctx = build_context_dict(_hist(), today="2026-04-28", travel_mode=False)
    assert ctx["weekday"] == 1

def test_build_context_vector_dimensions():
    ctx = {
        "travel_mode": True,
        "yesterday_score": 4,
        "days_since_upper_ankle": 7,
        "days_since_lower_ankle": 999,
        "days_since_stretch_ankle": 0,
        "week_checkin_count": 3,
        "weekday": 1,
        "last_same_arm_completion": 0.6,
    }
    vec = build_context_vector(ctx)
    assert vec.shape == (8,)

def test_build_context_vector_scales_values():
    ctx = {
        "travel_mode": True,
        "yesterday_score": 5,
        "days_since_upper_ankle": 14,
        "days_since_lower_ankle": 999,
        "days_since_stretch_ankle": 0,
        "week_checkin_count": 7,
        "weekday": 1,
        "last_same_arm_completion": 0.5,
    }
    vec = build_context_vector(ctx)
    assert vec.tolist() == [1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 0.5]
