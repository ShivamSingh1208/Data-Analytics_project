BEGIN;

-- DQ-C03: Unique payroll rows
INSERT INTO dw.dq_results (check_id, check_name, table_name, bad_rows, status, details)
SELECT 'DQ-C03', 'Unique payroll rows', 'dw.fact_payroll', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Duplicate employee_id + run_id groups'
FROM (
    SELECT employee_id, run_id
    FROM dw.fact_payroll
    GROUP BY employee_id, run_id
    HAVING COUNT(*) > 1
) q;

-- DQ-C04: No orphan employees
INSERT INTO dw.dq_results (check_id, check_name, table_name, bad_rows, status, details)
SELECT 'DQ-C04', 'No orphan employees', 'dw.fact_payroll', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Payroll rows without a matching employee'
FROM dw.fact_payroll f
WHERE NOT EXISTS (
    SELECT 1 FROM dw.dim_employee d
    WHERE d.employee_id = f.employee_id
);

-- DQ-C05: No attendance after employee exit
INSERT INTO dw.dq_results (check_id, check_name, table_name, bad_rows, status, details)
SELECT 'DQ-C05', 'No attendance after exit', 'dw.fact_attendance_monthly', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Attendance period ends after employee exit date'
FROM dw.fact_attendance_monthly a
WHERE EXISTS (
    SELECT 1 FROM dw.dim_employee d
    WHERE d.employee_id = a.employee_id
      AND d.exit_date IS NOT NULL
      AND a.period_end_date > d.exit_date
);

-- DQ-C06: Compare unpaid absence days with payroll LOP days
WITH attendance AS (
    SELECT employee_id, period_end_date,
           SUM(COALESCE(unpaid_absence_days, 0)) AS unpaid_days
    FROM dw.fact_attendance_monthly
    GROUP BY employee_id, period_end_date
),
payroll AS (
    SELECT employee_id, period_end_date,
           SUM(COALESCE(lop_days, 0)) AS lop_days
    FROM dw.fact_payroll
    GROUP BY employee_id, period_end_date
),
mismatches AS (
    SELECT a.employee_id, a.period_end_date
    FROM attendance a
    JOIN payroll p USING (employee_id, period_end_date)
    WHERE ABS(a.unpaid_days - p.lop_days) > 0.01
)
INSERT INTO dw.dq_results (check_id, check_name, table_name, bad_rows, status, details)
SELECT 'DQ-C06', 'Unpaid leave deducted', 'dw.fact_attendance_monthly + dw.fact_payroll',
       COUNT(*), CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Employee-month groups where unpaid absence days differ from LOP days'
FROM mismatches;

-- DQ-C10: Leave end date must not precede start date
INSERT INTO dw.dq_results (check_id, check_name, table_name, bad_rows, status, details)
SELECT 'DQ-C10', 'Leave dates sensible', 'dw.fact_leave', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Leave requests where end_date < start_date'
FROM dw.fact_leave
WHERE end_date < start_date;

-- DQ-C12: Employee dimension validity intervals must not overlap
INSERT INTO dw.dq_results (check_id, check_name, table_name, bad_rows, status, details)
SELECT 'DQ-C12', 'Dimension history does not overlap', 'dw.dim_employee', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Pairs of versions for one employee with overlapping validity dates'
FROM dw.dim_employee a
JOIN dw.dim_employee b
  ON a.employee_id = b.employee_id
 AND a.employee_key < b.employee_key
 AND a.valid_from <= COALESCE(b.valid_to, DATE '9999-12-31')
 AND b.valid_from <= COALESCE(a.valid_to, DATE '9999-12-31');

-- Checks requiring source tables not currently present in dw are BLOCKED.
INSERT INTO dw.dq_results
    (check_id, check_name, table_name, bad_rows, status, details)
VALUES
('DQ-C01', 'Payroll equals ledger', 'fact_ledger', 0, 'BLOCKED',
 'Ledger table is not loaded in dw; reconciliation cannot be evaluated.'),
('DQ-C02', 'Ledger balanced', 'fact_ledger', 0, 'BLOCKED',
 'Ledger table is not loaded in dw.'),
('DQ-C07', 'Invoice arithmetic', 'fact_invoice', 0, 'BLOCKED',
 'Invoice table is not loaded in dw.'),
('DQ-C08', 'Expense arithmetic', 'fact_expense', 0, 'BLOCKED',
 'Expense table is not loaded in dw.'),
('DQ-C09', 'Task dates sensible', 'fact_task', 0, 'BLOCKED',
 'Task table is not loaded in dw.'),
('DQ-C11', 'AI feeds are fresh', 'fact_attrition_risk', 0, 'BLOCKED',
 'Attrition-risk table is not loaded in dw.'),
('DQ-C13', 'Pipeline freshness', 'etl_run_log', 0, 'BLOCKED',
 'ETL run log table is not loaded in dw.'),
('DQ-C14', 'Minimum group size', 'query context', 0, 'BLOCKED',
 'Requires a real grouped query and configured minimum group size; no query context is available to this batch check.');

COMMIT;
