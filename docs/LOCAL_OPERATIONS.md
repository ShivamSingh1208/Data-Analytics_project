# PulseIQ — Local Operations Runbook

Review date: 16 November 2026

## 1. Local service access

| Service | Local address |
|---|---|
| PostgreSQL | 127.0.0.1:5434 |
| Superset | http://127.0.0.1:8088 |
| Metrics API | http://127.0.0.1:8765 |
| Streamlit Explorer | http://127.0.0.1:8502 |

PostgreSQL and Superset host ports are bound to 127.0.0.1.
Keep this deployment local and private.

## 2. Scheduled jobs

| Job | Schedule |
|---|---|
| PostgreSQL backup | Daily at 02:30 |
| Monthly report | Day 5 at 09:00 |

These are macOS LaunchAgents. They require the Mac user session and Docker Desktop to be available.

Check their status:

    launchctl print "gui/$(id -u)/com.pulseiq.local-postgres-backup"
    launchctl print "gui/$(id -u)/com.pulseiq.local-monthly-report"

## 3. Manual execution

From the project root:

    /bin/zsh scripts/local_ops/backup_postgres.sh
    /bin/zsh scripts/local_ops/monthly_report.sh

The monthly report defaults to the previous calendar month.
To select a month:

    REPORT_MONTH=2026-09 /bin/zsh scripts/local_ops/monthly_report.sh

The script skips a month when no P&L rows are available.

## 4. PostgreSQL backups

Backup directory: backups/postgres/

The backup script:
- Creates a PostgreSQL custom-format dump.
- Checks the dump using pg_restore --list.
- Applies restrictive file permissions.
- Removes backups older than 14 days.

The backups directory is excluded from Git.

## 5. Restore test procedure

Restore into a temporary database. Do not overwrite the live database for a routine restore test.

Example commands:

    BACKUP="backups/postgres/REPLACE_WITH_EXISTING_BACKUP.dump"
    TEST_DB="pulseiq_restore_test"

    docker compose exec -T postgres dropdb --if-exists -U pulseiq "$TEST_DB"
    docker compose exec -T postgres createdb -U pulseiq "$TEST_DB"

    docker compose exec -T postgres pg_restore \
      --exit-on-error --no-owner -U pulseiq -d "$TEST_DB" < "$BACKUP"

    docker compose exec -T postgres psql -U pulseiq -d "$TEST_DB" -c \
      "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'dw' AND table_type = 'BASE TABLE';"

    docker compose exec -T postgres dropdb -U pulseiq "$TEST_DB"

Replace the backup placeholder with the name of an existing dump before running the commands.

Restore test completed on 16 November 2026:
- 27 warehouse base tables restored.
- 1,606 dim_employee rows verified.
- 7,338 fact_payroll rows verified.
- Temporary restore database removed.

## 6. Logs and reports

Local job logs:
- logs/local_ops/postgres_backup.log
- logs/local_ops/monthly_report.log

Generated reports are stored in reports/monthly/.

Do not commit private logs, database backups, or credentials.

## 7. Data availability

September 2026 is the latest validated P&L month in this review.
October 2026 had no P&L rows, and the monthly job correctly skipped report generation.

## 8. Security and limitations

- This is a local-only deployment, not a production hosting setup.
- Explorer role environment variables are demonstration controls, not authentication.
- Production SSO/OIDC and authorization remain outstanding.
- Differencing-attack protection requires further design and testing.
- Public hosting and production database hosting are not configured.
- Scheduled GitHub workflow execution with production secrets is not verified.
