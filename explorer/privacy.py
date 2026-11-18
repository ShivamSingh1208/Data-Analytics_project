import numpy as np
import pandas as pd


def suppress_small_groups(data: pd.DataFrame, minimum: int):
    """Suppress groups with small or invalid group sizes."""

    if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 1:
        raise ValueError("Minimum group size must be a positive integer.")

    if "group_size" not in data.columns:
        raise ValueError("Missing required group_size column.")

    sizes = pd.to_numeric(data["group_size"], errors="coerce")

    # Fail closed: missing, infinite, negative and fractional sizes
    # must never be treated as publishable group sizes.
    valid = (
        sizes.notna()
        & np.isfinite(sizes)
        & sizes.ge(0)
        & sizes.mod(1).eq(0)
    )

    visible_mask = valid & sizes.ge(minimum)
    visible = data.loc[visible_mask].copy()
    hidden = len(data) - len(visible)

    return visible, hidden


# Phase 4: persistent privacy-release controls.
import hashlib
import hmac
from datetime import date, datetime, timedelta, timezone
from typing import Iterable, Mapping

from sqlalchemy import text


class PrivacyBudgetExceeded(ValueError):
    """Raised when a request overlaps a recent privacy release."""


def hash_principal(email: str, secret: str) -> str:
    """Create a keyed identifier without storing the user's email."""
    if not secret or len(secret) < 32:
        raise ValueError(
            "PULSEIQ_PRIVACY_HMAC_KEY must contain at least 32 characters."
        )

    normalized = str(email or "").strip().lower()
    if not normalized:
        raise ValueError("A verified user identity is required.")

    return hmac.new(
        secret.encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def has_recent_overlap(
    history: Iterable[Mapping],
    metric: str,
    department_id: str,
    reporting_month: date,
    now: datetime | None = None,
    lookback_days: int = 90,
) -> bool:
    """Detect same or adjacent-month releases within the lookback window."""
    if isinstance(reporting_month, datetime):
        reporting_month = reporting_month.date()

    if reporting_month.day != 1:
        raise ValueError("reporting_month must be the first day of a month.")

    if lookback_days < 1:
        raise ValueError("lookback_days must be positive.")

    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=lookback_days)

    previous_month = (
        reporting_month - timedelta(days=1)
    ).replace(day=1)

    next_month = (
        reporting_month.replace(day=28) + timedelta(days=4)
    ).replace(day=1)

    upper_exclusive = (
        next_month.replace(day=28) + timedelta(days=4)
    ).replace(day=1)

    for row in history:
        created_at = row["created_at"]
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        released_month = row["reporting_month"]
        if isinstance(released_month, datetime):
            released_month = released_month.date()

        if (
            row["metric"] == metric
            and row["department_id"] == department_id
            and created_at >= cutoff
            and previous_month <= released_month < upper_exclusive
        ):
            return True

    return False


def reserve_release(
    connection,
    principal_hash: str,
    metric: str,
    department_ids: list[str],
    reporting_month: date,
) -> None:
    """Atomically reserve all visible department releases or reject the request."""

    if (
        not isinstance(principal_hash, str)
        or len(principal_hash) != 64
        or any(char not in "0123456789abcdef" for char in principal_hash)
    ):
        raise ValueError("principal_hash must be a 64-character SHA-256 hex digest.")

    if not isinstance(metric, str) or not metric.strip():
        raise ValueError("Metric must be a non-empty string.")

    metric = metric.strip()

    if (
        not isinstance(reporting_month, date)
        or isinstance(reporting_month, datetime)
        or reporting_month.day != 1
    ):
        raise ValueError("reporting_month must be the first day of a month.")

    if not isinstance(department_ids, (list, tuple)):
        raise ValueError("Department identifiers must be a list or tuple.")

    if not department_ids:
        raise PrivacyBudgetExceeded(
            "No eligible department groups were found."
        )

    if any(
        not isinstance(department, str) or not department.strip()
        for department in department_ids
    ):
        raise ValueError("Department identifiers must be non-empty strings.")

    departments = sorted({department.strip() for department in department_ids})

    lock_key = f"pulseiq:global-privacy:{metric}"

    # Serialize overlapping requests across all authorized users.
    connection.execute(
        text(
            "SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"
        ),
        {"lock_key": lock_key},
    )

    for department_id in departments:
        existing = connection.execute(
            text("""
                SELECT 1
                FROM dw.privacy_query_log
                WHERE metric = :metric
                  AND department_id = :department_id
                  AND reporting_month BETWEEN
                      (CAST(:reporting_month AS date) - INTERVAL '1 month')::date
                      AND
                      (CAST(:reporting_month AS date) + INTERVAL '1 month')::date
                  AND created_at >= NOW() - INTERVAL '90 days'
                LIMIT 1
            """),
            {
                "metric": metric,
                "department_id": department_id,
                "reporting_month": reporting_month,
            },
        ).first()

        if existing:
            raise PrivacyBudgetExceeded(
                "This metric and department were already released for "
                "the same or an adjacent month within the last 90 days."
            )

    connection.execute(
        text("""
            INSERT INTO dw.privacy_query_log
                (principal_hash, metric, department_id, reporting_month)
            VALUES
                (:principal_hash, :metric, :department_id, :reporting_month)
        """),
        [
            {
                "principal_hash": principal_hash,
                "metric": metric,
                "department_id": department_id,
                "reporting_month": reporting_month,
            }
            for department_id in departments
        ],
    )
