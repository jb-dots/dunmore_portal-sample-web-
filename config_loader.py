"""Configuration loader for Dunmore Corp Portal."""

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict
import yaml

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.yaml"


@lru_cache(maxsize=1)
def load_config() -> Dict[str, Any]:
    """Load portal configuration from config.yaml with resolved paths."""
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    def resolve_path(key: str, default: str) -> Path:
        raw = Path(cfg.get(key, default))
        return raw if raw.is_absolute() else (BASE_DIR / raw)

    return {
        "audit_log_path": resolve_path("audit_log_path", "company_audit.jsonl"),
        "ground_truth_path": resolve_path("ground_truth_path", "company_ground_truth.csv"),
        "db_path": resolve_path("db_path", "portal.db"),
        "port": int(cfg.get("port", 8600)),
    }

