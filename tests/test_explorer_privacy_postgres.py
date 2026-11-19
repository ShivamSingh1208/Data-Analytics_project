"""Real PostgreSQL integration tests for the privacy release ledger."""
import os
import uuid
from calendar import monthrange
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier

import pytest
from sqlalchemy import create_engine, text

from explorer.privacy import PrivacyBudgetExceeded, reserve_release


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def shift_month(month, offset):
    index = month.year * 12 + month.month - 1 + offset
    year, month_number = divmod(index, 12)
    month_number += 1
    return date(year, month_number, 1)


@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

    # Fail closed: never run these tests against another database.
    if (
        engine.url.host != "127.0.0.1"
        or engine.url.port != 5545
        or engine.url.database != "pulseiq_privacy_test"
        or engine.url.username != "pulseiq_test_runtime"
    ):
        engine.dispose()
        raise RuntimeError(
            "Integration tests are restricted to the isolated "
            "PostgreSQL test database on 127.0.0.1:5545."
        )

    with engine.connect() as connection:
        exists = connection.execute(
            text("SELECT to_regclass('dw.privacy_query_log')")
        ).scalar()

    if exists is None:
        engine.dispose()
        raise RuntimeError("Apply the privacy migration before testing.")

    yield engine
    engine.dispose()


def new_principal():
    return uuid.uuid4().hex * 2


def ledger_rows(engine, principal):
    with engine.connect() as connection:
        return connection.execute(
            text("""
                SELECT department_id, reporting_month
                FROM dw.privacy_query_log
                WHERE principal_hash = :principal
                ORDER BY department_id
            """),
            {"principal": principal},
        ).all()


def test_postgres_inserts_all_unique_departments(db_engine):
    principal = new_principal()
    month = date.today().replace(day=1)
    metric = "Attendance-" + uuid.uuid4().hex

    with db_engine.begin() as connection:
        reserve_release(
            connection,
            principal,
            metric,
            ["D02", "D01", "D01"],
            month,
        )

    rows = ledger_rows(db_engine, principal)

    assert len(rows) == 2
    assert [row.department_id for row in rows] == ["D01", "D02"]
    assert all(row.reporting_month == month for row in rows)


@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_postgres_global_scope_rejects_different_principal(
    db_engine, offset
):
    first_principal = new_principal()
    second_principal = new_principal()
    metric = "Attendance-" + uuid.uuid4().hex
    target_month = date.today().replace(day=1)
    previous_release = shift_month(target_month, offset)

    with db_engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO dw.privacy_query_log
                    (principal_hash, metric, department_id, reporting_month)
                VALUES
                    (:principal, :metric, 'D01', :month)
            """),
            {
                "principal": first_principal,
                "metric": metric,
                "month": previous_release,
            },
        )

    with pytest.raises(PrivacyBudgetExceeded):
        with db_engine.begin() as connection:
            reserve_release(
                connection,
                second_principal,
                metric,
                ["D01"],
                target_month,
            )


def test_postgres_transaction_rollback_removes_reservation(db_engine):
    principal = new_principal()
    metric = "Attendance-" + uuid.uuid4().hex
    month = date.today().replace(day=1)

    with pytest.raises(RuntimeError, match="simulate application failure"):
        with db_engine.begin() as connection:
            reserve_release(
                connection,
                principal,
                metric,
                ["D01", "D02"],
                month,
            )
            raise RuntimeError("simulate application failure")

    assert ledger_rows(db_engine, principal) == []


def test_postgres_concurrent_requests_allow_only_one_release(db_engine):
    principal = new_principal()
    month = date.today().replace(day=1)
    metric = "Attendance-" + uuid.uuid4().hex
    barrier = Barrier(2)

    def attempt_release():
        with db_engine.begin() as connection:
            barrier.wait(timeout=15)
            reserve_release(
                connection,
                principal,
                metric,
                ["D01"],
                month,
            )
        return "released"

    def safe_attempt():
        try:
            return attempt_release()
        except PrivacyBudgetExceeded:
            return "blocked"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: safe_attempt(), range(2)))

    assert sorted(results) == ["blocked", "released"]
    assert len(ledger_rows(db_engine, principal)) == 1


def test_postgres_concurrent_different_principals_allow_only_one_release(
    db_engine,
):
    month = date.today().replace(day=1)
    metric = "Attendance-" + uuid.uuid4().hex
    principals = [new_principal(), new_principal()]
    barrier = Barrier(2)

    def attempt(principal):
        try:
            with db_engine.begin() as connection:
                barrier.wait(timeout=15)
                reserve_release(
                    connection, principal, metric, ["D01"], month
                )
            return "released"
        except PrivacyBudgetExceeded:
            return "blocked"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, principals))

    assert sorted(results) == ["blocked", "released"]
