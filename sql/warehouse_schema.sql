CREATE SCHEMA IF NOT EXISTS dw;

CREATE TABLE IF NOT EXISTS dw.dim_employee (
    employee_key BIGINT PRIMARY KEY,
    employee_id VARCHAR(20) NOT NULL,
    full_name VARCHAR(150),
    gender VARCHAR(30),
    date_of_birth DATE,
    hire_date DATE,
    exit_date DATE,
    employment_status VARCHAR(40),
    employment_type VARCHAR(40),
    department_id VARCHAR(20),
    role_id VARCHAR(20),
    role_title VARCHAR(150),
    job_level INTEGER,
    manager_id VARCHAR(20),
    work_location VARCHAR(100),
    work_mode VARCHAR(40),
    highest_education VARCHAR(150),
    valid_from DATE,
    valid_to DATE,
    is_current CHAR(1),
    change_reason VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS dw.fact_payroll (
    payroll_item_id VARCHAR(30) PRIMARY KEY,
    run_id VARCHAR(30),
    employee_id VARCHAR(20),
    date_key INTEGER,
    employee_key BIGINT,
    period_end_date DATE,
    department_id VARCHAR(20),
    role_id VARCHAR(20),
    payable_days NUMERIC(10,2),
    lop_days NUMERIC(10,2),
    overtime_hours_paid NUMERIC(10,2),
    variable_pay_type VARCHAR(100),
    monthly_fixed_gross NUMERIC(14,2),
    basic NUMERIC(14,2),
    hra NUMERIC(14,2),
    conveyance NUMERIC(14,2),
    medical NUMERIC(14,2),
    special_allowance NUMERIC(14,2),
    earned_fixed_pay NUMERIC(14,2),
    overtime_pay NUMERIC(14,2),
    variable_pay NUMERIC(14,2),
    gross_pay NUMERIC(14,2),
    pf_employee NUMERIC(14,2),
    esi_employee NUMERIC(14,2),
    professional_tax NUMERIC(14,2),
    tds NUMERIC(14,2),
    other_deductions NUMERIC(14,2),
    total_deductions NUMERIC(14,2),
    net_pay NUMERIC(14,2),
    pf_employer NUMERIC(14,2),
    esi_employer NUMERIC(14,2),
    employer_cost NUMERIC(14,2),
    headcount_flag INTEGER
);

CREATE TABLE IF NOT EXISTS dw.fact_attendance_monthly (
    attendance_fact_id VARCHAR(30) PRIMARY KEY,
    employee_id VARCHAR(20),
    date_key INTEGER,
    employee_key BIGINT,
    department_id VARCHAR(20),
    scheduled_days INTEGER,
    present_days INTEGER,
    wfh_days INTEGER,
    half_days_unpaid INTEGER,
    paid_leave_days INTEGER,
    unpaid_absence_days INTEGER,
    late_arrivals INTEGER,
    avg_hours_worked NUMERIC(8,2),
    overtime_hours NUMERIC(10,2),
    attendance_rate NUMERIC(8,4),
    period_end_date DATE
);

CREATE TABLE IF NOT EXISTS dw.fact_leave (
    leave_request_id VARCHAR(30) PRIMARY KEY,
    employee_id VARCHAR(20),
    employee_key BIGINT,
    leave_type_code VARCHAR(20),
    start_date_key INTEGER,
    end_date_key INTEGER,
    start_date DATE,
    end_date DATE,
    days INTEGER,
    status VARCHAR(40),
    applied_on DATE,
    decided_on DATE,
    approver_id VARCHAR(20),
    reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_dw_employee_business_id
    ON dw.dim_employee(employee_id);

CREATE INDEX IF NOT EXISTS idx_dw_employee_current
    ON dw.dim_employee(is_current);

CREATE INDEX IF NOT EXISTS idx_dw_payroll_employee_key
    ON dw.fact_payroll(employee_key);

CREATE INDEX IF NOT EXISTS idx_dw_payroll_period
    ON dw.fact_payroll(period_end_date);

CREATE INDEX IF NOT EXISTS idx_dw_payroll_department
    ON dw.fact_payroll(department_id);

CREATE INDEX IF NOT EXISTS idx_dw_attendance_employee_key
    ON dw.fact_attendance_monthly(employee_key);

CREATE INDEX IF NOT EXISTS idx_dw_attendance_period
    ON dw.fact_attendance_monthly(period_end_date);

CREATE INDEX IF NOT EXISTS idx_dw_leave_employee_key
    ON dw.fact_leave(employee_key);