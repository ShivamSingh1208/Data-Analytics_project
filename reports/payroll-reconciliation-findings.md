# Payroll Reconciliation Findings

## Summary
The department-month reconciliation identifies two payroll discrepancies. The differences match the cost of one record from each duplicate employee/run pair identified in the rejected payroll data.

## Department-level findings

| Department | Month | Reference employer cost | Actual employer cost | Difference | Employees paid: reference / actual |
|---|---|---:|---:|---:|---:|
| D08 | 2025-05 | 1,882,337.15 | 1,820,524.00 | 61,813.15 | 15 / 14 |
| D02 | 2026-02 | 3,728,454.38 | 3,573,642.49 | 154,811.89 | 25 / 24 |
| **Total difference** | | | | **216,625.04** | |

## Related duplicate records
- EMP-0598, PR-2025-05: PI-000761 and PI-X0002; employer cost per record 61,813.15.
- EMP-0194, PR-2026-02: PI-004059 and PI-X0001; employer cost per record 154,811.89.

The duplicate pairs exist in the source payroll CSV. The rejected records should not be deleted or silently altered; confirm the authoritative record with the data owner before any correction.

## Company-wide answer-key check
The reconciliation answer key reports a zero payroll-to-ledger difference for May 2025 (40,655,815.02 in both payroll employer cost and ledger salary-related expense) and February 2026 (44,044,038.71 in both fields). These are company-wide figures and are not directly comparable to the two department-level differences.

## Conclusion and limitation
The two department-level differences are consistent with the identified duplicate payroll records. Company-wide totals have not yet been independently recalculated from raw data. Further investigation is required before treating the department-level differences as fully resolved.
