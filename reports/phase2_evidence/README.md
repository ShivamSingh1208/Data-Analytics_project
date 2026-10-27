# PulseIQ Phase 2 — Generated Evidence

Generated from the live PostgreSQL warehouse using the existing metric views.
CSV files are the primary evidence; charts are derived visual summaries.
No individual-level attrition risk records are exported by this script.

## Export row counts
- `attendance_monthly.csv`: 18 rows
- `attendance_department_monthly.csv`: 198 rows
- `leave_monthly.csv`: 54 rows
- `attrition_monthly.csv`: 81 rows
- `attrition_department_monthly.csv`: 891 rows
- `attrition_risk_snapshot.csv`: 10 rows
- `productivity_team.csv`: 16 rows
- `productivity_sprint.csv`: 608 rows
- `payroll_reconciliation.csv`: 18 rows
- `payroll_department_budget.csv`: 198 rows
- `kpi_target_comparison.csv`: 180 rows

## Generated charts
- Charts created: 6

## Important interpretation notes
- Payroll reconciliation differences are not treated as resolved.
- KPI target results retain missing task targets as unavailable.
- Overtime share uses the documented 8-hours-per-scheduled-day assumption.
- Charts are analytical evidence, not screenshots of the Superset interface.
