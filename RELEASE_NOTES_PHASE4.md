# PulseIQ Phase 4 — Release Notes

Review date: 16 November 2026
Release status: Local validation / Release Candidate 1

## Delivered

### Task 16 — Monthly reporting
- PDF and Excel monthly report generation.
- September 2026 report generated.
- PDF: 3 pages.
- Excel: Cover, pnl, expenses, vendors, departments, scorecard.
- P&L arithmetic and report month consistency validated.

### Task 18 — Self-service explorer
- Streamlit aggregate KPI explorer prototype.
- Role-based metric selection for demonstration.
- Month selection and department-level metric display.
- Small-group suppression logic included.
- Production authentication and privacy verification remain outstanding.

### Task 19 — Metrics API
- FastAPI health endpoint.
- P&L endpoint.
- Expense category endpoint.
- Vendor expense endpoint.
- Department-month endpoint.
- Executive scorecard endpoint.
- Month filtering, row limits and input validation.

## Validation results

- 12 Phase 4 automated pytest tests passed.
- 26 total project tests passed in a clean Python 3.12 environment.
- All five metric endpoints returned September 2026 data.
- Unknown metric returned HTTP 404.
- Invalid limit and month returned HTTP 422.
- Excel report worksheets and row counts verified.
- PDF page count and key report content verified.

## September 2026 P&L

| Metric | Value |
|---|---:|
| Revenue | 80,601,695.00 |
| Expenses | 65,615,715.87 |
| Net profit | 14,985,979.13 |
| Profit margin | 18.59% |

## Known limitations

- No public production deployment.
- No verified SSO/OIDC authentication.
- Explorer role environment variables are demonstration controls, not security.
- Department-level privacy suppression needs adversarial testing.
- Scheduled GitHub workflow has not been verified with configured secrets.
- Clean-machine installation validation passed: 26 tests passed, Python compilation succeeded, and pip reported no broken requirements. Deployment tests remain outstanding.
- Browser KPI behavior was verified for Admin, HR, Manager and Executive roles.

## Release recommendation

Keep this release local and private until authentication,
authorization, privacy, database access, hosting and scheduled
refresh controls have been verified.
