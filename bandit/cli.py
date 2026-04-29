"""CLI for Day 0 smoke-testing the rule recommender."""
import argparse
import json
from datetime import date
from pathlib import Path

from bandit.history import load_from_file
from bandit.rules import rule_recommend
from bandit.arms import get_arm


def _build_context(history, today_str: str, travel_mode: bool) -> dict:
    from datetime import date as _date
    today = _date.fromisoformat(today_str)

    def days_since(arm_id):
        last = history.last_of_arm(arm_id)
        if last is None:
            return 999
        return (today - _date.fromisoformat(last["date"])).days

    yesterday = sorted(history.records, key=lambda r: r["date"])
    yesterday_score = yesterday[-1]["daily_score"] if yesterday else None

    return {
        "travel_mode": travel_mode,
        "yesterday_score": yesterday_score,
        "days_since_upper_ankle": days_since("upper_ankle"),
        "days_since_lower_ankle": days_since("lower_ankle"),
        "days_since_stretch_ankle": days_since("stretch_ankle"),
        "week_checkin_count": history.days_in_current_week(today_str),
        "weekday": today.weekday(),
        "last_same_arm_completion": 1.0,  # filled once bandit knows what arm it will pick
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["today"])
    parser.add_argument("--history", default="data/sample_checkins.json")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--travel", action="store_true")
    args = parser.parse_args()

    history = load_from_file(Path(args.history))
    ctx = _build_context(history, args.date, args.travel)
    arm_id = rule_recommend(ctx)
    arm = get_arm(arm_id)

    print(f"📅 {args.date}")
    print(f"💡 推荐: {arm_id} — {arm['description']}")
    print(f"依据: {json.dumps(ctx, ensure_ascii=False, indent=2)}")
