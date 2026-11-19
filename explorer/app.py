"""Authenticated, privacy-controlled PulseIQ KPI Explorer."""
from __future__ import annotations

import logging
import os

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

from access import METRIC_COLUMNS, get_allowed_metrics
from auth import AuthorizationError, authorize_identity, parse_user_assignments
from privacy import (
    PrivacyBudgetExceeded,
    hash_principal,
    reserve_release,
    suppress_small_groups,
)

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="PulseIQ KPI Explorer",
    layout="wide",
)

st.title("PulseIQ — Self-service KPI Explorer")

# Fail closed if the production identity policy is not configured.
try:
    assignments = parse_user_assignments(
        os.getenv("PULSEIQ_USER_ROLES", "")
    )
except AuthorizationError as exc:
    st.error("PulseIQ access policy is not configured correctly.")
    logger.error("PulseIQ role configuration rejected: %s", exc)
    st.stop()

url = os.getenv("DATABASE_URL", "").strip()
privacy_key = os.getenv("PULSEIQ_PRIVACY_HMAC_KEY", "")

if not url:
    st.error("PulseIQ database configuration is unavailable.")
    st.stop()

if len(privacy_key) < 32:
    st.error("PulseIQ privacy controls are not configured correctly.")
    st.stop()

# Require an authenticated OIDC session.
if not st.user.is_logged_in:
    st.info("Sign in with your approved company account to continue.")
    if st.button("Sign in"):
        st.login()
    st.stop()

# Only verified identity + explicit allowlist assignment grants access.
try:
    identity = authorize_identity(
        st.user.get("email"),
        st.user.get("email_verified"),
        assignments,
    )
except AuthorizationError as exc:
    logger.warning("PulseIQ identity authorization denied: %s", exc)
    st.error("Your account is not authorized to access PulseIQ.")
    if st.button("Sign out"):
        st.logout()
    st.stop()

email = identity["email"]
role = identity["role"]
dept = identity["department_id"]

st.caption(f"Signed in as {email} · Role: {role}")

if st.button("Sign out"):
    st.logout()
    st.stop()

# Use only metrics permitted by the server-side role policy.
allowed_metrics = get_allowed_metrics(role)

if not allowed_metrics:
    st.error("No metrics are assigned to your account.")
    st.stop()

metric = st.selectbox("Metric", list(allowed_metrics))
column, minimum, unit = METRIC_COLUMNS[metric]

principal_hash = hash_principal(email, privacy_key)
engine = create_engine(url, pool_pre_ping=True)

try:
    with engine.connect() as connection:
        cutoff = connection.execute(
            text("""
                SELECT MAX(month)
                FROM dw.metric_phase3_department_month
            """)
        ).scalar()

        if cutoff is None:
            st.info("No warehouse data is currently available.")
            st.stop()

        st.caption(f"Latest warehouse month: {cutoff}")

        # Fixed to the latest warehouse snapshot. Do not add a
        # historical month selector: repeated comparisons can enable
        # differencing of small changes in department metrics.
        selected_month = cutoff
        params = {"month": cutoff}

        where = "WHERE month = :month"

        # Department scope comes only from the authenticated allowlist.
        if role == "MANAGER":
            where += " AND department_id = :department"
            params["department"] = dept

        query = f"""
            SELECT
                department_id,
                "{column}" AS metric_value,
                COALESCE(headcount_end, 0) AS group_size
            FROM dw.metric_phase3_department_month
            {where}
            ORDER BY department_id
        """

        df = pd.read_sql_query(
            text(query),
            connection,
            params=params,
        )

    if df.empty:
        st.info("No records found for the latest reporting month.")
        st.stop()

    # Apply strict small-group suppression BEFORE reserving a release.
    safe, hidden = suppress_small_groups(df, minimum)

    if hidden:
        st.warning(
            f"{hidden} department group(s) hidden by the "
            f"minimum group-size rule ({minimum})."
        )

    if safe.empty:
        st.info("No department meets the minimum group-size rule.")
        st.stop()

    # Reserve every visible department atomically. No data is displayed
    # unless the persistent privacy ledger approves the release.
    department_ids = safe["department_id"].astype(str).tolist()

    with engine.begin() as ledger_connection:
        reserve_release(
            connection=ledger_connection,
            principal_hash=principal_hash,
            metric=metric,
            department_ids=department_ids,
            reporting_month=selected_month,
        )

    # Display only after successful privacy-budget reservation.
    st.subheader(f"{metric} — {selected_month}")

    st.caption(
        "Latest reporting month only. Historical month comparisons are "
        "disabled to reduce differencing risk. Percentages are not "
        "added across departments."
    )

    st.dataframe(
        safe[["department_id", "metric_value"]],
        width="stretch",
        hide_index=True,
    )

    st.caption(
        f"Privacy threshold: {minimum}. "
        "This release was recorded in the privacy ledger."
    )

except PrivacyBudgetExceeded:
    st.warning(
        "This metric and department have already been released for "
        "the same or an adjacent month within the privacy review window. "
        "The data has not been displayed."
    )

except Exception:
    logger.exception("PulseIQ Explorer request failed.")
    st.error(
        "The Explorer could not complete this request. "
        "No data was displayed. Contact the administrator."
    )

finally:
    engine.dispose()
