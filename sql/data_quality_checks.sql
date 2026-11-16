BEGIN;

-- Generate one run ID for this entire execution.
SELECT set_config('pulseiq.dq_run_id', gen_random_uuid()::TEXT, TRUE);

CREATE SCHEMA IF NOT EXISTS dw;

CREATE TABLE IF NOT EXISTS dw.dq_results (
    result_id BIGSERIAL PRIMARY KEY,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    check_id VARCHAR(20) NOT NULL,
    check_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    bad_rows BIGINT,
    status VARCHAR(30) NOT NULL,
    details TEXT NOT NULL
);

ALTER TABLE dw.dq_results
ADD COLUMN IF NOT EXISTS run_id UUID NOT NULL DEFAULT gen_random_uuid();

ALTER TABLE dw.dq_results
ALTER COLUMN run_id SET DEFAULT (
    COALESCE(
        NULLIF(current_setting('pulseiq.dq_run_id', TRUE), ''),
        gen_random_uuid()::TEXT
    )::UUID
);

-- Keep historical runs. Each execution appends a new set of results.

-- DQ-C01: Payroll-run ledger expense agrees with the monthly reference.
WITH monthly_ledger AS (
    SELECT posting_period,
           SUM(debit-credit) AS ledger_cost
    FROM dw.fact_ledger
    WHERE source_type='PAYROLL_RUN'
      AND account_code IN ('5001','5002','5003','5004','5005')
    GROUP BY posting_period
),
mismatches AS (
    SELECT r.month,
           COALESCE(l.ledger_cost,0) AS ledger_cost,
           r.ledger_salary_related_expense AS reference_cost
    FROM dw.phase2_payroll_reference r
    LEFT JOIN monthly_ledger l
      ON l.posting_period=TO_CHAR(r.month,'YYYY-MM')
    WHERE ABS(COALESCE(l.ledger_cost,0)
              -COALESCE(r.ledger_salary_related_expense,0))>0.01
)
INSERT INTO dw.dq_results
(check_id,check_name,table_name,bad_rows,status,details)
SELECT 'DQ-C01','Payroll ledger reconciliation',
       'dw.fact_ledger + dw.phase2_payroll_reference',
       COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'PASS' ELSE 'FAIL' END,
       COALESCE(
         STRING_AGG(
           TO_CHAR(month,'YYYY-MM') || ': ledger=' ||
           ROUND(ledger_cost,2)::TEXT || ', reference=' ||
           ROUND(reference_cost,2)::TEXT,
           '; ' ORDER BY month
         ),
         'All payroll-run ledger months reconcile within 0.01.'
       )
FROM mismatches;

-- DQ-C02: Every ledger entry balances.
INSERT INTO dw.dq_results
(check_id,check_name,table_name,bad_rows,status,details)
SELECT 'DQ-C02','Ledger entries balance','dw.fact_ledger',
       COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'PASS' ELSE 'FAIL' END,
       'Entry IDs where total debit differs from total credit by more than 0.01.'
FROM (
    SELECT entry_id
    FROM dw.fact_ledger
    GROUP BY entry_id
    HAVING ABS(SUM(debit)-SUM(credit))>0.01
) q;

-- DQ-C03: Payroll employee/run combination is unique.
INSERT INTO dw.dq_results
(check_id,check_name,table_name,bad_rows,status,details)
SELECT 'DQ-C03','Unique payroll employee and run',
       'dw.fact_payroll',COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'PASS' ELSE 'FAIL' END,
       'Duplicate employee_id + run_id groups.'
FROM (
    SELECT employee_id,run_id
    FROM dw.fact_payroll
    GROUP BY employee_id,run_id
    HAVING COUNT(*)>1
) q;

-- DQ-C04: Payroll employee ID and version key both resolve.
INSERT INTO dw.dq_results
(check_id,check_name,table_name,bad_rows,status,details)
SELECT 'DQ-C04','Payroll employee references resolve',
       'dw.fact_payroll + dw.dim_employee',COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'PASS' ELSE 'FAIL' END,
       'Payroll rows whose employee_id and employee_key do not resolve to the same dimension version.'
FROM dw.fact_payroll f
WHERE NOT EXISTS (
    SELECT 1
    FROM dw.dim_employee d
    WHERE d.employee_id=f.employee_id
      AND d.employee_key=f.employee_key
);

-- DQ-C05: Attendance month must overlap the employee's employment.
-- A month-end after exit is not an error if the employee worked earlier
-- in that month.
INSERT INTO dw.dq_results
(check_id,check_name,table_name,bad_rows,status,details)
SELECT 'DQ-C05','Attendance overlaps employment dates',
       'dw.fact_attendance_monthly + dw.dim_employee',COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'PASS' ELSE 'FAIL' END,
       'Attendance months entirely before hire or entirely after exit, using the exact employee_key version.'
FROM dw.fact_attendance_monthly a
JOIN dw.dim_employee d ON d.employee_key=a.employee_key
WHERE a.period_end_date < d.hire_date
   OR (d.exit_date IS NOT NULL
       AND DATE_TRUNC('month',a.period_end_date)::DATE > d.exit_date);

-- DQ-C06: Reconcile LOP, including half-day unpaid attendance.
-- Unmatched employee-months are counted as exceptions too.
WITH attendance AS (
    SELECT employee_id,period_end_date,
           SUM(COALESCE(unpaid_absence_days,0)
               +0.5*COALESCE(half_days_unpaid,0)) AS adjusted_lop
    FROM dw.fact_attendance_monthly
    GROUP BY employee_id,period_end_date
),
payroll AS (
    SELECT employee_id,period_end_date,
           SUM(COALESCE(lop_days,0)) AS payroll_lop
    FROM dw.fact_payroll
    GROUP BY employee_id,period_end_date
),
exceptions AS (
    SELECT a.employee_id,a.period_end_date
    FROM attendance a
    JOIN payroll p USING(employee_id,period_end_date)
    WHERE ABS(a.adjusted_lop-p.payroll_lop)>0.01

    UNION ALL

    SELECT a.employee_id,a.period_end_date
    FROM attendance a
    WHERE NOT EXISTS (
        SELECT 1 FROM payroll p
        WHERE p.employee_id=a.employee_id
          AND p.period_end_date=a.period_end_date
    )
)
INSERT INTO dw.dq_results
(check_id,check_name,table_name,bad_rows,status,details)
SELECT 'DQ-C06','Attendance LOP reconciles to payroll',
       'dw.fact_attendance_monthly + dw.fact_payroll',
       COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'PASS' ELSE 'FAIL' END,
       'Uses unpaid_absence_days + 0.5 * half_days_unpaid. Includes unmatched attendance employee-months.'
FROM exceptions;

-- DQ-C07: Invoice total equals subtotal plus GST.
INSERT INTO dw.dq_results
(check_id,check_name,table_name,bad_rows,status,details)
SELECT 'DQ-C07','Invoice arithmetic','dw.fact_invoice',
       COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'PASS' ELSE 'FAIL' END,
       'Invoices where total_amount differs from subtotal + gst_amount by more than 0.01.'
FROM dw.fact_invoice
WHERE ABS(total_amount-(subtotal+gst_amount))>0.01;

-- DQ-C08: Expense total equals amount excluding GST plus GST.
INSERT INTO dw.dq_results
(check_id,check_name,table_name,bad_rows,status,details)
SELECT 'DQ-C08','Expense arithmetic','dw.fact_expense',
       COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'PASS' ELSE 'FAIL' END,
       'Expenses where total_amount differs from amount_excl_gst + gst_amount by more than 0.01.'
FROM dw.fact_expense
WHERE ABS(total_amount-(amount_excl_gst+gst_amount))>0.01;

-- DQ-C09: Task chronology.
INSERT INTO dw.dq_results
(check_id,check_name,table_name,bad_rows,status,details)
SELECT 'DQ-C09','Task dates chronological','dw.fact_task',
       COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'PASS' ELSE 'FAIL' END,
       'Distinct tasks with started_date before created_date, due_date before created_date, completed_date before created_date, or completed_date before started_date.'
FROM dw.fact_task
WHERE (started_date IS NOT NULL AND started_date<created_date)
   OR (due_date IS NOT NULL AND due_date<created_date)
   OR (completed_date IS NOT NULL AND completed_date<created_date)
   OR (completed_date IS NOT NULL AND started_date IS NOT NULL
       AND completed_date<started_date);

-- DQ-C10: Leave end date must not precede start date.
INSERT INTO dw.dq_results
(check_id,check_name,table_name,bad_rows,status,details)
SELECT 'DQ-C10','Leave dates sensible','dw.fact_leave',
       COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'PASS' ELSE 'FAIL' END,
       'Leave requests where end_date is earlier than start_date.'
FROM dw.fact_leave
WHERE end_date<start_date;

-- DQ-C11: Risk feed freshness needs an agreed refresh SLA.
INSERT INTO dw.dq_results
(check_id,check_name,table_name,bad_rows,status,details)
SELECT 'DQ-C11','Attrition risk feed freshness',
       'dw.fact_attrition_risk',NULL,'REVIEW_REQUIRED',
       'Latest as_of_date=' ||
       COALESCE(MAX(as_of_date)::TEXT,'no date available') ||
       '. No approved freshness SLA was supplied; freshness is not asserted.'
FROM dw.fact_attrition_risk;

-- DQ-C12: Employee version validity intervals must not overlap.
INSERT INTO dw.dq_results
(check_id,check_name,table_name,bad_rows,status,details)
SELECT 'DQ-C12','Employee history intervals do not overlap',
       'dw.dim_employee',COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'PASS' ELSE 'FAIL' END,
       'Overlapping employee version pairs. Existing source overlap is reported, not repaired automatically.'
FROM dw.dim_employee a
JOIN dw.dim_employee b
  ON a.employee_id=b.employee_id
 AND a.employee_key<b.employee_key
 AND a.valid_from<=COALESCE(b.valid_to,DATE '9999-12-31')
 AND b.valid_from<=COALESCE(a.valid_to,DATE '9999-12-31');

-- DQ-C13: No ETL run log exists, so pipeline freshness cannot be measured.
INSERT INTO dw.dq_results
(check_id,check_name,table_name,bad_rows,status,details)
SELECT 'DQ-C13','Pipeline freshness','dw.etl_run_log',
       NULL,'BLOCKED',
       'dw.etl_run_log is absent. No pipeline freshness claim is made.';

-- DQ-C14: Requires a real grouped query and a configured minimum size.
INSERT INTO dw.dq_results
(check_id,check_name,table_name,bad_rows,status,details)
SELECT 'DQ-C14','Minimum group size','query context',
       NULL,'CONTEXT_REQUIRED',
       'Requires a specific grouped query and configured minimum group size; this batch run has no query context.';

-- DQ-C15: Invoice amount paid plus balance due equals total.
INSERT INTO dw.dq_results
(check_id,check_name,table_name,bad_rows,status,details)
SELECT 'DQ-C15','Invoice payment balance reconciliation',
       'dw.fact_invoice',COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'PASS' ELSE 'FAIL' END,
       'Invoices where amount_paid + balance_due differs from total_amount by more than 0.01.'
FROM dw.fact_invoice
WHERE ABS(total_amount-amount_paid-balance_due)>0.01;

-- DQ-C16: Invoice monetary fields must not be negative.
INSERT INTO dw.dq_results
(check_id,check_name,table_name,bad_rows,status,details)
SELECT 'DQ-C16','Invoice amounts non-negative',
       'dw.fact_invoice',COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'PASS' ELSE 'FAIL' END,
       'Invoices with negative total_amount, amount_paid, or balance_due.'
FROM dw.fact_invoice
WHERE total_amount<0 OR amount_paid<0 OR balance_due<0;

COMMIT;
