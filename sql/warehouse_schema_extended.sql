
-- PulseIQ Analytics: additive warehouse schema extension.
-- Existing tables and data must be preserved.

CREATE SCHEMA IF NOT EXISTS dw;

CREATE TABLE IF NOT EXISTS dw.dim_date (
    date_key INTEGER PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    year INTEGER,
    quarter INTEGER,
    month_number INTEGER,
    month_name VARCHAR(20),
    year_month VARCHAR(7),
    week_of_year INTEGER,
    day_of_week VARCHAR(20),
    is_weekend CHAR(1),
    is_holiday CHAR(1),
    is_working_day CHAR(1),
    financial_year VARCHAR(12),
    fiscal_quarter VARCHAR(10),
    fiscal_month_number INTEGER,
    is_month_end CHAR(1),
    month_start_date DATE,
    month_end_date DATE
);

CREATE TABLE IF NOT EXISTS dw.dim_department (
    department_id VARCHAR(20) PRIMARY KEY,
    department_name VARCHAR(150),
    cost_center VARCHAR(30),
    description TEXT,
    is_leadership CHAR(1)
);

CREATE TABLE IF NOT EXISTS dw.dim_role (
    role_id VARCHAR(20) PRIMARY KEY,
    department_id VARCHAR(20),
    role_title VARCHAR(150),
    level INTEGER,
    grade VARCHAR(30),
    band_min_annual NUMERIC(14,2),
    band_mid_annual NUMERIC(14,2),
    band_max_annual NUMERIC(14,2),
    overtime_eligible CHAR(1),
    band_reference_year INTEGER
);

CREATE TABLE IF NOT EXISTS dw.dim_leave_type (
    leave_type_code VARCHAR(20) PRIMARY KEY,
    leave_type_name VARCHAR(100),
    pay_type VARCHAR(30),
    annual_quota_days NUMERIC(8,2),
    prorated_for_joiners CHAR(1),
    carry_forward_allowed CHAR(1),
    max_carry_forward_days NUMERIC(8,2),
    policy_note TEXT
);

CREATE TABLE IF NOT EXISTS dw.dim_location (
    work_location VARCHAR(100) PRIMARY KEY,
    state VARCHAR(100),
    city_tier VARCHAR(50),
    tier_number INTEGER
);

CREATE TABLE IF NOT EXISTS dw.dim_account (
    account_code VARCHAR(30) PRIMARY KEY,
    account_name VARCHAR(150),
    account_type VARCHAR(50),
    normal_balance VARCHAR(30),
    parent_code VARCHAR(30),
    is_group CHAR(1),
    statement VARCHAR(50),
    is_active CHAR(1)
);

CREATE TABLE IF NOT EXISTS dw.dim_client (
    client_id VARCHAR(30) PRIMARY KEY,
    client_name VARCHAR(200),
    industry VARCHAR(100),
    city VARCHAR(100),
    state_or_region VARCHAR(100),
    country VARCHAR(100),
    client_type VARCHAR(50),
    gst_registration VARCHAR(50),
    payment_terms_days INTEGER,
    payment_behaviour VARCHAR(100),
    primary_service_line VARCHAR(150),
    contact_email VARCHAR(200),
    onboarded_on DATE,
    is_active CHAR(1)
);

CREATE TABLE IF NOT EXISTS dw.dim_vendor (
    vendor_id VARCHAR(30) PRIMARY KEY,
    vendor_name VARCHAR(200),
    primary_expense_account VARCHAR(30),
    payment_terms_days INTEGER,
    city VARCHAR(100),
    gst_registration VARCHAR(50),
    is_active CHAR(1)
);

CREATE TABLE IF NOT EXISTS dw.dim_team (
    team_id VARCHAR(30) PRIMARY KEY,
    team_name VARCHAR(150),
    department_id VARCHAR(20),
    team_lead_employee_id VARCHAR(20),
    active_members INTEGER,
    planning_cadence VARCHAR(100),
    board_tool VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS dw.dim_sprint (
    sprint_id VARCHAR(30) PRIMARY KEY,
    sprint_name VARCHAR(150),
    start_date DATE,
    end_date DATE,
    working_days INTEGER,
    financial_year VARCHAR(12)
);
