"""Seed script for Dunmore Corp Portal SQLite database.

Demo company. All data is fictional.
"""

import sqlite3
from config_loader import load_config

EMPLOYEES = [
    # HR (6)
    ("E001", "Elena Rostova", "HR", "HR Manager"),
    ("E002", "Marcus Vance", "HR", "Payroll Specialist"),
    ("E003", "Hannah Abbott", "HR", "Talent Recruiter"),
    ("E004", "David Kim", "HR", "Benefits Coordinator"),
    ("E005", "Priya Nair", "HR", "HR Generalist"),
    ("E006", "Lucas Thorne", "HR", "Compensation Analyst"),
    # Finance (6)
    ("E007", "Arthur Pendelton", "Finance", "Controller"),
    ("E008", "Sophia Chen", "Finance", "Senior Financial Analyst"),
    ("E009", "Omar Farooq", "Finance", "Accounts Payable Lead"),
    ("E010", "Claire Dubois", "Finance", "Tax Accountant"),
    ("E011", "Nathan Brooks", "Finance", "Treasury Analyst"),
    ("E012", "Mei Lin", "Finance", "Budget Specialist"),
    # Engineering (6)
    ("E013", "Liam O'Connor", "Engineering", "Staff Engineer"),
    ("E014", "Aisha Patel", "Engineering", "Backend Engineer"),
    ("E015", "Noah Takahashi", "Engineering", "DevOps Engineer"),
    ("E016", "Chloe Martin", "Engineering", "Frontend Engineer"),
    ("E017", "Victor Alvarez", "Engineering", "Security Engineer"),
    ("E018", "Grace Liu", "Engineering", "QA Lead"),
    # Sales (6)
    ("E019", "Jordan Belfry", "Sales", "Enterprise Account Exec"),
    ("E020", "Maya Santiago", "Sales", "Sales Manager"),
    ("E021", "Ethan Huntley", "Sales", "Account Representative"),
    ("E022", "Zoe Kravitz-Cole", "Sales", "Solutions Consultant"),
    ("E023", "Ryan Gallagher", "Sales", "Business Development Rep"),
    ("E024", "Tessa Lindqvist", "Sales", "Partner Manager"),
]

# 32 fake documents: 7 HR, 7 Finance, 7 Engineering, 7 Sales, 4 Shared
# Sizes range from 50 KB (51,200) to 800 MB (838,860,800)
KB = 1024
MB = 1024 * 1024

DOCUMENTS = [
    # HR (7) - Payroll & sensitive HR records marked restricted
    ("DOC-001", "Q3 Executive Payroll Register", "HR", "restricted", 18 * MB, 0),
    ("DOC-002", "2026 Employee Salary Bands", "HR", "restricted", 6 * MB, 0),
    ("DOC-003", "Monthly Payroll Disbursement Sheet", "HR", "restricted", 12 * MB, 0),
    ("DOC-004", "Employee Tax Withholding Ledger", "HR", "restricted", 9 * MB, 0),
    ("DOC-005", "Bonus & Equity Allocation Payroll", "HR", "restricted", 15 * MB, 0),
    ("DOC-006", "Onboarding Checklist 2026", "HR", "normal", 240 * KB, 0),
    ("DOC-007", "Annual Performance Review Template", "HR", "normal", 520 * KB, 0),

    # Finance (7) - Financial reports & ledgers marked restricted
    ("DOC-008", "FY2026 Consolidated Financial Report", "Finance", "restricted", 450 * MB, 0),
    ("DOC-009", "Q3 Board Audit & Revenue Report", "Finance", "restricted", 280 * MB, 0),
    ("DOC-010", "Month-End General Ledger Export", "Finance", "restricted", 600 * MB, 0),
    ("DOC-011", "Corporate Tax Filing Workpapers", "Finance", "restricted", 120 * MB, 0),
    ("DOC-012", "Vendor Payment Reconciliation", "Finance", "normal", 4 * MB, 0),
    ("DOC-013", "Departmental Budget Guidelines", "Finance", "normal", 850 * KB, 0),
    ("DOC-014", "Travel Expense Policy FAQ", "Finance", "normal", 110 * KB, 0),

    # Engineering (7)
    ("DOC-015", "Core Platform Database Snapshot", "Engineering", "restricted", 800 * MB, 0),
    ("DOC-016", "Production Secrets Rotation Runbook", "Engineering", "restricted", 2 * MB, 0),
    ("DOC-017", "API Gateway Architecture Spec", "Engineering", "normal", 3 * MB, 0),
    ("DOC-018", "CI/CD Pipeline Configuration Guide", "Engineering", "normal", 640 * KB, 0),
    ("DOC-019", "Microservices Telemetry Schema", "Engineering", "normal", 180 * KB, 0),
    ("DOC-020", "Release v4.2 QA Test Matrix", "Engineering", "normal", 950 * KB, 0),
    ("DOC-021", "Incident Postmortem Template", "Engineering", "normal", 75 * KB, 0),

    # Sales (7)
    ("DOC-022", "Global Enterprise CRM Dump", "Sales", "restricted", 620 * MB, 0),
    ("DOC-023", "Strategic Accounts Pricing Matrix", "Sales", "restricted", 14 * MB, 0),
    ("DOC-024", "Q4 Sales Pipeline Forecast", "Sales", "normal", 2 * MB, 0),
    ("DOC-025", "Enterprise Demo Playbook", "Sales", "normal", 5 * MB, 0),
    ("DOC-026", "Partner Reseller Agreement Draft", "Sales", "normal", 410 * KB, 0),
    ("DOC-027", "Customer Case Study Deck", "Sales", "normal", 11 * MB, 0),
    ("DOC-028", "Cold Outreach Email Templates", "Sales", "normal", 50 * KB, 0),

    # Shared across all departments (4)
    ("DOC-029", "Dunmore Corp Employee Handbook", "Shared", "normal", 1 * MB, 1),
    ("DOC-030", "2026 Company Holiday Calendar", "Shared", "normal", 65 * KB, 1),
    ("DOC-031", "IT Acceptable Use & Security Policy", "Shared", "normal", 320 * KB, 1),
    ("DOC-032", "Office Evacuation & Safety Map", "Shared", "normal", 780 * KB, 1),
]


def seed_database() -> None:
    """Create and populate portal.db with fictional employees and documents."""
    cfg = load_config()
    db_path = cfg["db_path"]

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS employees")
        cur.execute("DROP TABLE IF EXISTS documents")

        cur.execute(
            """
            CREATE TABLE employees (
                employee_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE documents (
                doc_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                department TEXT NOT NULL,
                sensitivity TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                is_shared INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        cur.executemany(
            "INSERT INTO employees (employee_id, name, department, role) VALUES (?, ?, ?, ?)",
            EMPLOYEES,
        )
        cur.executemany(
            "INSERT INTO documents (doc_id, title, department, sensitivity, size_bytes, is_shared) VALUES (?, ?, ?, ?, ?, ?)",
            DOCUMENTS,
        )
        conn.commit()
    finally:
        conn.close()

    print(f"Seeded {len(EMPLOYEES)} employees and {len(DOCUMENTS)} documents into {db_path}")


if __name__ == "__main__":
    seed_database()

