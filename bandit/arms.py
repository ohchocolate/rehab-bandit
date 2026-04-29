"""Daily plan templates ("arms" in bandit terminology)."""

ARMS = [
    {"id": "upper_ankle",    "description": "上肢日 + 踝 PT + 胸腰椎拉伸"},
    {"id": "lower_ankle",    "description": "下肢日 + 踝 PT + 胸腰椎拉伸"},
    {"id": "stretch_ankle",  "description": "拉伸 + 踝 PT（轻量）"},
    {"id": "travel_minimal", "description": "旅行最小化：单腿平衡 + 徒手踝"},
    {"id": "ankle_only",     "description": "只做踝 PT"},
    {"id": "rest",           "description": "休息日"},
]

ARM_IDS = [a["id"] for a in ARMS]
_BY_ID = {a["id"]: a for a in ARMS}


def get_arm(arm_id: str) -> dict:
    return _BY_ID[arm_id]
