import os
import re
from datetime import date, datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import create_engine, inspect, text
import pandas as pd
from explorer.access import METRIC_COLUMNS, get_allowed_metrics
from explorer.privacy import (
    PrivacyBudgetExceeded,
    hash_principal,
    reserve_release,
    suppress_small_groups,
)

URL = os.getenv("DATABASE_URL")

if not URL:
    raise RuntimeError("DATABASE_URL must be configured.")

engine = create_engine(URL, pool_pre_ping=True)

app = FastAPI(
    title="PulseIQ Metrics API",
    version="1.1.0"
)

from api.security import (
    get_allowed_api_metrics,
    get_current_identity,
    install_api_auth,
)

install_api_auth(app)

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
def catalogue(identity: dict = Depends(get_current_identity)):
    allowed_metrics = get_allowed_api_metrics(identity["role"])
    return [
        {
            "metric": key,
            "definition": DEFS[key],
            "source": view,
            "freshness": "Queried live per request"
        }
        for key, view in VIEWS.items()
        if key in allowed_metrics
    ]


@app.get("/metrics/{metric}")
def read_metric(
    metric: str,
    limit: int = Query(100, ge=1, le=500),
    month: str | None = Query(
        None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$"
    ),
    measure: str | None = Query(None),
    identity: dict = Depends(get_current_identity),
):
    if metric not in VIEWS:
        raise HTTPException(404, "Unknown metric")

    allowed_metrics = get_allowed_api_metrics(identity["role"])
    if metric not in allowed_metrics:
        raise HTTPException(403, "Your role is not authorized for this metric.")

    # Reject unsupported historical department queries before any DB access.
    if metric == "department_month" and month is not None:
        raise HTTPException(
            400,
            "Historical month filters are disabled for department metrics."
        )

    # Validate department access and privacy configuration before DB inspection.
    if metric == "department_month":
        if not measure or measure not in METRIC_COLUMNS:
            raise HTTPException(
                400,
                "Provide one valid measure: " + ", ".join(METRIC_COLUMNS)
            )

        try:
            role_measures = get_allowed_metrics(identity["role"])
        except ValueError as exc:
            raise HTTPException(403, "Role is not authorized.") from exc

        if measure not in role_measures:
            raise HTTPException(
                403, "Your role is not authorized for this measure."
            )

        if identity["role"] == "MANAGER" and not identity.get("department_id"):
            raise HTTPException(
                403, "Manager department assignment is missing."
            )

        column, minimum, unit = METRIC_COLUMNS[measure]
        privacy_key = os.getenv("PULSEIQ_PRIVACY_HMAC_KEY", "")
        try:
            principal_hash = hash_principal(identity.get("email"), privacy_key)
        except ValueError as exc:
            raise HTTPException(
                503, "API privacy security is not configured."
            ) from exc

    view = VIEWS[metric]
    schema, table = view.split(".")
    columns = inspect(engine).get_columns(table, schema=schema)
    available = {column["name"] for column in columns}

    if not available:
        raise HTTPException(503, f"Configured view {view} does not exist")

    date_column = DATE_COLUMNS[metric]
    if date_column not in available:
        raise HTTPException(503, f"Expected date column {date_column} is missing")

    if metric == "department_month":
        required_columns = {"month", "department_id", "headcount_end", column}
        if not required_columns.issubset(available):
            raise HTTPException(
                503, "Required privacy-protected department columns are missing."
            )

        params = {}
        manager_join_filter = ""
        if identity["role"] == "MANAGER":
            manager_join_filter = (
                f" AND department_data.{quoted_identifier('department_id')} "
                "= :department_id"
            )
            params["department_id"] = identity["department_id"]

        # Read the reporting month and its rows from one statement/snapshot.
        query = f"""
            WITH latest AS (
                SELECT MAX({quoted_identifier('month')}) AS reporting_month
                FROM {quoted_view(view)}
            )
            SELECT
                latest.reporting_month AS reporting_month,
                department_data.{quoted_identifier('department_id')} AS department_id,
                department_data.{quoted_identifier(column)} AS metric_value,
                COALESCE(
                    department_data.{quoted_identifier('headcount_end')}, 0
                ) AS group_size
            FROM latest
            LEFT JOIN {quoted_view(view)} AS department_data
                ON department_data.{quoted_identifier('month')}
                    = latest.reporting_month
                {manager_join_filter}
            ORDER BY department_data.{quoted_identifier('department_id')}
        """

        try:
            with engine.connect() as connection:
                rows = connection.execute(
                    text(query), params
                ).mappings().all()

            raw_rows = [dict(row) for row in rows]
            cutoff = (
                raw_rows[0]["reporting_month"] if raw_rows else None
            )

            if cutoff is None:
                return {
                    "metric": metric,
                    "measure": measure,
                    "unit": unit,
                    "definition": DEFS[metric],
                    "source": view,
                    "filter_month": None,
                    "row_count": 0,
                    "data": [],
                }

            frame = pd.DataFrame([
                {
                    "department_id": row["department_id"],
                    "metric_value": row["metric_value"],
                    "group_size": row["group_size"],
                }
                for row in raw_rows
                if row["department_id"] is not None
            ])
            if frame.empty:
                safe = frame
            else:
                safe, _hidden = suppress_small_groups(frame, minimum)

            if safe.empty:
                return {
                    "metric": metric,
                    "measure": measure,
                    "unit": unit,
                    "definition": DEFS[metric],
                    "source": view,
                    "filter_month": cutoff.isoformat(),
                    "row_count": 0,
                    "data": [],
                }

            department_ids = safe["department_id"].astype(str).tolist()

            # Reserve all visible groups atomically before any data is returned.
            with engine.begin() as ledger_connection:
                reserve_release(
                    connection=ledger_connection,
                    principal_hash=principal_hash,
                    metric=measure,
                    department_ids=department_ids,
                    reporting_month=cutoff,
                )

        except PrivacyBudgetExceeded as exc:
            raise HTTPException(
                429,
                "This measure and department have already been released "
                "for the same or an adjacent month within the last 90 days. "
                "No data was returned."
            ) from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                503,
                "Privacy validation or release-ledger reservation failed. "
                "No data was returned."
            ) from exc

        # Do not return group_size or any other unapproved view columns.
        safe_data = safe[["department_id", "metric_value"]].to_dict(
            orient="records"
        )
        return {
            "metric": metric,
            "measure": measure,
            "unit": unit,
            "definition": DEFS[metric],
            "source": view,
            "queried_at": datetime.now(timezone.utc).isoformat(),
            "filter_month": cutoff.isoformat(),
            "row_count": len(safe_data),
            "data": safe_data,
        }

    if measure is not None:
        raise HTTPException(
            400, "The measure parameter is only valid for department_month."
        )

    query = f"SELECT * FROM {quoted_view(view)}"
    params = {"n": limit}
    filters = []

    if month:
        year, month_number = map(int, month.split("-"))
        start_date = date(year, month_number, 1)
        end_date = (
            date(year + 1, 1, 1)
            if month_number == 12
            else date(year, month_number + 1, 1)
        )
        filters.append(
            f"{quoted_identifier(date_column)} >= :start"
            f" AND {quoted_identifier(date_column)} < :end"
        )
        params.update({"start": start_date, "end": end_date})

    if identity["role"] == "MANAGER":
        if "department_id" not in available:
            raise HTTPException(
                503, "Department scope column is missing from the configured view."
            )
        filters.append(
            f"{quoted_identifier('department_id')} = :department_id"
        )
        params["department_id"] = identity["department_id"]

    if filters:
        query += " WHERE " + " AND ".join(f"({item})" for item in filters)

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
        rows = connection.execute(text(query), params).mappings().all()

    return {
        "metric": metric,
        "definition": DEFS[metric],
        "source": view,
        "queried_at": datetime.now(timezone.utc).isoformat(),
        "filter_month": month,
        "row_count": len(rows),
        "data": [dict(row) for row in rows],
    }
