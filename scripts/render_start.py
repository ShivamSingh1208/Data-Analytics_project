"""Validate Render environment and create Streamlit OIDC secrets at runtime."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure the repository root is importable when launched as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from explorer.auth import AuthorizationError, parse_user_assignments


def required(name: str, minimum: int = 1) -> str:
    value = os.getenv(name, "").strip()
    if len(value) < minimum:
        raise SystemExit(
            f"Required Render environment variable {name} is missing or too short."
        )
    return value


def toml_string(value: str) -> str:
    """Return a safely escaped TOML basic string."""
    return json.dumps(value, ensure_ascii=False)


def main() -> None:
    client_id = required("OIDC_CLIENT_ID")
    client_secret = required("OIDC_CLIENT_SECRET")
    cookie_secret = required("STREAMLIT_COOKIE_SECRET", 32)
    metadata_url = os.getenv(
        "OIDC_SERVER_METADATA_URL",
        "https://accounts.google.com/.well-known/openid-configuration",
    ).strip()
    redirect_uri = required("OIDC_REDIRECT_URI")
    required("DATABASE_URL")
    required("PULSEIQ_PRIVACY_HMAC_KEY", 32)

    raw_assignments = required("PULSEIQ_USER_ROLES")
    try:
        parse_user_assignments(raw_assignments)
    except AuthorizationError as exc:
        raise SystemExit(
            "PULSEIQ_USER_ROLES contains an invalid authorization policy."
        ) from exc

    if not metadata_url.startswith("https://"):
        raise SystemExit("OIDC metadata URL must use HTTPS in production.")
    if not redirect_uri.startswith("https://"):
        raise SystemExit("OIDC redirect URL must use HTTPS in production.")

    # Validate the port before creating any secrets or files.
    raw_port = os.getenv("PORT", "10000").strip()
    try:
        port_number = int(raw_port)
    except ValueError as exc:
        raise SystemExit("Render PORT must be a valid TCP port.") from exc

    if not 1 <= port_number <= 65535:
        raise SystemExit("Render PORT must be between 1 and 65535.")

    secrets_dir = Path(".streamlit")
    secrets_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    secrets_dir.chmod(0o700)
    secrets_path = secrets_dir / "secrets.toml"

    contents = "\n".join([
        "[auth]",
        f"redirect_uri = {toml_string(redirect_uri)}",
        f"cookie_secret = {toml_string(cookie_secret)}",
        f"client_id = {toml_string(client_id)}",
        f"client_secret = {toml_string(client_secret)}",
        f"server_metadata_url = {toml_string(metadata_url)}",
        "",
    ])

    file_descriptor = os.open(
        secrets_path,
        os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        0o600,
    )
    try:
        os.fchmod(file_descriptor, 0o600)
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as secrets_file:
            file_descriptor = -1
            secrets_file.write(contents)
    finally:
        if file_descriptor >= 0:
            os.close(file_descriptor)

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "explorer/app.py",
        "--server.address=0.0.0.0",
        f"--server.port={port_number}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]
    os.execv(sys.executable, command)


if __name__ == "__main__":
    main()
