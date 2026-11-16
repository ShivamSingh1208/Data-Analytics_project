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
- Small-group suppression based on department headcount.
- Four demonstration roles tested across all 19 permitted role-metric combinations.
- Manager restricted to D01 in local testing; D00 suppressed.
- Streamlit browser smoke test passed locally.
- Automated role-policy and privacy tests added.
- Production authentication and differencing-attack protection remain outstanding.

### Task 19 — Metrics API
- FastAPI health endpoint.
- P&L endpoint.
- Expense category endpoint.
- Vendor expense endpoint.
- Department-month endpoint.
- Executive scorecard endpoint.
- Month filtering, row limits and input validation.

## Validation results

- 12 Phase 4 API pytest tests passed.
- Latest full local project suite: 41 tests passed.
- Latest Python compilation check passed.
- Initial clean Python 3.12 validation: 26 tests passed.
- Earlier local baseline before role-policy tests: 32 passed; the latest complete suite is 41 passed.
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
- Department-level suppression does not prevent all differencing attacks; adversarial testing and a robust disclosure-control design remain outstanding.
- Scheduled GitHub workflow has not been verified with configured secrets.
- Clean-machine installation validation passed: 26 tests passed, Python compilation succeeded, and pip reported no broken requirements. Deployment tests remain outstanding.
- Browser operation and local role behavior were verified for Admin, HR, Manager and Executive roles.
- Nineteen role-metric combinations passed local AppTest checks.
- Small-group suppression unit tests: 6 passed.

## Release recommendation

Keep this release local and private until authentication,
authorization, privacy, database access, hosting and scheduled
refresh controls have been verified.


## Latest local validation

- 41 tests passed in the latest full local project suite.
- Python compilation passed for explorer, phase4, src, and tests.
- Role-policy tests: 9 passed; privacy tests: 6 passed.
