"""JSON schema for daily check-in records."""

CURRENT_SCHEMA_VERSION = 2

REQUIRED_FIELDS = [
    "date", "template_id", "exercises", "completion_ratio",
    "daily_score", "was_override", "schema_version",
]


def validate_checkin(record: dict) -> None:
    for f in REQUIRED_FIELDS:
        if f not in record:
            raise ValueError(f"missing required field: {f}")
    if record["schema_version"] != CURRENT_SCHEMA_VERSION:
        raise ValueError(
            f"schema_version mismatch: got {record['schema_version']}, "
            f"expected {CURRENT_SCHEMA_VERSION}"
        )
    if not 0.0 <= record["completion_ratio"] <= 1.0:
        raise ValueError("completion_ratio must be in [0, 1]")
    if record["daily_score"] is not None and not 1 <= record["daily_score"] <= 5:
        raise ValueError("daily_score must be in [1, 5]")
