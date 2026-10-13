
import pandas as pd
from pathlib import Path

folder = Path("output/cleaned")

employees = pd.read_csv(folder / "cleaned_dim_employee.csv")
payroll = pd.read_csv(folder / "cleaned_fact_payroll.csv")
attendance = pd.read_csv(folder / "cleaned_fact_attendance_monthly.csv")
leave = pd.read_csv(folder / "cleaned_fact_leave.csv")

print("\n========== EMPLOYEE ANALYSIS ==========")
print("Total employee records:", len(employees))

current = employees["is_current"].astype(str).str.upper() == "Y"
print("Current employee records:", current.sum())

print("\nEmployment status:")
print(employees["employment_status"].value_counts(dropna=False))

print("\n========== PAYROLL ANALYSIS ==========")
print("Payroll records:", len(payroll))

for col in ["gross_pay", "net_pay", "total_deductions", "employer_cost"]:
    payroll[col] = pd.to_numeric(payroll[col], errors="coerce")
    print(f"Total {col}: {payroll[col].sum():,.2f}")

print("\n========== ATTENDANCE ANALYSIS ==========")
print("Attendance records:", len(attendance))

for col in [
    "attendance_rate", "present_days", "late_arrivals",
    "overtime_hours", "unpaid_absence_days"
]:
    attendance[col] = pd.to_numeric(attendance[col], errors="coerce")
    print(f"Average {col}: {attendance[col].mean():,.2f}")

print("\n========== LEAVE ANALYSIS ==========")
print("Leave requests:", len(leave))

print("\nRequest status:")
print(leave["status"].value_counts(dropna=False))

print("\nLeave days by status:")
print(leave.groupby("status")["days"].sum())

print("\n========== ANALYSIS COMPLETE ==========")
