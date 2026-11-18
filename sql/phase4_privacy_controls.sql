-- Phase 4 Tasks 17-18: persistent privacy-release ledger.
-- Apply with a dedicated migration/owner role, not the application runtime role.
BEGIN;
CREATE SCHEMA IF NOT EXISTS dw;
CREATE TABLE IF NOT EXISTS dw.privacy_query_log (
    privacy_query_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    principal_hash CHAR(64) NOT NULL,
    metric TEXT NOT NULL,
    department_id TEXT NOT NULL,
    reporting_month DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT privacy_query_metric_nonempty CHECK (length(trim(metric)) > 0),
    CONSTRAINT privacy_query_department_nonempty CHECK (length(trim(department_id)) > 0),
    CONSTRAINT privacy_query_month_first_day CHECK (EXTRACT(DAY FROM reporting_month) = 1)
);
-- Remove the obsolete per-user index during upgrades.
DROP INDEX IF EXISTS dw.ix_privacy_query_overlap;
CREATE INDEX IF NOT EXISTS ix_privacy_query_global_overlap
    ON dw.privacy_query_log (metric, department_id, reporting_month, created_at DESC);
COMMIT;
