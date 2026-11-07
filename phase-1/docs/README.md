# PulseIQ HR Analytics Pipeline

## Objective
Build a repeatable ETL pipeline to clean HR employee, payroll,
attendance, and leave datasets for analytics.

## Input datasets
- dim_employee.csv
- fact_payroll.csv
- fact_attendance_monthly.csv
- fact_leave.csv

The source files are stored in the project's data directory.

## Pipeline outputs
- output/cleaned/: records that pass validation
- output/rejected/: records rejected during validation
- logs/etl_quality_report.json: processing counts and rejection reasons

## Run the pipeline
From the project root, run:

    docker compose run --rm etl

## Repeatability check
Run the pipeline twice and compare checksums of the cleaned and rejected
CSV files. Identical checksums indicate identical file outputs.

## Data quality
Review logs/etl_quality_report.json after every run.
Investigate rejected rows rather than silently deleting them.

## Metric definitions
Refer to the source metric_dictionary.csv and data_dictionary.csv
files for the supplied dataset's metric and column definitions.
