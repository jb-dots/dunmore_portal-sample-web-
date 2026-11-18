# Dunmore Corp Portal

> **Demo company. All data is fictional.**

Dunmore Corp Portal is a standalone internal document portal simulator that generates realistic employee document-access audit logs (`company_audit.jsonl`) and scenario ground truth (`company_ground_truth.csv`) for **HuliCAP Insider Threat Monitor** to ingest and analyze.

## Quick Start

1. Seed the SQLite database (`portal.db` with 24 fictional employees and 32 fictional documents):
   ```bash
   python seed.py
   ```
2. Start the Streamlit portal on port `8600`:
   ```bash
   streamlit run app.py --server.port 8600
   ```
3. Open `http://localhost:8600`, go to the **Simulator** tab, and click **Backfill 14 days** to build baseline history before triggering threat scenarios.

## Configuration

All file paths and the server port are configured in `config.yaml`:

```yaml
audit_log_path: "company_audit.jsonl"
ground_truth_path: "company_ground_truth.csv"
db_path: "portal.db"
port: 8600
```

## Audit Log Format (`company_audit.jsonl`)

Each action appends one JSON object per line (no file contents are ever stored or logged):

```json
{
  "event_id": "evt_a1b2c3d4e5f6",
  "timestamp": "2026-11-17T09:14:22",
  "employee_id": "E014",
  "department": "Engineering",
  "role": "Backend Engineer",
  "action": "view",
  "doc_id": "DOC-017",
  "doc_title": "API Gateway Architecture Spec",
  "sensitivity": "normal",
  "bytes": 0,
  "device": "managed",
  "source_ip": "10.20.3.24",
  "outcome": "success"
}
```

- **Actions:** `login`, `login_failed`, `view`, `download`, `export`, `access_denied`
- **Sensitivity:** `normal`, `restricted`
- **Device:** `managed`, `unmanaged`
- **Outcome:** `success`, `denied`

