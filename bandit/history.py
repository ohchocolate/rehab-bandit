"""Check-in history loading and queries."""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from bandit.schema import validate_checkin


@dataclass
class History:
    records: list = field(default_factory=list)

    def last_of_arm(self, arm_id: str) -> Optional[dict]:
        matches = [r for r in self.records if r["template_id"] == arm_id]
        return matches[-1] if matches else None

    def days_in_current_week(self, today: str) -> int:
        """Count distinct check-in dates in the ISO week of `today`."""
        from datetime import date
        tgt = date.fromisoformat(today)
        year, week, _ = tgt.isocalendar()
        count = 0
        for r in self.records:
            d = date.fromisoformat(r["date"])
            y, w, _ = d.isocalendar()
            if y == year and w == week:
                count += 1
        return count


def load_from_file(path: Path) -> History:
    data = json.loads(Path(path).read_text())
    records = [r for r in data if "schema_version" in r]
    for r in records:
        validate_checkin(r)
    records = sorted(records, key=lambda r: r["date"])
    return History(records=records)
