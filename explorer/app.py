import os
from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

st.set_page_config(
    page_title="PulseIQ KPI Explorer",
    layout="wide"
)

st.title("PulseIQ — Self-service KPI Explorer")

st.warning(
    "LOCAL DEMONSTRATION ONLY. Environment-variable roles are not "
    "authentication. Do not expose this application publicly."
)

url = os.getenv("DATABASE_URL")
role = os.getenv("PULSEIQ_ROLE", "").upper()
dept = os.getenv("PULSEIQ_MANAGER_DEPARTMENT", "").strip()

roles = {"ADMIN", "HR", "MANAGER", "EXECUTIVE"}

if not url or role not in roles:
    st.error(
        "Configure DATABASE_URL and a demonstration PULSEIQ_ROLE."
    )
    st.stop()

if role == "MANAGER" and not dept:
    st.error("Manager department mapping is missing.")
    st.stop()

allowed = {
    "ADMIN": [
        "Headcount",
        "Attendance",
        "Attrition",
        "Employer cost",
        "Overtime",
        "Task completion",
    ],
    "HR": [
        "Headcount",
        "Attendance",
        "Attrition",
        "Task completion",
    ],
    "EXECUTIVE": [
        "Headcount",
        "Attendance",
        "Attrition",
        "Employer cost",
        "Overtime",
        "Task completion",
    ],
    "MANAGER": [
        "Headcount",
        "Attendance",
        "Task completion",
    ],
}

metric_columns = {
    "Headcount": ("headcount_end", 5, "Employees"),
    "Attendance": ("attendance_rate_pct", 5, "%"),
    "Attrition": ("attrition_rate_pct", 10, "%"),
    "Employer cost": ("employer_cost", 5, "Currency"),
    "Overtime": ("overtime_share_pct", 5, "%"),
    "Task completion": ("task_completion_pct", 5, "%"),
}

metric = st.selectbox("Metric", allowed[role])

column, minimum, unit = metric_columns[metric]

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
            st.error("No warehouse data is available.")
            st.stop()

        st.caption(f"Latest warehouse month: {cutoff}")

        selected_month = st.date_input(
            "Reporting month",
            value=cutoff,
            min_value=date(2020, 1, 1),
            max_value=cutoff,
        )

        params = {"month": selected_month}

        where = "WHERE month = :month"

        if role == "MANAGER":
            where += " AND department_id = :department"
            params["department"] = dept

        query = f"""
            SELECT
                department_id,
                "{column}" AS metric_value,
                COALESCE(employees_paid, headcount_end, 0) AS group_size
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
        st.info("No records found for the selected month.")
        st.stop()

    # Suppress small groups before displaying department metrics.
    safe = df[df["group_size"] >= minimum].copy()
    hidden = len(df) - len(safe)

    if hidden:
        st.warning(
            f"{hidden} department group(s) hidden by the "
            f"minimum group-size rule ({minimum})."
        )

    if safe.empty:
        st.info("No department meets the minimum group-size rule.")
        st.stop()

    st.subheader(f"{metric} — {selected_month}")

    st.caption(
        "Department-level values are displayed directly. "
        "Percentages are not added across departments."
    )

    st.dataframe(
        safe[["department_id", "metric_value"]],
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        f"Demonstration role: {role}. "
        f"Small-group suppression threshold: {minimum}."
    )

except Exception as exc:
    st.error(f"Explorer query failed: {exc}")

finally:
    engine.dispose()
