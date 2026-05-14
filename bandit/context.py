"""Context feature extraction from check-in history.

Soft Gate (this file): helpers below — pure plumbing, no design choices.
Hard Gate (this file): `build_context_vector(ctx_dict) -> np.ndarray` is
NOT defined here yet. The author writes it, owning the encoding decisions
(normalization, one-hot vs scalar, bias term, missing-value handling).
See docs/plan.md Task 11 Step 5 and CLAUDE.md Hard Gate rules.
"""
from datetime import date

from bandit.history import History
import numpy as np

def days_since_arm(history: History, arm_id: str, today: str) -> int:
    last = history.last_of_arm(arm_id)
    if last is None:
        return 999
    return (date.fromisoformat(today) - date.fromisoformat(last["date"])).days


def weekday_one_hot(weekday: int) -> list:
    v = [0] * 7
    v[weekday] = 1
    return v


def last_same_arm_completion(history: History, arm_id: str) -> float:
    last = history.last_of_arm(arm_id)
    return last["completion_ratio"] if last else 1.0


def build_context_dict(history: History, today: str, travel_mode: bool) -> dict:
    latest = history.records[-1] if history.records else None
    yesterday_score = latest["daily_score"] if latest else None
    today_d = date.fromisoformat(today)
    return {
        "travel_mode": travel_mode,
        "yesterday_score": yesterday_score,
        "days_since_upper_ankle": days_since_arm(history, "upper_ankle", today),
        "days_since_lower_ankle": days_since_arm(history, "lower_ankle", today),
        "days_since_stretch_ankle": days_since_arm(history, "stretch_ankle", today),
        "week_checkin_count": history.days_in_current_week(today),
        "weekday": today_d.weekday(),
        "last_same_arm_completion": last_same_arm_completion(history, "upper_ankle"),
    }

def build_context_vector(ctx_dict) -> np.ndarray(shape=(8,)):
    score =ctx_dict["yesterday_score"]
    if score is None:
        normalized_score = 0.5
    else:
        normalized_score = (score - 1) / 4

    def scale_days(days):
        # days coule be 999
        # cap to 14 and then to 0-1
        return min(days, 14)/14
    
    # [1.0,
    #  travel_mode,
    #  nomalized_score,
    #  capped_days_upper,
    #  capped_days_lower,
    #  capped_days_stretch,
    #  scaled_week_count,
    #  last_same_arm_completion]
    return np.array([
        1.0,
        1.0 if ctx_dict["travel_mode"] else 0.0,
        normalized_score,
        scale_days(ctx_dict["days_since_upper_ankle"]),
        scale_days(ctx_dict["days_since_lower_ankle"]),
        scale_days(ctx_dict["days_since_stretch_ankle"]),
        min(ctx_dict["week_checkin_count"], 7) / 7,
        ctx_dict["last_same_arm_completion"],
    ], dtype=float)
    