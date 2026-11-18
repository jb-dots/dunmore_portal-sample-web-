"""Attack and normal-traffic simulator for Dunmore Corp Portal.

Demo company. All data is fictional.
"""

from datetime import date, datetime, time, timedelta
import random
import threading
import time as time_mod
from typing import Dict, List, Optional

from audit import write_audit, write_ground_truth
from portal_db import (
    get_all_documents,
    get_all_employees,
    get_documents_for_department,
    get_employee,
)

_LIVE_LOCK = threading.Lock()
_LIVE_STOP_EVENT: Optional[threading.Event] = None
_LIVE_THREAD: Optional[threading.Thread] = None
_LIVE_STATS: Dict[str, object] = {"running": False, "events_emitted": 0, "last_event": ""}


def _dept_ip(employee_id: str) -> str:
    idx = int(employee_id[1:]) if employee_id[1:].isdigit() else 1
    return f"10.20.{(idx % 4) + 1}.{10 + idx}"


def _normal_docs_for_employee(department: str) -> List[dict]:
    docs = get_documents_for_department(department, include_shared=True)
    normal = [d for d in docs if d["sensitivity"] == "normal"]
    return normal or docs


def run_normal_workday(target_date: Optional[date] = None) -> int:
    """Generate 20 to 60 small normal actions (09:00-17:00) for all 24 employees."""
    day = target_date or date.today()
    employees = get_all_employees()
    events_written = 0

    for emp in employees:
        docs = _normal_docs_for_employee(emp["department"])
        ip = _dept_ip(emp["employee_id"])
        num_actions = random.randint(20, 60)

        # Generate sorted timestamps between 09:00:00 and 16:59:59
        seconds_pool = sorted(random.sample(range(0, 8 * 3600), k=num_actions))
        base_dt = datetime.combine(day, time(9, 0, 0))

        # First action is a login
        login_ts = base_dt + timedelta(seconds=seconds_pool[0])
        write_audit(
            employee_id=emp["employee_id"],
            department=emp["department"],
            role=emp["role"],
            action="login",
            doc_id="",
            doc_title="",
            sensitivity="normal",
            bytes_transferred=0,
            device="managed",
            source_ip=ip,
            outcome="success",
            timestamp=login_ts,
        )
        events_written += 1

        for offset in seconds_pool[1:]:
            doc = random.choice(docs)
            action = "download" if random.random() < 0.15 else "view"
            size = min(doc["size_bytes"], 5 * 1024 * 1024) if action == "download" else 0
            ts = base_dt + timedelta(seconds=offset)
            write_audit(
                employee_id=emp["employee_id"],
                department=emp["department"],
                role=emp["role"],
                action=action,
                doc_id=doc["doc_id"],
                doc_title=doc["title"],
                sensitivity=doc["sensitivity"],
                bytes_transferred=size,
                device="managed",
                source_ip=ip,
                outcome="success",
                timestamp=ts,
            )
            events_written += 1

    return events_written


def run_backfill_14_days() -> int:
    """Run normal workday simulation for the past 14 weekdays to build baselines."""
    weekdays: List[date] = []
    cursor = date.today() - timedelta(days=1)
    while len(weekdays) < 14:
        if cursor.weekday() < 5:  # Mon-Fri
            weekdays.append(cursor)
        cursor -= timedelta(days=1)

    total = 0
    for d in reversed(weekdays):
        total += run_normal_workday(target_date=d)
    return total


def run_bulk_read_at_night() -> int:
    """One employee reads 400 documents between 02:00 and 02:30."""
    emp = get_employee("E014") or get_all_employees()[0]
    docs = _normal_docs_for_employee(emp["department"])
    ip = _dept_ip(emp["employee_id"])
    base_dt = datetime.combine(date.today(), time(2, 0, 0))

    for i in range(400):
        doc = docs[i % len(docs)]
        ts = base_dt + timedelta(seconds=int((i / 400) * 1800))
        write_audit(
            employee_id=emp["employee_id"],
            department=emp["department"],
            role=emp["role"],
            action="view",
            doc_id=doc["doc_id"],
            doc_title=doc["title"],
            sensitivity=doc["sensitivity"],
            bytes_transferred=0,
            device="managed",
            source_ip=ip,
            outcome="success",
            timestamp=ts,
        )

    time_str = base_dt.strftime("%Y-%m-%dT%H:%M:%S")
    write_ground_truth("bulk_access", emp["employee_id"], time_str, "TP")
    write_ground_truth("off_hours", emp["employee_id"], time_str, "TP")
    return 400


def run_large_export() -> int:
    """A low-volume employee exports ~1.2 GB."""
    emp = get_employee("E016") or get_all_employees()[0]
    docs = get_documents_for_department(emp["department"], include_shared=False)
    large_doc = max(docs, key=lambda d: d["size_bytes"])
    ip = _dept_ip(emp["employee_id"])
    base_dt = datetime.combine(date.today(), time(14, 15, 0))

    # Two exports totaling ~1.2 GB (800 MB + 400 MB)
    sizes = [800 * 1024 * 1024, 400 * 1024 * 1024]
    for idx, sz in enumerate(sizes):
        ts = base_dt + timedelta(minutes=idx * 2)
        write_audit(
            employee_id=emp["employee_id"],
            department=emp["department"],
            role=emp["role"],
            action="export",
            doc_id=large_doc["doc_id"],
            doc_title=large_doc["title"],
            sensitivity=large_doc["sensitivity"],
            bytes_transferred=sz,
            device="managed",
            source_ip=ip,
            outcome="success",
            timestamp=ts,
        )

    write_ground_truth("atypical_download", emp["employee_id"], base_dt.strftime("%Y-%m-%dT%H:%M:%S"), "TP")
    return len(sizes)


def run_cross_department_access() -> int:
    """A Sales user opens 5 HR payroll files."""
    emp = get_employee("E019") or get_all_employees()[0]
    hr_docs = [
        d for d in get_documents_for_department("HR", include_shared=False)
        if d["sensitivity"] == "restricted"
    ][:5]
    ip = _dept_ip(emp["employee_id"])
    base_dt = datetime.combine(date.today(), time(11, 20, 0))

    for idx, doc in enumerate(hr_docs):
        ts = base_dt + timedelta(seconds=idx * 25)
        write_audit(
            employee_id=emp["employee_id"],
            department=emp["department"],
            role=emp["role"],
            action="view",
            doc_id=doc["doc_id"],
            doc_title=doc["title"],
            sensitivity=doc["sensitivity"],
            bytes_transferred=0,
            device="managed",
            source_ip=ip,
            outcome="success",
            timestamp=ts,
        )

    write_ground_truth("policy_violation", emp["employee_id"], base_dt.strftime("%Y-%m-%dT%H:%M:%S"), "TP")
    return len(hr_docs)


def run_unmanaged_device_download() -> int:
    """Restricted file downloaded with device = unmanaged."""
    emp = get_employee("E002") or get_all_employees()[0]
    restricted_docs = [
        d for d in get_documents_for_department(emp["department"], include_shared=False)
        if d["sensitivity"] == "restricted"
    ]
    doc = restricted_docs[0] if restricted_docs else get_all_documents()[0]
    ts = datetime.combine(date.today(), time(15, 5, 0))

    write_audit(
        employee_id=emp["employee_id"],
        department=emp["department"],
        role=emp["role"],
        action="download",
        doc_id=doc["doc_id"],
        doc_title=doc["title"],
        sensitivity=doc["sensitivity"],
        bytes_transferred=doc["size_bytes"],
        device="unmanaged",
        source_ip="203.0.113.45",
        outcome="success",
        timestamp=ts,
    )

    write_ground_truth("policy_violation", emp["employee_id"], ts.strftime("%Y-%m-%dT%H:%M:%S"), "TP")
    return 1


def run_repeated_failed_logins() -> int:
    """7 login_failed in a row, then 1 success."""
    emp = get_employee("E008") or get_all_employees()[0]
    ip = _dept_ip(emp["employee_id"])
    base_dt = datetime.combine(date.today(), time(10, 40, 0))

    for i in range(7):
        ts = base_dt + timedelta(seconds=i * 8)
        write_audit(
            employee_id=emp["employee_id"],
            department=emp["department"],
            role=emp["role"],
            action="login_failed",
            doc_id="",
            doc_title="",
            sensitivity="normal",
            bytes_transferred=0,
            device="managed",
            source_ip=ip,
            outcome="denied",
            timestamp=ts,
        )

    success_ts = base_dt + timedelta(seconds=7 * 8 + 5)
    write_audit(
        employee_id=emp["employee_id"],
        department=emp["department"],
        role=emp["role"],
        action="login",
        doc_id="",
        doc_title="",
        sensitivity="normal",
        bytes_transferred=0,
        device="managed",
        source_ip=ip,
        outcome="success",
        timestamp=success_ts,
    )

    write_ground_truth("policy_violation", emp["employee_id"], base_dt.strftime("%Y-%m-%dT%H:%M:%S"), "TP")
    return 8


def run_first_time_sensitive_access() -> int:
    """An employee opens a restricted doc never seen before."""
    emp = get_employee("E013") or get_all_employees()[0]
    docs = [
        d for d in get_documents_for_department(emp["department"], include_shared=False)
        if d["sensitivity"] == "restricted"
    ]
    doc = docs[-1] if docs else get_all_documents()[0]
    ip = _dept_ip(emp["employee_id"])
    ts = datetime.combine(date.today(), time(13, 10, 0))

    write_audit(
        employee_id=emp["employee_id"],
        department=emp["department"],
        role=emp["role"],
        action="view",
        doc_id=doc["doc_id"],
        doc_title=doc["title"],
        sensitivity=doc["sensitivity"],
        bytes_transferred=0,
        device="managed",
        source_ip=ip,
        outcome="success",
        timestamp=ts,
    )

    write_ground_truth("new_sensitive_resource", emp["employee_id"], ts.strftime("%Y-%m-%dT%H:%M:%S"), "TP")
    return 1


def run_legitimate_month_end_export() -> int:
    """A Finance user exports a large report (expected false positive for demo)."""
    emp = get_employee("E007") or get_all_employees()[0]
    finance_docs = get_documents_for_department("Finance", include_shared=False)
    large_report = max(finance_docs, key=lambda d: d["size_bytes"])
    ip = _dept_ip(emp["employee_id"])
    ts = datetime.combine(date.today(), time(16, 30, 0))

    write_audit(
        employee_id=emp["employee_id"],
        department=emp["department"],
        role=emp["role"],
        action="export",
        doc_id=large_report["doc_id"],
        doc_title=large_report["title"],
        sensitivity=large_report["sensitivity"],
        bytes_transferred=large_report["size_bytes"],
        device="managed",
        source_ip=ip,
        outcome="success",
        timestamp=ts,
    )

    write_ground_truth("atypical_download", emp["employee_id"], ts.strftime("%Y-%m-%dT%H:%M:%S"), "FP")
    return 1


def _live_worker(stop_event: threading.Event) -> None:
    employees = get_all_employees()
    while not stop_event.is_set():
        delay = random.uniform(3.0, 10.0)
        if stop_event.wait(delay):
            break
        emp = random.choice(employees)
        docs = _normal_docs_for_employee(emp["department"])
        doc = random.choice(docs)
        action = "download" if random.random() < 0.2 else "view"
        size = min(doc["size_bytes"], 2 * 1024 * 1024) if action == "download" else 0
        evt = write_audit(
            employee_id=emp["employee_id"],
            department=emp["department"],
            role=emp["role"],
            action=action,
            doc_id=doc["doc_id"],
            doc_title=doc["title"],
            sensitivity=doc["sensitivity"],
            bytes_transferred=size,
            device="managed",
            source_ip=_dept_ip(emp["employee_id"]),
            outcome="success",
        )
        _LIVE_STATS["events_emitted"] = int(_LIVE_STATS["events_emitted"]) + 1
        _LIVE_STATS["last_event"] = f"{evt['timestamp']} {emp['employee_id']} {action} {doc['doc_id']}"


def start_live_mode() -> None:
    """Start background thread emitting a random normal action every 3-10 seconds."""
    global _LIVE_STOP_EVENT, _LIVE_THREAD
    with _LIVE_LOCK:
        if _LIVE_THREAD is not None and _LIVE_THREAD.is_alive():
            return
        _LIVE_STOP_EVENT = threading.Event()
        _LIVE_STATS["running"] = True
        _LIVE_THREAD = threading.Thread(
            target=_live_worker,
            args=(_LIVE_STOP_EVENT,),
            daemon=True,
            name="dunmore-live-mode",
        )
        _LIVE_THREAD.start()


def stop_live_mode() -> None:
    """Stop the live mode background thread."""
    global _LIVE_STOP_EVENT, _LIVE_THREAD
    with _LIVE_LOCK:
        if _LIVE_STOP_EVENT is not None:
            _LIVE_STOP_EVENT.set()
        _LIVE_STATS["running"] = False
        _LIVE_THREAD = None


def get_live_stats() -> Dict[str, object]:
    """Return current live mode status and stats."""
    is_alive = _LIVE_THREAD is not None and _LIVE_THREAD.is_alive()
    return {
        "running": bool(is_alive),
        "events_emitted": _LIVE_STATS["events_emitted"],
        "last_event": _LIVE_STATS["last_event"],
    }

