from pathlib import Path
import os

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.types import Date

DATA = Path(" data")

from sqlalchemy.engine import URL

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host="localhost",
    port=5434,
    database=os.getenv("POSTGRES_DB", "pulseiq"),
)

TABLES = {
    "dim_account": {
        "key": "account_code",
        "string_columns": ["account_code", "parent_code"],
        "date_columns": [],
    },
    "dim_vendor": {
        "key": "vendor_id",
        "string_columns": ["vendor_id", "primary_expense_account"],
        "date_columns": [],
    },
    "dim_client": {
        "key": "client_id",
        "string_columns": ["client_id", "primary_service_line"],
        "date_columns": ["onboarded_on"],
    },
}


def normalize_code(value):
    if pd.isna(value) or str(value).strip() == "":
        return None

    value = str(value).strip()

    if value.endswith(".0") and value[:-2].isdigit():
        value = value[:-2]

    return value


def main():
    engine = create_engine(DATABASE_URL)

    prepared = {}

    # Prepare and validate all three CSVs before writing anything.
    for table, config in TABLES.items():
        matches = list(DATA.glob(f"* - {table}.csv"))

        if len(matches) != 1:
            raise RuntimeError(
                f"{table}: expected exactly one CSV, found {len(matches)}"
            )

        df = pd.read_csv(matches[0], low_memory=False)
        df.columns = df.columns.str.strip()

        for column in config["string_columns"]:
            if column in df.columns:
                df[column] = df[column].map(normalize_code)

        for column in config["date_columns"]:
            parsed = pd.to_datetime(df[column], errors="coerce")
            invalid = df[column].notna() & parsed.isna()

            if invalid.any():
                raise ValueError(
                    f"{table}.{column}: {invalid.sum()} invalid dates"
                )

            df[column] = parsed.dt.date

        key = config["key"]

        if df[key].isna().any():
            raise ValueError(f"{table}: missing primary keys")

        if df[key].duplicated().any():
            raise ValueError(f"{table}: duplicate primary keys")

        prepared[table] = df.astype(object).where(pd.notna(df), None)

        print(f"Validated {table}: {len(df)} rows")

    with engine.begin() as conn:
        for table, df in prepared.items():
            target_columns = conn.execute(
                text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'dw'
                      AND table_name = :table
                    ORDER BY ordinal_position
                """),
                {"table": table},
            ).scalars().all()

            if not target_columns:
                raise RuntimeError(f"Target dw.{table} does not exist")

            if set(df.columns) != set(target_columns):
                raise ValueError(
                    f"{table} column mismatch. "
                    f"CSV={sorted(df.columns)} "
                    f"DB={sorted(target_columns)}"
                )

            count = conn.execute(
                text(f'SELECT COUNT(*) FROM dw."{table}"')
            ).scalar_one()

            if count != 0:
                raise RuntimeError(
                    f"dw.{table} already contains {count} rows. "
                    "Refusing to overwrite."
                )

            df = df[target_columns]

            dtype = {
                column: Date()
                for column in TABLES[table]["date_columns"]
            }

            df.to_sql(
                table,
                conn,
                schema="dw",
                if_exists="append",
                index=False,
                chunksize=500,
                dtype=dtype,
            )

            print(f"Loaded dw.{table}: {len(df)} rows")

    print("\nDimension loading completed successfully.")


if __name__ == "__main__":
    main()
