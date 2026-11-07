from pathlib import Path
import os
import pandas as pd
from sqlalchemy import create_engine, text

key_files = list(Path(" data").glob("*reconciliation_answer_key.csv"))
if len(key_files) != 1:
    raise FileNotFoundError(
        f"Expected one reconciliation answer key; found {len(key_files)}"
    )

key = pd.read_csv(key_files[0], low_memory=False)
key.columns = key.columns.str.strip()

required = [
    "month", "employees_paid", "payroll_gross_pay", "payroll_net_pay",
    "payroll_employer_cost", "ledger_salary_related_expense",
    "ledger_revenue", "ledger_total_expense", "ledger_net_profit",
    "bank_closing_balance", "receivables_closing_balance",
    "payroll_vs_ledger_difference",
]
missing = [c for c in required if c not in key.columns]
if missing:
    raise ValueError(f"Missing answer-key columns: {missing}")

key = key[required].copy()
key["month"] = pd.to_datetime(key["month"], errors="raise").dt.to_period("M").dt.to_timestamp()

for col in required[1:]:
    key[col] = pd.to_numeric(
        key[col].astype("string").str.replace(",", "", regex=False).str.strip(),
        errors="raise"
    )

if key["month"].duplicated().any():
    raise ValueError("Answer key contains duplicate months")

if len(key) != 18:
    raise ValueError(f"Expected 18 monthly records, found {len(key)}")

url = os.environ.get("DATABASE_URL")
if not url:
    raise EnvironmentError(
        "DATABASE_URL is not set. Source your .env and export DATABASE_URL first."
    )

engine = create_engine(url)

with engine.begin() as conn:
    existing = conn.execute(
        text("SELECT COUNT(*) FROM dw.phase2_payroll_reference")
    ).scalar_one()

    if existing:
        raise RuntimeError(
            f"Reference table already has {existing} rows; refusing duplicate load."
        )

    key.to_sql(
        "phase2_payroll_reference",
        conn,
        schema="dw",
        if_exists="append",
        index=False,
        method="multi",
    )

    count = conn.execute(
        text("SELECT COUNT(*) FROM dw.phase2_payroll_reference")
    ).scalar_one()

    print(f"Loaded monthly reference rows: {count}")
    print(
        conn.execute(text("""
            SELECT MIN(month) AS first_month,
                   MAX(month) AS last_month,
                   SUM(payroll_employer_cost) AS reference_employer_cost,
                   SUM(payroll_vs_ledger_difference) AS total_reconciliation_difference
            FROM dw.phase2_payroll_reference
        """)).mappings().one()
    )
