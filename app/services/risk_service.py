def score_task_risk(task: dict) -> float:
    score = 1.0

    desc = task.get("description", "").lower()
    mh = float(task.get("manhours", 0))

    if "engine" in desc:
        score += 2.0
    if "landing gear" in desc:
        score += 1.5
    if "critical" in desc:
        score += 2.0
    if mh >= 8:
        score += 1.0

    return round(min(score, 10.0), 2)
