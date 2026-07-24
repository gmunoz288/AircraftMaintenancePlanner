from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
HISTORICAL_DB_PATH = DATA_DIR / "historical_tasks.json"
UPLOAD_DIR = DATA_DIR / "uploads"
RESULTS_DIR = DATA_DIR / "results"
MAX_UPLOAD_SIZE_BYTES = 250 * 1024 * 1024
UPLOAD_CHUNK_SIZE_BYTES = 1024 * 1024

HOURS_PER_DAY = 8
DEFAULT_TEAM_CAPACITY = 24  # 3 technicians * 8 h/day
MAX_RISK_SCORE = 10.0
