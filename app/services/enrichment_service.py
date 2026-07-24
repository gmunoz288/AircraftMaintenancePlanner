"""
Enrichment service: matches extracted tasks against the historical
repository and augments them with historical manhour estimates and
risk signal.
"""
from typing import List, Dict

from app.repositories.historical_repository import find_by_task_key


def enrich_tasks(tasks: List[Dict]) -> List[Dict]:
    """Enrich each task dict in-place with historical data.

    Adds the following fields to every task:
      - ``historical_avg_manhours``: average manhours from historical records
      - ``historical_risk_factor``: risk multiplier [0-1] from historical records
      - ``historical_occurrences``: how many historical executions were found
      - Overrides ``manhours`` with a weighted blend of the heuristic estimate
        and the historical average (60 % historical, 40 % heuristic) when a
        match is found.
      - Overrides ``resources`` with the historically-observed skills/tools/
        materials when a match is found.
    """
    enriched = []
    for task in tasks:
        task = dict(task)
        task_key = task.get("task_key", "")
        record = find_by_task_key(task_key) if task_key else None

        if record:
            heuristic_mh = float(task.get("manhours", 2.0))
            blended_mh = round(
                0.6 * record.avg_manhours + 0.4 * heuristic_mh, 1
            )
            task["manhours"] = blended_mh
            task["historical_avg_manhours"] = record.avg_manhours
            task["historical_risk_factor"] = record.risk_factor
            task["historical_occurrences"] = record.occurrences

            # Merge resources: prefer historical, fall back to heuristic
            existing_resources = task.get("resources", {})
            task["resources"] = {
                "skills": record.required_skills or existing_resources.get("skills", []),
                "tools": record.required_tools or existing_resources.get("tools", []),
                "materials": record.required_materials or existing_resources.get("materials", []),
            }

            # Promote ATA chapter from historical record if not already set
            if not task.get("ata_chapter") and record.ata_chapter:
                task["ata_chapter"] = record.ata_chapter
        else:
            task.setdefault("historical_avg_manhours", None)
            task.setdefault("historical_risk_factor", None)
            task.setdefault("historical_occurrences", 0)

        enriched.append(task)
    return enriched
