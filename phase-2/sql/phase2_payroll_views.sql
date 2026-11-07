CREATE OR REPLACE VIEW dw.metric_payroll_monthly AS
SELECT
    DATE_TRUNC('month', period_end_date)::date AS month,
    COUNT(*) AS payroll_rows,
    COUNT(DISTINCT employee_id) AS employees_paid,
    SUM(gross_pay) AS gross_pay,
    SUM(net_pay) AS net_pay,
    SUM(employer_cost) AS employer_cost,
    AVG(gross_pay) AS average_gross_per_payroll_row,
    AVG(employer_cost) AS average_employer_cost_per_payroll_row
FROM dw.fact_payroll
WHERE period_end_date IS NOT NULL
GROUP BY DATE_TRUNC('month', period_end_date)::date;

CREATE OR REPLACE VIEW dw.metric_payroll_department_monthly AS
SELECT
    DATE_TRUNC('month', period_end_date)::date AS month,
    department_id,
    COUNT(*) AS payroll_rows,
    COUNT(DISTINCT employee_id) AS employees_paid,
    SUM(gross_pay) AS gross_pay,
    SUM(net_pay) AS net_pay,
    SUM(employer_cost) AS employer_cost,
    SUM(employer_cost) / NULLIF(COUNT(DISTINCT employee_id), 0)
        AS employer_cost_per_employee
FROM dw.fact_payroll
WHERE period_end_date IS NOT NULL
GROUP BY DATE_TRUNC('month', period_end_date)::date, department_id;

CREATE OR REPLACE VIEW dw.metric_payroll_reconciliation AS
SELECT
    r.month,
    r.employees_paid AS reference_employees_paid,
    COALESCE(p.employees_paid, 0) AS actual_employees_paid,
    COALESCE(p.employees_paid, 0) - r.employees_paid
        AS employee_count_difference,
    r.payroll_gross_pay AS reference_gross_pay,
    COALESCE(p.gross_pay, 0) AS actual_gross_pay,
    COALESCE(p.gross_pay, 0) - r.payroll_gross_pay
        AS gross_pay_difference,
    r.payroll_net_pay AS reference_net_pay,
    COALESCE(p.net_pay, 0) AS actual_net_pay,
    COALESCE(p.net_pay, 0) - r.payroll_net_pay
        AS net_pay_difference,
    r.payroll_employer_cost AS reference_employer_cost,
    COALESCE(p.employer_cost, 0) AS actual_employer_cost,
    COALESCE(p.employer_cost, 0) - r.payroll_employer_cost
        AS employer_cost_difference,
    r.ledger_salary_related_expense,
    r.payroll_vs_ledger_difference AS reference_payroll_ledger_difference
FROM dw.phase2_payroll_reference r
LEFT JOIN dw.metric_payroll_monthly p
    ON p.month = r.month;

CREATE OR REPLACE VIEW dw.metric_payroll_department_reconciliation AS
WITH actual AS (
    SELECT
        DATE_TRUNC('month', period_end_date)::date AS month,
        department_id,
        COUNT(DISTINCT employee_id) AS actual_employees_paid,
        SUM(employer_cost) AS actual_employer_cost
    FROM dw.fact_payroll
    WHERE period_end_date IS NOT NULL
    GROUP BY DATE_TRUNC('month', period_end_date)::date, department_id
),
reference AS (
    SELECT
        month,
        department_id,
        budget_payroll_cost
    FROM dw.phase2_payroll_reference
    CROSS JOIN LATERAL (
        SELECT NULL::varchar AS department_id,
               NULL::numeric AS budget_payroll_cost
    ) unused
    WHERE FALSE
)
SELECT
    a.month,
    a.department_id,
    a.actual_employees_paid,
    a.actual_employer_cost
FROM actual a;
