import json
import os
import urllib.request
import urllib.error
from pathlib import Path

import pytest
from openpyxl import load_workbook
from pypdf import PdfReader

API = os.getenv("PULSEIQ_API_URL", "http://127.0.0.1:8765")
MONTH = "2026-09"

EXPECTED_ROWS = {
    "pnl": 1,
    "expenses": 11,
    "vendors": 17,
    "departments": 11,
    "scorecard": 8,
}

METRICS = [
    "pnl",
    "expense_categories",
    "vendor_expense",
    "department_month",
    "executive_scorecard",
]


def api_request(path):
    request = urllib.request.Request(f"{API}{path}")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def test_api_health():
    status, body = api_request("/health")
    assert status == 200
    assert body["status"] == "ok"


@pytest.mark.parametrize("metric", METRICS)
def test_metric_endpoint_for_september(metric):
    status, body = api_request(
        f"/metrics/{metric}?month={MONTH}&limit=500"
    )
    assert status == 200
    assert body["metric"] == metric
    assert body["filter_month"] == MONTH
    assert body["row_count"] == len(body["data"])
    assert body["row_count"] > 0


@pytest.mark.parametrize(
    ("path", "expected_status"),
    [
        ("/metrics/unknown_metric", 404),
        ("/metrics/pnl?limit=0", 422),
        ("/metrics/pnl?month=invalid", 422),
    ],
)
def test_api_rejects_invalid_requests(path, expected_status):
    status, _ = api_request(path)
    assert status == expected_status


def test_excel_report_sheets_and_row_counts():
    path = Path("reports/monthly/PulseIQ_Monthly_Report_2026-09.xlsx")
    assert path.exists()

    workbook = load_workbook(path, data_only=True)

    assert workbook.sheetnames == [
        "Cover", "pnl", "expenses", "vendors", "departments", "scorecard"
    ]

    for sheet, expected_count in EXPECTED_ROWS.items():
        worksheet = workbook[sheet]
        assert worksheet.max_row - 1 == expected_count

        headers = [cell.value for cell in worksheet[1]]
        date_column = "month_start" if "month_start" in headers else "month"
        date_index = headers.index(date_column) + 1

        for row_number in range(2, worksheet.max_row + 1):
            value = worksheet.cell(row_number, date_index).value
            assert str(value).startswith(MONTH)


def test_excel_pnl_calculation():
    path = Path("reports/monthly/PulseIQ_Monthly_Report_2026-09.xlsx")
    workbook = load_workbook(path, data_only=True)
    worksheet = workbook["pnl"]

    revenue = float(worksheet["C2"].value)
    expenses = float(worksheet["D2"].value)
    profit = float(worksheet["E2"].value)

    assert abs(revenue - expenses - profit) < 0.01


def test_pdf_report_content():
    path = Path("reports/monthly/PulseIQ_Monthly_Report_2026-09.pdf")
    assert path.exists()

    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    assert len(reader.pages) == 3
    assert MONTH in text
    assert "Employer Cost" in text
    assert "Attendance Rate" in text
