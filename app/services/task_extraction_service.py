import re
from typing import List, Dict

TASK_HINTS = [
    "inspect", "replace", "remove", "install", "check", "test",
    "lubricate", "clean", "adjust", "verify", "repair"
]

def estimate_manhours(line: str) -> float:
    l = line.lower()
    if "engine" in l:
        return 8.0
    if "landing gear" in l:
        return 6.0
    if "avionics" in l:
        return 4.0
    return 2.0

def infer_resources(line: str) -> Dict:
    l = line.lower()
    skills = []
    materials = []
    tools = []

    if "engine" in l:
        skills += ["B1", "Engine Specialist"]
        tools += ["Engine Stand", "Torque Wrench"]
        materials += ["Seals", "Consumables"]
    elif "avionics" in l:
        skills += ["B2"]
        tools += ["Multimeter", "Avionics Test Set"]
    elif "landing gear" in l:
        skills += ["B1"]
        tools += ["Hydraulic Jack", "Torque Wrench"]
    else:
        skills += ["Technician"]

    return {"skills": skills, "materials": materials, "tools": tools}

def extract_tasks_from_text(text: str) -> List[Dict]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    tasks = []

    for i, line in enumerate(lines, start=1):
        low = line.lower()
        if any(h in low for h in TASK_HINTS):
            resources = infer_resources(line)
            tasks.append({
                "id": f"T{i}",
                "description": line[:240],
                "manhours": estimate_manhours(line),
                "priority": "HIGH" if "critical" in low else "MEDIUM",
                "dependencies": [],
                "resources": resources
            })

    # fallback mínimo si no detecta nada
    if not tasks and text.strip():
        tasks.append({
            "id": "T1",
            "description": "General inspection based on uploaded work package",
            "manhours": 4.0,
            "priority": "MEDIUM",
            "dependencies": [],
            "resources": {"skills": ["Technician"], "materials": [], "tools": ["Basic Toolkit"]}
        })

    return tasks
