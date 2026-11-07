CREATE OR REPLACE VIEW dw.metric_phase3_department_month AS
WITH payroll AS (
         SELECT date_trunc('month'::text, fact_payroll.period_end_date::timestamp with time zone)::date AS month,
            fact_payroll.department_id,
            count(DISTINCT fact_payroll.employee_id) AS employees_paid,
            sum(fact_payroll.gross_pay) AS gross_pay,
            sum(fact_payroll.employer_cost) AS employer_cost,
            sum(fact_payroll.overtime_pay) AS overtime_pay,
            sum(fact_payroll.overtime_hours_paid) AS overtime_hours
           FROM dw.fact_payroll
          GROUP BY (date_trunc('month'::text, fact_payroll.period_end_date::timestamp with time zone)::date), fact_payroll.department_id
        ), attendance AS (
         SELECT date_trunc('month'::text, fact_attendance_monthly.period_end_date::timestamp with time zone)::date AS month,
            fact_attendance_monthly.department_id,
            sum(fact_attendance_monthly.scheduled_days) AS scheduled_days,
            sum(fact_attendance_monthly.present_days) AS present_days,
            sum(fact_attendance_monthly.late_arrivals) AS late_arrivals,
                CASE
                    WHEN sum(fact_attendance_monthly.scheduled_days) > 0 THEN 100.0 * (sum(fact_attendance_monthly.present_days)::numeric + 0.5 * sum(fact_attendance_monthly.half_days_unpaid)::numeric) / sum(fact_attendance_monthly.scheduled_days)::numeric
                    ELSE NULL::numeric
                END AS attendance_rate_pct
           FROM dw.fact_attendance_monthly
          GROUP BY (date_trunc('month'::text, fact_attendance_monthly.period_end_date::timestamp with time zone)::date), fact_attendance_monthly.department_id
        ), headcount AS (
         SELECT fact_headcount_monthly.month_start_date AS month,
            fact_headcount_monthly.department_id,
            sum(fact_headcount_monthly.headcount_end) AS headcount_end,
            sum(fact_headcount_monthly.hires) AS hires,
            sum(fact_headcount_monthly.exits) AS exits,
            avg(fact_headcount_monthly.attrition_rate_monthly_pct) AS attrition_rate_pct
           FROM dw.fact_headcount_monthly
          GROUP BY fact_headcount_monthly.month_start_date, fact_headcount_monthly.department_id
        ), leave_data AS (
         SELECT date_trunc('month'::text, l_1.start_date::timestamp with time zone)::date AS month,
            e.department_id,
            count(*) AS approved_leave_requests,
            sum(l_1.days) AS approved_leave_days
           FROM dw.fact_leave l_1
             JOIN dw.dim_employee e ON e.employee_key = l_1.employee_key
          WHERE l_1.status::text = 'Approved'::text
          GROUP BY (date_trunc('month'::text, l_1.start_date::timestamp with time zone)::date), e.department_id
        ), tasks AS (
         SELECT date_trunc('month'::text, t_1.created_date::timestamp with time zone)::date AS month,
            tm.department_id,
            count(*) FILTER (WHERE t_1.status::text <> 'Cancelled'::text) AS non_cancelled_tasks,
            count(*) FILTER (WHERE t_1.status::text = 'Done'::text) AS completed_tasks,
            sum(t_1.story_points) FILTER (WHERE t_1.status::text = 'Done'::text) AS story_points_done,
                CASE
                    WHEN count(*) FILTER (WHERE t_1.status::text <> 'Cancelled'::text) > 0 THEN 100.0 * count(*) FILTER (WHERE t_1.status::text = 'Done'::text)::numeric / count(*) FILTER (WHERE t_1.status::text <> 'Cancelled'::text)::numeric
                    ELSE NULL::numeric
                END AS task_completion_pct
           FROM dw.fact_task t_1
             JOIN dw.dim_team tm ON tm.team_id::text = t_1.team_id::text
          GROUP BY (date_trunc('month'::text, t_1.created_date::timestamp with time zone)::date), tm.department_id
        )
 SELECT r.month,
    r.department_id::character varying(20) AS department_id,
    p.employees_paid,
    p.gross_pay,
    p.employer_cost,
    p.overtime_pay,
    p.overtime_hours,
        CASE
            WHEN p.gross_pay > 0::numeric THEN 100.0 * p.overtime_pay / p.gross_pay
            ELSE NULL::numeric
        END AS overtime_share_pct,
    a.attendance_rate_pct,
    a.late_arrivals,
    h.headcount_end,
    h.hires,
    h.exits,
    h.attrition_rate_pct,
    COALESCE(l.approved_leave_requests, 0::bigint) AS approved_leave_requests,
    COALESCE(l.approved_leave_days, 0::bigint) AS approved_leave_days,
        CASE
            WHEN h.headcount_end > 0 THEN COALESCE(l.approved_leave_days, 0::bigint)::numeric / h.headcount_end::numeric
            ELSE NULL::numeric
        END AS approved_leave_days_per_head,
    t.non_cancelled_tasks,
    t.completed_tasks,
    t.story_points_done,
    t.task_completion_pct
   FROM dw.reference_summary_dept_month r
     LEFT JOIN payroll p ON p.month = r.month AND p.department_id::text = r.department_id
     LEFT JOIN attendance a ON a.month = r.month AND a.department_id::text = r.department_id
     LEFT JOIN headcount h ON h.month = r.month AND h.department_id::text = r.department_id
     LEFT JOIN leave_data l ON l.month = r.month AND l.department_id::text = r.department_id
     LEFT JOIN tasks t ON t.month = r.month AND t.department_id::text = r.department_id;
