"""Audit log and ground-truth writers for Dunmore Corp Portal.

Demo company. All data is fictional. No file contents are ever logged.
"""

import csv
from datetime import datetime
import json
import threading
from typing import Optional
import uuid

from config_loader import load_config

_AUDIT_LOCK = threading.Lock()
_GT_LOCK = threading.Lock()

VALID_ACTIONS = {"login", "login_failed", "view", "download", "export", "access_denied"}
VALID_DEVICES = {"managed", "unmanaged"}
VALID_OUTCOMES = {"success", "denied"}


def write_audit(
    employee_id: str,
    department: str,
    role: str,
    action: str,
    doc_id: str = "",
    doc_title: str = "",
    sensitivity: str = "normal",
    bytes_transferred: int = 0,
    device: str = "managed",
    source_ip: str = "10.20.1.15",
    outcome: str = "success",
    timestamp: Optional[datetime] = None,
    event_id: Optional[str] = None,
) -> dict:
    """Append a single JSON line to company_audit.jsonl and return the event dict."""
    if action not in VALID_ACTIONS:
        raise ValueError(f"Invalid action '{action}'. Expected one of {VALID_ACTIONS}")
    if device not in VALID_DEVICES:
        raise ValueError(f"Invalid device '{device}'. Expected one of {VALID_DEVICES}")
    if outcome not in VALID_OUTCOMES:
        raise ValueError(f"Invalid outcome '{outcome}'. Expected one of {VALID_OUTCOMES}")

    ts = timestamp or datetime.now()
    event = {
        "event_id": event_id or f"evt_{uuid.uuid4().hex[:12]}",
        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
        "employee_id": employee_id,
        "department": department,
        "role": role,
        "action": action,
        "doc_id": doc_id,
        "doc_title": doc_title,
        "sensitivity": sensitivity,
        "bytes": int(bytes_transferred),
        "device": device,
        "source_ip": source_ip,
        "outcome": outcome,
    }

    cfg = load_config()
    log_path = cfg["audit_log_path"]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, separators=(",", ":")) + "\n"

    with _AUDIT_LOCK:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)

    return event


def write_ground_truth(
    rule: str,
    employee_id: str,
    time_str: str,
    label: str,
) -> None:
    """Append an expected alert row (rule, employee_id, time, label) to company_ground_truth.csv."""
    cfg = load_config()
    gt_path = cfg["ground_truth_path"]
    gt_path.parent.mkdir(parents=True, exist_ok=True)

    with _GT_LOCK:
        write_header = not gt_path.exists() or gt_path.stat().st_size == 0
        with open(gt_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["rule", "employee_id", "time", "label"])
            writer.writerow([rule, employee_id, time_str, label])

