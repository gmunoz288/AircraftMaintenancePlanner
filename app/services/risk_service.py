from app.config import MAX_RISK_SCORE

# Risk weights for common high-criticality systems
SYSTEM_WEIGHTS = {
    "engine": 2.5,
    "landing gear": 2.0,
    "flight control": 2.5,
    "apu": 1.5,
    "hydraulic": 1.5,
    "fuel": 1.8,
    "avionics": 1.2,
    "airframe": 2.0,
    "structure": 2.0,
    "electrical": 1.0,
    "pneumatic": 1.0,
}

ACTION_WEIGHTS = {
    "overhaul": 1.5,
    "replace": 1.2,
    "repair": 1.3,
    "remove": 0.8,
    "install": 1.0,
    "adjust": 0.8,
    "inspect": 0.5,
    "check": 0.4,
    "clean": 0.2,
    "lubricate": 0.2,
    "test": 0.5,
    "verify": 0.3,
}


def score_task_risk(task: dict) -> float:
    """Compute a risk score in the range [1, MAX_RISK_SCORE].

    Factors:
    - System criticality (keyword match)
    - Action complexity
    - Manhours (proxy for scope)
    - Historical risk factor (when available from enrichment)
    - Priority override for tasks flagged CRITICAL
    """
    desc = task.get("description", "").lower()
    mh = float(task.get("manhours", 0))
    priority = task.get("priority", "MEDIUM")

    score = 1.0

    # System criticality
    for keyword, weight in SYSTEM_WEIGHTS.items():
        if keyword in desc:
            score += weight
            break  # take the highest matching system only

    # Action complexity (additive)
    for action, weight in ACTION_WEIGHTS.items():
        if action in desc:
            score += weight
            break

    # Manhour contribution (scope proxy)
    if mh >= 40:
        score += 2.0
    elif mh >= 20:
        score += 1.5
    elif mh >= 8:
        score += 1.0
    elif mh >= 4:
        score += 0.5

    # Priority override
    if priority == "HIGH" or "critical" in desc:
        score += 1.5

    # Historical risk factor: if the historical factor is high (>0.8)
    # add up to 1.0 extra; if low (<0.4) reduce by up to 0.5
    hist_rf = task.get("historical_risk_factor")
    if hist_rf is not None:
        if hist_rf >= 0.8:
            score += 1.0
        elif hist_rf >= 0.6:
            score += 0.5
        elif hist_rf < 0.4:
            score = max(1.0, score - 0.5)

    return round(min(score, MAX_RISK_SCORE), 2)
