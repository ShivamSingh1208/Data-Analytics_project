-- Additional governed metrics and privacy-filtered workforce views.
-- Headcount metrics are derived from dim_employee and are not authoritative snapshots.

CREATE OR REPLACE VIEW dw.metric_headcount_rolling_12m AS
WITH monthly AS (
    SELECT
        month_start,
        month_end,
        department_id,
        headcount_end,
        exits,
        SUM(exits) OVER (
            PARTITION BY department_id
            ORDER BY month_start
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) AS exits_12m,
        AVG(headcount_end::numeric) OVER (
            PARTITION BY department_id
            ORDER BY month_start
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) AS avg_headcount_12m,
        COUNT(*) OVER (
            PARTITION BY department_id
            ORDER BY month_start
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) AS months_in_window
    FROM dw.metric_headcount_monthly
)
SELECT
    month_start,
    month_end,
    department_id,
    exits_12m,
    avg_headcount_12m,
    exits_12m / NULLIF(avg_headcount_12m, 0) * 100
        AS rolling_12m_attrition_pct,
    months_in_window,
    'DERIVED_ESTIMATE'::text AS data_status
FROM monthly
WHERE months_in_window = 12;

-- Workforce distributions use current employee records and hide groups below five.
CREATE OR REPLACE VIEW dw.metric_work_mode_distribution AS
SELECT
    work_mode,
    COUNT(DISTINCT employee_id) AS employee_count
FROM dw.dim_employee
WHERE is_current = 'Y'
  AND (exit_date IS NULL OR exit_date > CURRENT_DATE)
GROUP BY work_mode
HAVING COUNT(DISTINCT employee_id) >= 5;

CREATE OR REPLACE VIEW dw.metric_work_location_distribution AS
SELECT
    work_location,
    COUNT(DISTINCT employee_id) AS employee_count
FROM dw.dim_employee
WHERE is_current = 'Y'
  AND (exit_date IS NULL OR exit_date > CURRENT_DATE)
GROUP BY work_location
HAVING COUNT(DISTINCT employee_id) >= 5;

-- Correct the late-arrival rate to avoid integer division.
CREATE OR REPLACE VIEW dw.metric_attendance_monthly AS
SELECT
    date_trunc('month', period_end_date)::date AS month_start,
    department_id,
    SUM(COALESCE(present_days, 0)) AS present_days,
    SUM(COALESCE(half_days_unpaid, 0)) AS half_days_unpaid,
    SUM(COALESCE(scheduled_days, 0)) AS scheduled_days,
    SUM(COALESCE(late_arrivals, 0)) AS late_arrivals,
    SUM(
        COALESCE(present_days, 0)::numeric
        + 0.5 * COALESCE(half_days_unpaid, 0)
    ) / NULLIF(SUM(COALESCE(scheduled_days, 0)), 0) * 100
        AS attendance_rate_pct,
    SUM(COALESCE(late_arrivals, 0))::numeric
        / NULLIF(SUM(COALESCE(present_days, 0)), 0) * 100
        AS late_arrival_rate_pct
FROM dw.fact_attendance_monthly
GROUP BY date_trunc('month', period_end_date)::date, department_id;

-- Update status: M05 is derived; M06 still needs voluntary-exit reason data.
CREATE OR REPLACE VIEW dw.metric_view_status AS
SELECT
    metric_id,
    metric_name,
    CASE
        WHEN metric_id = 'M05' THEN 'IMPLEMENTED_DERIVED'
        WHEN metric_id IN ('M01','M02','M03','M04') THEN 'IMPLEMENTED_DERIVED'
        WHEN metric_id IN ('M07','M08','M09','M10','M11','M12',
                           'M13','M14','M15') THEN 'IMPLEMENTED'
        ELSE 'SOURCE_REQUIRED'
    END AS implementation_status
FROM dw.metric_catalog;
