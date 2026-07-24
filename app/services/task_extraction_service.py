import re
from typing import List, Dict

# Maintenance action verbs — order matters (longer phrases first)
ACTIONS = [
    "overhaul", "calibrate", "lubricate", "replace", "inspect",
    "install", "remove", "repair", "adjust", "verify", "clean",
    "check", "test", "service",
]

# System keywords mapped to a normalized system name
SYSTEM_MAP = [
    (["flight control", "aileron", "elevator", "rudder", "spoiler", "flap"], "flight_controls"),
    (["landing gear", "undercarriage", "nose gear", "main gear"], "landing_gear"),
    (["engine", "turbine", "turbofan", "turboprop", "power plant"], "engine"),
    (["apu", "auxiliary power unit"], "apu"),
    (["avionics", "navigation", "communications", "radio", "transponder", "fms", "irs", "adiru"], "avionics"),
    (["hydraulic", "actuator", "hydraulics"], "hydraulic"),
    (["fuel", "tank", "fuel system", "refuel"], "fuel"),
    (["electrical", "wiring", "generator", "battery", "bus bar"], "electrical"),
    (["pneumatic", "bleed", "duct", "pressurization"], "pneumatic"),
    (["airframe", "fuselage", "structure", "skin", "frame", "stringer"], "airframe"),
    (["door", "hatch", "panel"], "doors"),
    (["window", "windshield", "windscreen"], "windows"),
    (["oxygen", "o2"], "oxygen"),
    (["ice", "rain", "de-ice", "anti-ice", "deice"], "ice_rain"),
]

# ATA chapter hints
ATA_PATTERN = re.compile(r'\bata[\s-]?(\d{2})\b', re.IGNORECASE)

# Structured task line pattern: optional task-number then action verb
STRUCTURED_PATTERN = re.compile(
    r'^(?:task\s*[\#:]?\s*\d+\s*[-:.]?\s*)?'
    r'(?P<action>' + '|'.join(ACTIONS) + r')\b',
    re.IGNORECASE
)

# Minimum line length to be considered a real task description
MIN_LINE_LEN = 10


def _detect_action(text: str) -> str:
    low = text.lower()
    for action in ACTIONS:
        if re.search(r'\b' + action + r'\b', low):
            return action
    return ""


def _detect_system(text: str) -> str:
    low = text.lower()
    for keywords, system in SYSTEM_MAP:
        if any(kw in low for kw in keywords):
            return system
    return "general"


def _detect_ata(text: str) -> str:
    m = ATA_PATTERN.search(text)
    return m.group(1) if m else ""


def normalize_task_key(description: str) -> str:
    """Return a normalized key like 'inspect_engine' for historical matching."""
    action = _detect_action(description) or "check"
    system = _detect_system(description)
    return f"{action}_{system}"


def estimate_manhours(line: str) -> float:
    """Heuristic manhour estimate based on system and action keywords."""
    low = line.lower()
    system = _detect_system(low)
    action = _detect_action(low)

    base = {
        "engine": 12.0,
        "landing_gear": 8.0,
        "avionics": 6.0,
        "hydraulic": 5.0,
        "fuel": 6.0,
        "electrical": 4.0,
        "flight_controls": 10.0,
        "apu": 6.0,
        "airframe": 16.0,
        "pneumatic": 5.0,
        "doors": 3.0,
        "windows": 2.0,
        "oxygen": 3.0,
        "ice_rain": 4.0,
        "general": 3.0,
    }.get(system, 3.0)

    # Adjust by action complexity
    action_multipliers = {
        "overhaul": 2.5,
        "repair": 1.8,
        "replace": 1.5,
        "install": 1.3,
        "remove": 1.0,
        "inspect": 0.8,
        "test": 0.7,
        "check": 0.6,
        "verify": 0.5,
        "adjust": 0.8,
        "calibrate": 0.7,
        "clean": 0.4,
        "lubricate": 0.4,
        "service": 0.6,
    }
    multiplier = action_multipliers.get(action, 1.0)
    return round(base * multiplier, 1)


def infer_resources(line: str) -> Dict:
    """Infer required skills, tools, and materials from the task description."""
    system = _detect_system(line)

    defaults: Dict[str, Dict] = {
        "engine": {
            "skills": ["B1", "Engine Specialist"],
            "tools": ["Engine Stand", "Torque Wrench", "Borescope"],
            "materials": ["Seals", "Consumables"],
        },
        "landing_gear": {
            "skills": ["B1", "Landing Gear Specialist"],
            "tools": ["Hydraulic Jack", "Torque Wrench"],
            "materials": ["Seals", "Lubricant"],
        },
        "avionics": {
            "skills": ["B2"],
            "tools": ["Multimeter", "Avionics Test Set"],
            "materials": [],
        },
        "hydraulic": {
            "skills": ["B1"],
            "tools": ["Hydraulic Test Equipment", "Pressure Gauge"],
            "materials": ["Hydraulic Fluid", "Seals"],
        },
        "fuel": {
            "skills": ["B1", "Fuel System Specialist"],
            "tools": ["Fuel Testing Kit", "Bonding Cable"],
            "materials": ["Seals"],
        },
        "electrical": {
            "skills": ["B2"],
            "tools": ["Multimeter", "Wiring Toolkit"],
            "materials": ["Consumables"],
        },
        "flight_controls": {
            "skills": ["B1", "Flight Controls Specialist"],
            "tools": ["Rigging Board", "Torque Wrench"],
            "materials": ["Seals", "Consumables"],
        },
        "apu": {
            "skills": ["B1", "Engine Specialist"],
            "tools": ["Borescope", "APU Test Equipment"],
            "materials": ["Seals", "Consumables"],
        },
        "airframe": {
            "skills": ["B1", "Structures Specialist"],
            "tools": ["NDT Equipment", "Inspection Mirror"],
            "materials": ["Consumables"],
        },
        "pneumatic": {
            "skills": ["B1"],
            "tools": ["Pressure Gauge", "Leak Detection Equipment"],
            "materials": ["Seals", "Consumables"],
        },
        "general": {
            "skills": ["Technician"],
            "tools": ["Basic Toolkit"],
            "materials": ["Consumables"],
        },
    }

    return defaults.get(system, defaults["general"])


def _is_task_line(line: str) -> bool:
    """Return True if the line looks like a maintenance task."""
    if len(line) < MIN_LINE_LEN:
        return False
    low = line.lower()
    return bool(STRUCTURED_PATTERN.match(line)) or any(
        re.search(r'\b' + a + r'\b', low) for a in ACTIONS
    )


def extract_tasks_from_text(text: str) -> List[Dict]:
    """Extract maintenance tasks from PDF text.

    Returns a list of task dicts with id, description, task_key,
    ata_chapter, manhours, priority, dependencies, and resources.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    tasks = []
    task_counter = 0

    for line in lines:
        if not _is_task_line(line):
            continue
        task_counter += 1
        low = line.lower()
        resources = infer_resources(line)
        tasks.append({
            "id": f"T{task_counter}",
            "description": line[:240],
            "task_key": normalize_task_key(line),
            "ata_chapter": _detect_ata(line),
            "manhours": estimate_manhours(line),
            "priority": "HIGH" if "critical" in low else "MEDIUM",
            "dependencies": [],
            "resources": resources,
        })

    # Minimal fallback if nothing was detected
    if not tasks and text.strip():
        tasks.append({
            "id": "T1",
            "description": "General inspection based on uploaded work package",
            "task_key": "inspect_general",
            "ata_chapter": "",
            "manhours": 4.0,
            "priority": "MEDIUM",
            "dependencies": [],
            "resources": {"skills": ["Technician"], "materials": [], "tools": ["Basic Toolkit"]},
        })

    return tasks
