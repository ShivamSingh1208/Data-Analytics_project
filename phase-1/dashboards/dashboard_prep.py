
import pandas as pd
from pathlib import Path

source = Path("output/cleaned")
output = Path("output/dashboard")
output.mkdir(parents=True, exist_ok=True)

payroll = pd.read_csv(source / "cleaned_fact_payroll.csv")
attendance = pd.read_csv(
    source / "cleaned_fact_attendance_monthly.csv"
)
employees = pd.read_csv(source / "cleaned_dim_employee.csv")
leave = pd.read_csv(source / "cleaned_fact_leave.csv")

# 1. Monthly payroll summary
payroll["period_end_date"] = pd.to_datetime(
    payroll["period_end_date"], errors="coerce"
)

payroll_cols = [
    "gross_pay", "net_pay", "total_deductions", "employer_cost"
]
for col in payroll_cols:
    payroll[col] = pd.to_numeric(payroll[col], errors="coerce")

monthly_payroll = (
    payroll.dropna(subset=["period_end_date"])
    .assign(month=lambda d: d["period_end_date"].dt.to_period("M").astype(str))
    .groupby("month", as_index=False)[payroll_cols]
    .sum()
)
monthly_payroll.to_csv(output / "monthly_payroll.csv", index=False)

# 2. Monthly attendance summary
attendance["period_end_date"] = pd.to_datetime(
    attendance["period_end_date"], errors="coerce"
)

attendance_cols = [
    "present_days", "scheduled_days", "late_arrivals",
    "overtime_hours", "unpaid_absence_days"
]
for col in attendance_cols:
    attendance[col] = pd.to_numeric(attendance[col], errors="coerce")

attendance_summary = (
    attendance.dropna(subset=["period_end_date"])
    .assign(month=lambda d: d["period_end_date"].dt.to_period("M").astype(str))
    .groupby("month", as_index=False)
    .agg(
        attendance_records=("attendance_fact_id", "count"),
        present_days=("present_days", "sum"),
        scheduled_days=("scheduled_days", "sum"),
        late_arrivals=("late_arrivals", "sum"),
        overtime_hours=("overtime_hours", "sum"),
        unpaid_absence_days=("unpaid_absence_days", "sum"),
    )
)

attendance_summary["attendance_rate_pct"] = (
    attendance_summary["present_days"]
    / attendance_summary["scheduled_days"].replace(0, pd.NA)
    * 100
).round(2)

attendance_summary.to_csv(
    output / "monthly_attendance.csv", index=False
)

# 3. Leave request summary
leave_summary = (
    leave.groupby("status", dropna=False)
    .agg(
        requests=("leave_request_id", "count"),
        leave_days=("days", "sum")
    )
    .reset_index()
)
leave_summary.to_csv(output / "leave_summary.csv", index=False)

# 4. Employee status summary
# This counts current employee dimension records only.
current_employees = employees[
    employees["is_current"].astype(str).str.upper().eq("Y")
].copy()

employee_summary = (
    current_employees.groupby("employment_status", dropna=False)
    .size()
    .reset_index(name="employee_records")
)
employee_summary.to_csv(output / "employee_status_summary.csv", index=False)

print("Dashboard datasets created in:", output)
for file in sorted(output.glob("*.csv")):
    df = pd.read_csv(file)
    print(f"{file.name}: {len(df)} rows")
