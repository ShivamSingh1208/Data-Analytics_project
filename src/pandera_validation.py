"""Pandera schemas for validating cleaned PulseIQ datasets."""
import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema
# Payroll: required identifiers and date key consistency.
PAYROLL_SCHEMA = DataFrameSchema(
    {
        "payroll_item_id": Column(str, nullable=False),
        "employee_id": Column(str, nullable=False),
        "employee_key": Column(str, nullable=False),
        "date_key": Column(
            int,
            Check(
                lambda values: values.astype(str).str.fullmatch(
                    r"\d{8}"
                ),
                element_wise=False,
            ),
            nullable=False,
        ),
        "period_end_date": Column(
            pa.DateTime,
            nullable=False,
        ),
        "gross_pay": Column(
            float,
            Check.ge(0),
            nullable=True,
        ),
        "net_pay": Column(
            float,
            Check.ge(0),
            nullable=True,
        ),
    },
    strict=False,
    coerce=True,
)


# Attendance: required identifiers and non-negative attendance measures.
ATTENDANCE_SCHEMA = DataFrameSchema(
    {
        "attendance_fact_id": Column(str, nullable=False),
        "employee_id": Column(str, nullable=False),
        "employee_key": Column(str, nullable=False),
        "date_key": Column(
            int,
            Check(
                lambda values: values.astype(str).str.fullmatch(
                    r"\d{8}"
                ),
                element_wise=False,
            ),
            nullable=False,
        ),
        "period_end_date": Column(
            pa.DateTime,
            nullable=False,
        ),
        "scheduled_days": Column(float, Check.ge(0), nullable=True),
        "present_days": Column(float, Check.ge(0), nullable=True),
        "late_arrivals": Column(float, Check.ge(0), nullable=True),
    },
    strict=False,
    coerce=True,
)


# Employee dimension: required identifiers and current-record indicator.
EMPLOYEE_SCHEMA = DataFrameSchema(
    {
        "employee_key": Column(str, nullable=False),
        "employee_id": Column(str, nullable=False),
        "full_name": Column(str, nullable=False),
        "valid_from": Column(pa.DateTime, nullable=False),
        "is_current": Column(
            str,
            Check.isin(["Y", "N"]),
            nullable=False,
        ),
    },
    strict=False,
    coerce=True,
)


SCHEMAS = {
    "fact_payroll": PAYROLL_SCHEMA,
    "fact_attendance_monthly": ATTENDANCE_SCHEMA,
    "dim_employee": EMPLOYEE_SCHEMA,
}

def prepare_dataframe(table_name, dataframe):
    """Normalize payroll amount strings before Pandera validation."""
    df = dataframe.copy()

    if table_name == "fact_payroll":
        for column in ["gross_pay", "net_pay"]:
            if column in df.columns:
                df[column] = pd.to_numeric(
                    df[column]
                    .astype("string")
                    .str.replace(",", "", regex=False),
                    errors="coerce",
                )

    return df
def get_validation_errors(table_name, dataframe):
    """Return row-level Pandera validation errors."""

    schema = SCHEMAS.get(table_name)

    if schema is None or dataframe.empty:
        return {}

    try:
        prepared_df = prepare_dataframe(table_name, dataframe)
        schema.validate(prepared_df, lazy=True)
        return {}

    except pa.errors.SchemaErrors as exc:
        error_cases = exc.failure_cases
        row_errors = {}

        for _, error in error_cases.iterrows():
            index = error.get("index")
            column = error.get("column")
            check = error.get("check")

            if index is None or pd.isna(index):
                continue

            message = (
                f"Pandera validation failed: "
                f"{column} - {check}"
            )

            row_errors.setdefault(index, []).append(message)

        return row_errors