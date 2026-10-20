-- Generated from the supplied metric dictionary. Do not edit by hand.
CREATE SCHEMA IF NOT EXISTS dw;

CREATE TABLE IF NOT EXISTS dw.metric_catalog (
  metric_id text PRIMARY KEY,
  metric_name text NOT NULL,
  business_definition text,
  formula text,
  source_table text,
  grain text,
  time_period text,
  owner_team text,
  unit text,
  good_direction text,
  caveat text,
  minimum_group_size integer
);

TRUNCATE TABLE dw.metric_catalog;
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M01', 'Headcount', 'Active employees on the last day of the month (permanent and contract).', 'COUNT(DISTINCT employee_id) with hire_date <= month_end AND (exit_date IS NULL OR exit_date > month_end)', 'fact_headcount_monthly / dim_employee', 'Department x month', 'Month end', 'HR Analytics', 'count', 'Context dependent', 'Excludes CEO if you compare departments only', 5);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M02', 'Hires', 'Employees whose hire_date falls in the month.', 'COUNT(employee_id) where hire_date in month', 'fact_headcount_monthly', 'Department x month', 'Month', 'HR Analytics', 'count', 'Context dependent', 'Transfers are not hires', 5);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M03', 'Exits', 'Employees whose exit_date falls in the month (resigned, terminated or contract ended).', 'COUNT(employee_id) where exit_date in month', 'fact_headcount_monthly', 'Department x month', 'Month', 'HR Analytics', 'count', 'Lower is better', '', 5);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M04', 'Attrition rate (monthly)', 'Share of people who left in the month.', 'Exits / headcount_start x 100', 'fact_headcount_monthly', 'Department x month', 'Month', 'HR Analytics', 'percent', 'Lower is better', 'Very noisy for small departments', 10);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M05', 'Attrition rate (rolling 12 months)', 'Leavers in the last 12 months divided by average headcount over the same months.', 'SUM(exits, 12m) / AVG(headcount_end, 12m) x 100', 'fact_headcount_monthly', 'Department x month', '12 months', 'HR Analytics', 'percent', 'Lower is better', 'Use for headline reporting; monthly is too noisy', 10);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M06', 'Voluntary attrition rate', 'Same as M05 but only resignations (voluntary_exits).', 'SUM(voluntary_exits, 12m) / AVG(headcount_end, 12m) x 100', 'fact_headcount_monthly', 'Department x month', '12 months', 'HR Analytics', 'percent', 'Lower is better', '', 10);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M07', 'Gross pay', 'Total earnings before deductions for the month.', 'SUM(gross_pay)', 'fact_payroll', 'Employee x month', 'Month', 'Payroll', 'INR', 'Context dependent', 'Includes overtime and variable pay', 5);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M08', 'Net pay', 'Take-home pay after employee deductions.', 'SUM(net_pay)', 'fact_payroll', 'Employee x month', 'Month', 'Payroll', 'INR', 'Context dependent', '', 5);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M09', 'Payroll cost (employer cost)', 'Full cost of employees to the company: gross pay plus employer PF and ESI.', 'SUM(employer_cost)', 'fact_payroll', 'Employee x month', 'Month', 'Finance', 'INR', 'Lower is better when output is equal', 'Must reconcile with ledger accounts 5001-5005', 5);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M10', 'Cost per head', 'Average employer cost per paid employee.', 'SUM(employer_cost) / COUNT(DISTINCT employee_id)', 'fact_payroll', 'Department x month', 'Month', 'Finance', 'INR', 'Context dependent', 'Part-month joiners lower the average', 5);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M11', 'Overtime share', 'How much of payroll cost is overtime pay.', 'SUM(overtime_pay) / SUM(employer_cost) x 100', 'fact_payroll', 'Department x month', 'Month', 'Payroll', 'percent', 'Lower is better', 'Only overtime-eligible roles earn overtime', 5);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M12', 'Variable pay share', 'Bonus, incentive and award pay as a share of gross pay.', 'SUM(variable_pay) / SUM(gross_pay) x 100', 'fact_payroll', 'Department x month', 'Month', 'Payroll', 'percent', 'Context dependent', 'April bonus and quarter-end incentives create spikes', 5);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M13', 'Attendance rate', 'Days present (half day counts 0.5) divided by scheduled working days.', '(SUM(present_days) + 0.5 x SUM(half_days_unpaid)) / SUM(scheduled_days)', 'fact_attendance_monthly', 'Department x month', 'Month', 'HR Analytics', 'ratio', 'Higher is better', 'Paid leave counts as not present', 5);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M14', 'Late arrival rate', 'Late check-ins per present day.', 'SUM(late_arrivals) / SUM(present_days)', 'fact_attendance_monthly', 'Department x month', 'Month', 'HR Analytics', 'ratio', 'Lower is better', 'Work-from-home days use web check-in time', 5);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M15', 'Leave without pay days', 'Unpaid absence and unpaid leave days.', 'SUM(lop_days) in fact_payroll', 'fact_payroll', 'Employee x month', 'Month', 'Payroll', 'days', 'Lower is better', 'Half-day unpaid counts 0.5', 5);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M16', 'Revenue', 'Income booked in the ledger (accounts 4001-4004).', '-SUM(signed_amount) for accounts 4001-4004', 'fact_ledger', 'Account x month', 'Month', 'Finance', 'INR', 'Higher is better', 'Excludes GST (booked to 2200)', NULL);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M17', 'Net profit', 'Revenue minus all expenses (4xxx less 5xxx).', '-SUM(signed_amount) for accounts 4xxx and 5xxx', 'fact_ledger', 'Month', 'Month', 'Finance', 'INR', 'Higher is better', 'Interest income (4900) is included', NULL);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M18', 'Operating margin', 'Net profit as a share of revenue.', 'Net profit / Revenue x 100', 'fact_ledger', 'Month', 'Month', 'Finance', 'percent', 'Higher is better', '', NULL);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M19', 'Payroll as % of revenue', 'Share of revenue consumed by payroll cost.', 'Payroll cost / Revenue x 100', 'fact_payroll + fact_ledger', 'Month', 'Month', 'Finance', 'percent', 'Lower is better', 'Use ledger payroll accounts to avoid mismatch', NULL);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M20', 'Days sales outstanding (DSO)', 'Average days to collect: receivables divided by credit sales x days.', 'Closing receivables / revenue incl GST (last 90 days) x 90', 'fact_invoice, fact_ledger', 'Month', '90 days', 'Finance', 'days', 'Lower is better', 'Carried-in invoices included', NULL);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M21', 'Overdue receivables', 'Unpaid invoice balance past due date at the report date.', 'SUM(balance_due) where due_date < report date and status not DRAFT/CANCELLED', 'fact_invoice', 'Client x date', 'Point in time', 'Finance', 'INR', 'Lower is better', '', NULL);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M22', 'Task completion rate', 'Tasks done divided by tasks planned in the sprint (cancelled tasks excluded).', 'COUNT(status = Done) / COUNT(status != Cancelled)', 'fact_task', 'Team x sprint', 'Sprint', 'Engineering Ops', 'percent', 'Higher is better', 'Sample feed until the live board is ready', NULL);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M23', 'On-time delivery rate', 'Done tasks completed on or before the sprint end date.', 'COUNT(completed_on_time = Y) / COUNT(status = Done)', 'fact_task', 'Team x sprint', 'Sprint', 'Engineering Ops', 'percent', 'Higher is better', '', NULL);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M24', 'Velocity', 'Story points completed in the sprint.', 'SUM(story_points) where status = Done', 'fact_task', 'Team x sprint', 'Sprint', 'Engineering Ops', 'points', 'Context dependent', 'Do not compare across teams', NULL);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M25', 'Average cycle time', 'Days from start to completion for done tasks.', 'AVG(completed_date - started_date)', 'fact_task', 'Team x sprint', 'Sprint', 'Engineering Ops', 'days', 'Lower is better', 'Negative values are data errors', NULL);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M26', 'Anomaly flag rate', 'Share of scored records flagged by the AI anomaly service.', 'COUNT(flagged = Y) / COUNT(*)', 'fact_anomaly', 'Source x month', 'Month', 'AI/ML', 'percent', 'Context dependent', 'Flags are leads, not proof', NULL);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M27', 'High-risk share', 'Share of employees in the High attrition-risk band.', 'COUNT(risk_band = High) / COUNT(*)', 'fact_attrition_risk', 'Department', 'Point in time', 'AI/ML', 'percent', 'Lower is better', 'Show by group only; never rank named people', 10);
INSERT INTO dw.metric_catalog (metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) VALUES ('M28', 'Forecast error (MAPE)', 'Average absolute percentage error of headcount forecasts versus actuals.', 'AVG(ABS(actual - forecast) / actual) x 100', 'fact_forecast vs fact_headcount', 'Department x month', 'Rolling', 'AI/ML', 'percent', 'Lower is better', 'Needs actuals for the forecast months', NULL);

-- Monthly employee metrics from current employee dimension.
-- This is a derived snapshot estimate, not a substitute for a source headcount fact.
CREATE OR REPLACE VIEW dw.metric_headcount_monthly AS
WITH months AS (
  SELECT generate_series(
    date_trunc('month', MIN(hire_date))::date,
    date_trunc('month', CURRENT_DATE)::date,
    interval '1 month'
  )::date AS month_start
  FROM dw.dim_employee
),
counts AS (
  SELECT m.month_start,
         (m.month_start + interval '1 month - 1 day')::date AS month_end,
         d.department_id,
         COUNT(DISTINCT d.employee_id) FILTER (
           WHERE d.hire_date <= (m.month_start + interval '1 month - 1 day')::date
             AND (d.exit_date IS NULL OR d.exit_date > (m.month_start + interval '1 month - 1 day')::date)
         ) AS headcount_end,
         COUNT(DISTINCT d.employee_id) FILTER (
           WHERE d.hire_date >= m.month_start
             AND d.hire_date < m.month_start + interval '1 month'
         ) AS hires,
         COUNT(DISTINCT d.employee_id) FILTER (
           WHERE d.exit_date >= m.month_start
             AND d.exit_date < m.month_start + interval '1 month'
         ) AS exits
  FROM months m
  CROSS JOIN dw.dim_employee d
  WHERE d.hire_date IS NOT NULL
  GROUP BY m.month_start, d.department_id
)
SELECT month_start, month_end, department_id, headcount_end, hires, exits
FROM counts;


-- M07-M12: payroll metrics at department x month grain.
CREATE OR REPLACE VIEW dw.metric_payroll_monthly AS
SELECT
  date_trunc('month', period_end_date)::date AS month_start,
  department_id,
  SUM(COALESCE(gross_pay,0)) AS gross_pay,
  SUM(COALESCE(net_pay,0)) AS net_pay,
  SUM(COALESCE(employer_cost,0)) AS employer_cost,
  COUNT(DISTINCT employee_id) AS paid_employees,
  SUM(COALESCE(overtime_pay,0)) AS overtime_pay,
  SUM(COALESCE(variable_pay,0)) AS variable_pay,
  SUM(COALESCE(lop_days,0)) AS lop_days,
  SUM(COALESCE(overtime_pay,0)) / NULLIF(SUM(COALESCE(employer_cost,0)),0) * 100 AS overtime_share_pct,
  SUM(COALESCE(variable_pay,0)) / NULLIF(SUM(COALESCE(gross_pay,0)),0) * 100 AS variable_pay_share_pct,
  SUM(COALESCE(employer_cost,0)) / NULLIF(COUNT(DISTINCT employee_id),0) AS cost_per_head
FROM dw.fact_payroll
GROUP BY date_trunc('month', period_end_date)::date, department_id;


-- M13-M14: attendance metrics at department x month grain.
CREATE OR REPLACE VIEW dw.metric_attendance_monthly AS
SELECT
  date_trunc('month', period_end_date)::date AS month_start,
  department_id,
  SUM(COALESCE(present_days,0)) AS present_days,
  SUM(COALESCE(half_days_unpaid,0)) AS half_days_unpaid,
  SUM(COALESCE(scheduled_days,0)) AS scheduled_days,
  SUM(COALESCE(late_arrivals,0)) AS late_arrivals,
  SUM(COALESCE(present_days,0) + 0.5 * COALESCE(half_days_unpaid,0))
    / NULLIF(SUM(COALESCE(scheduled_days,0)),0) * 100 AS attendance_rate_pct,
  SUM(COALESCE(late_arrivals,0))
    / NULLIF(SUM(COALESCE(present_days,0)),0) * 100 AS late_arrival_rate_pct
FROM dw.fact_attendance_monthly
GROUP BY date_trunc('month', period_end_date)::date, department_id;


-- M15: leave without pay days from payroll.
CREATE OR REPLACE VIEW dw.metric_lop_monthly AS
SELECT date_trunc('month', period_end_date)::date AS month_start,
       department_id, SUM(COALESCE(lop_days,0)) AS lop_days
FROM dw.fact_payroll
GROUP BY date_trunc('month', period_end_date)::date, department_id;

-- M01-M03: department/month headcount snapshots.
CREATE OR REPLACE VIEW dw.metric_headcount_kpis AS
SELECT month_start, month_end, department_id, headcount_end, hires, exits,
       LAG(headcount_end) OVER (PARTITION BY department_id ORDER BY month_start) AS headcount_start,
       exits::numeric / NULLIF(
         LAG(headcount_end) OVER (PARTITION BY department_id ORDER BY month_start), 0
       ) * 100 AS monthly_attrition_pct
FROM dw.metric_headcount_monthly;

-- Privacy-filtered department metrics. Groups below the catalog minimum of 5 are hidden.
CREATE OR REPLACE VIEW dw.metric_department_dashboard AS
SELECT p.month_start, p.department_id, p.paid_employees,
       p.gross_pay, p.net_pay, p.employer_cost, p.cost_per_head,
       p.overtime_share_pct, p.variable_pay_share_pct, p.lop_days,
       a.attendance_rate_pct, a.late_arrival_rate_pct,
       h.headcount_end, h.hires, h.exits
FROM dw.metric_payroll_monthly p
LEFT JOIN dw.metric_attendance_monthly a
  USING (month_start, department_id)
LEFT JOIN dw.metric_headcount_monthly h
  USING (month_start, department_id)
WHERE p.paid_employees >= 5;


-- Registry of views actually implemented from available warehouse data.
CREATE OR REPLACE VIEW dw.metric_view_status AS
SELECT metric_id, metric_name,
       CASE
         WHEN metric_id IN ('M01','M02','M03','M04') THEN 'IMPLEMENTED_DERIVED'
         WHEN metric_id IN ('M07','M08','M09','M10','M11','M12') THEN 'IMPLEMENTED'
         WHEN metric_id IN ('M13','M14','M15') THEN 'IMPLEMENTED'
         ELSE 'SOURCE_REQUIRED'
       END AS implementation_status
FROM dw.metric_catalog;

