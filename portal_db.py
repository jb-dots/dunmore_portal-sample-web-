"""Database query helpers for Dunmore Corp Portal."""

import sqlite3
from typing import Any, Dict, List, Optional
from config_loader import load_config


def _get_conn() -> sqlite3.Connection:
    cfg = load_config()
    conn = sqlite3.connect(cfg["db_path"])
    conn.row_factory = sqlite3.Row
    return conn


def get_all_employees() -> List[Dict[str, Any]]:
    """Return all fictional employees sorted by employee_id."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT employee_id, name, department, role FROM employees ORDER BY employee_id"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_employee(employee_id: str) -> Optional[Dict[str, Any]]:
    """Return a single employee by employee_id."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT employee_id, name, department, role FROM employees WHERE employee_id = ?",
            (employee_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_documents() -> List[Dict[str, Any]]:
    """Return all fictional documents sorted by doc_id."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT doc_id, title, department, sensitivity, size_bytes, is_shared FROM documents ORDER BY doc_id"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_documents_for_department(department: str, include_shared: bool = True) -> List[Dict[str, Any]]:
    """Return documents belonging to a department (and optionally shared docs)."""
    conn = _get_conn()
    try:
        if include_shared:
            rows = conn.execute(
                "SELECT doc_id, title, department, sensitivity, size_bytes, is_shared "
                "FROM documents WHERE department = ? OR is_shared = 1 ORDER BY doc_id",
                (department,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT doc_id, title, department, sensitivity, size_bytes, is_shared "
                "FROM documents WHERE department = ? ORDER BY doc_id",
                (department,),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

