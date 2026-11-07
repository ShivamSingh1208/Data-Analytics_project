-- PulseIQ Phase 2: Attendance and Leave Metrics
-- Source data is preserved. This file creates/replaces metric views only.

CREATE OR REPLACE VIEW dw.metric_attendance_monthly AS
SELECT
    DATE_TRUNC('month', period_end_date)::date AS month_start,
    COUNT(*) AS attendance_records,
    COUNT(DISTINCT department_id) AS departments_reporting,
    SUM(scheduled_days) AS scheduled_days,
    SUM(present_days) AS present_days,
    SUM(half_days_unpaid) AS half_days_unpaid,
    SUM(paid_leave_days) AS paid_leave_days,
    SUM(unpaid_absence_days) AS unpaid_absence_days,
    SUM(late_arrivals) AS late_arrivals,
    ROUND(SUM(overtime_hours), 2) AS overtime_hours,
    ROUND(
        100.0 * (
            SUM(present_days)::numeric
            + 0.5 * SUM(half_days_unpaid)::numeric
        ) / NULLIF(SUM(scheduled_days), 0),
        2
    ) AS attendance_rate_pct
FROM dw.fact_attendance_monthly
GROUP BY 1;


CREATE OR REPLACE VIEW dw.metric_attendance_department_monthly AS
SELECT
    DATE_TRUNC('month', a.period_end_date)::date AS month_start,
    a.department_id,
    d.department_name,
    COUNT(*) AS attendance_records,
    SUM(a.scheduled_days) AS scheduled_days,
    SUM(a.present_days) AS present_days,
    SUM(a.half_days_unpaid) AS half_days_unpaid,
    SUM(a.paid_leave_days) AS paid_leave_days,
    SUM(a.unpaid_absence_days) AS unpaid_absence_days,
    SUM(a.late_arrivals) AS late_arrivals,
    ROUND(SUM(a.overtime_hours), 2) AS overtime_hours,
    ROUND(
        100.0 * (
            SUM(a.present_days)::numeric
            + 0.5 * SUM(a.half_days_unpaid)::numeric
        ) / NULLIF(SUM(a.scheduled_days), 0),
        2
    ) AS attendance_rate_pct
FROM dw.fact_attendance_monthly AS a
LEFT JOIN dw.dim_department AS d
    ON a.department_id = d.department_id
GROUP BY
    DATE_TRUNC('month', a.period_end_date)::date,
    a.department_id,
    d.department_name;


-- Leave requests are grouped by the month they start.
-- Statuses remain separate; rejected/cancelled/pending leave
-- is not counted as approved leave.
CREATE OR REPLACE VIEW dw.metric_leave_monthly AS
SELECT
    DATE_TRUNC('month', start_date)::date AS month_start,
    status,
    COUNT(*) AS leave_requests,
    SUM(days) AS leave_days,
    COUNT(DISTINCT employee_id) AS employees_with_requests
FROM dw.fact_leave
GROUP BY 1, 2;


CREATE OR REPLACE VIEW dw.metric_leave_type_monthly AS
SELECT
    DATE_TRUNC('month', start_date)::date AS month_start,
    leave_type_code,
    status,
    COUNT(*) AS leave_requests,
    SUM(days) AS leave_days
FROM dw.fact_leave
GROUP BY 1, 2, 3;


CREATE OR REPLACE VIEW dw.metric_leave_type_summary AS
SELECT
    leave_type_code,
    status,
    COUNT(*) AS leave_requests,
    SUM(days) AS leave_days
FROM dw.fact_leave
GROUP BY leave_type_code, status;
