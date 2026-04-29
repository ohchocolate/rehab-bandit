from bandit.rules import rule_recommend


def _ctx(**overrides):
    base = {
        "travel_mode": False,
        "yesterday_score": 3,
        "days_since_upper_ankle": 99,
        "days_since_lower_ankle": 99,
        "days_since_stretch_ankle": 99,
        "week_checkin_count": 0,
        "weekday": 1,
        "last_same_arm_completion": 1.0,
    }
    base.update(overrides)
    return base


def test_travel_mode_always_returns_travel_minimal():
    assert rule_recommend(_ctx(travel_mode=True)) == "travel_minimal"


def test_low_yesterday_score_returns_stretch():
    assert rule_recommend(_ctx(yesterday_score=2)) == "stretch_ankle"
    assert rule_recommend(_ctx(yesterday_score=1)) == "stretch_ankle"


def test_default_picks_longest_gap_split():
    ctx = _ctx(days_since_upper_ankle=5, days_since_lower_ankle=2, days_since_stretch_ankle=3)
    assert rule_recommend(ctx) == "upper_ankle"

    ctx = _ctx(days_since_upper_ankle=1, days_since_lower_ankle=7, days_since_stretch_ankle=3)
    assert rule_recommend(ctx) == "lower_ankle"
