
from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# The source folder has a leading space in its name: " data"
DATA_DIR = PROJECT_ROOT / " data"

FILE_PREFIX = (
    "03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx - "
)

SCHEMA = "dw"


# ============================================================
# 2. DATABASE CONNECTION
# ============================================================

load_dotenv(PROJECT_ROOT / ".env")

DB_USER = os.getenv("POSTGRES_USER", "pulseiq")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB", "pulseiq")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

if not DB_PASSWORD:
    raise RuntimeError(
        "POSTGRES_PASSWORD is missing from your .env file."
    )

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)

engine = create_engine(database_url)


# ============================================================
# 3. DIMENSION TABLES AND SOURCE FILES
# ============================================================

DIMENSIONS = {
    "dim_account": [
        "account_code",
        "account_name",
        "account_type",
        "normal_balance",
        "parent_code",
        "is_group",
        "statement",
        "is_active",
    ],
    "dim_client": [
        "client_id",
        "client_name",
        "industry",
        "city",
        "state_or_region",
        "country",
        "client_type",
        "gst_registration",
        "payment_terms_days",
        "payment_behaviour",
        "primary_service_line",
        "contact_email",
        "onboarded_on",
        "is_active",
    ],
    "dim_date": [
        "date",
        "date_key",
        "year",
        "quarter",
        "month_number",
        "month_name",
        "year_month",
        "week_of_year",
        "day_of_week",
        "is_weekend",
        "is_holiday",
        "is_working_day",
        "financial_year",
        "fiscal_quarter",
        "fiscal_month_number",
        "is_month_end",
        "month_start_date",
        "month_end_date",
    ],
    "dim_department": [
        "department_id",
        "department_name",
        "cost_center",
        "description",
        "is_leadership",
    ],
    "dim_leave_type": [
        "leave_type_code",
        "leave_type_name",
        "pay_type",
        "annual_quota_days",
        "prorated_for_joiners",
        "carry_forward_allowed",
        "max_carry_forward_days",
        "policy_note",
    ],
    "dim_location": [
        "work_location",
        "state",
        "city_tier",
        "tier_number",
    ],
    "dim_role": [
        "role_id",
        "department_id",
        "role_title",
        "level",
        "grade",
        "band_min_annual",
        "band_mid_annual",
        "band_max_annual",
        "overtime_eligible",
        "band_reference_year",
    ],
    "dim_sprint": [
        "sprint_id",
        "sprint_name",
        "start_date",
        "end_date",
        "working_days",
        "financial_year",
    ],
    "dim_team": [
        "team_id",
        "team_name",
        "department_id",
        "team_lead_employee_id",
        "active_members",
        "planning_cadence",
        "board_tool",
    ],
    "dim_vendor": [
        "vendor_id",
        "vendor_name",
        "primary_expense_account",
        "payment_terms_days",
        "city",
        "gst_registration",
        "is_active",
    ],
}


# ============================================================
# 4. DATE AND STRING COLUMN CONVERSIONS
# ============================================================

DATE_COLUMNS = {
    "dim_client": [
        "onboarded_on",
    ],
    "dim_date": [
        "date",
        "month_start_date",
        "month_end_date",
    ],
    "dim_sprint": [
        "start_date",
        "end_date",
    ],
}

# These columns are VARCHAR in PostgreSQL but may contain
# numeric-looking values in the CSV.
STRING_COLUMNS = {
    "dim_client": [
        "primary_service_line",
    ],
}


# ============================================================
# 5. HELPER FUNCTIONS
# ============================================================

def get_csv_path(table_name):
    """Return the CSV path associated with a dimension table."""

    filename = f"{FILE_PREFIX}{table_name}.csv"
    return DATA_DIR / filename


def prepare_dataframe(table_name, csv_path):
    """Read, validate, and convert a dimension CSV."""

    df = pd.read_csv(csv_path)

    # Validate required source columns.
    expected_columns = DIMENSIONS[table_name]
    missing_columns = [
        column
        for column in expected_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{table_name}: missing CSV columns: "
            f"{missing_columns}"
        )

    # Keep only the columns expected by the destination table,
    # in the same order as the schema definition above.
    df = df[expected_columns].copy()

    # Convert date strings to Python date objects.
    for column in DATE_COLUMNS.get(table_name, []):
        parsed_dates = pd.to_datetime(
            df[column],
            errors="raise",
        )

        df[column] = [
            value.date() if pd.notna(value) else None
            for value in parsed_dates
        ]

    # Convert numeric-looking values to strings where the
    # PostgreSQL destination column is VARCHAR.
    for column in STRING_COLUMNS.get(table_name, []):
        df[column] = df[column].map(
            lambda value: (
                str(value) if pd.notna(value) else None
            )
        )

    # Reject duplicate primary-key values before insertion.
    primary_key_columns = {
        "dim_account": ["account_code"],
        "dim_client": ["client_id"],
        "dim_date": ["date_key"],
        "dim_department": ["department_id"],
        "dim_leave_type": ["leave_type_code"],
        "dim_location": ["work_location"],
        "dim_role": ["role_id"],
        "dim_sprint": ["sprint_id"],
        "dim_team": ["team_id"],
        "dim_vendor": ["vendor_id"],
    }

    keys = primary_key_columns[table_name]

    if df[keys].isnull().any().any():
        raise ValueError(
            f"{table_name}: primary key contains null values."
        )

    duplicate_mask = df.duplicated(
        subset=keys,
        keep=False,
    )

    if duplicate_mask.any():
        duplicates = df.loc[duplicate_mask, keys].head(10)

        raise ValueError(
            f"{table_name}: duplicate primary keys found.\n"
            f"{duplicates.to_string(index=False)}"
        )

    return df


# ============================================================
# 6. MAIN LOADING PROCESS
# ============================================================

def main():
    print("=" * 60)
    print("PulseIQ Dimension Loader")
    print("=" * 60)

    print(f"Project directory: {PROJECT_ROOT}")
    print(f"CSV directory: {DATA_DIR}")
    print(f"Database: {DB_NAME}")
    print()

    if not DATA_DIR.is_dir():
        raise FileNotFoundError(
            f"CSV directory not found: {DATA_DIR}"
        )

    inspector = inspect(engine)

    if not inspector.has_schema(SCHEMA):
        raise RuntimeError(
            f"Database schema '{SCHEMA}' does not exist."
        )

    # Confirm every destination table exists.
    existing_tables = set(
        inspector.get_table_names(schema=SCHEMA)
    )

    missing_tables = [
        table
        for table in DIMENSIONS
        if table not in existing_tables
    ]

    if missing_tables:
        raise RuntimeError(
            f"Missing destination tables in {SCHEMA}: "
            f"{missing_tables}"
        )

    # Prepare and validate every CSV before inserting anything.
    

    prepared_data = {}

    for table_name in DIMENSIONS:
        csv_path = get_csv_path(table_name)

        if not csv_path.is_file():
            raise FileNotFoundError(
                f"CSV file not found: {csv_path}"
            )

        df = prepare_dataframe(table_name, csv_path)
        prepared_data[table_name] = df

        print(
            f"Validated {table_name}: {len(df)} source rows"
        )

    print()
    print("Checking destination tables...")

    # Safety check: refuse to insert into nonempty tables.
    with engine.connect() as connection:
        for table_name in DIMENSIONS:
            count = connection.execute(
                text(
                    f'SELECT COUNT(*) FROM "{SCHEMA}"'
                    f'."{table_name}"'
                )
            ).scalar_one()

            if count != 0:
                raise RuntimeError(
                    f"{SCHEMA}.{table_name} already contains "
                    f"{count} rows. No loading performed."
                )

    print("All ten destination tables are empty.")
    print("Starting database transaction...")

    # All inserts share one transaction.
    # If an insertion fails, the transaction rolls back.
    with engine.begin() as connection:
        for table_name, df in prepared_data.items():
            df.to_sql(
                name=table_name,
                con=connection,
                schema=SCHEMA,
                if_exists="append",
                index=False,
                chunksize=500,
                method="multi",
            )

            print(
                f"Inserted {len(df)} rows into "
                f"{SCHEMA}.{table_name}"
            )

    print()
    print("Loading transaction committed successfully.")
    print("Final destination counts:")

    with engine.connect() as connection:
        for table_name in DIMENSIONS:
            count = connection.execute(
                text(
                    f'SELECT COUNT(*) FROM "{SCHEMA}"'
                    f'."{table_name}"'
                )
            ).scalar_one()

            print(f"{table_name}: {count}")

    print("Dimension loading completed successfully.")


if __name__ == "__main__":
    try:
        main()
    finally:
        engine.dispose()
