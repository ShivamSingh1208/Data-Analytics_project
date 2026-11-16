# PulseIQ Phase 4 implementation notes

This pack is starter code, not evidence of a working deployment. Phase 3 confirms
`dw.metric_phase3_department_month` and the underlying warehouse tables.
The report/API defaults for `metric_pnl_monthly`, `metric_expense_category`,
`metric_vendor_expense`, and `metric_phase3_executive_scorecard` must be
checked against the live database before running. Override names using the
environment variables documented in the code.

## Privacy policy
- Never publish employee names, IDs, individual payroll rows or individual anomaly records.
- Manager role is restricted to one assigned department by server-side configuration.
- Attrition requires at least 10 people; other people metrics require at least 5.
- A team of 3 must not see attrition. Suppress it; also prevent recovery by subtraction
  from totals or other filtered views.
- Do not trust URL parameters or user-editable widgets for role assignment.
  Configure verified OIDC claims and server-side role mapping before public launch.
- Use a read-only database account with SELECT access only to approved aggregate views.

## Hosting comparison
| Host | Strength | Limitation |
|---|---|---|
| Streamlit Community Cloud | Simple GitHub deployment | Resource/sleep limits; no production SLA |
| Render | Separate web services and scheduled jobs | Free services may sleep; persistent DB often paid |
| Railway | Convenient app/database deployment | Usage billing and free allowance can change |
| Managed VM + Superset | Keeps current dashboards and SQL | Requires paid operations, TLS, backups |

Recommended demonstration route: Streamlit Community Cloud plus a managed
PostgreSQL database. Verify current limits/pricing before deployment. Never
upload raw HR/payroll CSVs to a public repository or public app.

## Clean-machine checklist
1. Create fresh Python 3.12 venv and install `requirements-phase4.txt`.
2. Supply a read-only DATABASE_URL from environment/secret store.
3. Confirm all configured views and columns using information_schema.
4. Build a monthly report for at least two different months.
5. Test API health, catalogue and all five metric routes.
6. Test role views with group sizes 2, 3, 4, 5, 9 and 10.
7. Attempt differencing attacks using totals and filters.
8. Verify private-window and mobile access after deployment.
9. Save actual outputs, screenshots, test logs and failures.

## Five lineage paths
- P&L: raw ledger CSV -> Phase 3 validation/load -> `dw.fact_ledger` +
  `dw.dim_account` -> monthly P&L view -> Finance dashboard.
- Expense category: expense CSV -> load -> `dw.fact_expense` +
  `dw.dim_account` -> category view -> Finance dashboard.
- Vendor expense: expense CSV -> load -> `dw.fact_expense` +
  `dw.dim_vendor` -> vendor view -> Finance dashboard.
- Attendance: attendance CSV -> ETL -> `dw.fact_attendance_monthly` ->
  `dw.metric_phase3_department_month` -> Department dashboard.
- Executive scorecard: payroll/attendance/ledger/task feeds -> Phase 3 ETL ->
  warehouse facts/reference summary -> scorecard view -> Executive dashboard.

Confirm exact view names and intermediate SQL objects in the live database
before signing off lineage.

## Final release blockers
Configure host, secrets, authentication and department mapping; confirm actual
view names; run DB-backed tests; reconcile report figures; deploy and verify
public URLs on mobile/private browser; capture screenshots; record the demo;
then create `v1.0.0` and `phase-4` tags.
