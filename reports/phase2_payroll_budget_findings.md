# Phase 2 — Payroll Reconciliation and Budget Findings

## Payroll reconciliation

The cleaned payroll warehouse was compared with the official monthly
reference for April 2025 through September 2026.

- 18 monthly periods were checked.
- 16 months matched the official employer-cost and employee-count reference.
- May 2025 was short by 1 employee and ₹61,813.15 in employer cost.
- February 2026 was short by 1 employee and ₹154,811.89 in employer cost.
- Both differences match the costs of duplicate employee/run pairs found
  in the rejected payroll data.
- The ETL rejected both records in each duplicate pair. No rejected record
  was manually restored or silently changed.
- The authoritative records require confirmation from the data owner.

## Department payroll budget

The budget analysis covers 198 department-month records, 11 departments,
and April 2025 through September 2026.

- Total budget: ₹862,030,000.00.
- Actual cleaned payroll employer cost: ₹861,369,767.38.
- Net variance (actual minus budget): -₹660,232.62.
- Negative variance indicates underspend; positive variance indicates overspend.

### Largest net overspends

| Department | Net variance | Net variance % |
|---|---:|---:|
| Data & AI | ₹992,768.20 | 0.90% |
| Customer Support | ₹482,050.62 | 1.01% |
| Product & Design | ₹453,539.93 | 0.65% |

Engineering had the largest net underspend at ₹2,054,508.87 below budget
(-0.60%).

### Manual validation

Three department-month budget values were compared with the original CSV:
- April 2025, Engineering (D01)
- April 2026, Engineering (D01)
- June 2026, Data & AI (D03)

All three source budget values matched the warehouse view.

## Limitations and follow-up

Budget variance alone does not establish the cause of a difference or whether
underspending is beneficial. Payroll actuals are based on cleaned warehouse
records and retain the two unresolved monthly reconciliation differences.
The official reference is company-level; it must not be treated as a
department-level payroll reconciliation source.

The 18 missing task-completion targets remain NULL and must not be treated
as zero or replaced with an assumed value.
