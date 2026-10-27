from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)

out = Path("reports/DataAnalytics_Shivam_Kumar_Phase2_Report.pdf")
out.parent.mkdir(parents=True, exist_ok=True)

doc = SimpleDocTemplate(
    str(out),
    pagesize=A4,
    rightMargin=17 * mm,
    leftMargin=17 * mm,
    topMargin=16 * mm,
    bottomMargin=16 * mm,
    title="PulseIQ HR Analytics — Phase 2 Report",
    author="Shivam Kumar",
)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="ReportTitle", parent=styles["Title"],
    fontSize=21, leading=26, alignment=TA_CENTER,
    textColor=colors.HexColor("#17365D"), spaceAfter=8
))
styles.add(ParagraphStyle(
    name="Subtitle", parent=styles["Normal"],
    fontSize=10, leading=14, alignment=TA_CENTER,
    textColor=colors.HexColor("#555555"), spaceAfter=14
))
styles.add(ParagraphStyle(
    name="Section", parent=styles["Heading2"],
    fontSize=13, leading=16, textColor=colors.HexColor("#17365D"),
    spaceBefore=8, spaceAfter=5
))
styles.add(ParagraphStyle(
    name="BodySmall", parent=styles["BodyText"],
    fontSize=8.5, leading=11, spaceAfter=4
))
styles.add(ParagraphStyle(
    name="Cell", parent=styles["BodyText"],
    fontSize=7.2, leading=9
))
styles.add(ParagraphStyle(
    name="CellHead", parent=styles["BodyText"],
    fontSize=7.2, leading=9, textColor=colors.white
))

P = lambda text, style="BodySmall": Paragraph(text, styles[style])

def footer(canvas, document):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(17 * mm, 9 * mm, "PulseIQ HR Analytics | Phase 2")
    canvas.drawRightString(
        A4[0] - 17 * mm, 9 * mm, f"Page {document.page}"
    )
    canvas.restoreState()

story = []

# PAGE 1
story.append(P("PulseIQ HR Analytics", "ReportTitle"))
story.append(P("Phase 2 — Data Analytics Project Report", "Subtitle"))

meta = [
    [P("<b>Prepared by</b>", "Cell"), P("Shivam Kumar", "Cell")],
    [P("<b>Track</b>", "Cell"), P("Data Analytics", "Cell")],
    [P("<b>Repository</b>", "Cell"),
     P("github.com/ShivamSingh1208/Data-Analytics_project", "Cell")],
    [P("<b>Git branch</b>", "Cell"), P("main", "Cell")],
    [P("<b>Git tag</b>", "Cell"),
     P("phase-2 — created and pushed to GitHub", "Cell")],
    [P("<b>Reporting period</b>", "Cell"),
     P("April 2025 – September 2026 for budget and KPI source data", "Cell")],
]
t = Table(meta, colWidths=[38 * mm, 139 * mm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF0F7")),
    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D1D9E0")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]))
story.append(t)
story.append(Spacer(1, 8))
story.append(P("Executive summary", "Section"))
story.append(P(
    "Phase 2 extends the PulseIQ HR Analytics warehouse with attendance and "
    "leave metrics, attrition metrics and grouped risk summaries, productivity "
    "metrics, payroll reconciliation, and department payroll budget analysis. "
    "The work uses PostgreSQL tables and SQL views, Python loaders, source-data "
    "checks, and manual comparisons. Seven automated ETL tests passed. "
    "The work includes KPI target comparisons, budget analysis, and documented "
    "payroll reconciliation differences that remain pending data-owner review."
))

story.append(P("Task status and evidence", "Section"))
rows = [[
    P("<b>Workstream</b>", "CellHead"),
    P("<b>Status</b>", "CellHead"),
    P("<b>Evidence / remaining work</b>", "CellHead"),
]]
task_rows = [
    ("Attendance & leave", "Implemented; verified",
     "SQL views created. Monthly attendance, department metrics, leave status totals and date checks reviewed."),
    ("Attrition", "Implemented; verified",
     "891 monthly department records and 430 risk predictions loaded. Group risk reporting suppresses groups under 10."),
    ("Productivity", "Implemented; verified",
     "16 teams, 38 sprints and 28,868 tasks loaded. Cancelled work excluded from key completion metrics."),
    ("Payroll reconciliation", "Implemented; caveats documented",
     "18 monthly reference checks completed. Four months differ from the official reference; rejected rows and reasons documented."),
    ("Budget & KPI targets", "Implemented; validated with caveats",
     "198 budget rows and 180 KPI target rows loaded. Budget source checks passed; KPI comparison view validated. Eighteen task targets are missing."),
]
for a, b, c in task_rows:
    rows.append([P(a, "Cell"), P(b, "Cell"), P(c, "Cell")])

t = Table(rows, colWidths=[34 * mm, 34 * mm, 109 * mm], repeatRows=1)
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CCD4DD")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1),
     [colors.white, colors.HexColor("#F5F7FA")]),
]))
story.append(t)
story.append(PageBreak())

# PAGE 2
story.append(P("Verified Results", "ReportTitle"))
story.append(P("Attendance, attrition, productivity and payroll", "Subtitle"))

story.append(P("Attendance and leave", "Section"))
story.append(P(
    "Monthly attendance ranged from 92.89% in May 2026 to 95.51% in July 2025. "
    "Finance & Accounts recorded 90.82% across 6,076 scheduled days, and HR "
    "recorded 92.51%. These are investigation signals, not proof of a cause. "
    "The leave warehouse contains 3,439 records; leave-status totals were "
    "checked. Seven approved medical-leave records each span 130 days (910 days "
    "in total) and should be validated with the source owner before interpretation."
))

story.append(P("Attrition", "Section"))
story.append(P(
    "The headcount source contains 891 department-month records from January "
    "2020 through September 2026. The risk source contains 430 predictions, "
    "including 43 High and 86 Medium predictions in the September 2026 snapshot. "
    "Risk predictions are not actual exits and are not presented as certainty. "
    "The March 2026 snapshot had only five predictions and is suppressed from "
    "group reporting under the minimum-group-size rule."
))

story.append(P("Productivity", "Section"))
story.append(P(
    "The task warehouse contains 28,868 tasks across 16 teams and 38 sprints. "
    "There are 24,139 Done tasks, 898 Cancelled tasks and 999 tasks with Blocked "
    "status. Overall on-time completion was 92.86% among completed tasks with "
    "a valid on-time result; average valid cycle time was 4.80 days. QA Automation "
    "had a 94.01% on-time rate, while Growth Marketing had 91.30%. These "
    "differences do not establish why team performance varies."
))

story.append(P("Payroll reconciliation", "Section"))
story.append(P(
    "The official reference covers 18 months. Four months differ after ETL "
    "cleaning: May 2025 (INR 61,813.15), December 2025 (INR 98,327.42), February "
    "2026 (INR 154,811.89), and April 2026 (INR 96,015.00) in employer cost. The "
    "May and February records include duplicate employee/run pairs. The "
    "December and April records have employee IDs not found in the employee "
    "dimension. Rejected rows remain excluded pending data-owner review."
))

story.append(P("Budget analysis", "Section"))
story.append(P(
    "The 198 department-month budget rows total INR 862,030,000.00. Cleaned payroll "
    "employer cost totals INR 861,369,767.38, giving a net variance of −INR 660,232.62 "
    "(actual minus budget). Largest net overspends are Data & AI INR 992,768.20 "
    "(0.90%), Customer Support INR 482,050.62 (1.01%), and Product & Design "
    "INR 453,539.93 (0.65%). Engineering had the largest net underspend at "
    "INR 2,054,508.87. Three department-month budget values matched the original CSV."
))
story.append(PageBreak())

# PAGE 3
story.append(P("Quality, Lessons and Next Steps", "ReportTitle"))

story.append(P("Testing and quality controls", "Section"))
story.append(P(
    "<b>Automated tests:</b> 7 passed using the existing "
    "ETL test suite. Tests cover reversed leave dates, date-key consistency, "
    "duplicate identifiers, negative payroll amounts and open-ended validity dates."
))
story.append(P(
    "<b>Warehouse checks:</b> Source-to-warehouse department/month counts and "
    "three manual budget checks were reviewed. The payroll budget view contains "
    "198 rows across 11 departments and 18 months. KPI targets contain 180 rows "
    "across 10 departments and 18 months."
))
story.append(P(
    "<b>KPI comparison results:</b> The view contains 180 department-month rows "
    "across 10 departments and 18 months. Attendance met target in 106 rows, "
    "overtime in 152, attrition in 121, and task completion in 136 of 162 rows "
    "with an available target. Eighteen task-completion targets remain NULL. "
    "Attendance target 0.94 was converted to 94%. Overtime share assumes "
    "overtime hours divided by scheduled days multiplied by 8 hours; this "
    "denominator needs confirmation. Recorded overtime is zero in 126 of 198 "
    "attendance department-month rows, so overtime findings need source validation."
))

story.append(P("Problems and resolutions", "Section"))
story.append(P(
    "• Source budget values included comma separators; the loader removes commas "
    "before numeric conversion.<br/>"
    "• A pre-existing SQL view had a different column layout; it was safely "
    "recreated without deleting payroll or budget data.<br/>"
    "• Payroll duplicate pairs caused two monthly reconciliation gaps; the records "
    "remain excluded pending data-owner confirmation.<br/>"
    "• Missing KPI targets are preserved as NULL instead of being fabricated."
))

story.append(P("Learning reflection", "Section"))
story.append(P(
    "This phase strengthened my practical understanding of loading source data "
    "into PostgreSQL, designing SQL metric views, validating keys and totals, "
    "testing ETL rules, and reconciling payroll with an official reference. I also "
    "learned to distinguish actual results from model predictions, preserve missing "
    "values, and document unresolved issues instead of hiding them."
))

story.append(P("Next steps", "Section"))
story.append(P(
    "1. Confirm the four monthly payroll reconciliation differences with the data "
    "owner and resolve them through an approved process.<br/>"
    "2. Confirm the overtime-share denominator and investigate zero-overtime "
    "source values.<br/>"
    "3. Confirm rejected payroll rows with the data owner and keep missing task "
    "targets unavailable rather than inventing values.<br/>"
    "4. Capture fresh screenshots, regenerate and verify this PDF, rerun tests, "
    "and commit and push the final report and KPI SQL changes to GitHub."
))

story.append(Spacer(1, 8))
story.append(P(
    "<b>Submission note:</b> This report reflects verified work as of 27 October "
    "2026. The phase-2 Git tag has already been pushed. The KPI target "
    "comparisons are available with documented caveats; fresh Phase 2 screenshots and publication of this updated report remain outstanding."
))

doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f"PDF created: {out}")
print(f"File size: {out.stat().st_size:,} bytes")
