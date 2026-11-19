"""Google OIDC authentication and signed sessions for the PulseIQ Metrics API."""
from __future__ import annotations

import os
import time

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from explorer.auth import (
    AuthorizationError,
    authorize_identity,
    parse_user_assignments,
)

SESSION_NAME = "pulseiq_api_session"
SESSION_MAX_AGE = 3600


def install_api_auth(app) -> None:
    """Register OIDC routes and secure session middleware."""
    session_secret = os.getenv("API_SESSION_SECRET")
    client_id = os.getenv("OIDC_CLIENT_ID")
    client_secret = os.getenv("OIDC_CLIENT_SECRET")
    metadata_url = os.getenv(
        "OIDC_SERVER_METADATA_URL",
        "https://accounts.google.com/.well-known/openid-configuration",
    )
    redirect_uri = os.getenv("API_OIDC_REDIRECT_URI")

    oauth = OAuth()
    if client_id and client_secret and metadata_url:
        oauth.register(
            name="google",
            server_metadata_url=metadata_url,
            client_id=client_id,
            client_secret=client_secret,
            client_kwargs={"scope": "openid email profile"},
        )

    if session_secret:
        app.add_middleware(
            SessionMiddleware,
            secret_key=session_secret,
            session_cookie=SESSION_NAME,
            max_age=SESSION_MAX_AGE,
            same_site="lax",
            https_only=os.getenv("API_COOKIE_SECURE", "true").lower()
            in {"1", "true", "yes"},
        )

    def require_configuration():
        if not session_secret:
            raise HTTPException(503, "API session security is not configured.")
        if not (client_id and client_secret and redirect_uri):
            raise HTTPException(503, "API Google OIDC is not configured.")

    @app.get("/auth/login", include_in_schema=False)
    async def auth_login(request: Request):
        require_configuration()
        return await oauth.google.authorize_redirect(
            request,
            redirect_uri=redirect_uri,
        )

    @app.get("/auth/callback", include_in_schema=False)
    async def auth_callback(request: Request):
        require_configuration()
        try:
            token = await oauth.google.authorize_access_token(request)
            userinfo = token.get("userinfo")
            if not userinfo:
                userinfo = await oauth.google.userinfo(token=token)

            assignments = parse_user_assignments(
                os.getenv("PULSEIQ_USER_ROLES", "")
            )
            identity = authorize_identity(
                userinfo.get("email"),
                userinfo.get("email_verified"),
                assignments,
            )
        except AuthorizationError as exc:
            raise HTTPException(403, str(exc)) from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                401, "Google authentication could not be completed."
            ) from exc

        # Store only minimal, allowlisted identity details; never store tokens.
        request.session["pulseiq_identity"] = {
            "email": identity["email"],
            "email_verified": True,
            "expires_at": int(time.time()) + SESSION_MAX_AGE,
        }
        return RedirectResponse(url="/docs", status_code=303)

    @app.get("/auth/me", include_in_schema=False)
    def auth_me(request: Request):
        require_configuration()
        try:
            session = request.session
        except AssertionError as exc:
            raise HTTPException(503, "API sessions are unavailable.") from exc

        saved = session.get("pulseiq_identity")
        if not isinstance(saved, dict):
            raise HTTPException(401, "Authentication required.")
        if saved.get("expires_at", 0) <= int(time.time()):
            session.clear()
            raise HTTPException(401, "Session expired.")

        try:
            assignments = parse_user_assignments(
                os.getenv("PULSEIQ_USER_ROLES", "")
            )
            identity = authorize_identity(
                saved.get("email"),
                saved.get("email_verified"),
                assignments,
            )
        except AuthorizationError as exc:
            session.clear()
            raise HTTPException(403, str(exc)) from exc

        return {
            "email": identity["email"],
            "role": identity["role"],
            "department_id": identity["department_id"],
        }

    @app.post("/auth/logout", include_in_schema=False)
    def auth_logout(request: Request):
        require_configuration()
        request.session.clear()
        return {"status": "logged_out"}


API_ROLE_METRICS = {
    "ADMIN": {
        "pnl",
        "expense_categories",
        "vendor_expense",
        "department_month",
        "executive_scorecard",
    },
    "EXECUTIVE": {
        "pnl",
        "expense_categories",
        "vendor_expense",
        "department_month",
        "executive_scorecard",
    },
    "HR": {"department_month"},
    "MANAGER": {"department_month"},
}


def get_current_identity(request: Request) -> dict[str, str]:
    """Validate the signed API session and re-check the current allowlist."""
    try:
        saved = request.session.get("pulseiq_identity")
    except AssertionError as exc:
        raise HTTPException(
            503, "API session security is not configured."
        ) from exc

    if not isinstance(saved, dict):
        raise HTTPException(401, "Authentication required.")

    if saved.get("expires_at", 0) <= int(time.time()):
        request.session.clear()
        raise HTTPException(401, "Session expired. Please sign in again.")

    try:
        assignments = parse_user_assignments(
            os.getenv("PULSEIQ_USER_ROLES", "")
        )
        return authorize_identity(
            saved.get("email"),
            saved.get("email_verified"),
            assignments,
        )
    except AuthorizationError as exc:
        request.session.clear()
        raise HTTPException(403, str(exc)) from exc


def get_allowed_api_metrics(role: str) -> set[str]:
    """Return the explicitly permitted Metrics API catalogue for a role."""
    normalized = str(role or "").strip().upper()
    if normalized not in API_ROLE_METRICS:
        raise HTTPException(403, "Role is not authorized for the Metrics API.")
    return set(API_ROLE_METRICS[normalized])
