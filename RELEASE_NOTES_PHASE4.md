# PulseIQ Phase 4 — Release Notes

Review date: 16 November 2026
Release status: Local validation / Release Candidate 1

## Delivered

### Task 16 — Monthly reporting
- PDF and Excel monthly report generation.
- September 2026 report generated and checked.
- PDF: 3 pages.
- Excel worksheets: Cover, pnl, expenses, vendors, departments, scorecard.
- P&L arithmetic and report month consistency validated.
- Monthly job checks for P&L data before generating files.
- Months without P&L data are skipped instead of producing empty reports.

### Task 17 — Local operations
- PostgreSQL host port 5434 restricted to 127.0.0.1.
- Superset host port 8088 restricted to 127.0.0.1.
- Local PostgreSQL custom-format backup script created.
- Backup archive verified using pg_restore --list.
- Restore test completed in a temporary database.
- Restore test verified 27 warehouse base tables, 1,606 employees and 7,338 payroll rows.
- Temporary restore database removed after verification.
- Daily PostgreSQL backup LaunchAgent configured for 02:30.
- Monthly report LaunchAgent configured for day 5 at 09:00.
- Backup retention policy: 14 days.
- Local operations instructions documented in docs/LOCAL_OPERATIONS.md.

### Task 18 — Self-service explorer
- Streamlit aggregate KPI explorer prototype.
- Role-based metric selection for demonstration.
- Month selection and department-level metric display.
- Small-group suppression based on department headcount.
- Four demonstration roles tested across 19 permitted role-metric combinations.
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
- 12 Phase 4 API tests passed.
- Latest full local project suite: 45 tests passed.
- Python compilation passed for explorer, phase4, src and tests.
- Backup archive integrity verified.
- Temporary database restore test passed.
- Restored warehouse counts verified.
- September 2026 PDF and Excel report generation passed.
- October 2026 report correctly skipped because no P&L data was available.
- Local backup and monthly report LaunchAgents loaded.
- Local API and Explorer previously returned HTTP 200.
- Superset login endpoint returned its expected HTTP 302 redirect.

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
- Local LaunchAgents require the Mac user session and Docker Desktop to be available.
- Clean-environment validation of the latest local operations changes remains outstanding.

## Release recommendation
Keep this release local and private until authentication, authorization, privacy, database access, hosting and scheduled refresh controls have been verified.
