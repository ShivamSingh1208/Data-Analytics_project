CREATE TABLE IF NOT EXISTS dw.phase2_kpi_targets (
    month DATE NOT NULL,
    department_id VARCHAR(20) NOT NULL,
    attendance_rate_target NUMERIC(8,2),
    overtime_share_target_pct NUMERIC(8,2),
    attrition_monthly_target_pct NUMERIC(8,2),
    task_completion_target_pct NUMERIC(8,2),
    PRIMARY KEY (month, department_id),
    FOREIGN KEY (department_id)
        REFERENCES dw.dim_department(department_id),
    CHECK (attendance_rate_target IS NULL
           OR attendance_rate_target BETWEEN 0 AND 100),
    CHECK (overtime_share_target_pct IS NULL
           OR overtime_share_target_pct BETWEEN 0 AND 100),
    CHECK (attrition_monthly_target_pct IS NULL
           OR attrition_monthly_target_pct BETWEEN 0 AND 100),
    CHECK (task_completion_target_pct IS NULL
           OR task_completion_target_pct BETWEEN 0 AND 100)
);
