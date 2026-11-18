"""Dunmore Corp Portal — Fictional Internal Document Portal & Audit Simulator.

Run:
    python seed.py
    streamlit run app.py --server.port 8600
"""

from pathlib import Path
import pandas as pd
import streamlit as st

from audit import write_audit
from config_loader import load_config
from portal_db import get_all_documents, get_all_employees
from seed import seed_database
from simulator import (
    get_live_stats,
    run_backfill_14_days,
    run_bulk_read_at_night,
    run_cross_department_access,
    run_first_time_sensitive_access,
    run_large_export,
    run_legitimate_month_end_export,
    run_normal_workday,
    run_repeated_failed_logins,
    run_unmanaged_device_download,
    start_live_mode,
    stop_live_mode,
)

st.set_page_config(
    page_title="Dunmore Corp Portal",
    page_icon="🏢",
    layout="wide",
)


def _format_size(num_bytes: int) -> str:
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MB"
    return f"{num_bytes / 1024:.0f} KB"


def _ensure_db_seeded() -> None:
    cfg = load_config()
    if not cfg["db_path"].exists():
        seed_database()


_ensure_db_seeded()
cfg = load_config()

# Header & Fictional Data Notice
st.markdown(
    """
    <div style="background:#0f172a;color:#f8fafc;padding:14px 20px;border-radius:10px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;">
        <div>
            <div style="font-size:1.35rem;font-weight:700;letter-spacing:-0.01em;">🏢 Dunmore Corp — Internal Document Portal</div>
            <div style="font-size:0.85rem;color:#94a3b8;">Audit stream target: <code>company_audit.jsonl</code></div>
        </div>
        <div style="background:#1e293b;border:1px solid #334155;color:#fde68a;padding:6px 12px;border-radius:6px;font-size:0.82rem;font-weight:600;">
            Demo company. All data is fictional.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

employees = get_all_employees()
emp_map = {e["employee_id"]: e for e in employees}

if "current_user" not in st.session_state:
    st.session_state["current_user"] = None
if "current_device" not in st.session_state:
    st.session_state["current_device"] = "managed"
if "viewed_doc" not in st.session_state:
    st.session_state["viewed_doc"] = None

tab_portal, tab_simulator = st.tabs(["📁 Document Portal", "🧪 Simulator"])

with tab_portal:
    col_auth, col_main = st.columns([1, 3], gap="large")

    with col_auth:
        st.subheader("Employee Sign-In")
        emp_labels = {
            e["employee_id"]: f"{e['employee_id']} — {e['name']} ({e['department']})"
            for e in employees
        }
        selected_id = st.selectbox(
            "Select Employee",
            options=list(emp_labels.keys()),
            format_func=lambda k: emp_labels[k],
            key="signin_select",
        )
        device_choice = st.radio(
            "Device Posture",
            options=["managed", "unmanaged"],
            horizontal=True,
            key="device_radio",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sign In", type="primary", use_container_width=True):
                emp = emp_map[selected_id]
                st.session_state["current_user"] = emp
                st.session_state["current_device"] = device_choice
                st.session_state["viewed_doc"] = None
                ip = "10.20.1.50" if device_choice == "managed" else "203.0.113.88"
                write_audit(
                    employee_id=emp["employee_id"],
                    department=emp["department"],
                    role=emp["role"],
                    action="login",
                    device=device_choice,
                    source_ip=ip,
                    outcome="success",
                )
                st.success(f"Signed in as {emp['name']}")
        with c2:
            if st.button("Sign Out", use_container_width=True):
                st.session_state["current_user"] = None
                st.session_state["viewed_doc"] = None

        user = st.session_state["current_user"]
        if user:
            st.info(
                f"**Active User:** {user['name']} (`{user['employee_id']}`)\n\n"
                f"**Department:** {user['department']}\n\n"
                f"**Role:** {user['role']}\n\n"
                f"**Device:** `{st.session_state['current_device']}`"
            )
        else:
            st.warning("Select an employee and click **Sign In** to access documents.")

    with col_main:
        st.subheader("Document Library")
        search_col, dept_col, sens_col = st.columns([2, 1, 1])
        with search_col:
            search_q = st.text_input("Search documents", placeholder="Search by title or doc ID...")
        with dept_col:
            dept_filter = st.selectbox(
                "Department",
                options=["All", "HR", "Finance", "Engineering", "Sales", "Shared"],
            )
        with sens_col:
            sens_filter = st.selectbox("Sensitivity", options=["All", "normal", "restricted"])

        docs = get_all_documents()
        if search_q.strip():
            q = search_q.strip().lower()
            docs = [d for d in docs if q in d["title"].lower() or q in d["doc_id"].lower()]
        if dept_filter != "All":
            docs = [d for d in docs if d["department"] == dept_filter]
        if sens_filter != "All":
            docs = [d for d in docs if d["sensitivity"] == sens_filter]

        user = st.session_state["current_user"]
        device = st.session_state["current_device"]
        ip = "10.20.1.50" if device == "managed" else "203.0.113.88"

        if st.session_state["viewed_doc"] and user:
            vd = st.session_state["viewed_doc"]
            st.success(
                f"Viewing **{vd['doc_id']} — {vd['title']}** "
                f"(Department: `{vd['department']}`, Sensitivity: `{vd['sensitivity']}`, "
                f"Size: {_format_size(vd['size_bytes'])}). *Metadata only — no file contents stored.*"
            )

        st.caption(f"Showing {len(docs)} of 32 fictional documents. Cross-department reads are permitted and logged.")

        for doc in docs:
            with st.container(border=True):
                c_info, c_meta, c_actions = st.columns([3, 2, 2])
                with c_info:
                    badge = "🔒 RESTRICTED" if doc["sensitivity"] == "restricted" else "📄 NORMAL"
                    st.markdown(f"**`{doc['doc_id']}` — {doc['title']}**")
                    st.caption(f"Department: **{doc['department']}** · {badge}")
                with c_meta:
                    st.write(f"Size: **{_format_size(doc['size_bytes'])}**")
                    if user and doc["department"] not in (user["department"], "Shared"):
                        st.caption("⚠️ Outside your department (logged)")
                with c_actions:
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("View", key=f"view_{doc['doc_id']}", disabled=(user is None), use_container_width=True):
                            write_audit(
                                employee_id=user["employee_id"],
                                department=user["department"],
                                role=user["role"],
                                action="view",
                                doc_id=doc["doc_id"],
                                doc_title=doc["title"],
                                sensitivity=doc["sensitivity"],
                                bytes_transferred=0,
                                device=device,
                                source_ip=ip,
                                outcome="success",
                            )
                            st.session_state["viewed_doc"] = doc
                            st.rerun()
                    with b2:
                        if st.button("Download", key=f"dl_{doc['doc_id']}", disabled=(user is None), use_container_width=True):
                            write_audit(
                                employee_id=user["employee_id"],
                                department=user["department"],
                                role=user["role"],
                                action="download",
                                doc_id=doc["doc_id"],
                                doc_title=doc["title"],
                                sensitivity=doc["sensitivity"],
                                bytes_transferred=doc["size_bytes"],
                                device=device,
                                source_ip=ip,
                                outcome="success",
                            )
                            st.toast(f"Logged download of {doc['doc_id']} ({_format_size(doc['size_bytes'])})")

with tab_simulator:
    st.subheader("Audit & Threat Scenario Simulator")
    st.caption(
        "Run **Backfill 14 days** first so HuliCAP's median/MAD baselines have history before running attack scenarios."
    )

    # Baseline & Live Mode Row
    b_col1, b_col2, b_col3 = st.columns([1, 1, 1.5])
    with b_col1:
        if st.button("📅 Backfill 14 days", type="primary", use_container_width=True):
            count = run_backfill_14_days()
            st.success(f"Backfilled 14 weekdays ({count:,} normal audit events written).")
    with b_col2:
        if st.button("☀️ Normal workday", use_container_width=True):
            count = run_normal_workday()
            st.success(f"Simulated 1 normal workday ({count:,} audit events written).")
    with b_col3:
        stats = get_live_stats()
        live_on = st.toggle("🟢 Live mode (random normal action every 3–10s)", value=bool(stats["running"]))
        if live_on and not stats["running"]:
            start_live_mode()
            st.rerun()
        elif not live_on and stats["running"]:
            stop_live_mode()
            st.rerun()
        if stats["running"]:
            st.caption(f"Live mode active · Emitted: {stats['events_emitted']} · Last: `{stats['last_event']}`")

    st.divider()
    st.markdown("#### Insider Threat & Policy Scenarios")

    s_col1, s_col2, s_col3, s_col4 = st.columns(4)
    with s_col1:
        if st.button("🌙 Bulk read at night", use_container_width=True):
            n = run_bulk_read_at_night()
            st.warning(f"Logged {n} reads at 02:00–02:30 for E014. Ground truth: bulk_access + off_hours (TP).")
        if st.button("🔑 Repeated failed logins", use_container_width=True):
            n = run_repeated_failed_logins()
            st.warning(f"Logged 7 login_failed + 1 login for E008 ({n} events). Ground truth: policy_violation (TP).")
    with s_col2:
        if st.button("📦 Large export (~1.2 GB)", use_container_width=True):
            n = run_large_export()
            st.warning(f"Logged ~1.2 GB export for E016 ({n} events). Ground truth: atypical_download (TP).")
        if st.button("🆕 First-time sensitive access", use_container_width=True):
            n = run_first_time_sensitive_access()
            st.warning(f"Logged first-time restricted view for E013 ({n} event). Ground truth: new_sensitive_resource (TP).")
    with s_col3:
        if st.button("🔀 Cross-department access", use_container_width=True):
            n = run_cross_department_access()
            st.warning(f"Sales user E019 opened {n} HR payroll files. Ground truth: policy_violation (TP).")
        if st.button("📅 Legitimate month-end export (FP)", use_container_width=True):
            n = run_legitimate_month_end_export()
            st.info(f"Finance user E007 exported month-end ledger ({n} event). Ground truth: atypical_download (FP).")
    with s_col4:
        if st.button("📱 Unmanaged device download", use_container_width=True):
            n = run_unmanaged_device_download()
            st.warning(f"Logged restricted download from unmanaged device for E002 ({n} event). Ground truth: policy_violation (TP).")

    st.divider()
    log_col, gt_col = st.columns(2)
    with log_col:
        st.markdown("#### Recent `company_audit.jsonl` Lines")
        log_path: Path = cfg["audit_log_path"]
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            st.caption(f"Total lines: {len(lines):,} | Path: `{log_path}`")
            st.code("".join(lines[-10:]), language="json")
        else:
            st.info("No audit log entries yet. Click **Backfill 14 days** to begin.")

    with gt_col:
        st.markdown("#### `company_ground_truth.csv`")
        gt_path: Path = cfg["ground_truth_path"]
        if gt_path.exists():
            gt_df = pd.read_csv(gt_path)
            st.dataframe(gt_df, use_container_width=True, hide_index=True)
        else:
            st.info("No ground truth scenarios triggered yet.")

