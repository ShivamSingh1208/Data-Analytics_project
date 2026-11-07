from pathlib import Path
import os

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.types import Date

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://pulseiq:pulseiq123@localhost:5432/pulseiq",
)

engine = create_engine(DATABASE_URL)

DATA_FOLDER = Path("output/cleaned")

FILES = {
    "cleaned_dim_employee.csv": "dim_employee",
    "cleaned_fact_payroll.csv": "fact_payroll",
    "cleaned_fact_attendance_monthly.csv": "fact_attendance_monthly",
    "cleaned_fact_leave.csv": "fact_leave",
}

DATE_COLUMNS = {
    "dim_employee": [
        "date_of_birth",
        "hire_date",
        "exit_date",
        "valid_from",
        "valid_to",
    ],
    "fact_payroll": ["period_end_date"],
    "fact_attendance_monthly": ["period_end_date"],
    "fact_leave": [
        "start_date",
        "end_date",
        "applied_on",
        "decided_on",
    ],
}


def main():
    # Confirm that the warehouse schema exists.
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        schema_exists = connection.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.schemata
                    WHERE schema_name = 'dw'
                )
            """)
        ).scalar()

    if not schema_exists:
        raise RuntimeError(
            "Warehouse schema 'dw' does not exist. "
            "Create it before loading data."
        )

    print("Connected to PostgreSQL.")
    print("Target schema: dw")

    for filename, table_name in FILES.items():
        file_path = DATA_FOLDER / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"CSV file not found: {file_path}"
            )

        print(f"\nPreparing {table_name}...")

        df = pd.read_csv(file_path)

        # Validate required date columns and parse dates.
        for column in DATE_COLUMNS[table_name]:
            if column not in df.columns:
                raise ValueError(
                    f"Missing column '{column}' in {file_path}"
                )

            original = df[column]
            parsed = pd.to_datetime(
                original,
                errors="coerce",
            )

            invalid = (
                original.notna()
                & original.astype(str).str.strip().ne("")
                & parsed.isna()
            )

            if invalid.any():
                raise ValueError(
                    f"{table_name}.{column}: "
                    f"{invalid.sum()} invalid date values"
                )

            df[column] = parsed.dt.date

        # Validate that the CSV columns match the target table.
        with engine.connect() as connection:
            target_columns = connection.execute(
                text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'dw'
                      AND table_name = :table_name
                    ORDER BY ordinal_position
                """),
                {"table_name": table_name},
            ).scalars().all()

        if not target_columns:
            raise RuntimeError(
                f"Target table dw.{table_name} does not exist."
            )

        if set(df.columns) != set(target_columns):
            missing = sorted(set(target_columns) - set(df.columns))
            extra = sorted(set(df.columns) - set(target_columns))

            raise ValueError(
                f"Column mismatch for dw.{table_name}. "
                f"Missing from CSV: {missing}; "
                f"extra in CSV: {extra}"
            )

        # Match the target table's column order.
        df = df[target_columns]

        # Ensure primary-key values are present and unique.
        primary_keys = {
            "dim_employee": "employee_key",
            "fact_payroll": "payroll_item_id",
            "fact_attendance_monthly": "attendance_fact_id",
            "fact_leave": "leave_request_id",
        }

        pk = primary_keys[table_name]

        if df[pk].isna().any():
            raise ValueError(
                f"{file_path} contains missing primary keys."
            )

        if df[pk].duplicated().any():
            raise ValueError(
                f"{file_path} contains duplicate primary keys."
            )

        # Convert pandas missing values to SQL NULL.
        df = df.astype(object).where(pd.notna(df), None)

        column_types = {
            column: Date()
            for column in DATE_COLUMNS[table_name]
        }

        # Use a unique temporary staging table in schema dw.
        staging_table = f"stg_{table_name}"

        with engine.begin() as connection:
            # Refuse to overwrite existing warehouse data.
            target_count = connection.execute(
                text(f'SELECT COUNT(*) FROM dw."{table_name}"')
            ).scalar_one()

            if target_count != 0:
                raise RuntimeError(
                    f"dw.{table_name} already contains "
                    f"{target_count} rows. Stopping to avoid "
                    "overwriting existing data."
                )

            # Recreate only this loader's staging table.
            connection.execute(
                text(
                    f'DROP TABLE IF EXISTS dw."{staging_table}"'
                )
            )

            df.to_sql(
                staging_table,
                con=connection,
                schema="dw",
                if_exists="fail",
                index=False,
                chunksize=500,
                dtype=column_types,
            )

            # Insert explicitly by column name.
            columns_sql = ", ".join(
                f'"{column}"' for column in target_columns
            )

            connection.execute(
                text(
                    f'INSERT INTO dw."{table_name}" '
                    f'({columns_sql}) '
                    f'SELECT {columns_sql} '
                    f'FROM dw."{staging_table}"'
                )
            )

            connection.execute(
                text(
                    f'DROP TABLE dw."{staging_table}"'
                )
            )

        print(
            f"Loaded {len(df):,} rows into dw.{table_name}."
        )

    print("\nAll four warehouse tables loaded successfully.")


if __name__ == "__main__":
    main()