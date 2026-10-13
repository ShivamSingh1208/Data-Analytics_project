
from pathlib import Path
import json
import pandas as pd

# Project folders
PROJECT = Path(".")
OUTPUT = PROJECT / "output" / "cleaned"
REJECTED = PROJECT / "output" / "rejected"
REPORTS = PROJECT / "logs"

for folder in [OUTPUT, REJECTED, REPORTS]:
    folder.mkdir(parents=True, exist_ok=True)

# Tables for our first ETL run
TABLES = {
    "fact_payroll": {
        "required": [
            "payroll_item_id", "employee_id", "employee_key",
            "date_key", "period_end_date"
        ],
        "id": "payroll_item_id",
        "dates": ["period_end_date"],
        "money": [
            "monthly_fixed_gross", "basic", "hra", "conveyance",
            "medical", "special_allowance", "earned_fixed_pay",
            "overtime_pay", "variable_pay", "gross_pay",
            "pf_employee", "esi_employee", "professional_tax",
            "tds", "other_deductions", "total_deductions",
            "net_pay", "pf_employer", "esi_employer", "employer_cost"
        ],
    },
    "fact_attendance_monthly": {
        "required": [
            "attendance_fact_id", "employee_id", "employee_key",
            "date_key", "period_end_date"
        ],
        "id": "attendance_fact_id",
        "dates": ["period_end_date"],
        "money": [],
    },
    "dim_employee": {
        "required": [
            "employee_key", "employee_id", "full_name",
            "valid_from", "is_current"
        ],
        "id": "employee_key",
        "dates": [
            "date_of_birth", "hire_date", "exit_date",
            "valid_from", "valid_to"
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


def find_source(table_name):
    """Find the original CSV, not a generated output file."""
    candidates = [
        path for path in PROJECT.rglob("*.csv")
        if path.name.lower().endswith(table_name.lower() + ".csv")
        and "output" not in [part.lower() for part in path.parts]
        and not path.name.lower().startswith("cleaned_")
        and ".venv" not in path.parts
    ]

    if not candidates:
        return None

    # Prefer a CSV directly in the data folder.
    candidates.sort(
        key=lambda p: (
            0 if p.parent.name.strip().lower() == "data" else 1,
            len(p.parts)
        )
    )
    return candidates[0]


def clean_table(table_name, rules):
    source = find_source(table_name)

    if source is None:
        print(f"SKIPPED: {table_name} CSV not found")
        return {
            "table": table_name,
            "status": "missing source",
        }

    print(f"\nProcessing: {table_name}")
    print(f"Source: {source}")

    df = pd.read_csv(source, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    original_rows = len(df)

    # Remove leading/trailing spaces in text fields.
    for column in df.select_dtypes(include="object").columns:
        df[column] = df[column].map(
            lambda value: value.strip() if isinstance(value, str)
            else value
        )
        df[column] = df[column].replace("", pd.NA)

     
    # Convert date columns. Treat 9999-12-31 as an open-ended valid_to date.
    for column in rules["dates"]:
        if column in df.columns:
            if column == "valid_to":
                df[column] = df[column].replace(
                    "9999-12-31", pd.NA
                )

            df[column] = pd.to_datetime(
                df[column], errors="coerce"
            )

    # Convert payroll amounts such as "144,460.00" into numbers.
    for column in rules["money"]:
        if column in df.columns:
            values = (
                df[column].astype("string")
                .str.replace(",", "", regex=False)
                .str.strip()
            )
            df[column] = pd.to_numeric(
                values, errors="coerce"
            )

    # Collect reasons why a row should be rejected.
    reasons = pd.Series("", index=df.index, dtype="object")

    def flag(condition, message):
        nonlocal reasons
        condition = condition.fillna(False)
        reasons.loc[condition] = reasons.loc[condition].map(
            lambda old: old + "; " + message if old else message
        )

    # Required fields must exist and must not be empty.
    for column in rules["required"]:
        if column not in df.columns:
            raise ValueError(
                f"{table_name}: required column missing: {column}"
            )
        flag(
            df[column].isna(),
            f"missing required {column}"
        )

    # Reject non-empty dates that could not be parsed.
    for column in rules["dates"]:
        if column in df.columns:
            raw = pd.read_csv(
                source,
                usecols=[column],
                encoding="utf-8-sig",
                keep_default_na=False
            )[column]

            raw_text = raw.astype(str).str.strip()
            raw_present = raw_text.ne("")
            invalid_date = raw_present & df[column].isna()

            if column == "valid_to":
                invalid_date = (
                    invalid_date
                    & raw_text.ne("9999-12-31")
                )

            flag(
                invalid_date,
                f"invalid date in {column}"
            )


    # A fact's date_key should match its period-end date.
    if "date_key" in df.columns and "period_end_date" in df.columns:
        date_key = pd.to_numeric(df["date_key"], errors="coerce")
        expected_key = pd.to_numeric(
            df["period_end_date"].dt.strftime("%Y%m%d"),
            errors="coerce"
        )
        flag(
            date_key.isna() | expected_key.isna() |
            date_key.ne(expected_key),
            "date_key does not match period_end_date"
        )
        df["date_key"] = date_key

    # Reject negative payroll amounts, but do not replace them with zero.
    for column in rules["money"]:
        if column in df.columns:
            flag(
                df[column].lt(0),
                f"negative amount in {column}"
            )

    # Identifiers configured as unique must not be missing or duplicated.
    unique_id = rules["id"]
    if unique_id and unique_id in df.columns:
        duplicate_id = (
            df[unique_id].notna()
            & df[unique_id].duplicated(keep=False)
        )
        flag(duplicate_id, f"duplicate {unique_id}")

    # Attendance after employee exit check
    if table_name == "fact_attendance_monthly":

        employee_source = find_source("dim_employee")

        if employee_source is None:
            raise FileNotFoundError(
                "Cannot validate attendance: dim_employee source not found"
            )

        employee_dim = pd.read_csv(
            employee_source,
            usecols=["employee_id", "exit_date"],
            dtype={"employee_id": "string"},
            encoding="utf-8-sig"
        )

        employee_dim["employee_id"] = (
            employee_dim["employee_id"].str.strip()
        )
        employee_dim["exit_date"] = pd.to_datetime(
            employee_dim["exit_date"],
            errors="coerce"
        )

        # Consolidate historical employee records into one exit date.
        exit_dates = employee_dim.groupby("employee_id")[
            "exit_date"
        ].max()

        attendance_employee_ids = (
            df["employee_id"].astype("string").str.strip()
        )
        attendance_dates = pd.to_datetime(
            df["period_end_date"],
            errors="coerce"
        )
        employee_exit_dates = attendance_employee_ids.map(exit_dates)

        # Reject attendance only when its calendar month is
        # later than the employee's exit month.
        attendance_month = attendance_dates.dt.to_period("M")
        exit_month = employee_exit_dates.dt.to_period("M")

        attendance_after_exit = (
            attendance_month.notna()
            & exit_month.notna()
            & (attendance_month > exit_month)
        )

        flag(
            attendance_after_exit,
            "attendance month ends after employee exit month"
        )

    # Payroll business-rule checks
    if table_name == "fact_payroll":

        # DQ-C03: One payroll row per employee per run.
        duplicate_payroll = df.duplicated(
            subset=["employee_id", "run_id"],
            keep="first"
        )
        flag(
            duplicate_payroll,
            "duplicate employee_id + run_id combination" 
        )

        # DQ-C04: Payroll employee IDs must exist in source dimension.
        employee_source = find_source("dim_employee")

        if employee_source is None:
            raise FileNotFoundError(
                "Cannot validate payroll: dim_employee source not found"
            )

        employee_dim = pd.read_csv(
            employee_source,
            usecols=["employee_id"],
            dtype={"employee_id": "string"},
            encoding="utf-8-sig"
        )

        valid_employee_ids = set(
            employee_dim["employee_id"].dropna().str.strip()
        )

        payroll_employee_ids = (
            df["employee_id"].astype("string").str.strip()
        )

        orphan_employee = (
            payroll_employee_ids.notna()
            & ~payroll_employee_ids.isin(valid_employee_ids)
        )

        flag(
            orphan_employee,
            "employee_id not found in dim_employee"
        )

    # Separate valid and rejected rows.
    rejected_mask = reasons.ne("")
    rejected = df.loc[rejected_mask].copy()
    rejected["reject_reason"] = reasons.loc[rejected_mask]

    clean = df.loc[~rejected_mask].copy()

    # Remove exact duplicate rows from the valid output.
    before_duplicates = len(clean)
    clean = clean.drop_duplicates()
    exact_duplicates_removed = before_duplicates - len(clean)

    # Save the cleaned and rejected data separately.
    clean.to_csv(OUTPUT / f"cleaned_{table_name}.csv", index=False)
    
    # Count the rejected rows by reason.
    rejection_reason_counts = {}

    if not rejected.empty:
        rejection_reason_counts = {
            str(reason): int(count)
            for reason, count in (
                rejected["reject_reason"]
                .value_counts()
                .items()
            )
        }

    result = {
        "table": table_name,
        "source_file": str(source),
        "input_rows": original_rows,
        "clean_rows": len(clean),
        "rejected_rows": len(rejected),
        "exact_duplicates_removed": exact_duplicates_removed,
        "rejection_reason_counts": rejection_reason_counts,
        "status": "completed",
    }
 

     
    # Count the rejected rows by reason.
    rejection_reason_counts = {}

    if not rejected.empty:
        rejection_reason_counts = {
            str(reason): int(count)
            for reason, count in (
                rejected["reject_reason"]
                .value_counts()
                .items()
            )
        }

    result = {
        "table": table_name,
        "source_file": str(source),
        "input_rows": original_rows,
        "clean_rows": len(clean),
        "rejected_rows": len(rejected),
        "exact_duplicates_removed": exact_duplicates_removed,
        "rejection_reason_counts": rejection_reason_counts,
        "status": "completed",
    }

    print("Input rows:", original_rows)
    print("Clean rows:", len(clean))
    print("Rejected rows:", len(rejected))
    print("Exact duplicate rows removed:", exact_duplicates_removed)

    return result


    print("Input rows:", original_rows)
    print("Clean rows:", len(clean))
    print("Rejected rows:", len(rejected))
    print("Exact duplicate rows removed:", exact_duplicates_removed)

    return result


def main():
    results = []

    for table_name, rules in TABLES.items():
        try:
            results.append(clean_table(table_name, rules))
        except Exception as error:
            print(f"ERROR processing {table_name}: {error}")
            results.append({
                "table": table_name,
                "status": "error",
                "error": str(error),
            })

    report_path = REPORTS / "etl_quality_report.json"
    report_path.write_text(
        json.dumps(results, indent=2, default=str),
        encoding="utf-8"
    )

    print("\n" + "=" * 55)
    print("ETL RUN FINISHED")
    print("Quality report:", report_path)
    print("Clean files:", OUTPUT)
    print("Rejected files:", REJECTED)


if __name__ == "__main__":
    main()
