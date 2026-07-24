from math import ceil
from collections import defaultdict

HOURS_PER_DAY = 8
DEFAULT_TEAM_CAPACITY = 24  # 3 técnicos * 8h/día

def build_daily_plan(tasks: list, team_capacity_hours: int = DEFAULT_TEAM_CAPACITY):
    # Orden simple: mayor riesgo y luego más horas
    sorted_tasks = sorted(tasks, key=lambda t: (t.get("risk_score", 0), t.get("manhours", 0)), reverse=True)

    day = 1
    remaining = team_capacity_hours
    plan = defaultdict(list)

    for task in sorted_tasks:
        needed = float(task["manhours"])
        while needed > 0:
            if remaining <= 0:
                day += 1
                remaining = team_capacity_hours

            alloc = min(needed, remaining)
            plan[f"Day {day}"].append({
                "task_id": task["id"],
                "description": task["description"],
                "allocated_hours": alloc,
                "risk_score": task.get("risk_score", 0),
                "skills": task["resources"]["skills"]
            })
            needed -= alloc
            remaining -= alloc

    return dict(plan)

def build_gantt(daily_plan: dict):
    # Salida JSON simple compatible con frontend
    gantt = []
    current_day_idx = 0
    for day_name, items in daily_plan.items():
        for item in items:
            gantt.append({
                "id": item["task_id"],
                "name": item["description"][:80],
                "start_day": current_day_idx,
                "end_day": current_day_idx + ceil(item["allocated_hours"] / HOURS_PER_DAY),
                "hours": item["allocated_hours"],
                "risk_score": item["risk_score"]
            })
        current_day_idx += 1
    return gantt
