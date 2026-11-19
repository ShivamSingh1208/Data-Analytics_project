# PulseIQ Data Warehouse Schema

## 1. Overview

The PulseIQ warehouse currently contains four core tables in PostgreSQL's `public` schema. They support employee, payroll, attendance, and leave analysis.

**Note:** The current implementation uses `public`. The target warehouse schema must be confirmed against the project requirements before migrating or creating tables under `dw`.

## 2. Dimension Table

### dim_employee

**Grain:** One row per employee version.

Each row represents an employee's attributes during a validity period. Multiple rows can exist for the same employee because historical changes are retained.

**Primary key:** `employee_key`

**Business identifier:** `employee_id`

**Historical tracking columns:**
- `valid_from`
- `valid_to`
- `is_current`
- `change_reason`

The dimension contains 1,606 rows for 745 distinct employees, including 745 current versions.

## 3. Fact Tables

### fact_payroll

**Grain:** One row per payroll item.

**Primary key:** `payroll_item_id`

**Important columns:** `employee_id`, `employee_key`, `run_id`, `period_end_date`, `gross_pay`, `net_pay`, and `employer_cost`.

This table supports payroll cost, deductions, and employee payment analysis.

### fact_attendance_monthly

**Grain:** One row per employee attendance record for a reporting period.

**Primary key:** `attendance_fact_id`

**Important columns:** `employee_id`, `employee_key`, `period_end_date`, `present_days`, `late_arrivals`, `overtime_hours`, and `attendance_rate`.

This table supports monthly attendance and workforce attendance analysis.

### fact_leave

**Grain:** One row per leave request.

**Primary key:** `leave_request_id`

**Important columns:** `employee_id`, `employee_key`, `start_date`, `end_date`, `days`, and `status`.

This table supports leave volume, duration, and approval-status analysis.

## 4. Relationship Design

The fact tables contain `employee_key` and/or `employee_id` to associate records with employees.

`employee_key` identifies a particular historical version in `dim_employee`, while `employee_id` identifies the business employee.

The existing tables have primary keys, but foreign-key constraints are not currently defined.

## 5. Data Quality and Reconciliation

The ETL report records:
- 7,338 cleaned payroll rows and 6 rejected payroll rows.
- 7,339 cleaned attendance rows and 4 rejected attendance rows.
- 1,606 cleaned employee dimension rows.
- 3,441 cleaned leave rows.

The payroll reconciliation checks passed:
- Payroll run `PR-2025-04`: employer cost of 53,363,392.08.
- Payroll run `PR-2026-09`: 444 employees paid.

An overlapping employee-history validity period was identified and requires investigation before the historical date convention is finalized.

## 6. Warehouse Loading and Refresh Limitations

The project currently has separate ETL and database-loading workflows:

- `src/etl_pipeline.py` cleans and validates source CSV files and writes cleaned and rejected outputs. It does not connect to PostgreSQL or refresh warehouse tables.
- `src/load_warehouse.py` is an initial-load-only loader. It validates the cleaned CSV files, uses staging tables, and refuses to insert into non-empty target tables.
- `src/load_dimensions.py` also refuses to load into non-empty destination tables.
- `src/load_to_postgres.py` is a legacy loader that truncates target tables before inserting replacement data. Do not use it against the existing recovered warehouse.

There is currently no verified repeatable incremental warehouse refresh with safe upserts, refresh auditing, and post-refresh reconciliation.

The existing warehouse must remain preserved until a separate refresh implementation has been tested against an isolated database backup. Production refresh verification remains incomplete.
