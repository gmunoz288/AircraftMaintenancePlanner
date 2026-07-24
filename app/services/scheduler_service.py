from math import ceil
from collections import defaultdict

from app.config import HOURS_PER_DAY, DEFAULT_TEAM_CAPACITY


def build_daily_plan(tasks: list, team_capacity_hours: int = DEFAULT_TEAM_CAPACITY) -> dict:
    """Build a day-by-day work plan from a list of enriched tasks.

    Tasks are ordered by risk score (descending) then by manhours (descending)
    so the most critical and largest jobs start first.
    """
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (t.get("risk_score", 0), t.get("manhours", 0)),
        reverse=True,
    )

    day = 1
    remaining = team_capacity_hours
    plan: dict = defaultdict(list)

    for task in sorted_tasks:
        needed = float(task.get("manhours", 0))
        while needed > 0:
            if remaining <= 0:
                day += 1
                remaining = team_capacity_hours

            alloc = min(needed, remaining)
            plan[f"Day {day}"].append({
                "task_id": task["id"],
                "description": task["description"],
                "task_key": task.get("task_key", ""),
                "ata_chapter": task.get("ata_chapter", ""),
                "allocated_hours": round(alloc, 2),
                "risk_score": task.get("risk_score", 0),
                "skills": task.get("resources", {}).get("skills", []),
                "tools": task.get("resources", {}).get("tools", []),
                "materials": task.get("resources", {}).get("materials", []),
                "historical_avg_manhours": task.get("historical_avg_manhours"),
                "historical_occurrences": task.get("historical_occurrences", 0),
            })
            needed -= alloc
            remaining -= alloc

    return dict(plan)


def build_gantt(daily_plan: dict) -> list:
    """Convert a daily plan into a Gantt JSON array.

    Each entry represents one task segment (a task may span multiple days).
    The ``start_day`` and ``end_day`` are 0-indexed integers.
    """
    gantt = []
    for day_index, (day_name, items) in enumerate(daily_plan.items()):
        for item in items:
            duration_days = ceil(item["allocated_hours"] / HOURS_PER_DAY)
            gantt.append({
                "id": item["task_id"],
                "name": item["description"][:80],
                "task_key": item.get("task_key", ""),
                "ata_chapter": item.get("ata_chapter", ""),
                "start_day": day_index,
                "end_day": day_index + max(duration_days, 1),
                "hours": item["allocated_hours"],
                "risk_score": item["risk_score"],
                "skills": item.get("skills", []),
            })
    return gantt
