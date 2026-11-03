# Phase 3 Task 13 — Cross-Department Impact Findings

## Scope and method
- Grain: department and month.
- Period: April 2025 to September 2026.
- Coverage: 198 department-month rows across 11 department IDs.
- Payroll, attendance, headcount, leave and task sources were aggregated independently before joining.
- Approved leave days are used for leave analysis.
- Overtime cost is represented by overtime pay.
- Leave days per head and overtime share are retained as separate measures.

## Coverage validation
- Payroll, attendance and headcount are populated across all 198 rows.
- Task metrics are not populated for every department-month. Missing task values are retained as NULL rather than converted to zero.
- D00 appears in the department-month source view but is not part of the 10-department target comparison. Its department mapping should be treated as a source-data coverage item.

## September 2026 target findings
- Attendance was below target in 3 departments.
- Overtime share was above target in 2 departments.
- Attrition was above target in 2 departments.
- No department with an available task target was below its task-completion target.

## Payroll reconciliation exceptions
Two payroll differences remain between the reference summary and the independently aggregated payroll data:
- D08 Finance & Accounts, May 2025: ₹61,813.15 difference, associated with duplicate payroll records EMP-0598 (PI-000761 and PI-X0002).
- D02 Product & Design, February 2026: ₹154,811.89 difference, associated with duplicate payroll records EMP-0194 (PI-004059 and PI-X0001).

These exceptions are documented rather than silently adjusted.

## Interpretation
Department-level target breaches can coexist with an overall average that meets its target. The executive scorecard therefore uses Attention when one or more departments breach a target. Missing task data is not interpreted as zero performance.

## Attendance reconciliation

The department mart now applies the same half-day credit convention as the Phase 2 attendance metrics:

`100 * (SUM(present_days) + 0.5 * SUM(half_days_unpaid)) / SUM(scheduled_days)`

The mart was reconciled against `dw.reference_summary_dept_month` after converting the reference proportions to percentages. All 198 of 198 department-month rows are within 0.01 percentage points; the maximum absolute difference is 0.005 percentage points, consistent with the reference values being stored to two decimal places. September 2026 values also match the reference at two decimal places.

The underlying attendance source and reference values were not changed; only the department mart calculation was corrected. D00 remains outside the 10-department target comparison.

For September 2026, D06 (92.43%), D08 (88.87%) and D10 (93.29%) were below the 94% attendance target. The executive scorecard reports 94.60% overall attendance with status Attention, reflecting that department-level breaches can coexist with an overall result above target.
