# PulseIQ Phase 4 — Final Checklist

Review date: 16 November 2026
Release status: Local validation / Release Candidate 1

## Task 16 — Monthly report builder
- [x] PDF generated
- [x] Excel generated
- [x] Worksheet names checked
- [x] September 2026 data consistency checked
- [x] P&L arithmetic checked
- [x] PDF text and page count checked
- [x] Monthly report skips months without P&L data

## Task 17 — Deployment and operations
- [x] PostgreSQL and Superset host ports restricted to localhost
- [x] Local PostgreSQL backup script created
- [x] Backup archive integrity checked with pg_restore
- [x] Backup restored successfully into a temporary database
- [x] Restored warehouse tables and key row counts verified
- [x] Daily backup LaunchAgent configured
- [x] Monthly report LaunchAgent configured
- [x] Local operations runbook created
- [ ] Production database hosting
- [ ] Public application hosting
- [ ] Verified production authentication and authorization
- [ ] Production refresh verification

## Task 18 — Self-service explorer
- [x] Streamlit application compiles
- [x] Local server responds HTTP 200
- [x] Role-based prototype implemented
- [x] Browser KPI behavior verified across Admin, HR, Manager, and Executive roles
- [x] Small-group suppression logic and browser behavior verified locally
- [x] Small-group privacy unit tests and 19 role-metric combinations passed
- [x] Explorer historical month selector disabled; latest-month-only regression tests passed (2 tests)
- [ ] Differencing-attack protection and adversarial privacy tests
- [ ] Production identity integration

## Task 19 — Metrics API
- [x] Health endpoint
- [x] Five metric endpoints
- [x] September month filtering
- [x] Invalid metric validation
- [x] Invalid limit validation
- [x] Invalid month validation
- [x] Automated API tests: 12 passed

## Task 20 — Final project artifacts and validation
- [x] Executive presentation created
- [x] Release notes created
- [x] Final checklist created
- [x] Local operations runbook created
- [x] Follow-up repository review, commit and remote push verified
- [x] Initial RC1 tag created (phase-4-rc1)
- [x] Latest full local project suite: 45 tests passed
- [x] Python compilation passed
- [ ] Clean-environment validation of latest local operations changes

## Release limitations
- No public production deployment.
- No verified SSO/OIDC authentication.
- Explorer role environment variables are demonstration controls, not security.
- Department-level suppression does not prevent all differencing attacks.
- Scheduled GitHub workflow has not been verified with configured secrets.
- Local LaunchAgents require the Mac user session and Docker Desktop to be available.
