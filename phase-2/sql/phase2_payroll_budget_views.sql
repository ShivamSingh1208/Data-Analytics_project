DROP VIEW IF EXISTS dw.metric_payroll_department_reconciliation;

CREATE VIEW dw.metric_payroll_department_reconciliation AS
SELECT
    b.month,
    b.department_id,
    d.department_name,
    COALESCE(a.actual_employees_paid, 0) AS actual_employees_paid,
    COALESCE(a.actual_employer_cost, 0)::NUMERIC(18,2)
        AS actual_employer_cost,
    b.budget_payroll_cost,
    (
        COALESCE(a.actual_employer_cost, 0)
        - b.budget_payroll_cost
    )::NUMERIC(18,2) AS variance,
    CASE
        WHEN b.budget_payroll_cost = 0 THEN NULL
        ELSE ROUND(
            (
                COALESCE(a.actual_employer_cost, 0)
                - b.budget_payroll_cost
            ) * 100.0 / b.budget_payroll_cost,
            2
        )
    END AS variance_pct,
    CASE
        WHEN COALESCE(a.actual_employer_cost, 0)
             > b.budget_payroll_cost THEN 'Overspend'
        WHEN COALESCE(a.actual_employer_cost, 0)
             < b.budget_payroll_cost THEN 'Underspend'
        ELSE 'On Budget'
    END AS budget_status
FROM dw.phase2_payroll_budget b
JOIN dw.dim_department d
    ON d.department_id = b.department_id
LEFT JOIN (
    SELECT
        DATE_TRUNC('month', period_end_date)::DATE AS month,
        department_id,
        COUNT(DISTINCT employee_id) AS actual_employees_paid,
        SUM(employer_cost) AS actual_employer_cost
    FROM dw.fact_payroll
    WHERE period_end_date IS NOT NULL
    GROUP BY 1, 2
) a
    ON a.month = b.month
   AND a.department_id = b.department_id;
