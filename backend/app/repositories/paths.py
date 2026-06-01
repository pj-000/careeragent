import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _runtime_data_dir() -> Path:
    configured = os.getenv("CAREERAGENT_DATA_DIR")
    if not configured:
        return PROJECT_ROOT / "data" / "runtime"
    path = Path(configured)
    return path if path.is_absolute() else PROJECT_ROOT / path


RUNTIME_DATA_DIR = _runtime_data_dir()
