# ETL Rejected Records Review

## Summary

| Table | Rejected records |
|---|---:|
| `fact_payroll` | 6 |
| `fact_attendance_monthly` | 4 |
| `fact_leave` | 2 |

## fact_payroll

Rejected records: **6**

### Rejection reasons

- duplicate employee_id + run_id combination: 4
- employee_id not found in dim_employee: 2

## fact_attendance_monthly

Rejected records: **4**

### Rejection reasons

- attendance month ends after employee exit month: 4

## fact_leave

Rejected records: **2**

### Rejection reasons

- start_date is after end_date: 2

## Recommended actions

- Confirm duplicate payroll keys with the payroll data owner.
- Resolve missing employee references with the employee-data owner.
- Verify attendance periods against employee exit dates.
- Review reversed leave dates, prioritizing approved requests.
- Preserve source records and document approved corrections.

Generated from the current ETL rejected-record CSV files.
