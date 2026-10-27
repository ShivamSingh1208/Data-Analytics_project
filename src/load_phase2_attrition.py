
from pathlib import Path
import os

import pandas as pd
from sqlalchemy import create_engine, text

folder = Path(" data")
head_files = list(folder.glob("*fact_headcount_monthly.csv"))
risk_files = list(folder.glob("*fact_attrition_risk.csv"))

if len(head_files) != 1 or len(risk_files) != 1:
    raise SystemExit(
        f"Expected one CSV of each type; found "
        f"{len(head_files)} headcount and {len(risk_files)} risk files."
    )

head = pd.read_csv(head_files[0], low_memory=False)
risk = pd.read_csv(risk_files[0], low_memory=False)
head.columns = head.columns.str.strip()
risk.columns = risk.columns.str.strip()

head_cols = [
    "date_key", "month_start_date", "department_id", "headcount_start",
    "hires", "exits", "voluntary_exits", "transfers_in", "transfers_out",
    "headcount_end", "attrition_rate_monthly_pct"
]
risk_cols = [
    "prediction_id", "employee_id", "as_of_date_key", "department_id",
    "as_of_date", "risk_score_12m", "risk_band", "top_reason_1",
    "top_reason_2", "top_reason_3", "model_version", "model_note",
    "employee_key"
]

if set(head.columns) != set(head_cols):
    raise SystemExit(f"Unexpected headcount columns: {list(head.columns)}")
if set(risk.columns) != set(risk_cols):
    raise SystemExit(f"Unexpected risk columns: {list(risk.columns)}")
if head.duplicated(["date_key", "department_id"]).any():
    raise SystemExit("Duplicate headcount keys found.")
if risk["prediction_id"].duplicated().any():
    raise SystemExit("Duplicate prediction IDs found.")

for col in [
    "headcount_start", "hires", "exits", "voluntary_exits",
    "transfers_in", "transfers_out", "headcount_end"
]:
    head[col] = pd.to_numeric(head[col], errors="raise").astype(int)

risk["risk_score_12m"] = pd.to_numeric(
    risk["risk_score_12m"], errors="raise"
)
if not risk["risk_score_12m"].between(0, 1).all():
    raise SystemExit("Risk scores must be between 0 and 1.")
if not risk["risk_band"].isin(["Low", "Medium", "High"]).all():
    raise SystemExit("Unexpected risk band found.")

head["month_start_date"] = pd.to_datetime(
    head["month_start_date"], errors="raise"
).dt.date
risk["as_of_date"] = pd.to_datetime(
    risk["as_of_date"], errors="raise"
).dt.date

def clean_records(df):
    output = []
    for row in df.to_dict("records"):
        output.append({
            key: (
                None if pd.isna(value)
                else value.item() if hasattr(value, "item")
                else value
            )
            for key, value in row.items()
        })
    return output

head_sql = text("""
INSERT INTO dw.fact_headcount_monthly
(date_key, month_start_date, department_id, headcount_start, hires, exits,
 voluntary_exits, transfers_in, transfers_out, headcount_end,
 attrition_rate_monthly_pct)
VALUES
(:date_key, :month_start_date, :department_id, :headcount_start, :hires,
 :exits, :voluntary_exits, :transfers_in, :transfers_out, :headcount_end,
 :attrition_rate_monthly_pct)
""")

risk_sql = text("""
INSERT INTO dw.fact_attrition_risk
(prediction_id, employee_id, as_of_date_key, department_id, as_of_date,
 risk_score_12m, risk_band, top_reason_1, top_reason_2, top_reason_3,
 model_version, model_note, employee_key)
VALUES
(:prediction_id, :employee_id, :as_of_date_key, :department_id, :as_of_date,
 :risk_score_12m, :risk_band, :top_reason_1, :top_reason_2, :top_reason_3,
 :model_version, :model_note, :employee_key)
""")

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise SystemExit("DATABASE_URL is not set. Load .env in the terminal first.")

engine = create_engine(database_url)

try:
    with engine.begin() as conn:
        existing = conn.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM dw.fact_headcount_monthly),
                (SELECT COUNT(*) FROM dw.fact_attrition_risk)
        """)).one()

        if existing[0] or existing[1]:
            raise SystemExit(
                f"Safety stop: target tables already contain rows: {existing}"
            )

        departments = set(conn.execute(
            text("SELECT department_id FROM dw.dim_department")
        ).scalars())

        if not set(head["department_id"]).issubset(departments):
            raise SystemExit("Unknown department IDs in headcount CSV.")
        if not set(risk["department_id"]).issubset(departments):
            raise SystemExit("Unknown department IDs in risk CSV.")

        conn.execute(head_sql, clean_records(head))
        conn.execute(risk_sql, clean_records(risk))

        head_count = conn.execute(
            text("SELECT COUNT(*) FROM dw.fact_headcount_monthly")
        ).scalar_one()
        risk_count = conn.execute(
            text("SELECT COUNT(*) FROM dw.fact_attrition_risk")
        ).scalar_one()

        if head_count != len(head) or risk_count != len(risk):
            raise RuntimeError("Verification failed; rolling back transaction.")

    print(f"SUCCESS: Loaded {head_count} headcount records.")
    print(f"SUCCESS: Loaded {risk_count} risk predictions.")
finally:
    engine.dispose()
