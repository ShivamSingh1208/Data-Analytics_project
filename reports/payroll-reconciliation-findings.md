# Payroll Reconciliation Findings

## 1. Executive summary

The cleaned payroll warehouse has two unresolved department-month
reconciliation differences against the payroll reference. Both differences
match the employer cost of one record in a duplicate employee/run pair
identified in the rejected payroll data.

The matching amounts are evidence for investigation, not proof of which
source record is authoritative. No rejected payroll records have been
restored or silently altered.

## 2. Department-level reconciliation

| Department | Month | Reference employer cost | Cleaned actual employer cost | Reference minus actual | Employees paid: reference / actual |
|---|---|---:|---:|---:|---:|
| D08 — Finance & Accounts | 2025-05 | ₹1,882,337.15 | ₹1,820,524.00 | ₹61,813.15 | 15 / 14 |
| D02 — Product & Design | 2026-02 | ₹3,728,454.38 | ₹3,573,642.49 | ₹154,811.89 | 25 / 24 |
| **Combined difference** | | | | **₹216,625.04** | **One employee short in each month** |

The combined difference is the sum of these two department-month
reference-to-actual gaps. It is not the company-wide budget variance.

## 3. Related rejected payroll records

| Month | Employee | Payroll run | Payroll item IDs | Employer cost per record |
|---|---|---|---|---:|
| 2025-05 | EMP-0598 | PR-2025-05 | PI-000761, PI-X0002 | ₹61,813.15 |
| 2026-02 | EMP-0194 | PR-2026-02 | PI-004059, PI-X0001 | ₹154,811.89 |

Checks against `dw.fact_payroll` found none of these four payroll item IDs
in the cleaned fact table. The two employee/month checks also returned no
payroll rows for EMP-0598 in May 2025 and EMP-0194 in February 2026.

The source rejected payroll data also contains two other rejected rows:
- PI-X0003, employee EMP-9001, April 2026, D01, employer cost ₹96,015.00.
- PI-X0004, employee EMP-9002, December 2025, D09, employer cost ₹98,327.42.

Those two rows were rejected because their employee IDs were missing from
`dim_employee`; they are separate data-quality issues and should not be
assumed to explain the two department-month differences above.

### Required action

Ask the payroll/data owner to confirm the authoritative records for both
duplicate employee/run pairs and determine whether the reference or source
data needs correction. Until confirmation:
- Keep the ETL duplicate-key and employee-dimension validation rules.
- Preserve rejected rows and the rejection evidence.
- Do not manually restore, delete, or modify payroll records just to force
  the reconciliation to match.
- Re-run the reconciliation after any approved source correction.

## 4. Company-wide payroll-to-ledger check

The reconciliation answer key reports the following company-wide totals:

| Month | Reference payroll employer cost | Ledger salary-related expense | Difference |
|---|---:|---:|---:|
| 2025-05 | ₹40,655,815.02 | ₹40,655,815.02 | ₹0.00 |
| 2026-02 | ₹44,044,038.71 | ₹44,044,038.71 | ₹0.00 |

These company-wide reference-to-ledger checks are zero-difference checks.
They do not establish that the cleaned department-level payroll matches
the reference. The cleaned department actuals remain lower by ₹61,813.15
and ₹154,811.89 for the two periods above.

## 5. Separate department payroll budget analysis

The overall budget comparison covers 198 department-month records, 11
departments, and April 2025 through September 2026.

| Measure | Amount |
|---|---:|
| Total budget | ₹862,030,000.00 |
| Cleaned actual employer cost | ₹861,369,767.38 |
| Net variance (actual minus budget) | **−₹660,232.62** |

A negative variance indicates that cleaned actual employer cost is below
budget overall. This budget variance is a separate measure from the
₹216,625.04 combined payroll-reference difference and must not be added to
or substituted for it.

## 6. Conclusion and limitations

The two department-level payroll discrepancies remain unresolved. Their
amounts match the costs of the identified rejected duplicate employee/run
records, but the authoritative record has not been confirmed by the data
owner. The company-wide payroll-to-ledger checks show zero difference in
the two cited months, but they are not a substitute for reconciling cleaned
department-level actuals to the reference.

Report the differences transparently until the source records and reference
are confirmed. Do not describe these discrepancies as resolved.
