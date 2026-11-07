# Phase 3 — Task 14: AI Insights and Forecasts

## Payroll anomaly screening
The anomaly mart matches fact_anomaly exactly across all 11 reason codes,
including source row counts and flagged counts. The source flag value is Y.
Where money_at_risk is absent in the source, the mart reports zero.

The largest reason groups include STATISTICAL_OUTLIER (145),
PATTERN_SHIFT (125), and NO_ATTENDANCE (50). Monetary amounts are
screening indicators and categories can overlap. They must not be summed
as unique employee exposure or treated as confirmed fraud or errors.

## Forecasts
The forecast mart contains 72 rows:
- Attrition rate: 6 monthly overall forecasts.
- Headcount: 66 monthly forecasts across 11 departments.
- Forecast horizon: October 2026 to March 2027.
- Training cutoff: September 2026.
- Model: trend-seasonal-baseline-0.1.

The model uses a same-month average of the prior three years for
attrition and a 36-month linear trend with half-strength seasonality
for headcount. Forecasts are estimates, not actual results, and are
labelled for human review.

## Dashboard
Dashboard: AI Insights & Forecast Dashboard.
Charts: payroll anomaly counts, money at risk by reason, forecast
headcount by department, and forecast attrition rate.
