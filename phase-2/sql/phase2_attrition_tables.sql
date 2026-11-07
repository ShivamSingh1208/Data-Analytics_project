-- PulseIQ Phase 2: Actual headcount outcomes and predicted attrition risk.
-- These are separate tables because outcomes and predictions are different.

CREATE TABLE IF NOT EXISTS dw.fact_headcount_monthly (
    date_key INTEGER NOT NULL,
    month_start_date DATE NOT NULL,
    department_id VARCHAR(20) NOT NULL,
    headcount_start INTEGER NOT NULL,
    hires INTEGER NOT NULL,
    exits INTEGER NOT NULL,
    voluntary_exits INTEGER NOT NULL,
    transfers_in INTEGER NOT NULL,
    transfers_out INTEGER NOT NULL,
    headcount_end INTEGER NOT NULL,
    attrition_rate_monthly_pct NUMERIC(8,4),
    CONSTRAINT pk_fact_headcount_monthly
        PRIMARY KEY (date_key, department_id),
    CONSTRAINT chk_headcount_nonnegative
        CHECK (
            headcount_start >= 0 AND hires >= 0 AND exits >= 0
            AND voluntary_exits >= 0 AND transfers_in >= 0
            AND transfers_out >= 0 AND headcount_end >= 0
        ),
    CONSTRAINT chk_voluntary_exits
        CHECK (voluntary_exits <= exits)
);

CREATE TABLE IF NOT EXISTS dw.fact_attrition_risk (
    prediction_id VARCHAR(30) PRIMARY KEY,
    employee_id VARCHAR(20) NOT NULL,
    as_of_date_key INTEGER,
    department_id VARCHAR(20) NOT NULL,
    as_of_date DATE NOT NULL,
    risk_score_12m NUMERIC(8,6) NOT NULL,
    risk_band VARCHAR(20) NOT NULL,
    top_reason_1 VARCHAR(200),
    top_reason_2 VARCHAR(200),
    top_reason_3 VARCHAR(200),
    model_version VARCHAR(100),
    model_note TEXT,
    employee_key BIGINT,
    CONSTRAINT chk_risk_score_range
        CHECK (risk_score_12m >= 0 AND risk_score_12m <= 1),
    CONSTRAINT chk_risk_band
        CHECK (risk_band IN ('Low', 'Medium', 'High'))
);
