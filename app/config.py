from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
HISTORICAL_DB_PATH = DATA_DIR / "historical_tasks.json"

HOURS_PER_DAY = 8
DEFAULT_TEAM_CAPACITY = 24  # 3 technicians * 8 h/day
MAX_RISK_SCORE = 10.0
