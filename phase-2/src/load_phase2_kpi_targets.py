from pathlib import Path
import os
import pandas as pd
from sqlalchemy import create_engine, text

files = list(Path(" data").glob("*kpi_targets.csv"))
if len(files) != 1:
    raise FileNotFoundError(
        f"Expected one KPI targets CSV; found {len(files)}"
    )

df = pd.read_csv(files[0], low_memory=False)
df.columns = df.columns.str.strip()

columns = [
    "month",
    "department_id",
    "attendance_rate_target",
    "overtime_share_target_pct",
    "attrition_monthly_target_pct",
    "task_completion_target_pct",
]

if any(c not in df.columns for c in columns):
    raise ValueError(f"Required columns missing. Found: {df.columns.tolist()}")

df = df[columns].copy()
df["month"] = (
    pd.to_datetime(df["month"], errors="raise")
    .dt.to_period("M")
    .dt.to_timestamp()
)
df["department_id"] = df["department_id"].astype("string").str.strip()

numeric_columns = columns[2:]
for col in numeric_columns:
    df[col] = pd.to_numeric(
        df[col].astype("string").str.replace(",", "", regex=False),
        errors="raise",
    )

if df[["month", "department_id"]].isna().any().any():
    raise ValueError("Missing month or department ID")

if df.duplicated(["month", "department_id"]).any():
    raise ValueError("Duplicate month-department keys found")

if len(df) != 180:
    raise ValueError(f"Expected 180 rows; found {len(df)}")

if df["department_id"].nunique() != 10:
    raise ValueError("Expected 10 departments in the source targets")

url = os.environ.get("DATABASE_URL")
if not url:
    raise EnvironmentError("DATABASE_URL is not set")

engine = create_engine(url)

with engine.begin() as conn:
    existing = conn.execute(
        text("SELECT COUNT(*) FROM dw.phase2_kpi_targets")
    ).scalar_one()
    if existing:
        raise RuntimeError(
            f"KPI target table already has {existing} rows; refusing duplicate load."
        )

    known_departments = {
        row[0] for row in conn.execute(
            text("SELECT department_id FROM dw.dim_department")
        )
    }
    unknown = sorted(set(df["department_id"]) - known_departments)
    if unknown:
        raise ValueError(f"Unknown department IDs: {unknown}")

    df.to_sql(
        "phase2_kpi_targets",
        conn,
        schema="dw",
        if_exists="append",
        index=False,
        method="multi",
    )

    result = conn.execute(text("""
        SELECT
            COUNT(*) AS rows_loaded,
            COUNT(DISTINCT department_id) AS departments,
            COUNT(DISTINCT month) AS months,
            MIN(month) AS first_month,
            MAX(month) AS last_month,
            COUNT(*) FILTER (
                WHERE task_completion_target_pct IS NULL
            ) AS missing_task_targets
        FROM dw.phase2_kpi_targets
    """)).mappings().one()

    print("KPI targets loaded successfully:")
    print(dict(result))
