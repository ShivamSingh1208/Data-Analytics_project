
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

PROJECT_DIR = Path(__file__).resolve().parent.parent

REFERENCE_FILE = (
    PROJECT_DIR
    / " data/03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx - reference_summary_dept_month.csv"
)

DATABASE_URL = (
    "postgresql+psycopg://pulseiq:pulseiq123@localhost:5432/pulseiq"
)

engine = create_engine(DATABASE_URL)


def main():
    if not REFERENCE_FILE.exists():
        raise FileNotFoundError(
            f"Reference file not found: {REFERENCE_FILE}"
        )

    # Read the reference CSV.
    reference = pd.read_csv(REFERENCE_FILE)

    # Convert formatted monetary values, such as "21,428,108.75",
    # into numeric values.
    for column in ["employer_cost", "gross_pay", "overtime_pay"]:
        reference[column] = pd.to_numeric(
            reference[column]
            .astype(str)
            .str.replace(",", "", regex=False),
            errors="coerce",
        )

    # The reference month is the first day of the month.
    reference["month"] = pd.to_datetime(
        reference["month"], errors="raise"
    ).dt.to_period("M")

    # Calculate actual payroll measures from PostgreSQL.
    query = text("""
        SELECT
            department_id,
            DATE_TRUNC('month', period_end_date)::date AS month,
            COUNT(DISTINCT employee_id) AS employees_paid,
            SUM(gross_pay) AS gross_pay,
            SUM(overtime_pay) AS overtime_pay,
            SUM(employer_cost) AS employer_cost
        FROM dw.fact_payroll
        GROUP BY
            department_id,
            DATE_TRUNC('month', period_end_date)::date
    """)

    with engine.connect() as connection:
        actual = pd.read_sql(query, connection)

    actual["month"] = pd.to_datetime(
        actual["month"], errors="raise"
    ).dt.to_period("M")

    # Merge reference and actual values.
    comparison = reference.merge(
        actual,
        on=["department_id", "month"],
        how="outer",
        suffixes=("_reference", "_actual"),
        indicator=True,
    )

    print(f"Reference rows: {len(reference)}")
    print(f"Actual department-month rows: {len(actual)}")
    print(f"Matched keys: {(comparison['_merge'] == 'both').sum()}")
    print(f"Reference-only keys: {(comparison['_merge'] == 'left_only').sum()}")
    print(f"Actual-only keys: {(comparison['_merge'] == 'right_only').sum()}")

    # Compare payroll metrics for matching keys.
    matched = comparison[comparison["_merge"] == "both"].copy()

    for metric in ["employer_cost", "gross_pay", "overtime_pay"]:
        matched[f"{metric}_difference"] = (
            matched[f"{metric}_actual"]
            - matched[f"{metric}_reference"]
        )

    print("\nPayroll metric differences (actual minus reference):")

    for metric in ["employer_cost", "gross_pay", "overtime_pay"]:
        differences = matched[f"{metric}_difference"]
        nonzero = differences.abs() > 0.01

        print(
            f"{metric}: "
            f"{nonzero.sum()} mismatches out of {len(matched)} matched records"
        )

        if nonzero.any():
            print(
                matched.loc[
                    nonzero,
                    [
                        "department_id",
                        "month",
                        f"{metric}_reference",
                        f"{metric}_actual",
                        f"{metric}_difference",
                    ],
                ].head(10).to_string(index=False)
            )

    output_file = PROJECT_DIR / "output" / "department_month_reconciliation.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(output_file, index=False)

    print(f"\nDetailed comparison saved to: {output_file}")


if __name__ == "__main__":
    main()
