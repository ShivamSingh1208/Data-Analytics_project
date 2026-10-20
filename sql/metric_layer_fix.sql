BEGIN;

-- Recreate dependent views so PostgreSQL can accept the numeric type change.
DROP VIEW IF EXISTS dw.metric_department_dashboard;
DROP VIEW IF EXISTS dw.metric_attendance_monthly;

CREATE VIEW dw.metric_attendance_monthly AS
SELECT
    date_trunc('month', period_end_date)::date AS month_start,
    department_id,
    SUM(COALESCE(present_days, 0)) AS present_days,
    SUM(COALESCE(half_days_unpaid, 0)) AS half_days_unpaid,
    SUM(COALESCE(scheduled_days, 0)) AS scheduled_days,
    SUM(COALESCE(late_arrivals, 0)) AS late_arrivals,
    (
        SUM(COALESCE(present_days, 0))::numeric
        + 0.5 * SUM(COALESCE(half_days_unpaid, 0))::numeric
    ) / NULLIF(SUM(COALESCE(scheduled_days, 0)), 0) * 100
        AS attendance_rate_pct,
    SUM(COALESCE(late_arrivals, 0))::numeric
        / NULLIF(SUM(COALESCE(present_days, 0)), 0) * 100
        AS late_arrival_rate_pct
FROM dw.fact_attendance_monthly
GROUP BY date_trunc('month', period_end_date)::date, department_id;

CREATE VIEW dw.metric_department_dashboard AS
SELECT
    p.month_start,
    p.department_id,
    p.paid_employees,
    p.gross_pay,
    p.net_pay,
    p.employer_cost,
    p.cost_per_head,
    p.overtime_share_pct,
    p.variable_pay_share_pct,
    p.lop_days,
    a.attendance_rate_pct,
    a.late_arrival_rate_pct,
    h.headcount_end,
    h.hires,
    h.exits
FROM dw.metric_payroll_monthly p
LEFT JOIN dw.metric_attendance_monthly a USING (month_start, department_id)
LEFT JOIN dw.metric_headcount_monthly h USING (month_start, department_id)
WHERE p.paid_employees >= 5;

CREATE OR REPLACE VIEW dw.metric_view_status AS
SELECT
    metric_id,
    metric_name,
    CASE
        WHEN metric_id IN ('M01','M02','M03','M04','M05')
            THEN 'IMPLEMENTED_DERIVED'
        WHEN metric_id IN ('M07','M08','M09','M10','M11','M12',
                           'M13','M14','M15')
            THEN 'IMPLEMENTED'
        ELSE 'SOURCE_REQUIRED'
    END AS implementation_status
FROM dw.metric_catalog;

COMMIT;
