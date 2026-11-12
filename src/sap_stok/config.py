from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
DB_PATH = DATA_RAW / "inventory_management.db"

SERVICE_LEVEL_Z = 1.65