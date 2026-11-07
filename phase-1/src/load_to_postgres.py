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

FILES = {
    "cleaned_dim_employee.csv": "dim_employee",
    "cleaned_fact_payroll.csv": "fact_payroll",
    "cleaned_fact_attendance_monthly.csv": "fact_attendance_monthly",
    "cleaned_fact_leave.csv": "fact_leave",
}

DATA_FOLDER = Path("output/cleaned")

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
    # Confirm that PostgreSQL is reachable.
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    print("Connected to PostgreSQL successfully.")

    for filename, table_name in FILES.items():
        file_path = DATA_FOLDER / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"CSV file not found: {file_path}"
            )

        print(f"\nPreparing {table_name}...")

        df = pd.read_csv(file_path)

        # Validate that all expected date columns exist.
        for column in DATE_COLUMNS[table_name]:
            if column not in df.columns:
                raise ValueError(
                    f"Missing column '{column}' in {file_path}"
                )

            # Convert dates to Python datetime.date objects.
            parsed_dates = pd.to_datetime(
                df[column],
                errors="coerce",
            )

            # Avoid silently replacing invalid non-empty dates with NULL.
            invalid_dates = (
                df[column].notna()
                & df[column].astype(str).str.strip().ne("")
                & parsed_dates.isna()
            )

            if invalid_dates.any():
                raise ValueError(
                    f"{table_name}.{column} contains "
                    f"{invalid_dates.sum()} invalid date values."
                )

            df[column] = parsed_dates.dt.date

        # Convert pandas missing values into SQL NULL.
        df = df.astype(object).where(pd.notna(df), None)

        # Tell SQLAlchemy which CSV columns are SQL DATE fields.
        column_types = {
            column: Date()
            for column in DATE_COLUMNS[table_name]
        }

        # Load into a staging table first.
        staging_table = f"{table_name}_staging"

        with engine.begin() as connection:
            connection.execute(
                text(f'DROP TABLE IF EXISTS "{staging_table}"')
            )

            df.to_sql(
                staging_table,
                con=connection,
                if_exists="replace",
                index=False,
                chunksize=100,
                dtype=column_types,
                method=None,
            )

            # Replace the target only after the staging load succeeds.
            connection.execute(
                text(f'TRUNCATE TABLE "{table_name}"')
            )

            connection.execute(
                text(
                    f'INSERT INTO "{table_name}" '
                    f'SELECT * FROM "{staging_table}"'
                )
            )

            connection.execute(
                text(f'DROP TABLE "{staging_table}"')
            )

        print(
            f"Loaded {len(df):,} rows into {table_name}."
        )

    print("\nAll four CSV files loaded successfully.")


if __name__ == "__main__":
    main()