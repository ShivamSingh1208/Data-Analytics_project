# PulseIQ HR Analytics

An end-to-end HR analytics project that transforms employee, payroll,
attendance, and leave data into validated datasets and interactive
business intelligence dashboards.

## Project Overview

PulseIQ demonstrates a data analytics workflow using Python, Pandas,
Pandera, PostgreSQL, SQL, Docker, and Apache Superset.

The pipeline focuses on data cleaning, validation, traceability,
monthly HR metrics, and dashboard reporting.

## Architecture

CSV Source Data
      |
      v
Python ETL Pipeline
(Pandas + Pandera)
      |
      v
Data Quality Validation
      |
      +----> Rejected Records and Quality Reports
      |
      v
PostgreSQL Data Warehouse
      |
      v
SQL Metric Views
      |
      v
Apache Superset Dashboard

## Technology Stack

- Python and Pandas for data processing
- Pandera for data validation
- PostgreSQL for warehouse storage
- SQL for metric calculations and reporting
- Docker Compose for running services
- Apache Superset for interactive dashboards
- Pytest for automated testing

## Project Structure

    GrowmarProject/
    ├── data/                 # Local source datasets
    ├── dashboards/           # Dashboard preparation scripts
    ├── docs/                 # Documentation and screenshots
    ├── reports/              # Data-quality and validation findings
    ├── sql/                  # Schema, metric views, and quality checks
    ├── src/                  # ETL and warehouse scripts
    ├── test/                 # Automated tests
    ├── output/               # Generated cleaned/rejected data
    ├── logs/                 # ETL quality logs
    ├── Dockerfile
    ├── docker-compose.yml
    ├── requirements.txt
    └── README.md

## Dashboard

The PulseIQ HR Analytics dashboard includes:

- Total headcount
- Employer cost
- Attendance rate
- Monthly exits
- Monthly headcount trend
- Monthly payroll trend
- Monthly attendance trend

Dashboard screenshot: `docs/screenshots/pulseiq_dashboard.png`

The dashboard runs locally through Apache Superset at:

`http://localhost:8088`

## Data Quality and ETL

The ETL workflow includes:

- Reading source datasets
- Cleaning and standardizing data
- Validating data using configured rules
- Separating accepted and rejected records
- Generating quality reports and processing logs
- Preparing data for downstream warehouse metrics

The current validation run processed 19,734 input rows:
19,722 clean rows and 12 rejected rows, with no failed tables.

Rejected records should be investigated rather than silently discarded.

## Warehouse and Metrics

PostgreSQL contains the `dw` schema and SQL-based metric views for
monthly HR reporting.

The latest validated common reporting month is September 2026:

| Metric | Value |
|---|---:|
| Total headcount | 452 |
| Employer cost | 55,519,621.87 |
| Monthly exits | 3 |
| Attendance rate | 95.00% |
| Monthly attrition | 0.68% |

Employer cost is expressed in the source dataset's currency units.
These figures describe the current project dataset and are not
claims about a real company's workforce.

Headcount data extends through October 2026, while payroll and
attendance data currently extend through September 2026.

## Prerequisites

- Docker Desktop
- Docker Compose
- Git
- Python 3.10 or a compatible project environment for local tests

## Setup

1. Clone the repository:

   `git clone git@github.com:ShivamSingh1208/Data-Analytics_project.git`

2. Enter the project directory:

   `cd Data-Analytics_project`

3. Create a local environment file using the template:

   `cp .env.example .env`

4. Edit `.env` and set strong local passwords and a unique secret key.
   Never commit `.env` or share its contents.

5. Review `docker-compose.yml` and ensure the expected source CSV files
   are available in the local `data/` directory.

6. Start the services:

   `docker compose up -d --build`

7. Open Superset:

   `http://localhost:8088`

Follow the repository's deployment and database initialization steps
if this is a fresh installation. Do not assume the existing local
database or dashboard configuration is automatically recreated
by starting the containers.

## Run Tests

With the project Python environment activated:

`python -m pytest -v test/`

The latest recorded test run passed all 7 tests.

## Useful Commands

Check running containers:

`docker compose ps`

Run ETL through the configured service:

`docker compose run --rm etl`

Connect to PostgreSQL:

`docker compose exec postgres psql -U pulseiq -d pulseiq`

Stop services:

`docker compose down`

Persistent database data is stored in a Docker volume. Do not remove
volumes unless you intentionally want to delete their stored data.

## Security and Data Handling

- Keep `.env`, passwords, API keys, and private credentials out of Git.
- `.env.example` contains placeholders, not production credentials.
- Source CSV files are excluded from Git by default.
- Confirm you have permission to publish any dataset or screenshot.
- Review staged files before committing or pushing.

## Future Improvements

- Add automated ETL scheduling and monitoring.
- Add continuous integration for tests and data-quality checks.
- Document fresh-install dashboard and database initialization.
- Add more HR metrics and dashboard filters.
- Add reproducible sample data for portfolio demonstrations.

## Author

Shivam Kumar

GitHub: https://github.com/ShivamSingh1208
LinkedIn: https://linkedin.com/in/shivam-kumar-6973a3352
