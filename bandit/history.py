"""Check-in history loading and queries."""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from bandit.rehab_adapter import adapt
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
    """Load a JSON array of bandit-internal v2 records (e.g. data/sample_checkins.json)."""
    data = json.loads(Path(path).read_text())
    for r in data:
        validate_checkin(r)
    records = sorted(data, key=lambda r: r["date"])
    return History(records=records)


def load_from_rehab_dir(path: Path) -> History:
    """Load all rehab frontend session files from a directory, adapt to v2.

    Reads every `*.json` in `path`, runs each through `rehab_adapter.adapt`.
    Records the adapter rejects (missing schemaVersion / feedback_score /
    template_id) are silently dropped — see DEC-001.
    """
    records = []
    for fp in sorted(Path(path).glob("*.json")):
        raw = json.loads(fp.read_text())
        adapted = adapt(raw)
        if adapted is None:
            continue
        validate_checkin(adapted)
        records.append(adapted)
    records.sort(key=lambda r: r["date"])
    return History(records=records)
