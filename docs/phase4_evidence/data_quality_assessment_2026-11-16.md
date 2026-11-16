# PulseIQ Phase 4 — Data Quality Assessment

**Assessment date:** 16 November 2026
**Environment:** Isolated restored PostgreSQL test database
**Database:** `pulseiq_refresh_test_20261116`
**SQL source:** `sql/data_quality_checks.sql`
**Latest verified run ID:** `c1e8c320-1d99-4202-8aed-20e8f04cbfe9`

## 1. Executive summary

The data-quality SQL executed successfully. All 16 checks inserted one result each and shared a single run ID.

| Result | Count |
|---|---:|
| PASS | 6 |
| FAIL | 7 |
| REVIEW_REQUIRED / BLOCKED / CONTEXT_REQUIRED | 3 |
| **Total** | **16** |

The SQL execution and run tracking passed validation. The failed checks represent observed source-data exceptions; they have not been silently corrected or excluded.

## 2. Check results

| Check | Description | Status | Exceptions |
|---|---|---|---:|
| DQ-C01 | Payroll ledger reconciliation | FAIL | 1 |
| DQ-C02 | Ledger entries balance | PASS | 0 |
| DQ-C03 | Unique payroll employee and run | PASS | 0 |
| DQ-C04 | Payroll employee references resolve | PASS | 0 |
| DQ-C05 | Attendance overlaps employment dates | PASS | 0 |
| DQ-C06 | Attendance LOP reconciles to payroll | FAIL | 2 |
| DQ-C07 | Invoice arithmetic | PASS | 0 |
| DQ-C08 | Expense arithmetic | FAIL | 1 |
| DQ-C09 | Task dates chronological | FAIL | 12 |
| DQ-C10 | Leave dates sensible | PASS | 0 |
| DQ-C11 | Attrition risk feed freshness | REVIEW_REQUIRED | Not measured |
| DQ-C12 | Employee history intervals do not overlap | FAIL | 1 |
| DQ-C13 | Pipeline freshness | BLOCKED | Not measured |
| DQ-C14 | Minimum group size | CONTEXT_REQUIRED | Not measured |
| DQ-C15 | Invoice payment balance reconciliation | FAIL | 4 |
| DQ-C16 | Invoice amounts non-negative | FAIL | 1 |

## 3. Observed exceptions

### DQ-C01 — Payroll ledger reconciliation

June 2026 payroll-run ledger expense is ₹54,682,683.35, compared with the reference amount of ₹54,664,233.35.

**Difference: ₹18,450.00.**

The mismatch is in account-level ledger data. It requires finance/source reconciliation.

### DQ-C06 — Attendance and payroll matching

Two attendance employee-months have no corresponding payroll employee-month:

- EMP-0598 — May 2025 — employee key 101421.
- EMP-0194 — February 2026 — employee key 100652.

The LOP comparison includes half-day unpaid attendance using:
`unpaid_absence_days + 0.5 * half_days_unpaid`.

### DQ-C08 — Expense arithmetic

Expense `EXP-00371`, dated 4 May 2026:

- Amount excluding GST: ₹164,090.00
- GST: ₹19,690.80
- Recorded total: ₹184,280.80
- Expected total: ₹183,780.80
- Difference: ₹500.00

The source record needs review.

### DQ-C09 — Task chronology

12 task records have completion dates earlier than their start dates. The inspected records include:

`TASK-02741`, `TASK-02895`, `TASK-06380`, `TASK-07633`,
`TASK-09527`, `TASK-10799`, `TASK-17389`, `TASK-19891`,
`TASK-22599`, `TASK-24674`, `TASK-27078`, `TASK-27674`.

These records require review against the source task history.

### DQ-C12 — Employee history overlap

One overlapping SCD validity pair was found:

- Employee: EMP-0001
- Version key 100000: 19 January 2012 – 12 May 2012
- Version key 100001: 3 May 2012 – 13 May 2015

The validity periods overlap from 3 May through 12 May 2012.

### DQ-C15 — Invoice payment balance

Four invoices have positive totals but both recorded amount paid and balance due are zero:

- INV-00187 — ₹2,450,388.00
- INV-00198 — ₹1,087,016.00
- INV-00334 — ₹1,177,994.00
- INV-00421 — ₹824,820.00

These require payment-status and source reconciliation.

### DQ-C16 — Negative invoice amount

Invoice `INV-00385` has:

- Total: ₹1,049,728.00
- Amount paid: ₹1,049,828.00
- Balance due: -₹100.00

The payment and balance sum to the total, but the negative balance still requires investigation.

## 4. Checks requiring additional operational context

- **DQ-C11:** Latest attrition risk `as_of_date` is 30 September 2026. No approved freshness SLA was supplied, so freshness is not asserted.
- **DQ-C13:** `dw.etl_run_log` is absent from the restored test database. Pipeline freshness cannot be measured.
- **DQ-C14:** Minimum-group-size validation requires a specific grouped query and configured threshold. This batch execution does not provide that context.

These are limitations, not passing results.

## 5. Run tracking validation

The latest execution used one shared run ID:

`c1e8c320-1d99-4202-8aed-20e8f04cbfe9`

Verification confirmed:

- Exactly 16 result rows for the run.
- All 16 checks share the same run ID.
- One UUID is generated at the beginning of the script transaction.
- The `run_id` column has a safe fallback UUID default for inserts outside the script.
- SQL execution completed with COMMIT.
- `git diff --check` passed.

Earlier test executions remain in the result history. They are not part of the latest 16-check summary.

## 6. Data integrity and scope

This assessment was run against an isolated restored test database, not the original `pulseiq` database.

No source financial, attendance, task, invoice, or employee-history records were changed to force checks to pass.

The assessment does not establish production refresh reliability, production access controls, or production data quality. Those require separate production infrastructure and verification.

## 7. Recommended remediation order

1. Reconcile the June 2026 payroll ledger difference with finance.
2. Investigate the two attendance-only employee-months.
3. Correct or formally explain the expense arithmetic exception at source.
4. Validate task chronology against original task history.
5. Resolve the EMP-0001 SCD overlap using an approved history correction.
6. Reconcile the four invoice balances and investigate the INV-00385 overpayment.
7. Define a freshness SLA and implement ETL run logging.
8. Execute minimum-group-size checks in the actual privacy-aware query context.

**Assessment conclusion:** The 16-check SQL batch and run tracking are operational in the isolated test environment. Seven checks identify source-data exceptions, and three require additional operational context. These issues remain visible and must be resolved or formally accepted before claiming complete data-quality compliance.
