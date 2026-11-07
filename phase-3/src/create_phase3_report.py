from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

OUT = Path("reports/PulseIQ_Phase3_Analytics_Report.pdf")
OUT.parent.mkdir(parents=True, exist_ok=True)

doc = SimpleDocTemplate(
    str(OUT), pagesize=A4,
    rightMargin=16*mm, leftMargin=16*mm,
    topMargin=15*mm, bottomMargin=16*mm,
    title="PulseIQ HR Analytics — Phase 3 Report",
    author="Shivam Kumar",
)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="CoverTitle", parent=styles["Title"], fontSize=23,
    leading=28, alignment=TA_CENTER, textColor=colors.HexColor("#17365D"),
    spaceAfter=8
))
styles.add(ParagraphStyle(
    name="SubTitle", parent=styles["Normal"], fontSize=10,
    leading=14, alignment=TA_CENTER, textColor=colors.HexColor("#555555"),
    spaceAfter=12
))
styles.add(ParagraphStyle(
    name="SectionX", parent=styles["Heading2"], fontSize=13,
    leading=16, textColor=colors.HexColor("#17365D"),
    spaceBefore=8, spaceAfter=5
))
styles.add(ParagraphStyle(
    name="SubSectionX", parent=styles["Heading3"], fontSize=10,
    leading=13, textColor=colors.HexColor("#24476A"),
    spaceBefore=5, spaceAfter=3
))
styles.add(ParagraphStyle(
    name="BodyX", parent=styles["BodyText"], fontSize=8.6,
    leading=11.5, spaceAfter=5
))
styles.add(ParagraphStyle(
    name="SmallX", parent=styles["BodyText"], fontSize=7.5,
    leading=9.5, spaceAfter=3
))
styles.add(ParagraphStyle(
    name="CellX", parent=styles["BodyText"], fontSize=7.2, leading=9
))
styles.add(ParagraphStyle(
    name="CellHeadX", parent=styles["BodyText"], fontSize=7.2,
    leading=9, textColor=colors.white
))

def P(s, style="BodyX"):
    return Paragraph(s, styles[style])

def footer(canvas, document):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(16*mm, 8*mm, "PulseIQ HR Analytics | Phase 3")
    canvas.drawRightString(A4[0]-16*mm, 8*mm, f"Page {document.page}")
    canvas.restoreState()

def make_table(headers, rows, widths):
    data = [[P(f"<b>{x}</b>", "CellHeadX") for x in headers]]
    for row in rows:
        data.append([P(str(x), "CellX") for x in row])
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#17365D")),
        ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#CCD4DD")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
         [colors.white, colors.HexColor("#F4F7FA")]),
    ]))
    return t

story = []

# Cover and executive overview
story += [
    Spacer(1, 18*mm),
    P("PulseIQ HR Analytics", "CoverTitle"),
    P("Phase 3 — Finance, Department Performance, AI Insights and Executive Reporting",
      "SubTitle"),
    Spacer(1, 5*mm),
    make_table(
        ["Project detail", "Value"],
        [
            ("Prepared by", "Shivam Kumar"),
            ("Project", "PulseIQ HR Analytics"),
            ("Repository", "ShivamSingh1208/Data-Analytics_project"),
            ("Reporting period", "April 2025 – September 2026, unless otherwise stated"),
            ("Forecast horizon", "October 2026 – March 2027"),
            ("Report date", "3 November 2026"),
        ], [43*mm, 130*mm]
    ),
    Spacer(1, 8),
    P("Executive summary", "SectionX"),
    P(
        "Phase 3 extends the PulseIQ warehouse and Superset reporting with "
        "profit and loss analysis, receivables ageing, cash movement, "
        "department-level performance, payroll anomaly screening, forecasts "
        "and an executive KPI scorecard. The work includes five documented "
        "analysis workstreams and four published Phase 3 dashboards."
    ),
    P(
        "<b>Key results:</b> the FY 2025–26 official P&amp;L reports revenue of "
        "INR 790.16 million and profit of INR 135.16 million. At the reporting "
        "cutoff, 62 issued open invoices total INR 139.39 million. Cash movement "
        "over 18 months is net positive by INR 1,233.52 million. The department "
        "mart contains 198 department-month rows, and its attendance calculation "
        "now reconciles to the reference within 0.01 percentage points."
    ),
    P(
        "<b>Important caveats:</b> an INR 18,450 June 2026 salary-ledger difference "
        "remains unexplained and requires Finance review. Department target "
        "breaches remain visible even when overall KPIs meet their targets. "
        "Anomaly categories can overlap, and model forecasts are estimates "
        "requiring human review."
    ),
    P("Phase 3 deliverables", "SectionX"),
    make_table(
        ["Task", "Workstream", "Dashboard / output"],
        [
            ("11", "Profit and loss analysis", "PulseIQ Finance & P&L Dashboard"),
            ("12", "Receivables and cash movement", "Receivables & Cash Dashboard"),
            ("13", "Cross-department impact", "Department Performance Dashboard"),
            ("14", "AI insights and forecasts", "AI Insights & Forecast Dashboard"),
            ("15", "Executive KPI scorecard", "Executive Scorecard Dashboard"),
        ], [15*mm, 75*mm, 83*mm]
    ),
    PageBreak(),
]

# Task 11
story += [
    P("Task 11 — Profit and Loss Analysis", "SectionX"),
    P("Method and reconciliation", "SubSectionX"),
    P(
        "Revenue is calculated as ledger credit minus debit; expenses as debit "
        "minus credit. Only detail accounts are included to avoid parent-account "
        "double counting. Expense category and vendor analysis uses expense-bill "
        "amounts excluding GST and is not added again to ledger P&amp;L."
    ),
    make_table(
        ["Period", "Revenue (INR)", "Expenses (INR)", "Profit (INR)"],
        [
            ("FY 2025–26", "790,160,535.00", "655,004,422.46", "135,156,112.54"),
            ("Apr–Sep 2026 official", "470,769,517.00", "381,242,041.96", "89,527,475.04"),
            ("Apr–Sep 2026 ledger", "470,769,517.00", "381,260,491.96", "89,509,025.04"),
        ], [35*mm, 46*mm, 46*mm, 46*mm]
    ),
    P("June 2026 payroll reconciliation exception", "SubSectionX"),
    P(
        "Payroll earned fixed pay and ledger account 5001 (Salaries &amp; Wages) "
        "match in 10 of 11 departments. D01 payroll earned fixed pay is "
        "INR 19,873,074.18, compared with an account 5001 ledger debit of "
        "INR 19,891,524.18. The unexplained excess is INR 18,450. Employer cost "
        "agrees with the reference across departments; overtime and incentive "
        "accounts reconcile. The cause remains unresolved and requires Finance "
        "review. No source data has been adjusted."
    ),
    P("Business findings", "SubSectionX"),
    P(
        "1. Revenue rose 11.1% from March to April 2026, while expenses rose "
        "20.7%; net profit fell 26.0% and margin declined from 20.60% to 13.72%.<br/>"
        "2. Incentives and Bonus increased by INR 9,467,647.06; Salaries and "
        "Wages by INR 3,630,082.51; and Insurance by INR 2,120,000.00.<br/>"
        "3. Professional Fees includes a manual INR 1.8 million credit journal "
        "(MJ-0002) dated 1 April 2026. After an INR 448,840 expense debit, the "
        "category shows net expense of negative INR 1,351,160. Finance should "
        "confirm the journal's purpose and supporting evidence."
    ),
    P(
        "Expense bills analysed: 501, totalling INR 168,245,930 excluding GST. "
        "Category and vendor rankings are based on these bills, not added to "
        "ledger P&amp;L."
    ),
    PageBreak(),
]

# Task 12
story += [
    P("Task 12 — Receivables and Cash Movement", "SectionX"),
    P(
        "The receivables ageing mart reconciles exactly to issued open invoices "
        "in fact_invoice. It contains 62 issued open invoices with a balance "
        "of INR 139,394,278."
    ),
    make_table(
        ["Ageing bucket", "Invoices", "Open balance (INR)"],
        [
            ("Not yet due", "49", "112,283,412"),
            ("1–30 days", "10", "22,133,626"),
            ("61–90 days", "1", "1,940,982"),
            ("90+ days", "2", "3,036,258"),
            ("Total", "62", "139,394,278"),
        ], [55*mm, 35*mm, 83*mm]
    ),
    P(
        "A further invoice, INV/2026-27/0217, is in DRAFT status with a balance "
        "of INR 1,028,724. It is correctly excluded from issued open receivables."
    ),
    P("Cash movement", "SubSectionX"),
    P(
        "The monthly cash movement view covers April 2025 to September 2026. "
        "Cash inflows are recorded invoice payments; cash outflows are paid "
        "expenses. Both measures reconcile exactly to their source records "
        "in all 18 months."
    ),
    make_table(
        ["Measure", "Amount (INR)"],
        [
            ("Cash inflows", "1,419,349,558.00"),
            ("Cash outflows", "185,831,316.70"),
            ("Net cash movement", "1,233,518,241.30"),
        ], [75*mm, 98*mm]
    ),
    P(
        "<b>Interpretation:</b> this is a receipts-and-paid-expenses view. "
        "It is not a substitute for accrual-basis profit and loss. Client "
        "payment-speed analysis is presented separately."
    ),
    PageBreak(),
]

# Task 13
story += [
    P("Task 13 — Cross-Department Impact", "SectionX"),
    P(
        "The department-month mart covers April 2025 to September 2026: "
        "198 rows across 11 department IDs. Payroll, attendance, headcount, "
        "leave and task sources were aggregated independently before joining. "
        "Approved leave days are used; overtime cost is represented by overtime "
        "pay. Leave days per head and overtime share are separate measures."
    ),
    P("Coverage and reconciliation", "SubSectionX"),
    P(
        "Payroll, attendance and headcount are populated across all 198 rows. "
        "Task metrics are missing for some department-months and remain NULL, "
        "not zero. D00 appears in the source view but is outside the 10-department "
        "target comparison."
    ),
    P(
        "The attendance mart uses the same half-day credit convention as the "
        "Phase 2 attendance metrics: "
        "<b>100 × (SUM(present_days) + 0.5 × SUM(half_days_unpaid)) / "
        "SUM(scheduled_days)</b>. Against the reference summary, all 198 of "
        "198 rows are within 0.01 percentage points; maximum absolute difference "
        "is 0.005 percentage points. September 2026 values match the reference "
        "at two decimal places. Only the mart calculation was corrected; "
        "attendance source and reference values were not changed."
    ),
    P("September 2026 target findings", "SubSectionX"),
    make_table(
        ["Measure", "Department breaches", "Finding"],
        [
            ("Attendance", "3", "D06 92.43%; D08 88.87%; D10 93.29% (target 94%)"),
            ("Overtime share", "2", "Above departmental target"),
            ("Attrition", "2", "Above departmental target"),
            ("Task completion", "0", "No department with an available target below target"),
        ], [35*mm, 36*mm, 102*mm]
    ),
    P(
        "The executive scorecard reports 94.60% overall attendance with status "
        "Attention. Department-level breaches can coexist with an overall result "
        "above target."
    ),
    P("Payroll reconciliation exceptions", "SubSectionX"),
    P(
        "D08 Finance &amp; Accounts, May 2025: INR 61,813.15 difference associated "
        "with duplicate payroll records for EMP-0598 (PI-000761 and PI-X0002). "
        "D02 Product &amp; Design, February 2026: INR 154,811.89 difference "
        "associated with duplicate payroll records for EMP-0194 "
        "(PI-004059 and PI-X0001). These exceptions are documented rather "
        "than silently adjusted."
    ),
    PageBreak(),
]

# Task 14
story += [
    P("Task 14 — AI Insights and Forecasts", "SectionX"),
    P(
        "The payroll anomaly mart matches fact_anomaly across all 11 reason "
        "codes, including source row counts and flagged counts. Source flag "
        "value is Y. Where money_at_risk is absent in the source, the mart "
        "reports zero."
    ),
    P("Anomaly screening results", "SubSectionX"),
    make_table(
        ["Reason code", "Flags", "Money at risk (INR)"],
        [
            ("STATISTICAL_OUTLIER", "145", "19,432,986.26"),
            ("GROSS_ABOVE_NORM", "13", "9,417,924.27"),
            ("GROSS_BELOW_EXPECTED", "4", "927,063.83"),
            ("NEGATIVE_NET_PAY", "8", "909,114.81"),
            ("ZERO_PAY", "5", "431,262.75"),
            ("OVERTIME_ABOVE_CAP", "8", "272,767.51"),
            ("PF_NOT_DEDUCTED", "1", "30,119.64"),
            ("LONG_UNPAID_ABSENCE", "43", "0.00"),
            ("FREQUENT_LATE", "3", "0.00"),
            ("NO_ATTENDANCE", "50", "0.00"),
            ("PATTERN_SHIFT", "125", "0.00"),
        ], [73*mm, 28*mm, 72*mm]
    ),
    P(
        "<b>Important:</b> anomaly categories can overlap. Monetary amounts "
        "are screening indicators and must not be summed as unique employee "
        "exposure or treated as confirmed fraud or errors. Investigate flags "
        "before taking action."
    ),
    P("Forecasts", "SubSectionX"),
    P(
        "The forecast mart contains 72 rows: six overall monthly attrition "
        "forecasts and 66 headcount forecasts across 11 departments. The "
        "forecast horizon is October 2026 to March 2027, trained through "
        "September 2026. Model provenance is trend-seasonal-baseline-0.1."
    ),
    P(
        "Attrition uses the same-month average of the prior three years. "
        "Headcount uses a 36-month linear trend with half-strength seasonality. "
        "Forecasts are estimates, not actual results, and are labelled for "
        "human review."
    ),
    PageBreak(),
]

# Task 15 and quality
story += [
    P("Task 15 — Executive KPI Scorecard", "SectionX"),
    P(
        "The scorecard contains 144 rows: eight KPIs over 18 months from "
        "April 2025 through September 2026."
    ),
    P("September 2026 snapshot", "SubSectionX"),
    make_table(
        ["KPI", "Actual", "Target", "Status / interpretation"],
        [
            ("Employer cost", "INR 55,519,621.87", "Not defined", "No pass/fail target"),
            ("Revenue", "INR 80,601,695.00", "Not defined", "No pass/fail target"),
            ("Net profit", "INR 14,985,979.13", "Not defined", "No pass/fail target"),
            ("Operating margin", "18.59%", "Not defined", "No pass/fail target"),
            ("Attendance", "94.60%", "94.00%", "Attention"),
            ("Overtime share", "1.17%", "1.50%", "Attention"),
            ("Monthly attrition", "0.34%", "1.00%", "Attention"),
            ("Task completion", "85.65%", "80.00%", "On Track"),
        ], [38*mm, 43*mm, 35*mm, 57*mm]
    ),
    P(
        "Attendance, overtime share and attrition carry Attention because the "
        "scorecard incorporates department-level target breaches. Their overall "
        "values can meet targets while individual departments require review. "
        "Task completion is On Track. Employer cost, revenue, net profit and "
        "operating margin have no target defined; absence of a target is not "
        "a pass/fail result."
    ),
    P("Quality controls and limitations", "SectionX"),
    P(
        "The Phase 3 marts contain 198 department-month rows, 18 monthly cash "
        "rows, 144 executive scorecard rows and 72 forecast rows. Attendance "
        "reconciliation passed for all 198 rows within the stated tolerance. "
        "Cash-in and cash-out reconciled to their source records across all "
        "18 months. Anomaly source counts matched all 11 reason codes."
    ),
    P(
        "Seven automated ETL tests passed in the latest run. The documented "
        "payroll reconciliation exceptions, missing task coverage, manual "
        "journal review and model limitations remain visible rather than "
        "being concealed or converted into unsupported conclusions."
    ),
    P("Dashboards", "SectionX"),
    make_table(
        ["Dashboard", "Charts"],
        [
            ("Receivables & Cash Dashboard", "Ageing, cash movement, client payment speed"),
            ("Department Performance Dashboard", "Attendance, attrition, overtime share, task completion"),
            ("AI Insights & Forecast Dashboard", "Anomaly counts, money at risk, headcount and attrition forecasts"),
            ("Executive Scorecard Dashboard", "Monthly KPI actuals and targets"),
        ], [73*mm, 100*mm]
    ),
    Spacer(1, 7),
    P(
        "<b>Review priorities:</b> obtain Finance review of the INR 18,450 "
        "June 2026 salary-ledger difference; confirm the purpose and support "
        "for journal MJ-0002; investigate documented payroll duplicates; "
        "retain NULL task coverage as missing data; and review anomaly flags "
        "and forecasts with appropriate data owners."
    ),
    Spacer(1, 8),
    P(
        "<b>Report scope:</b> this document consolidates the five Phase 3 "
        "findings reports and the associated warehouse/dashboard validation "
        "results available on 3 November 2026. Forecasts are estimates and "
        "all unresolved reconciliation items remain disclosed."
    , "SmallX"),
]

doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f"PDF created: {OUT}")
print(f"Size: {OUT.stat().st_size:,} bytes")
