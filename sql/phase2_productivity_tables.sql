CREATE TABLE IF NOT EXISTS dw.fact_task (
    task_id VARCHAR(30) PRIMARY KEY,
    team_id VARCHAR(20) NOT NULL,
    sprint_id VARCHAR(30) NOT NULL,
    assignee_employee_id VARCHAR(20),
    task_type VARCHAR(50),
    priority VARCHAR(20),
    story_points NUMERIC(10,2),
    created_date DATE NOT NULL,
    started_date DATE,
    due_date DATE,
    completed_date DATE,
    status VARCHAR(30) NOT NULL,
    reopened_count INTEGER NOT NULL DEFAULT 0,
    cycle_time_days NUMERIC(10,2),
    is_overdue_at_cutoff CHAR(1),
    completed_on_time CHAR(1),

    CONSTRAINT chk_task_reopened_nonnegative
        CHECK (reopened_count >= 0),

    CONSTRAINT chk_task_story_points_nonnegative
        CHECK (story_points IS NULL OR story_points >= 0),

    CONSTRAINT chk_task_cycle_time_nonnegative
        CHECK (cycle_time_days IS NULL OR cycle_time_days >= 0),

    CONSTRAINT chk_task_status
        CHECK (status IN (
            'Done',
            'In Progress',
            'Blocked',
            'To Do',
            'Cancelled'
        )),

    CONSTRAINT chk_task_overdue_flag
        CHECK (
            is_overdue_at_cutoff IS NULL
            OR is_overdue_at_cutoff IN ('Y', 'N')
        ),

    CONSTRAINT chk_task_on_time_flag
        CHECK (
            completed_on_time IS NULL
            OR completed_on_time IN ('Y', 'N')
        )
);

CREATE INDEX IF NOT EXISTS idx_fact_task_team_sprint
    ON dw.fact_task (team_id, sprint_id);

CREATE INDEX IF NOT EXISTS idx_fact_task_status
    ON dw.fact_task (status);
