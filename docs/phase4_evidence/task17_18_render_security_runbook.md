# Phase 4 Tasks 17–18 — Render deployment and security runbook

Status: **implementation package prepared; production deployment and live verification are not yet complete.**

## What this change provides

- Streamlit OpenID Connect (OIDC) sign-in; the old `PULSEIQ_ROLE` demonstration shortcut is removed.
- Exact-email allowlisting with verified-email requirement and explicit `ADMIN`, `HR`, `MANAGER`, or `EXECUTIVE` assignments.
- Manager access remains restricted to the department assigned in the server-side allowlist.
- Fail-closed access when authentication, role assignments, database, privacy key, or privacy ledger is missing.
- Small-cell suppression (5 for ordinary metrics; 10 for attrition).
- Persistent PostgreSQL privacy-release ledger. The 90-day restriction applies globally across all authorized users. After any user releases a metric for a department and reporting month, all users are blocked from releasing that metric and department for the same or an adjacent month during the 90-day window. The ledger uses an HMAC of the verified email, not the email itself, and logs the full query scope before displaying results.
- A Render Blueprint for a Singapore-region Streamlit service and managed PostgreSQL database. `autoDeploy: false` is intentional until data and identity configuration are reviewed.
- Runtime generation of `.streamlit/secrets.toml` from Render secrets; no OIDC credentials are committed.

## Important privacy limitation

The release ledger reduces straightforward repeat/adjacent-month differencing across authorized users. It is not a formal differential-privacy guarantee and does not prevent inference from external information or data already exported elsewhere. Do not describe it as mathematically private or use it as a substitute for a formal privacy review. The 90-day policy is intentionally restrictive and should be approved by the data owner before production use.

## 1. Apply the code

From the local repository root, create a branch and copy the files in this package to their matching paths. Keep any local uncommitted work safe first. Then run:

```bash
# Already prepared on phase4-task17-18-render-security; do not recreate the branch.
# Copy/merge the supplied files into the repository, preserving unrelated local changes.
git diff --check
python -m pip install -r requirements-phase4.txt
python -m pytest -q tests/test_explorer_auth.py tests/test_explorer_privacy.py tests/test_explorer_access.py
```

If your existing test layout differs, inspect it before adjusting the test command. Do not force-push or overwrite `main`.

## 2. Apply the database migration

Back up the target database first. Apply the privacy migration using a
dedicated database migration/owner role, not the application runtime role.
Do not use a superuser unless the database provider explicitly requires it.

After migration, the database owner should grant the runtime role only the
required permissions. The following is an example; replace the role name
with the confirmed production PostgreSQL role before executing:

    GRANT USAGE ON SCHEMA dw TO pulseiq_runtime;
    GRANT SELECT ON TABLE dw.metric_phase3_department_month TO pulseiq_runtime;
    GRANT SELECT, INSERT ON TABLE dw.privacy_query_log TO pulseiq_runtime;
    GRANT USAGE ON SEQUENCE dw.privacy_query_log_privacy_query_id_seq TO pulseiq_runtime;

Keep migration credentials separate from the application DATABASE_URL.
The runtime role must not own the schema or tables or receive superuser,
schema CREATE, or broad warehouse write privileges.

The Render Blueprint intentionally leaves DATABASE_URL as a manually
configured secret. Set it to the database's internal connection URL using
the restricted runtime role (for example, pulseiq_runtime), not the
default database-owner connection string. Keep the migration/owner URL
separate and never place it in the application environment.

## 3. Prepare Google OIDC

Create an OAuth/OIDC web client in the identity provider. Register the exact production callback URL:

`https://YOUR-RENDER-SERVICE.onrender.com/oauth2callback`

For local testing, use `http://localhost:8501/oauth2callback` as a separate development client. Never use a wildcard redirect URI. Configure the client with the Google OIDC metadata URL:

`https://accounts.google.com/.well-known/openid-configuration`

Use accounts with verified email claims. Do not enable anonymous or public access. If using another OIDC provider, update the metadata URL and validate its verified-email claim before production.

## 4. Create Render services

1. Push the deployment branch to the GitHub repository.
2. In Render, create a new Blueprint from that repository and select `render.yaml`.
3. Review the proposed Singapore-region web service and managed PostgreSQL plan/pricing before provisioning.
4. Supply the prompted secret values in Render; do not commit them.
5. Set `OIDC_REDIRECT_URI` to the exact `https://...onrender.com/oauth2callback` callback for the created service.
6. Set `PULSEIQ_USER_ROLES` to a JSON allowlist. Example structure only (replace with real approved accounts and department IDs):

```json
{
  "approved.admin@example.com": {"role": "ADMIN"},
  "approved.hr@example.com": {"role": "HR"},
  "approved.manager@example.com": {"role": "MANAGER", "department_id": "D01"},
  "approved.executive@example.com": {"role": "EXECUTIVE"}
}
```

7. Set `OIDC_CLIENT_ID` and `OIDC_CLIENT_SECRET` from the identity provider. Render generates `STREAMLIT_COOKIE_SECRET` and `PULSEIQ_PRIVACY_HMAC_KEY` from the Blueprint.
8. Deploy only after the warehouse data migration/restore and privacy SQL migration are complete.

## 5. Production data prerequisite

The Render Blueprint creates a **new, empty managed PostgreSQL database**. It does not copy the local Docker warehouse, Superset metadata, source CSV files, or existing metric views. The repository excludes source data. Before the app can show real metrics, restore/import only approved data into Render PostgreSQL, recreate required schemas/views (including `dw.metric_phase3_department_month`), validate row counts and KPI reconciliations, and apply the privacy ledger migration. Do not upload personal or confidential data until the data owner has approved the transfer, region, retention, and access model.

## 6. Verification checklist

- [ ] Render Blueprint validates and services are provisioned in the approved region/plan.
- [ ] Build succeeds and `/_stcore/health` returns healthy.
- [ ] Unauthenticated visitor sees sign-in only; no metric data is returned.
- [ ] Authenticated but unlisted email is denied.
- [ ] Unverified email is denied.
- [ ] Each role sees only its approved metrics.
- [ ] Manager cannot query a different department by changing browser/UI parameters.
- [ ] Department group sizes below threshold are suppressed; attrition uses threshold 10.
- [ ] Repeat and adjacent-month requests are rejected across different authorized users, including after app restart.
- [ ] Two concurrent same-scope requests cannot both pass the ledger check.
- [ ] Missing ledger/database/role configuration fails closed.
- [ ] No secrets appear in Git, build logs, or UI error messages.
- [ ] Data owner signs off on privacy policy, database region, backup/retention, and user allowlist.

## 7. Remaining manual actions

The repository owner must supply the real OIDC client credentials and approved user-role JSON, provision Render resources, approve the paid plan, migrate the approved warehouse data, run the migration, and test the live service. No public URL, successful deployment, live database, or identity-provider configuration is claimed by this patch.

## 8. Existing scheduled monthly report workflow

The repository's `.github/workflows/monthly-report.yml` uses the GitHub Actions repository secret `DATABASE_URL`. Add that secret in **GitHub → Settings → Secrets and variables → Actions** using the approved database connection URL. The Render private connection string is not reachable from GitHub-hosted runners; use the database's external connection URL and restrict external access to the extent supported by the selected Render plan. Verify a manual `workflow_dispatch` run and inspect its PDF/Excel artifacts before relying on the monthly cron schedule. Do not copy the database URL into workflow YAML.


## Restricted-role verification — 2026-11-18

The isolated PostgreSQL privacy integration suite was successfully
executed using the non-superuser role `pulseiq_test_runtime`.

Verified permissions:
- CONNECT on the isolated test database.
- USAGE on schema `dw`.
- SELECT and INSERT on `dw.privacy_query_log`.
- CREATE on schema `dw` denied.

The role has no superuser, database-creation, role-creation,
replication, or BYPASSRLS privileges.

The restricted-role database login succeeded.
The complete test suite reported **96 passed in 0.93s**.

Evidence: `reports/phase4_evidence/task17_18_restricted_role_verification.txt`

This verifies the isolated test environment only. Production database
provisioning, production credentials, OIDC configuration, and deployment
must be verified separately.

## 9. Optional separate PulseIQ Metrics API service

The current `render.yaml` provisions the Streamlit Explorer only. The
FastAPI Metrics API is a separate application and is not provisioned by
that Blueprint. Do not assume that deploying the Explorer also deploys
the API.

If the API is approved for deployment, create a separate Render Web
Service from the same repository and deployment branch. Review service
pricing and region before creation. Suggested service configuration:

- Runtime: Python
- Build command: `pip install -r requirements-phase4.txt`
- Start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`
- Region: Singapore, subject to data-owner approval
- Auto-deploy: disabled until release approval

Configure these API service environment variables:

| Variable | Configuration |
| --- | --- |
| `DATABASE_URL` | Restricted runtime PostgreSQL connection URL; never use the owner/migration URL |
| `API_SESSION_SECRET` | A newly generated high-entropy secret, at least 32 characters |
| `API_COOKIE_SECURE` | `true` in production |
| `API_OIDC_REDIRECT_URI` | Exact API callback URL: `https://YOUR-API-SERVICE.onrender.com/auth/callback` |
| `OIDC_CLIENT_ID` | Approved OIDC web-client ID |
| `OIDC_CLIENT_SECRET` | Approved OIDC web-client secret |
| `OIDC_SERVER_METADATA_URL` | `https://accounts.google.com/.well-known/openid-configuration` |
| `PULSEIQ_USER_ROLES` | Approved JSON role and department allowlist |
| `PULSEIQ_PRIVACY_HMAC_KEY` | The exact same secret value used by the Explorer service |

The API callback is `/auth/callback`. Register that exact URL as an
additional authorized redirect URI in the identity provider. Do not
replace the Explorer callback `/oauth2callback`; the two applications
have separate callback routes and separate signed sessions.

**Critical shared privacy configuration:** use the same
`PULSEIQ_PRIVACY_HMAC_KEY` value in the Explorer and API services so
verified users are hashed consistently when they access the shared
privacy-release ledger. Do not independently generate a different key
for the API. Store the value in Render secrets, never in Git.

The API session cookie is named `pulseiq_api_session`, is HttpOnly,
uses SameSite=Lax, and is Secure when `API_COOKIE_SECURE=true`. The API
session secret is separate from the Streamlit cookie secret. The API
does not reuse the Streamlit session cookie.

After configuration, verify `/health`, `/auth/login`, `/auth/callback`,
`/auth/me`, and `POST /auth/logout` using approved test accounts. Verify
that unauthenticated metric requests fail, removed users lose access,
role restrictions are enforced, manager queries remain department-scoped,
and privacy-ledger conflicts return HTTP 429 without returning data.

Do not expose the API publicly or treat it as production-ready until the
database migration, restricted-role grants, OIDC callback, secrets,
allowlist, privacy controls, and live authorization tests have all been
approved and verified. No API Render service is created by this
documentation change.
