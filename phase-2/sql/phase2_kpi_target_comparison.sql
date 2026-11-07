CREATE OR REPLACE VIEW dw.metric_kpi_target_comparison AS
WITH attendance AS (
    SELECT
        month_start AS month,
        department_id,
        attendance_rate_pct,
        scheduled_days,
        overtime_hours,
        CASE
            WHEN scheduled_days > 0
            THEN 100.0 * overtime_hours / (scheduled_days * 8.0)
            ELSE NULL
        END AS overtime_share_pct
    FROM dw.metric_attendance_department_monthly
),
attrition AS (
    SELECT
        month_start_date AS month,
        department_id,
        attrition_rate_pct
    FROM dw.metric_attrition_department_monthly
),
productivity AS (
    SELECT
        end_date AS month_end,
        department_id,
        SUM(non_cancelled_tasks) AS non_cancelled_tasks,
        SUM(completed_tasks) AS completed_tasks,
        CASE
            WHEN SUM(non_cancelled_tasks) > 0
            THEN 100.0 * SUM(completed_tasks)
                 / SUM(non_cancelled_tasks)
            ELSE NULL
        END AS task_completion_pct
    FROM dw.metric_productivity_sprint
    WHERE end_date IS NOT NULL
    GROUP BY end_date, department_id
),
productivity_monthly AS (
    SELECT
        DATE_TRUNC('month', month_end)::date AS month,
        department_id,
        SUM(non_cancelled_tasks) AS non_cancelled_tasks,
        SUM(completed_tasks) AS completed_tasks,
        CASE
            WHEN SUM(non_cancelled_tasks) > 0
            THEN 100.0 * SUM(completed_tasks)
                 / SUM(non_cancelled_tasks)
            ELSE NULL
        END AS task_completion_pct
    FROM productivity
    GROUP BY DATE_TRUNC('month', month_end)::date, department_id
)
SELECT
    t.month,
    t.department_id,
    d.department_name,

    a.attendance_rate_pct,
    100.0 * t.attendance_rate_target AS attendance_target_pct,
    a.attendance_rate_pct
        - 100.0 * t.attendance_rate_target AS attendance_variance_pct_points,
    CASE
        WHEN a.attendance_rate_pct IS NULL THEN 'No data'
        WHEN a.attendance_rate_pct >= 100.0 * t.attendance_rate_target
            THEN 'Met target'
        ELSE 'Below target'
    END AS attendance_status,

    a.overtime_share_pct,
    t.overtime_share_target_pct AS overtime_target_pct,
    a.overtime_share_pct - t.overtime_share_target_pct
        AS overtime_variance_pct_points,
    CASE
        WHEN a.overtime_share_pct IS NULL THEN 'No data'
        WHEN a.overtime_share_pct <= t.overtime_share_target_pct
            THEN 'Met target'
        ELSE 'Above target'
    END AS overtime_status,

    r.attrition_rate_pct,
    t.attrition_monthly_target_pct AS attrition_target_pct,
    r.attrition_rate_pct - t.attrition_monthly_target_pct
        AS attrition_variance_pct_points,
    CASE
        WHEN r.attrition_rate_pct IS NULL THEN 'No data'
        WHEN r.attrition_rate_pct <= t.attrition_monthly_target_pct
            THEN 'Met target'
        ELSE 'Above target'
    END AS attrition_status,

    p.task_completion_pct,
    t.task_completion_target_pct AS task_completion_target_pct,
    p.task_completion_pct - t.task_completion_target_pct
        AS task_completion_variance_pct_points,
    CASE
        WHEN t.task_completion_target_pct IS NULL THEN 'Target unavailable'
        WHEN p.task_completion_pct IS NULL THEN 'No data'
        WHEN p.task_completion_pct >= t.task_completion_target_pct
            THEN 'Met target'
        ELSE 'Below target'
    END AS task_completion_status,

    p.non_cancelled_tasks,
    p.completed_tasks

FROM dw.phase2_kpi_targets t
JOIN dw.dim_department d
    ON d.department_id = t.department_id
LEFT JOIN attendance a
    ON a.month = t.month
   AND a.department_id = t.department_id
LEFT JOIN attrition r
    ON r.month = t.month
   AND r.department_id = t.department_id
LEFT JOIN productivity_monthly p
    ON p.month = t.month
   AND p.department_id = t.department_id;
