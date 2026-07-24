"""
Historical task repository backed by a local JSON seed file.

Provides a deterministic lookup layer to enrich extracted tasks with
data from past maintenance records.
"""
import json
from functools import lru_cache
from typing import List, Optional

from app.config import HISTORICAL_DB_PATH
from app.models.task import HistoricalRecord


@lru_cache(maxsize=1)
def _load_records() -> List[HistoricalRecord]:
    """Load and cache historical records from the JSON seed file."""
    with open(HISTORICAL_DB_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return [HistoricalRecord(**r) for r in data.get("records", [])]


def get_all_records() -> List[HistoricalRecord]:
    return _load_records()


def find_by_task_key(task_key: str) -> Optional[HistoricalRecord]:
    """Return the best-matching historical record for a given task key.

    Matching priority:
      1. Exact key match
      2. Partial match on action (e.g. ``inspect_*``) with the same system
      3. Partial match on system alone
      4. Generic fallback (``<action>_general``)
    """
    records = _load_records()
    key_lower = task_key.lower()

    # 1. Exact match
    for rec in records:
        if rec.task_key == key_lower:
            return rec

    # Parse action and system from key
    parts = key_lower.split("_", 1)
    action = parts[0] if parts else ""
    system = parts[1] if len(parts) > 1 else ""

    # 2. Same action, same system (substring match)
    if action and system:
        for rec in records:
            if rec.task_key.startswith(action + "_") and system in rec.task_key:
                return rec

    # 3. Same system, any action
    if system:
        for rec in records:
            if system in rec.task_key and "general" not in rec.task_key:
                return rec

    # 4. Generic fallback: <action>_general
    fallback_key = f"{action}_general" if action else "check_general"
    for rec in records:
        if rec.task_key == fallback_key:
            return rec

    # 5. Ultimate fallback
    for rec in records:
        if rec.task_key == "check_general":
            return rec

    return None
