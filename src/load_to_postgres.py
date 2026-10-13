
from pathlib import Path
import os

import pandas as pd
from sqlalchemy import create_engine, text

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
        "date_of_birth", "hire_date", "exit_date",
        "valid_from", "valid_to",
    ],
    "fact_payroll": ["period_end_date"],
    "fact_attendance_monthly": ["period_end_date"],
    "fact_leave": [
        "start_date", "end_date", "applied_on", "decided_on",
    ],
}


def main():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    print("Connected to PostgreSQL successfully.")

    for filename, table_name in FILES.items():
        file_path = DATA_FOLDER / filename

        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        df = pd.read_csv(file_path)

        # Convert date strings into Python date objects.
        for column in DATE_COLUMNS[table_name]:
            df[column] = pd.to_datetime(
                df[column], errors="coerce"
            ).dt.date

        # Convert missing values to SQL NULL.
        df = df.astype(object).where(pd.notna(df), None)

        # Each table's replacement is transactional.
        # The table is cleared only when its new data can be loaded.
        with engine.begin() as connection:
            connection.execute(text(f"TRUNCATE TABLE {table_name}"))

            df.to_sql(
                table_name,
                con=connection,
                if_exists="append",
                index=False,
                chunksize=100,
                method=None,
            )

        print(f"Loaded {len(df):,} rows into {table_name}.")

    print("\nAll four CSV files loaded successfully.")


if __name__ == "__main__":
    main()