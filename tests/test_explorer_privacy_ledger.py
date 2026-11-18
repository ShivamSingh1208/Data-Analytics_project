from datetime import date, datetime, timezone

import pytest

from explorer.privacy import (
    hash_principal,
    has_recent_overlap,
    PrivacyBudgetExceeded,
    reserve_release,
)


def test_hash_principal_normalizes_email():
    secret = "a" * 40
    assert hash_principal(" USER@example.com ", secret) == hash_principal(
        "user@example.com", secret
    )


def test_hash_principal_does_not_return_email():
    result = hash_principal("user@example.com", "a" * 40)
    assert result != "user@example.com"
    assert len(result) == 64


def test_hash_principal_rejects_short_secret():
    with pytest.raises(ValueError):
        hash_principal("user@example.com", "short")


def test_hash_principal_rejects_empty_email():
    with pytest.raises(ValueError):
        hash_principal("", "a" * 40)


def test_same_month_release_is_detected():
    history = [{
        "metric": "Attendance",
        "department_id": "D01",
        "reporting_month": date(2026, 9, 1),
        "created_at": datetime(2026, 9, 10, tzinfo=timezone.utc),
    }]
    assert has_recent_overlap(
        history, "Attendance", "D01",
        date(2026, 9, 1),
        now=datetime(2026, 9, 15, tzinfo=timezone.utc),
    )


def test_previous_adjacent_month_release_is_detected():
    history = [{
        "metric": "Attendance",
        "department_id": "D01",
        "reporting_month": date(2026, 8, 1),
        "created_at": datetime(2026, 9, 10, tzinfo=timezone.utc),
    }]
    assert has_recent_overlap(
        history, "Attendance", "D01",
        date(2026, 9, 1),
        now=datetime(2026, 9, 15, tzinfo=timezone.utc),
    )


def test_next_adjacent_month_release_is_detected():
    history = [{
        "metric": "Attendance",
        "department_id": "D01",
        "reporting_month": date(2026, 10, 1),
        "created_at": datetime(2026, 9, 10, tzinfo=timezone.utc),
    }]
    assert has_recent_overlap(
        history, "Attendance", "D01",
        date(2026, 9, 1),
        now=datetime(2026, 9, 15, tzinfo=timezone.utc),
    )


def test_different_metric_does_not_overlap():
    history = [{
        "metric": "Headcount",
        "department_id": "D01",
        "reporting_month": date(2026, 9, 1),
        "created_at": datetime(2026, 9, 10, tzinfo=timezone.utc),
    }]
    assert not has_recent_overlap(
        history, "Attendance", "D01",
        date(2026, 9, 1),
        now=datetime(2026, 9, 15, tzinfo=timezone.utc),
    )


def test_different_department_does_not_overlap():
    history = [{
        "metric": "Attendance",
        "department_id": "D02",
        "reporting_month": date(2026, 9, 1),
        "created_at": datetime(2026, 9, 10, tzinfo=timezone.utc),
    }]
    assert not has_recent_overlap(
        history, "Attendance", "D01",
        date(2026, 9, 1),
        now=datetime(2026, 9, 15, tzinfo=timezone.utc),
    )


def test_release_older_than_90_days_does_not_overlap():
    history = [{
        "metric": "Attendance",
        "department_id": "D01",
        "reporting_month": date(2026, 9, 1),
        "created_at": datetime(2026, 5, 1, tzinfo=timezone.utc),
    }]
    assert not has_recent_overlap(
        history, "Attendance", "D01",
        date(2026, 9, 1),
        now=datetime(2026, 9, 15, tzinfo=timezone.utc),
    )


def test_reporting_month_must_be_first_day():
    with pytest.raises(ValueError):
        has_recent_overlap(
            [], "Attendance", "D01", date(2026, 9, 15)
        )


def test_empty_department_release_is_rejected():
    assert issubclass(PrivacyBudgetExceeded, ValueError)


@pytest.mark.parametrize(
    "principal",
    [None, "", "short", "g" * 64, "A" * 64],
)
def test_reserve_release_rejects_invalid_principal_hash(principal):
    with pytest.raises(ValueError, match="principal_hash"):
        reserve_release(
            None, principal, "Attendance", ["D01"], date(2026, 9, 1)
        )


@pytest.mark.parametrize("metric", [None, "", "   "])
def test_reserve_release_rejects_invalid_metric(metric):
    with pytest.raises(ValueError, match="Metric"):
        reserve_release(
            None, "a" * 64, metric, ["D01"], date(2026, 9, 1)
        )


def test_reserve_release_rejects_datetime_reporting_month():
    with pytest.raises(ValueError, match="reporting_month"):
        reserve_release(
            None,
            "a" * 64,
            "Attendance",
            ["D01"],
            datetime(2026, 9, 1, tzinfo=timezone.utc),
        )


def test_reserve_release_rejects_invalid_department_collection():
    with pytest.raises(ValueError, match="list or tuple"):
        reserve_release(
            None, "a" * 64, "Attendance", None, date(2026, 9, 1)
        )


def test_reserve_release_rejects_blank_department_identifier():
    with pytest.raises(ValueError, match="non-empty strings"):
        reserve_release(
            None, "a" * 64, "Attendance", [" "], date(2026, 9, 1)
        )
