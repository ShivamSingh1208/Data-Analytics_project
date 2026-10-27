CREATE TABLE IF NOT EXISTS dw.phase2_payroll_budget (
    department_id VARCHAR(20) NOT NULL,
    month DATE NOT NULL,
    budget_payroll_cost NUMERIC(18,2) NOT NULL
        CHECK (budget_payroll_cost >= 0),
    PRIMARY KEY (department_id, month),
    FOREIGN KEY (department_id)
        REFERENCES dw.dim_department(department_id)
);
