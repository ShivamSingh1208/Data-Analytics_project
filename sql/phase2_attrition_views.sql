CREATE OR REPLACE VIEW dw.metric_attrition_monthly AS
SELECT
    month_start_date,
    SUM(headcount_start) AS headcount_start,
    SUM(hires) AS hires,
    SUM(exits) AS exits,
    SUM(voluntary_exits) AS voluntary_exits,
    SUM(exits - voluntary_exits) AS other_exits,
    SUM(transfers_in) AS transfers_in,
    SUM(transfers_out) AS transfers_out,
    SUM(headcount_end) AS headcount_end,
    ROUND(
        100.0 * SUM(exits)::numeric / NULLIF(SUM(headcount_start), 0),
        2
    ) AS attrition_rate_pct,
    ROUND(
        100.0 * SUM(voluntary_exits)::numeric / NULLIF(SUM(exits), 0),
        2
    ) AS voluntary_exit_share_pct
FROM dw.fact_headcount_monthly
GROUP BY month_start_date;


CREATE OR REPLACE VIEW dw.metric_attrition_department_monthly AS
SELECT
    f.month_start_date,
    f.department_id,
    d.department_name,
    SUM(f.headcount_start) AS headcount_start,
    SUM(f.hires) AS hires,
    SUM(f.exits) AS exits,
    SUM(f.voluntary_exits) AS voluntary_exits,
    SUM(f.exits - f.voluntary_exits) AS other_exits,
    SUM(f.headcount_end) AS headcount_end,
    ROUND(
        100.0 * SUM(f.exits)::numeric / NULLIF(SUM(f.headcount_start), 0),
        2
    ) AS attrition_rate_pct
FROM dw.fact_headcount_monthly f
LEFT JOIN dw.dim_department d
    ON d.department_id = f.department_id
GROUP BY
    f.month_start_date,
    f.department_id,
    d.department_name;


CREATE OR REPLACE VIEW dw.metric_attrition_risk_snapshot AS
SELECT
    as_of_date,
    department_id,
    COUNT(*) AS employees_scored,
    COUNT(*) FILTER (WHERE risk_band = 'Low') AS low_risk_count,
    COUNT(*) FILTER (WHERE risk_band = 'Medium') AS medium_risk_count,
    COUNT(*) FILTER (WHERE risk_band = 'High') AS high_risk_count,
    ROUND(AVG(risk_score_12m), 4) AS average_risk_score,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE risk_band = 'High')::numeric
        / NULLIF(COUNT(*), 0),
        2
    ) AS high_risk_share_pct
FROM dw.fact_attrition_risk
GROUP BY as_of_date, department_id
HAVING COUNT(*) >= 10;
