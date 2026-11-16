import os
import re
from datetime import date, datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import create_engine, inspect, text

URL = os.getenv("DATABASE_URL")

if not URL:
    raise RuntimeError("DATABASE_URL must be configured.")

engine = create_engine(URL, pool_pre_ping=True)

app = FastAPI(
    title="PulseIQ Metrics API",
    version="1.1.0"
)

VIEWS = {
    "pnl": os.getenv("VIEW_PNL", "dw.metric_pnl_monthly"),
    "expense_categories": os.getenv(
        "VIEW_EXPENSES", "dw.metric_expense_category"
    ),
    "vendor_expense": os.getenv(
        "VIEW_VENDORS", "dw.metric_vendor_expense"
    ),
    "department_month": os.getenv(
        "VIEW_DEPARTMENT", "dw.metric_phase3_department_month"
    ),
    "executive_scorecard": os.getenv(
        "VIEW_SCORECARD", "dw.metric_phase3_executive_scorecard"
    ),
}

DEFS = {
    "pnl": "Monthly revenue, expenses and net profit.",
    "expense_categories": "Expense-bill category totals excluding GST.",
    "vendor_expense": "Expense-bill totals by vendor excluding GST.",
    "department_month": "Department-month aggregate workforce metrics.",
    "executive_scorecard": "Executive KPI actuals and targets.",
}

DATE_COLUMNS = {
    "pnl": "month_start",
    "expense_categories": "month_start",
    "vendor_expense": "month_start",
    "department_month": "month",
    "executive_scorecard": "month",
}

SORT_COLUMNS = {
    "pnl": ["financial_year"],
    "expense_categories": ["account_code", "expense_category"],
    "vendor_expense": ["vendor_id"],
    "department_month": ["department_id"],
    "executive_scorecard": ["kpi_code"],
}


def quoted_identifier(value):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise HTTPException(500, "Invalid SQL identifier")
    return '"' + value + '"'


def quoted_view(value):
    parts = value.split(".")
    if len(parts) != 2:
        raise HTTPException(500, "Invalid configured view")
    return ".".join(quoted_identifier(x) for x in parts)


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "checked_at": datetime.now(timezone.utc).isoformat()
        }

    except Exception:
        raise HTTPException(503, "Warehouse unavailable")


@app.get("/metrics")
def catalogue():
    return [
        {
            "metric": key,
            "definition": DEFS[key],
            "source": view,
            "freshness": "Queried live per request"
        }
        for key, view in VIEWS.items()
    ]


@app.get("/metrics/{metric}")
def read_metric(
    metric: str,
    limit: int = Query(100, ge=1, le=500),
    month: str | None = Query(
        None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$"
    ),
):
    if metric not in VIEWS:
        raise HTTPException(404, "Unknown metric")

    view = VIEWS[metric]
    schema, table = view.split(".")

    columns = inspect(engine).get_columns(table, schema=schema)
    available = {column["name"] for column in columns}

    if not available:
        raise HTTPException(503, f"Configured view {view} does not exist")

    date_column = DATE_COLUMNS[metric]

    if date_column not in available:
        raise HTTPException(
            503,
            f"Expected date column {date_column} is missing"
        )

    query = f"SELECT * FROM {quoted_view(view)}"
    params = {"n": limit}

    if month:
        year, month_number = map(int, month.split("-"))
        start = date(year, month_number, 1)

        if month_number == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month_number + 1, 1)

        query += (
            f" WHERE {quoted_identifier(date_column)} >= :start"
            f" AND {quoted_identifier(date_column)} < :end"
        )

        params.update({"start": start, "end": end})

    sort_columns = [date_column]

    for column in SORT_COLUMNS[metric]:
        if column in available:
            sort_columns.append(column)

    order_clause = ", ".join(
        quoted_identifier(column) + (
            " DESC" if column == date_column else " ASC"
        )
        for column in sort_columns
    )

    query += f" ORDER BY {order_clause} LIMIT :n"

    with engine.connect() as connection:
        rows = connection.execute(
            text(query), params
        ).mappings().all()

    return {
        "metric": metric,
        "definition": DEFS[metric],
        "source": view,
        "queried_at": datetime.now(timezone.utc).isoformat(),
        "filter_month": month,
        "row_count": len(rows),
        "data": [dict(row) for row in rows],
    }
