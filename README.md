# PulseIQ — End-to-End Business Analytics Platform

PulseIQ is an end-to-end analytics project demonstrating how raw business data can be transformed into reliable datasets, business metrics, and interactive dashboards.

The project uses Python, Pandas, Pandera, SQL, PostgreSQL, Docker, and Apache Superset.

## Project Overview

PulseIQ is organized into three phases, covering data engineering, analytics, and business intelligence.

### Phase 1 — Data Foundation and ETL

Focus: Data ingestion, cleaning, validation, and database preparation.

Key technologies:
- Python and Pandas
- Pandera data validation
- PostgreSQL
- SQL
- Docker

[Explore Phase 1](phase-1/README.md)

### Phase 2 — HR Analytics and Dashboards

Focus: Workforce analytics, payroll, attendance, attrition, productivity, and budget analysis.

Key deliverables:
- HR analytics metrics
- Department-level analysis
- Payroll and budget reconciliation
- Interactive Apache Superset dashboard
- Analytics report and supporting evidence

[Explore Phase 2](phase-2/README.md)

### Phase 3 — Business Analytics and Advanced Insights

Focus: Financial analysis, receivables, departmental performance, AI-driven signals, and business scorecards.

Key deliverables:
- Profit and loss analysis
- Expense analytics
- Receivables and cash analysis
- Department performance insights
- AI-related analytical findings
- Business scorecard and final report

[Explore Phase 3](phase-3/README.md)

## Technology Stack

| Area | Technologies |
|---|---|
| Programming | Python |
| Data processing | Pandas |
| Data validation | Pandera |
| Database | PostgreSQL |
| Query language | SQL |
| Data visualization | Apache Superset |
| Containers | Docker and Docker Compose |
| Reporting | Python and ReportLab |
| Version control | Git and GitHub |

## Repository Structure

```text
PulseIQ/
├── README.md
├── phase-1/
│   └── README.md
├── phase-2/
│   └── README.md
├── phase-3/
│   └── README.md
├── src/
├── sql/
├── test/
├── reports/
├── " data"/  # Local source CSVs (not tracked by Git)
├── docker-compose.yml
└── other project configuration files
```

The phase directories contain organized copies of the project documentation, scripts, SQL files, reports, and supporting evidence. The original project files remain in the repository root.

## Dashboard and Reports

The project includes an interactive Apache Superset dashboard and phase-wise analytical reports.

The dashboard presents workforce, payroll, attendance, attrition, budget, productivity, and leave-related insights.

## Data and Reproducibility

The project uses structured CSV source data and a PostgreSQL database.

Source CSV datasets are excluded from Git and are kept locally in the ` data/` directory (the directory name begins with a space). A fresh ETL run requires these source files and the correct local configuration.

## Prerequisites and Local Setup

- Docker Desktop with Docker Compose
- Git
- Python and the project dependencies

From the repository root, start the configured services:

```bash
docker compose up -d --build
```

Open Apache Superset at `http://localhost:8088`.

For a local test run, activate the project Python environment and run:

```bash
python -m pytest -v test/
```

A fresh installation may require database initialization and dashboard setup. Starting the containers alone does not recreate the existing local database or Superset configuration.

## Data Quality Results

The recorded ETL validation run processed:

| Result | Records |
|---|---:|
| Input rows | 19,734 |
| Clean rows | 19,722 |
| Rejected rows | 12 |

Rejected records are reported for investigation rather than silently discarded. The recorded automated test run passed all 7 tests.

The verified September 2026 dashboard KPIs are:

| Metric | Value |
|---|---:|
| Total headcount | 441 |
| Employer cost | 55,519,621.87 |
| Attendance rate | 95.19% |

These figures describe the project's dataset, not a real company's workforce.

## Security and Data Handling

- Keep `.env`, passwords, API keys, and private credentials out of Git.
- Use `.env.example` for configuration placeholders.
- Source CSV datasets are excluded from Git.
- Confirm permission before publishing datasets or screenshots.
- Review staged files before committing or pushing.

## Learning Outcomes

- Building data pipelines using Python
- Cleaning and validating business data
- Designing relational database structures
- Writing analytical SQL queries
- Creating business intelligence dashboards
- Performing financial and workforce analysis
- Documenting analytical findings
- Organizing a multi-phase analytics project

## Repository

GitHub: https://github.com/ShivamSingh1208/Data-Analytics_project

---

PulseIQ — From raw data to actionable business insights.
