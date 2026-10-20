from pathlib import Path
from datetime import datetime, timezone
import json
import sys

import pandas as pd
from pandera_validation import get_validation_errors


# --------------------------------------------------
# Project paths
# --------------------------------------------------

PROJECT = Path(__file__).resolve().parent.parent
DATA_FOLDER = PROJECT / " data"

OUTPUT = PROJECT / "output" / "cleaned"
REJECTED = PROJECT / "output" / "rejected"
LOGS = PROJECT / "logs"

for folder in [OUTPUT, REJECTED, LOGS]:
    folder.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# Dataset validation rules
# --------------------------------------------------

TABLES = {
    "fact_payroll": {
        "required": [
            "payroll_item_id",
            "employee_id",
            "employee_key",
            "date_key",
            "period_end_date",
        ],
        "id": "payroll_item_id",
        "dates": ["period_end_date"],
        "money": [
            "monthly_fixed_gross",
            "basic",
            "hra",
            "conveyance",
            "medical",
            "special_allowance",
            "earned_fixed_pay",
            "overtime_pay",
            "variable_pay",
            "gross_pay",
            "pf_employee",
            "esi_employee",
            "professional_tax",
            "tds",
            "other_deductions",
            "total_deductions",
            "net_pay",
            "pf_employer",
            "esi_employer",
            "employer_cost",
        ],
    },
    "fact_attendance_monthly": {
        "required": [
            "attendance_fact_id",
            "employee_id",
            "employee_key",
            "date_key",
            "period_end_date",
        ],
        "id": "attendance_fact_id",
        "dates": ["period_end_date"],
        "money": [],
    },
    "dim_employee": {
        "required": [
            "employee_key",
            "employee_id",
            "full_name",
            "valid_from",
            "is_current",
        ],
        "id": "employee_key",
        "dates": [
            "date_of_birth",
            "hire_date",
            "exit_date",
            "valid_from",
            "valid_to",
        ],
        "money": [],
    },
    "fact_leave": {
        "required": ["employee_id"],
        "id": None,
        "dates": [],
        "money": [],
    },
}


# --------------------------------------------------
# Locate source CSVs
# --------------------------------------------------

def find_source(table_name):
    """Find a source CSV without using generated output files."""

    candidates = [
        path
        for path in DATA_FOLDER.glob("*.csv")
        if path.name.lower().endswith(
            f"{table_name.lower()}.csv"
        )
        and not path.name.lower().startswith("cleaned_")
    ]

    if not candidates:
        raise FileNotFoundError(
            f"Source CSV not found for {table_name} "
            f"in {DATA_FOLDER}"
        )

    return sorted(candidates)[0]


# --------------------------------------------------
# Read source data
# --------------------------------------------------

def read_source(table_name):
    """Read a source CSV and normalize column names."""

    source = find_source(table_name)

    df = pd.read_csv(
        source,
        encoding="utf-8-sig",
        keep_default_na=False,
    )

    df.columns = df.columns.str.strip()

    # Normalize blank cells without converting valid text to NaN.
    for column in df.columns:
        if df[column].dtype == object:
            df[column] = df[column].map(
                lambda value: (
                    value.strip()
                    if isinstance(value, str)
                    else value
                )
            )

    df = df.replace("", pd.NA)

    return source, df


# --------------------------------------------------
# Clean and validate a dataset
# --------------------------------------------------

def clean_table(table_name, rules):
    source, df = read_source(table_name)

    original_rows = len(df)

    print(f"\nProcessing: {table_name}")
    print(f"Source: {source.name}")
    print(f"Input rows: {original_rows}")

    # Confirm required columns exist.
    for column in rules["required"]:
        if column not in df.columns:
            raise ValueError(
                f"{table_name}: required column missing: {column}"
            )

    # Preserve the original values for invalid-date checks.
    original_date_values = {
        column: df[column].copy()
        for column in rules["dates"]
        if column in df.columns
    }

    reasons = pd.Series(
        "",
        index=df.index,
        dtype="object",
    )

    def flag(condition, message):
        """Append a rejection reason for every matching row."""

        condition = pd.Series(
            condition,
            index=df.index,
        ).fillna(False).astype(bool)

        existing = reasons.loc[condition]

        reasons.loc[condition] = existing.map(
            lambda old: (
                f"{old}; {message}"
                if old
                else message
            )
        )

    # Validate required values.
    for column in rules["required"]:
        flag(
            df[column].isna(),
            f"missing required {column}",
        )

    # Parse dates and reject invalid non-empty values.
    for column in rules["dates"]:
        if column not in df.columns:
            continue

        original = original_date_values[column].astype("string").str.strip()

        # 9999-12-31 represents an open-ended valid_to value.
        if column == "valid_to":
            open_ended = original.eq("9999-12-31")
            df.loc[open_ended, column] = pd.NA
            original = original.mask(open_ended, pd.NA)

        parsed = pd.to_datetime(
            df[column],
            errors="coerce",
        )

        invalid_date = (
            original.notna()
            & original.ne("")
            & parsed.isna()
        )

        flag(
            invalid_date,
            f"invalid date in {column}",
        )

        df[column] = parsed

    # Convert monetary fields to numbers.
    # Validate leave date ranges.
    if table_name == "fact_leave":
        for column in ["start_date", "end_date"]:
            if column not in df.columns:
                raise ValueError(
                    f"fact_leave: required date column missing: {column}"
                )

        start_date = pd.to_datetime(
            df["start_date"],
            errors="coerce",
        )

        end_date = pd.to_datetime(
            df["end_date"],
            errors="coerce",
        )

        flag(
            start_date.notna()
            & end_date.notna()
            & start_date.gt(end_date),
            "start_date is after end_date",
        )
    for column in rules["money"]:
        if column not in df.columns:
            continue

        original = df[column].astype("string").str.strip()

        normalized = original.str.replace(
            ",",
            "",
            regex=False,
        )

        parsed = pd.to_numeric(
            normalized,
            errors="coerce",
        )

        invalid_money = (
            original.notna()
            & original.ne("")
            & parsed.isna()
        )

        flag(
            invalid_money,
            f"invalid numeric amount in {column}",
        )

        df[column] = parsed

        flag(
            parsed.lt(0),
            f"negative amount in {column}",
        )

    # Validate date_key against period_end_date.
    if (
        "date_key" in df.columns
        and "period_end_date" in df.columns
    ):
        date_key = pd.to_numeric(
            df["date_key"],
            errors="coerce",
        )

        expected_key = pd.to_numeric(
            df["period_end_date"].dt.strftime("%Y%m%d"),
            errors="coerce",
        )

        flag(
            date_key.isna()
            | expected_key.isna()
            | date_key.ne(expected_key),
            "date_key does not match period_end_date",
        )

        df["date_key"] = date_key

    # Validate unique identifiers.
    unique_id = rules["id"]

    if unique_id:
        flag(
            df[unique_id].notna()
            & df[unique_id].duplicated(keep=False),
            f"duplicate {unique_id}",
        )

    # Validate attendance against employee exit month.
    if table_name == "fact_attendance_monthly":
        _, employee_dim = read_source("dim_employee")

        for column in ["employee_id", "exit_date"]:
            if column not in employee_dim.columns:
                raise ValueError(
                    f"Employee source is missing {column}"
                )

        employee_dim["employee_id"] = (
            employee_dim["employee_id"].astype("string").str.strip()
        )

        employee_dim["exit_date"] = pd.to_datetime(
            employee_dim["exit_date"],
            errors="coerce",
        )

        exit_dates = employee_dim.groupby(
            "employee_id"
        )["exit_date"].max()

        employee_ids = (
            df["employee_id"].astype("string").str.strip()
        )

        exit_date = employee_ids.map(exit_dates)

        attendance_month = (
            df["period_end_date"].dt.to_period("M")
        )

        employee_exit_month = exit_date.dt.to_period("M")

        after_exit = (
            attendance_month.notna()
            & employee_exit_month.notna()
            & attendance_month.gt(employee_exit_month)
        )

        flag(
            after_exit,
            "attendance month ends after employee exit month",
        )

    # Validate payroll employee IDs against the dimension.
    if table_name == "fact_payroll":
        _, employee_dim = read_source("dim_employee")

        valid_employee_ids = set(
            employee_dim["employee_id"]
            .dropna()
            .astype("string")
            .str.strip()
        )

        payroll_employee_ids = (
            df["employee_id"].astype("string").str.strip()
        )

        flag(
            payroll_employee_ids.notna()
            & ~payroll_employee_ids.isin(valid_employee_ids),
            "employee_id not found in dim_employee",
        )

        if "run_id" not in df.columns:
            raise ValueError(
                "fact_payroll is missing required business key run_id"
            )

        duplicate_payroll = df.duplicated(
            subset=["employee_id", "run_id"],
            keep=False,
        )

        flag(
            duplicate_payroll,
            "duplicate employee_id + run_id combination",
        )

    
        # Apply Pandera validation to records that passed existing checks.
    candidate_mask = reasons.eq("")
    candidates = df.loc[candidate_mask].copy()

    pandera_errors = get_validation_errors(
        table_name,
        candidates,
    )

    # Add Pandera errors to the existing rejection reasons.
    for row_index, error_messages in pandera_errors.items():
        if row_index not in reasons.index:
            continue

        existing = reasons.loc[row_index]

        for message in error_messages:
            if existing:
                existing = f"{existing}; {message}"
            else:
                existing = message

        reasons.loc[row_index] = existing

    # Separate rejected and clean records.
    rejected_mask = reasons.ne("")

    rejected = df.loc[rejected_mask].copy()
    rejected["reject_reason"] = reasons.loc[rejected_mask]

    clean = df.loc[~rejected_mask].copy()

    # Remove exact duplicates only from otherwise valid records.
    before_duplicates = len(clean)

    clean = clean.drop_duplicates()

    exact_duplicates_removed = (
        before_duplicates - len(clean)
    )

    # Save outputs.
    clean_path = OUTPUT / f"cleaned_{table_name}.csv"
    rejected_path = REJECTED / f"rejected_{table_name}.csv"

    clean.to_csv(
        clean_path,
        index=False,
        date_format="%Y-%m-%d",
    )

    rejected.to_csv(
        rejected_path,
        index=False,
        date_format="%Y-%m-%d",
    )

    # Count rejection reasons.
    rejection_reason_counts = {}

    if not rejected.empty:
        all_reasons = (
            rejected["reject_reason"]
            .str.split("; ")
            .explode()
        )

        rejection_reason_counts = {
            str(reason): int(count)
            for reason, count in all_reasons.value_counts().items()
        }

    result = {
        "table": table_name,
        "source_file": str(source.relative_to(PROJECT)),
        "input_rows": original_rows,
        "clean_rows": len(clean),
        "rejected_rows": len(rejected),
        "exact_duplicates_removed": exact_duplicates_removed,
        "rejection_reason_counts": rejection_reason_counts,
        "clean_file": str(clean_path.relative_to(PROJECT)),
        "rejected_file": str(rejected_path.relative_to(PROJECT)),
        "status": "completed",
    }

    print(f"Clean rows: {len(clean)}")
    print(f"Rejected rows: {len(rejected)}")
    print(f"Clean output: {clean_path}")
    print(f"Rejected output: {rejected_path}")

    return result


# --------------------------------------------------
# Pipeline entry point
# --------------------------------------------------

def main():
    started_at = datetime.now(timezone.utc)

    print("=" * 55)
    print("PulseIQ ETL pipeline")
    print("Started at:", started_at.isoformat())
    print("=" * 55)

    results = []

    for table_name, rules in TABLES.items():
        try:
            result = clean_table(table_name, rules)

        except Exception as error:
            print(f"ERROR processing {table_name}: {error}")

            result = {
                "table": table_name,
                "status": "error",
                "error": str(error),
            }

        results.append(result)

    finished_at = datetime.now(timezone.utc)

    input_rows = sum(
        item.get("input_rows", 0)
        for item in results
    )

    clean_rows = sum(
        item.get("clean_rows", 0)
        for item in results
    )

    rejected_rows = sum(
        item.get("rejected_rows", 0)
        for item in results
    )

    failed_tables = [
        item["table"]
        for item in results
        if item.get("status") != "completed"
    ]

    report = {
        "run_started_at": started_at.isoformat(),
        "run_finished_at": finished_at.isoformat(),
        "duration_seconds": round(
            (finished_at - started_at).total_seconds(),
            3,
        ),
        "status": "failed" if failed_tables else "completed",
        "input_rows": input_rows,
        "clean_rows": clean_rows,
        "rejected_rows": rejected_rows,
        "failed_tables": failed_tables,
        "tables": results,
    }

    report_path = LOGS / "etl_quality_report.json"

    report_path.write_text(
        json.dumps(report, indent=2, default=str),
        encoding="utf-8",
    )

    print("\n" + "=" * 55)
    print("ETL RUN FINISHED")
    print("Started:", started_at.isoformat())
    print("Finished:", finished_at.isoformat())
    print("Input rows:", input_rows)
    print("Clean rows:", clean_rows)
    print("Rejected rows:", rejected_rows)
    print("Status:", report["status"])
    print("Quality report:", report_path)
    print("=" * 55)

    if failed_tables:
        print("Failed tables:", ", ".join(failed_tables))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())