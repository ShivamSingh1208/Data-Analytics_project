from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "phase2_evidence"
CSV_DIR = OUT / "csv"
CHART_DIR = OUT / "charts"
SCREEN_DIR = ROOT / "docs" / "screenshots"

CSV_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)
SCREEN_DIR.mkdir(parents=True, exist_ok=True)

# Export through psql inside the existing PostgreSQL container.
queries = {
    "attendance_monthly": """
        SELECT * FROM dw.metric_attendance_monthly ORDER BY month_start
    """,
    "attendance_department_monthly": """
        SELECT * FROM dw.metric_attendance_department_monthly
        ORDER BY month_start, department_name
    """,
    "leave_monthly": """
        SELECT * FROM dw.metric_leave_monthly ORDER BY month_start
    """,
    "attrition_monthly": """
        SELECT * FROM dw.metric_attrition_monthly ORDER BY month_start_date
    """,
    "attrition_department_monthly": """
        SELECT * FROM dw.metric_attrition_department_monthly
        ORDER BY month_start_date, department_name
    """,
    "attrition_risk_snapshot": """
        SELECT * FROM dw.metric_attrition_risk_snapshot
        ORDER BY as_of_date, department_id
    """,
    "productivity_team": """
        SELECT * FROM dw.metric_productivity_team ORDER BY team_name
    """,
    "productivity_sprint": """
        SELECT * FROM dw.metric_productivity_sprint
        ORDER BY start_date, team_name
    """,
    "payroll_reconciliation": """
        SELECT * FROM dw.metric_payroll_reconciliation ORDER BY month
    """,
    "payroll_department_budget": """
        SELECT * FROM dw.metric_payroll_department_reconciliation
        ORDER BY month, department_name
    """,
    "kpi_target_comparison": """
        SELECT * FROM dw.metric_kpi_target_comparison
        ORDER BY month, department_name
    """,
}

def export_csv(name, query):
    sql = f"COPY ({query.strip().rstrip(';')}) TO STDOUT WITH CSV HEADER;"
    cmd = [
        "docker", "compose", "exec", "-T", "postgres",
        "sh", "-lc",
        'psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" '
        '-d "$POSTGRES_DB" -P pager=off'
    ]
    result = subprocess.run(
        cmd, input=sql, text=True, capture_output=True, cwd=ROOT
    )
    if result.returncode:
        raise RuntimeError(
            f"Export failed for {name}:\n{result.stderr.strip()}"
        )
    destination = CSV_DIR / f"{name}.csv"
    destination.write_text(result.stdout)
    rows = max(0, sum(1 for _ in destination.open()) - 1)
    print(f"EXPORTED {destination.relative_to(ROOT)} ({rows} rows)")
    return destination, rows

def main():
    # Use the project's Python environment.
    try:
        import pandas as pd
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        print("Missing Python package:", exc)
        print("Install pandas and matplotlib in .report-venv, then rerun.")
        sys.exit(2)

    exported = {}
    for name, query in queries.items():
        path, count = export_csv(name, query)
        exported[name] = (path, count)

    def read(name):
        return pd.read_csv(exported[name][0])

    charts = 0

    def save_chart(df, x, y, title, xlabel, ylabel, filename, rotate=45):
        nonlocal charts
        if df.empty or x not in df.columns or y not in df.columns:
            print(f"SKIP chart {filename}: required data unavailable")
            return
        data = df[[x, y]].copy()
        data[y] = pd.to_numeric(data[y], errors="coerce")
        data = data.dropna(subset=[y])
        if data.empty:
            print(f"SKIP chart {filename}: no numeric values")
            return
        fig, ax = plt.subplots(figsize=(10, 5.5))
        ax.plot(data[x].astype(str), data[y], marker="o")
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", labelrotation=rotate)
        fig.tight_layout()
        fig.savefig(CHART_DIR / filename, dpi=160)
        plt.close(fig)
        charts += 1
        print(f"CHART {CHART_DIR.relative_to(ROOT)}/{filename}")

    att = read("attendance_monthly")
    save_chart(att, "month_start", "attendance_rate_pct",
               "Monthly Attendance Rate", "Month", "Attendance (%)",
               "attendance_monthly.png")

    att_dept = read("attendance_department_monthly")
    if "attendance_rate_pct" in att_dept.columns:
        latest_month = att_dept["month_start"].max()
        latest = att_dept[att_dept["month_start"] == latest_month].sort_values(
            "attendance_rate_pct"
        )
        save_chart(latest, "department_name", "attendance_rate_pct",
                   f"Department Attendance — {latest_month}", "Department",
                   "Attendance (%)", "attendance_by_department_latest.png")

    attr = read("attrition_monthly")
    save_chart(attr, "month_start_date", "attrition_rate_pct",
               "Monthly Attrition Rate", "Month", "Attrition (%)",
               "attrition_monthly.png")

    prod = read("productivity_team")
    save_chart(prod, "team_name", "on_time_rate_pct",
               "Team On-Time Completion Rate", "Team", "On-time (%)",
               "productivity_team_ontime.png")

    pay = read("payroll_reconciliation")
    if "employer_cost_difference" in pay.columns:
        save_chart(pay, "month", "employer_cost_difference",
                   "Monthly Payroll Reconciliation Difference", "Month",
                   "Difference (INR)", "payroll_reconciliation_difference.png")
    elif "employer_cost_diff" in pay.columns:
        save_chart(pay, "month", "employer_cost_diff",
                   "Monthly Payroll Reconciliation Difference", "Month",
                   "Difference (INR)", "payroll_reconciliation_difference.png")
    else:
        print("NOTE: payroll reconciliation column names:", list(pay.columns))

    budget = read("payroll_department_budget")
    if "variance" in budget.columns and "department_name" in budget.columns:
        totals = budget.groupby("department_name", as_index=False)["variance"].sum()
        totals = totals.sort_values("variance")
        save_chart(totals, "department_name", "variance",
                   "Net Payroll Budget Variance by Department", "Department",
                   "Actual minus budget (INR)", "payroll_budget_variance.png")

    kpi = read("kpi_target_comparison")
    summary = [
        "# PulseIQ Phase 2 — Generated Evidence",
        "",
        "Generated from the live PostgreSQL warehouse using the existing metric views.",
        "CSV files are the primary evidence; charts are derived visual summaries.",
        "No individual-level attrition risk records are exported by this script.",
        "",
        "## Export row counts",
    ]
    for name, (_, count) in exported.items():
        summary.append(f"- `{name}.csv`: {count:,} rows")

    summary.extend([
        "",
        "## Generated charts",
        f"- Charts created: {charts}",
        "",
        "## Important interpretation notes",
        "- Payroll reconciliation differences are not treated as resolved.",
        "- KPI target results retain missing task targets as unavailable.",
        "- Overtime share uses the documented 8-hours-per-scheduled-day assumption.",
        "- Charts are analytical evidence, not screenshots of the Superset interface.",
        "",
    ])
    (OUT / "README.md").write_text("\n".join(summary))
    print(f"\nEvidence summary: {OUT / 'README.md'}")
    print(f"CSV exports: {len(exported)}; charts created: {charts}")

if __name__ == "__main__":
    main()
