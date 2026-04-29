"""Phase 1 rule-based recommender. Used before bandit takes over."""


def rule_recommend(ctx: dict) -> str:
    if ctx["travel_mode"]:
        return "travel_minimal"
    if ctx["yesterday_score"] is not None and ctx["yesterday_score"] <= 2:
        return "stretch_ankle"
    gaps = {
        "upper_ankle": ctx["days_since_upper_ankle"],
        "lower_ankle": ctx["days_since_lower_ankle"],
        "stretch_ankle": ctx["days_since_stretch_ankle"],
    }
    return max(gaps, key=gaps.get)
