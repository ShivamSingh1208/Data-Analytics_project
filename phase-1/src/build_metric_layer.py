from pathlib import Path
import glob
import pandas as pd

root = Path(".")
matches = glob.glob("./ data/*metric_dictionary.csv")
if not matches:
    raise FileNotFoundError("Could not find the original metric_dictionary.csv")

df = pd.read_csv(matches[0]).fillna("")
required = {
    "metric_id", "metric_name", "business_definition", "formula",
    "source_table", "grain", "time_period", "owner_team", "unit",
    "good_direction", "caveat", "minimum_group_size"
}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"Missing dictionary columns: {sorted(missing)}")
if len(df) != 28:
    raise ValueError(f"Expected 28 metrics; found {len(df)}")

def sqlstr(value):
    return "'" + str(value).replace("'", "''") + "'"

out = [
    "-- Generated from the supplied metric dictionary. Do not edit by hand.",
    "CREATE SCHEMA IF NOT EXISTS dw;",
    """
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
""",
"TRUNCATE TABLE dw.metric_catalog;"
]
for _, r in df.iterrows():
    try:
        minimum = int(float(r["minimum_group_size"])) if str(r["minimum_group_size"]).strip() else "NULL"
    except ValueError:
        minimum = "NULL"
    cols = [
        r["metric_id"], r["metric_name"], r["business_definition"], r["formula"],
        r["source_table"], r["grain"], r["time_period"], r["owner_team"],
        r["unit"], r["good_direction"], r["caveat"]
    ]
    vals = ", ".join(sqlstr(x) for x in cols) + ", " + str(minimum)
    out.append(
        "INSERT INTO dw.metric_catalog "
        "(metric_id,metric_name,business_definition,formula,source_table,grain,time_period,owner_team,unit,good_direction,caveat,minimum_group_size) "
        f"VALUES ({vals});"
    )

out.append("""
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
""")

out.append("""
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
""")

out.append("""
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
""")

out.append("""
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
""")

out.append("""
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
""")

path = root / "sql" / "metric_views.sql"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"Generated {path} from {len(df)} official metrics.")
print("Review SQL before executing against your warehouse.")
