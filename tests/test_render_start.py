"""Tests for secure Render startup configuration."""

import importlib
import json
from pathlib import Path

import pytest


render_start = importlib.import_module("scripts.render_start")


def configure_valid_environment(monkeypatch):
    values = {
        "OIDC_CLIENT_ID": "test-client-id",
        "OIDC_CLIENT_SECRET": "test-client-secret",
        "STREAMLIT_COOKIE_SECRET": "c" * 40,
        "OIDC_SERVER_METADATA_URL": (
            "https://accounts.google.com/.well-known/openid-configuration"
        ),
        "OIDC_REDIRECT_URI": "https://example.test/oauth2callback",
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        "PULSEIQ_USER_ROLES": json.dumps({
            "approved@example.com": {"role": "ADMIN"}
        }),
        "PULSEIQ_PRIVACY_HMAC_KEY": "h" * 40,
        "PORT": "10000",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def test_startup_rejects_missing_required_configuration(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for key in (
        "OIDC_CLIENT_ID",
        "OIDC_CLIENT_SECRET",
        "STREAMLIT_COOKIE_SECRET",
        "OIDC_REDIRECT_URI",
        "DATABASE_URL",
        "PULSEIQ_USER_ROLES",
        "PULSEIQ_PRIVACY_HMAC_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(SystemExit, match="OIDC_CLIENT_ID"):
        render_start.main()

    assert not (tmp_path / ".streamlit" / "secrets.toml").exists()


def test_startup_rejects_invalid_manager_assignment(monkeypatch, tmp_path):
    configure_valid_environment(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(
        "PULSEIQ_USER_ROLES",
        json.dumps({
            "manager@example.com": {"role": "MANAGER"}
        }),
    )

    with pytest.raises(SystemExit, match="invalid authorization policy"):
        render_start.main()

    assert not (tmp_path / ".streamlit" / "secrets.toml").exists()


def test_valid_startup_writes_private_oidc_secrets_and_launches(
    monkeypatch, tmp_path
):
    configure_valid_environment(monkeypatch)
    monkeypatch.chdir(tmp_path)

    launched = {}

    def fake_execv(executable, arguments):
        launched["executable"] = executable
        launched["arguments"] = arguments

    monkeypatch.setattr(render_start.os, "execv", fake_execv)

    render_start.main()

    secrets_path = tmp_path / ".streamlit" / "secrets.toml"
    assert secrets_path.exists()
    assert secrets_path.stat().st_mode & 0o777 == 0o600

    contents = secrets_path.read_text()
    assert '[auth]' in contents
    assert 'redirect_uri = "https://example.test/oauth2callback"' in contents
    assert 'client_id = "test-client-id"' in contents
    assert "client_secret" in contents

    assert launched["executable"]
    assert "explorer/app.py" in launched["arguments"]
    assert "--server.address=0.0.0.0" in launched["arguments"]
    assert "--server.port=10000" in launched["arguments"]


def test_startup_rejects_invalid_port_before_writing_secrets(
    monkeypatch, tmp_path
):
    configure_valid_environment(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PORT", "70000")

    with pytest.raises(SystemExit, match="between 1 and 65535"):
        render_start.main()

    assert not (tmp_path / ".streamlit" / "secrets.toml").exists()
