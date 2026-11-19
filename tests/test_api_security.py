import json
import os
import time
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://unused:unused@localhost/unused",
)

from api import main
from api import security


@pytest.fixture
def client():
    main.app.dependency_overrides.clear()

    # Install test-only session middleware when local API secrets are absent.
    if not any(
        middleware.cls is SessionMiddleware
        for middleware in main.app.user_middleware
    ):
        main.app.add_middleware(
            SessionMiddleware,
            secret_key="test-only-session-secret",
            session_cookie=security.SESSION_NAME,
            https_only=False,
        )

    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()


def identity(role="ADMIN", department_id=""):
    return {
        "email": "approved@example.com",
        "role": role,
        "department_id": department_id,
    }


def test_metrics_catalogue_rejects_unauthenticated_request(client):
    response = client.get("/metrics")
    assert response.status_code == 401


def test_metric_endpoint_rejects_unauthenticated_request(client):
    response = client.get("/metrics/pnl")
    assert response.status_code == 401


@pytest.mark.parametrize("role", ["ADMIN", "EXECUTIVE"])
def test_admin_and_executive_can_see_all_metrics(client, role):
    main.app.dependency_overrides[security.get_current_identity] = (
        lambda: identity(role)
    )
    response = client.get("/metrics")
    assert response.status_code == 200
    assert {item["metric"] for item in response.json()} == set(main.VIEWS)


@pytest.mark.parametrize("role", ["HR", "MANAGER"])
def test_hr_and_manager_catalogue_is_limited(client, role):
    main.app.dependency_overrides[security.get_current_identity] = (
        lambda: identity(role, "D01" if role == "MANAGER" else "")
    )
    response = client.get("/metrics")
    assert response.status_code == 200
    assert [item["metric"] for item in response.json()] == [
        "department_month"
    ]


@pytest.mark.parametrize("role", ["HR", "MANAGER"])
def test_hr_and_manager_cannot_read_finance_metrics(client, role):
    main.app.dependency_overrides[security.get_current_identity] = (
        lambda: identity(role, "D01" if role == "MANAGER" else "")
    )
    response = client.get("/metrics/pnl")
    assert response.status_code == 403


def test_unknown_role_is_rejected():
    with pytest.raises(Exception) as exc:
        security.get_allowed_api_metrics("UNKNOWN")
    assert getattr(exc.value, "status_code", None) == 403


def make_request(session):
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/metrics",
        "headers": [],
        "query_string": b"",
        "server": ("testserver", 80),
        "client": ("testclient", 12345),
        "scheme": "http",
        "session": session,
    }
    return Request(scope)


def test_current_identity_accepts_verified_allowlisted_user(monkeypatch):
    monkeypatch.setenv(
        "PULSEIQ_USER_ROLES",
        json.dumps({
            "approved@example.com": {"role": "ADMIN"}
        }),
    )
    request = make_request({
        "pulseiq_identity": {
            "email": "approved@example.com",
            "email_verified": True,
            "expires_at": int(time.time()) + 300,
        }
    })
    result = security.get_current_identity(request)
    assert result["role"] == "ADMIN"


def test_current_identity_rejects_expired_session():
    session = {
        "pulseiq_identity": {
            "email": "approved@example.com",
            "email_verified": True,
            "expires_at": int(time.time()) - 1,
        }
    }
    request = make_request(session)
    with pytest.raises(Exception) as exc:
        security.get_current_identity(request)
    assert getattr(exc.value, "status_code", None) == 401
    assert session == {}


def test_current_identity_rejects_user_removed_from_allowlist(monkeypatch):
    monkeypatch.setenv(
        "PULSEIQ_USER_ROLES",
        json.dumps({
            "another@example.com": {"role": "ADMIN"}
        }),
    )
    session = {
        "pulseiq_identity": {
            "email": "approved@example.com",
            "email_verified": True,
            "expires_at": int(time.time()) + 300,
        }
    }
    request = make_request(session)
    with pytest.raises(Exception) as exc:
        security.get_current_identity(request)
    assert getattr(exc.value, "status_code", None) == 403
    assert session == {}


def test_department_metric_rejects_historical_month_filter(client):
    main.app.dependency_overrides[security.get_current_identity] = (
        lambda: identity("MANAGER", "D01")
    )
    response = client.get(
        "/metrics/department_month?measure=Headcount&month=2026-09"
    )
    assert response.status_code == 400
    assert "Historical month filters are disabled" in response.json()["detail"]


def test_manager_query_is_scoped_and_privacy_protected(
    client, monkeypatch
):
    from datetime import date

    main.app.dependency_overrides[security.get_current_identity] = (
        lambda: identity("MANAGER", "D01")
    )
    monkeypatch.setenv("PULSEIQ_PRIVACY_HMAC_KEY", "x" * 40)

    inspector = MagicMock()
    inspector.get_columns.return_value = [
        {"name": "month"},
        {"name": "department_id"},
        {"name": "headcount_end"},
    ]
    monkeypatch.setattr(main, "inspect", lambda engine: inspector)
    monkeypatch.setattr(main, "hash_principal", lambda email, key: "a" * 64)

    reservation = MagicMock()
    monkeypatch.setattr(main, "reserve_release", reservation)

    rows_result = MagicMock()
    rows_result.mappings.return_value.all.return_value = [
        {
            "reporting_month": date(2026, 9, 1),
            "department_id": "D01",
            "metric_value": 12,
            "group_size": 12,
        }
    ]

    connection = MagicMock()
    connection.execute.return_value = rows_result

    connect_context = MagicMock()
    connect_context.__enter__.return_value = connection
    connect_context.__exit__.return_value = False

    ledger_connection = MagicMock()
    begin_context = MagicMock()
    begin_context.__enter__.return_value = ledger_connection
    begin_context.__exit__.return_value = False

    fake_engine = MagicMock()
    fake_engine.connect.return_value = connect_context
    fake_engine.begin.return_value = begin_context
    monkeypatch.setattr(main, "engine", fake_engine)

    response = client.get(
        "/metrics/department_month?measure=Headcount"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["measure"] == "Headcount"
    assert body["filter_month"] == "2026-09-01"
    assert body["data"] == [
        {"department_id": "D01", "metric_value": 12}
    ]
    assert "group_size" not in str(body)

    executed_query, parameters = connection.execute.call_args.args
    query_text = str(executed_query)
    assert "WITH latest AS" in query_text
    assert "latest.reporting_month" in query_text
    assert 'department_data."department_id" = :department_id' in query_text
    assert parameters["department_id"] == "D01"
    assert connection.execute.call_count == 1

    reservation.assert_called_once()
    reserved = reservation.call_args.kwargs
    assert reserved["metric"] == "Headcount"
    assert reserved["department_ids"] == ["D01"]
    assert reserved["reporting_month"] == date(2026, 9, 1)


def test_manager_scope_fails_closed_if_department_column_missing(
    client, monkeypatch
):
    main.app.dependency_overrides[security.get_current_identity] = (
        lambda: identity("MANAGER", "D01")
    )

    inspector = MagicMock()
    inspector.get_columns.return_value = [
        {"name": "month"},
        {"name": "headcount_end"},
    ]
    monkeypatch.setattr(main, "inspect", lambda engine: inspector)

    response = client.get(
        "/metrics/department_month?measure=Headcount"
    )
    assert response.status_code == 503


def test_department_metric_suppresses_small_groups_before_reservation(
    client, monkeypatch
):
    from datetime import date

    main.app.dependency_overrides[security.get_current_identity] = (
        lambda: identity("MANAGER", "D01")
    )
    monkeypatch.setenv("PULSEIQ_PRIVACY_HMAC_KEY", "x" * 40)
    monkeypatch.setattr(main, "hash_principal", lambda email, key: "b" * 64)

    inspector = MagicMock()
    inspector.get_columns.return_value = [
        {"name": "month"},
        {"name": "department_id"},
        {"name": "headcount_end"},
    ]
    monkeypatch.setattr(main, "inspect", lambda engine: inspector)

    rows_result = MagicMock()
    rows_result.mappings.return_value.all.return_value = [
        {
            "reporting_month": date(2026, 9, 1),
            "department_id": "D01",
            "metric_value": 4,
            "group_size": 4,
        }
    ]

    connection = MagicMock()
    connection.execute.return_value = rows_result

    connect_context = MagicMock()
    connect_context.__enter__.return_value = connection
    connect_context.__exit__.return_value = False

    fake_engine = MagicMock()
    fake_engine.connect.return_value = connect_context
    monkeypatch.setattr(main, "engine", fake_engine)

    reservation = MagicMock()
    monkeypatch.setattr(main, "reserve_release", reservation)

    response = client.get(
        "/metrics/department_month?measure=Headcount"
    )

    assert response.status_code == 200
    assert response.json()["row_count"] == 0
    assert response.json()["data"] == []
    reservation.assert_not_called()


def test_department_metric_requires_measure_before_database_inspection(
    client, monkeypatch
):
    main.app.dependency_overrides[security.get_current_identity] = (
        lambda: identity("ADMIN")
    )

    def unexpected_inspection(_engine):
        raise AssertionError("Database inspection should not run")

    monkeypatch.setattr(main, "inspect", unexpected_inspection)

    response = client.get("/metrics/department_month")
    assert response.status_code == 400
    assert "Provide one valid measure" in response.json()["detail"]


def test_department_metric_rejects_unauthorized_measure_before_database_inspection(
    client, monkeypatch
):
    main.app.dependency_overrides[security.get_current_identity] = (
        lambda: identity("HR")
    )

    def unexpected_inspection(_engine):
        raise AssertionError("Database inspection should not run")

    monkeypatch.setattr(main, "inspect", unexpected_inspection)

    response = client.get(
        "/metrics/department_month?measure=Employer%20cost"
    )
    assert response.status_code == 403


def test_manager_without_department_is_rejected_before_database_inspection(
    client, monkeypatch
):
    main.app.dependency_overrides[security.get_current_identity] = (
        lambda: identity("MANAGER")
    )

    def unexpected_inspection(_engine):
        raise AssertionError("Database inspection should not run")

    monkeypatch.setattr(main, "inspect", unexpected_inspection)

    response = client.get(
        "/metrics/department_month?measure=Headcount"
    )
    assert response.status_code == 403
    assert "department assignment is missing" in response.json()["detail"]
