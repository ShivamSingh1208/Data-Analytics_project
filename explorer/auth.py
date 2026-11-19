"""Fail-closed OIDC identity and role authorization helpers."""
from __future__ import annotations

import json
import re
from typing import Any

ROLES = {"ADMIN", "HR", "MANAGER", "EXECUTIVE"}
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class AuthorizationError(ValueError):
    """Raised when an authenticated identity has no valid authorization."""


def parse_user_assignments(raw: str) -> dict[str, dict[str, str]]:
    """Parse an explicit email-to-role JSON map; no wildcard/default role."""
    if not raw or not raw.strip():
        raise AuthorizationError("PULSEIQ_USER_ROLES is not configured.")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AuthorizationError("PULSEIQ_USER_ROLES must contain valid JSON.") from exc
    if not isinstance(payload, dict) or not payload:
        raise AuthorizationError("PULSEIQ_USER_ROLES must be a non-empty JSON object.")

    assignments: dict[str, dict[str, str]] = {}
    for email, details in payload.items():
        normalized_email = str(email).strip().lower()
        if not _EMAIL_RE.fullmatch(normalized_email):
            raise AuthorizationError("Every role assignment must use a valid email address.")
        if not isinstance(details, dict):
            raise AuthorizationError("Each role assignment must be a JSON object.")
        role = str(details.get("role", "")).strip().upper()
        if role not in ROLES:
            raise AuthorizationError(f"Unsupported role assignment for {normalized_email}.")
        department = str(details.get("department_id", "")).strip().upper()
        if role == "MANAGER" and not department:
            raise AuthorizationError("Every MANAGER assignment requires department_id.")
        if role != "MANAGER" and department:
            raise AuthorizationError("department_id is only valid for MANAGER assignments.")
        assignments[normalized_email] = {"role": role, "department_id": department}
    return assignments


def authorize_identity(email: Any, email_verified: Any, assignments: dict[str, dict[str, str]]) -> dict[str, str]:
    """Authorize a verified OIDC email against an explicit allowlist."""
    normalized_email = str(email or "").strip().lower()
    if email_verified is not True:
        raise AuthorizationError("The identity provider did not verify this email address.")
    if not _EMAIL_RE.fullmatch(normalized_email):
        raise AuthorizationError("The identity provider did not supply a valid email address.")
    assignment = assignments.get(normalized_email)
    if assignment is None:
        raise AuthorizationError("This account is not approved to access PulseIQ.")
    # Return a copy so callers cannot mutate the configured policy.
    return {"email": normalized_email, **assignment}
