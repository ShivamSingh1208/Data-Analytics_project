import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

st.set_page_config(page_title="PulseIQ Workforce Analytics", layout="wide")
st.title("PulseIQ Workforce Analytics")
st.caption("Phase 1 dashboard • Headcount is derived from employee history; verify before executive reporting.")

@st.cache_resource
def get_engine():
    url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://pulseiq:pulseiq123@localhost:5433/pulseiq"
    )
    return create_engine(url, pool_pre_ping=True)

@st.cache_data(ttl=60)
def load_data():
    engine = get_engine()
    with engine.connect() as conn:
        payroll = pd.read_sql(
            text("""
                SELECT month_start, department_id, paid_employees,
                       gross_pay, net_pay, employer_cost, cost_per_head,
                       overtime_share_pct, variable_pay_share_pct, lop_days
                FROM dw.metric_payroll_monthly
                WHERE paid_employees >= 5
                ORDER BY month_start
            """), conn)
        attendance = pd.read_sql(
            text("""
                SELECT month_start, department_id, present_days,
                       scheduled_days, attendance_rate_pct, late_arrival_rate_pct
                FROM dw.metric_attendance_monthly
                ORDER BY month_start
            """), conn)
        headcount = pd.read_sql(
            text("""
                SELECT month_start, department_id, headcount_end, hires, exits
                FROM dw.metric_headcount_monthly
                ORDER BY month_start
            """), conn)
        work_modes = pd.read_sql(
            text("""
                SELECT work_mode, employee_count
                FROM dw.metric_work_mode_distribution
                ORDER BY employee_count DESC
            """), conn)

        work_locations = pd.read_sql(
            text("""
                SELECT work_location, employee_count
                FROM dw.metric_work_location_distribution
                ORDER BY employee_count DESC
            """), conn)
        return payroll, attendance, headcount, work_modes, work_locations
try:
        payroll, attendance, headcount, work_modes, work_locations = load_data()
except Exception as exc:
    st.error("Unable to load dashboard data. Check PostgreSQL and DATABASE_URL.")
    st.code(str(exc))
    st.stop()

if payroll.empty:
    st.warning("No department-month groups meet the privacy threshold.")
    st.stop()

departments = sorted(
    set(payroll["department_id"].dropna().astype(str))
    | set(headcount["department_id"].dropna().astype(str))
)
selected_departments = st.multiselect(
    "Department filter", departments, default=departments
)

payroll["department_id"] = payroll["department_id"].astype(str)
attendance["department_id"] = attendance["department_id"].astype(str)
headcount["department_id"] = headcount["department_id"].astype(str)

p = payroll[payroll["department_id"].isin(selected_departments)].copy()
a = attendance[attendance["department_id"].isin(selected_departments)].copy()
h = headcount[headcount["department_id"].isin(selected_departments)].copy()

if p.empty:
    st.info("Choose at least one department with eligible payroll data.")
    st.stop()

latest_month = p["month_start"].max()
latest = p[p["month_start"] == latest_month]
latest_h = h[h["month_start"] == latest_month]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Paid employees", f"{int(latest['paid_employees'].sum()):,}")
c2.metric("Employer cost", f"₹{latest['employer_cost'].sum():,.0f}")
c3.metric("Gross pay", f"₹{latest['gross_pay'].sum():,.0f}")
c4.metric("Derived headcount", f"{int(latest_h['headcount_end'].sum()):,}")

st.caption(f"Latest payroll month: {pd.to_datetime(latest_month).strftime('%B %Y')}")

st.subheader("Monthly workforce trend")
trend = h.groupby("month_start", as_index=False).agg(
    headcount=("headcount_end", "sum"),
    hires=("hires", "sum"),
    exits=("exits", "sum")
)
st.line_chart(trend.set_index("month_start")[["headcount"]])
if len(trend) >= 2:
    delta = int(trend["headcount"].iloc[-1] - trend["headcount"].iloc[-2])
    st.write(f"**Insight:** Derived headcount changed by {delta:+,} from the previous month.")
else:
    st.write("**Insight:** More than one month is needed to compare headcount trends.")

st.subheader("Employer cost by department")
dept_cost = latest.groupby("department_id", as_index=False)["employer_cost"].sum()
st.bar_chart(dept_cost.set_index("department_id"))
if not dept_cost.empty:
    top = dept_cost.sort_values("employer_cost", ascending=False).iloc[0]
    st.write(f"**Insight:** {top['department_id']} has the highest employer cost among the selected departments.")

st.subheader("Attendance rate by month")
attendance_trend = a.groupby("month_start", as_index=False).agg(
    present_days=("present_days", "sum"),
    scheduled_days=("scheduled_days", "sum")
)
attendance_trend["attendance_rate_pct"] = (
    attendance_trend["present_days"] /
    attendance_trend["scheduled_days"].replace(0, pd.NA) * 100
)
st.line_chart(attendance_trend.set_index("month_start")[["attendance_rate_pct"]])
if not attendance_trend.empty:
    last_att = attendance_trend.iloc[-1]["attendance_rate_pct"]
    if pd.notna(last_att):
        st.write(f"**Insight:** The latest calculated attendance rate is {last_att:.1f}%.")


st.subheader("Work location distribution")

if not work_locations.empty:
    location_counts = work_locations.set_index("work_location")["employee_count"]
    st.bar_chart(location_counts)

    top_location = work_locations.iloc[0]
    st.write(
        f"**Insight:** {top_location['work_location']} is the largest "
        f"work-location group, with {int(top_location['employee_count']):,} employees."
    )
else:
    st.info("Work-location breakdown is unavailable.")
st.subheader("Data notes")
st.markdown("""
- Department payroll groups with fewer than five paid employees are excluded from the payroll view.
- Headcount is derived from employee dimension dates, not an authoritative monthly snapshot.
- Attrition, finance-ledger, invoice, task, anomaly and forecast metrics are not yet available.
- Check `dw.dq_results` before using these numbers for decisions.
""")
