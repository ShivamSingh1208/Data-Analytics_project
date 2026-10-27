CREATE OR REPLACE VIEW dw.metric_productivity_team AS
SELECT
    t.team_id,
    t.team_name,
    t.department_id,
    COUNT(*) FILTER (
        WHERE f.status <> 'Cancelled'
    ) AS non_cancelled_tasks,
    COUNT(*) FILTER (
        WHERE f.status = 'Done'
    ) AS completed_tasks,
    COUNT(*) FILTER (
        WHERE f.status = 'Done'
          AND f.completed_on_time = 'Y'
    ) AS completed_on_time,
    COUNT(*) FILTER (
        WHERE f.status = 'Done'
          AND f.completed_on_time IN ('Y', 'N')
    ) AS completed_with_due_result,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE f.status = 'Done'
              AND f.completed_on_time = 'Y'
        ) / NULLIF(
            COUNT(*) FILTER (
                WHERE f.status = 'Done'
                  AND f.completed_on_time IN ('Y', 'N')
            ), 0
        ), 2
    ) AS on_time_rate_pct,
    ROUND(
        AVG(f.cycle_time_days) FILTER (
            WHERE f.status = 'Done'
              AND f.cycle_time_days >= 0
        ), 2
    ) AS avg_cycle_time_days,
    COUNT(*) FILTER (
        WHERE f.status = 'Done'
          AND f.cycle_time_days >= 0
    ) AS completed_with_valid_cycle_time,
    COALESCE(SUM(f.story_points) FILTER (
        WHERE f.status = 'Done'
    ), 0) AS completed_story_points,
    COUNT(*) FILTER (
        WHERE f.status = 'Blocked'
    ) AS blocked_tasks,
    COUNT(*) FILTER (
        WHERE f.reopened_count > 0
          AND f.status <> 'Cancelled'
    ) AS reopened_tasks,
    COALESCE(SUM(f.reopened_count) FILTER (
        WHERE f.status <> 'Cancelled'
    ), 0) AS total_reopen_events
FROM dw.fact_task f
JOIN dw.dim_team t ON t.team_id = f.team_id
GROUP BY t.team_id, t.team_name, t.department_id;


CREATE OR REPLACE VIEW dw.metric_productivity_sprint AS
SELECT
    s.sprint_id,
    s.sprint_name,
    s.start_date,
    s.end_date,
    s.financial_year,
    t.team_id,
    t.team_name,
    t.department_id,
    COUNT(*) FILTER (
        WHERE f.status <> 'Cancelled'
    ) AS non_cancelled_tasks,
    COUNT(*) FILTER (
        WHERE f.status = 'Done'
    ) AS completed_tasks,
    COUNT(*) FILTER (
        WHERE f.status = 'Done'
          AND f.completed_on_time = 'Y'
    ) AS completed_on_time,
    COUNT(*) FILTER (
        WHERE f.status = 'Done'
          AND f.completed_on_time IN ('Y', 'N')
    ) AS completed_with_due_result,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE f.status = 'Done'
              AND f.completed_on_time = 'Y'
        ) / NULLIF(
            COUNT(*) FILTER (
                WHERE f.status = 'Done'
                  AND f.completed_on_time IN ('Y', 'N')
            ), 0
        ), 2
    ) AS on_time_rate_pct,
    ROUND(
        AVG(f.cycle_time_days) FILTER (
            WHERE f.status = 'Done'
              AND f.cycle_time_days >= 0
        ), 2
    ) AS avg_cycle_time_days,
    COALESCE(SUM(f.story_points) FILTER (
        WHERE f.status = 'Done'
    ), 0) AS completed_story_points,
    COUNT(*) FILTER (
        WHERE f.status = 'Blocked'
    ) AS blocked_tasks,
    COUNT(*) FILTER (
        WHERE f.reopened_count > 0
          AND f.status <> 'Cancelled'
    ) AS reopened_tasks,
    COALESCE(SUM(f.reopened_count) FILTER (
        WHERE f.status <> 'Cancelled'
    ), 0) AS total_reopen_events
FROM dw.fact_task f
JOIN dw.dim_team t ON t.team_id = f.team_id
JOIN dw.dim_sprint s ON s.sprint_id = f.sprint_id
GROUP BY
    s.sprint_id, s.sprint_name, s.start_date, s.end_date,
    s.financial_year, t.team_id, t.team_name, t.department_id;


CREATE OR REPLACE VIEW dw.metric_productivity_kpis AS
SELECT
    COUNT(*) FILTER (
        WHERE status <> 'Cancelled'
    ) AS non_cancelled_tasks,
    COUNT(*) FILTER (
        WHERE status = 'Done'
    ) AS completed_tasks,
    COUNT(*) FILTER (
        WHERE status = 'Done'
          AND completed_on_time IN ('Y', 'N')
    ) AS completed_with_due_result,
    COUNT(*) FILTER (
        WHERE status = 'Done'
          AND completed_on_time = 'Y'
    ) AS completed_on_time,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE status = 'Done'
              AND completed_on_time = 'Y'
        ) / NULLIF(
            COUNT(*) FILTER (
                WHERE status = 'Done'
                  AND completed_on_time IN ('Y', 'N')
            ), 0
        ), 2
    ) AS on_time_rate_pct,
    ROUND(
        AVG(cycle_time_days) FILTER (
            WHERE status = 'Done'
              AND cycle_time_days >= 0
        ), 2
    ) AS avg_cycle_time_days,
    COALESCE(SUM(story_points) FILTER (
        WHERE status = 'Done'
    ), 0) AS completed_story_points,
    COUNT(*) FILTER (
        WHERE status = 'Blocked'
    ) AS blocked_tasks,
    COUNT(*) FILTER (
        WHERE reopened_count > 0
          AND status <> 'Cancelled'
    ) AS reopened_tasks,
    COALESCE(SUM(reopened_count) FILTER (
        WHERE status <> 'Cancelled'
    ), 0) AS total_reopen_events,
    COUNT(*) FILTER (
        WHERE status = 'Done'
          AND cycle_time_days IS NULL
    ) AS completed_without_valid_cycle_time
FROM dw.fact_task;
