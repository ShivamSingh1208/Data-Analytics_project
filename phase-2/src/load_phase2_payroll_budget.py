from pathlib import Path
import os
import pandas as pd
from sqlalchemy import create_engine, text

files = list(Path(" data").glob("*budget_payroll_dept_month.csv"))
if len(files) != 1:
    raise FileNotFoundError(
        f"Expected one payroll budget CSV; found {len(files)}"
    )

df = pd.read_csv(files[0], low_memory=False)
df.columns = df.columns.str.strip()

required = ["department_id", "month", "budget_payroll_cost"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

df = df[required].copy()
df["department_id"] = df["department_id"].astype("string").str.strip()
df["month"] = pd.to_datetime(df["month"], errors="raise").dt.to_period("M").dt.to_timestamp()
df["budget_payroll_cost"] = pd.to_numeric(
    df["budget_payroll_cost"]
      .astype("string")
      .str.replace(",", "", regex=False)
      .str.strip(),
    errors="raise",
)

if df[required].isna().any().any():
    raise ValueError("Budget file contains missing required values")

if df.duplicated(["department_id", "month"]).any():
    raise ValueError("Duplicate department-month budget keys found")

if (df["budget_payroll_cost"] < 0).any():
    raise ValueError("Negative budget values found")

if len(df) != 198:
    raise ValueError(f"Expected 198 rows, found {len(df)}")

url = os.environ.get("DATABASE_URL")
if not url:
    raise EnvironmentError("DATABASE_URL is not set")

engine = create_engine(url)

with engine.begin() as conn:
    existing = conn.execute(
        text("SELECT COUNT(*) FROM dw.phase2_payroll_budget")
    ).scalar_one()

    if existing:
        raise RuntimeError(
            f"Budget table already has {existing} rows; refusing duplicate load."
        )

    departments = {
        row[0] for row in conn.execute(
            text("SELECT department_id FROM dw.dim_department")
        )
    }
    unknown = sorted(set(df["department_id"]) - departments)
    if unknown:
        raise ValueError(f"Unknown department IDs: {unknown}")

    df.to_sql(
        "phase2_payroll_budget",
        conn,
        schema="dw",
        if_exists="append",
        index=False,
        method="multi",
    )

    result = conn.execute(text("""
        SELECT COUNT(*) AS rows_loaded,
               COUNT(DISTINCT department_id) AS departments,
               COUNT(DISTINCT month) AS months,
               MIN(month) AS first_month,
               MAX(month) AS last_month,
               SUM(budget_payroll_cost) AS total_budget
        FROM dw.phase2_payroll_budget
    """)).mappings().one()

    print("Payroll budget loaded successfully:")
    print(dict(result))
