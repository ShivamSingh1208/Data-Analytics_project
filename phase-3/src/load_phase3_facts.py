from pathlib import Path
from decimal import Decimal
import os

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.types import Numeric, Date, DateTime, Float

DATA = Path(" data")

TABLES = {
    "fact_ledger": {
        "pk": ["line_id"],
        "codes": ["account_code"],
        "money": ["debit", "credit", "signed_amount_debit_positive"],
        "dates": ["entry_date"],
    },
    "fact_expense": {
        "pk": ["expense_id"],
        "codes": ["category_account"],
        "money": ["amount_excl_gst", "gst_amount", "total_amount"],
        "dates": ["expense_date", "due_date", "paid_date"],
    },
    "fact_invoice": {
        "pk": ["invoice_id"],
        "codes": ["service_line_account"],
        "money": ["subtotal", "gst_amount", "total_amount",
                  "amount_paid", "balance_due"],
        "dates": ["invoice_date", "due_date", "last_payment_date"],
    },
    "fact_invoice_payment": {
        "pk": ["payment_id"],
        "codes": [],
        "money": ["amount"],
        "dates": ["payment_date"],
    },
    "fact_anomaly": {
        "pk": ["result_id"],
        "codes": [],
        "money": ["money_at_risk"],
        "dates": [],
        "timestamps": ["scored_at"],
    },
    "fact_forecast": {
        "pk": ["forecast_id"],
        "codes": [],
        "money": [],
        "dates": ["forecast_month", "trained_through"],
        "floats": ["forecast_value", "lower_80", "upper_80"],
    },
    "reference_summary_dept_month": {
        "pk": ["department_id", "month"],
        "codes": [],
        "money": ["employer_cost", "gross_pay", "overtime_pay",
                  "cost_per_head"],
        "dates": ["month"],
        "floats": ["overtime_hours", "attendance_rate",
                   "attrition_rate_monthly_pct", "tasks", "tasks_done",
                   "story_points_done", "task_completion_rate_pct",
                   "overtime_share_pct"],
    },
}

FOREIGN_KEYS = [
    ("fact_ledger", "account_code", "dim_account", "account_code"),
    ("fact_expense", "category_account", "dim_account", "account_code"),
    ("fact_expense", "vendor_id", "dim_vendor", "vendor_id"),
    ("fact_invoice", "service_line_account", "dim_account", "account_code"),
    ("fact_invoice", "client_id", "dim_client", "client_id"),
    ("fact_invoice_payment", "invoice_id", "fact_invoice", "invoice_id"),
]

def normalize_code(value):
    if pd.isna(value) or str(value).strip() == "":
        return None
    value = str(value).strip()
    if value.endswith(".0") and value[:-2].isdigit():
        value = value[:-2]
    return value

def money_value(value):
    if pd.isna(value) or str(value).strip() == "":
        return None
    cleaned = str(value).replace(",", "").replace("₹", "").strip()
    return Decimal(cleaned)

def main():
    url = URL.create(
        "postgresql+psycopg",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host="localhost",
        port=5434,
        database=os.getenv("POSTGRES_DB", "pulseiq"),
    )
    engine = create_engine(url)

    prepared = {}

    print("========== VALIDATE PHASE 3 SOURCE FILES ==========")

    for table, config in TABLES.items():
        matches = list(DATA.glob(f"* - {table}.csv"))
        if len(matches) != 1:
            raise RuntimeError(
                f"{table}: expected one source CSV, found {len(matches)}"
            )

        df = pd.read_csv(matches[0], low_memory=False)
        df.columns = df.columns.str.strip()

        for col in config.get("codes", []):
            df[col] = df[col].map(normalize_code)

        for col in config.get("money", []):
            df[col] = df[col].map(money_value)

        for col in config.get("dates", []):
            parsed = pd.to_datetime(df[col], errors="coerce")
            invalid = df[col].notna() & parsed.isna()
            if invalid.any():
                raise ValueError(
                    f"{table}.{col}: {invalid.sum()} invalid dates"
                )
            df[col] = parsed.dt.date

        for col in config.get("timestamps", []):
            parsed = pd.to_datetime(df[col], errors="coerce")
            invalid = df[col].notna() & parsed.isna()
            if invalid.any():
                raise ValueError(
                    f"{table}.{col}: {invalid.sum()} invalid timestamps"
                )
            df[col] = parsed

        for col in config.get("floats", []):
            df[col] = pd.to_numeric(df[col], errors="raise")

        for key in config["pk"]:
            if df[key].isna().any():
                raise ValueError(f"{table}: null primary key in {key}")

        if df.duplicated(config["pk"]).any():
            raise ValueError(f"{table}: duplicate primary key")

        df = df.astype(object).where(pd.notna(df), None)
        prepared[table] = df
        print(f"Validated {table}: {len(df)} rows")

    print("\n========== CHECK DATABASE TARGETS ==========")

    with engine.begin() as conn:
        for table in TABLES:
            exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'dw'
                      AND table_name = :table
                )
            """), {"table": table}).scalar_one()

            if exists:
                raise RuntimeError(
                    f"dw.{table} already exists. Refusing to overwrite."
                )

        for table, df in prepared.items():
            dtype = {}

            for col in TABLES[table].get("money", []):
                dtype[col] = Numeric(20, 2)

            for col in TABLES[table].get("floats", []):
                dtype[col] = Float()

            for col in TABLES[table].get("dates", []):
                dtype[col] = Date()

            for col in TABLES[table].get("timestamps", []):
                dtype[col] = DateTime()

            df.to_sql(
                table,
                conn,
                schema="dw",
                if_exists="fail",
                index=False,
                chunksize=500,
                dtype=dtype,
            )

            pk = TABLES[table]["pk"]
            pk_name = f"pk_{table}"
            pk_cols = ", ".join(f'"{col}"' for col in pk)

            conn.execute(text(
                f'ALTER TABLE dw."{table}" '
                f'ADD CONSTRAINT "{pk_name}" PRIMARY KEY ({pk_cols})'
            ))

            print(f"Loaded dw.{table}: {len(df)} rows")

        for source, source_col, target, target_col in FOREIGN_KEYS:
            constraint = f"fk_{source}_{source_col}"
            conn.execute(text(
                f'ALTER TABLE dw."{source}" '
                f'ADD CONSTRAINT "{constraint}" '
                f'FOREIGN KEY ("{source_col}") '
                f'REFERENCES dw."{target}" ("{target_col}")'
            ))
            print(f"Created relationship: {source}.{source_col} -> {target}.{target_col}")

    engine.dispose()
    print("\nPhase 3 fact/reference loading completed successfully.")

if __name__ == "__main__":
    main()
