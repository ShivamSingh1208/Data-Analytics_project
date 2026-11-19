import json
import pytest

from explorer.auth import AuthorizationError, authorize_identity, parse_user_assignments


def assignments():
    return parse_user_assignments(json.dumps({
        "admin@example.com": {"role": "ADMIN"},
        "manager@example.com": {"role": "MANAGER", "department_id": "D01"},
    }))


def test_verified_email_gets_explicit_role():
    result = authorize_identity("ADMIN@example.com", True, assignments())
    assert result == {"email": "admin@example.com", "role": "ADMIN", "department_id": ""}


def test_unverified_email_is_rejected():
    with pytest.raises(AuthorizationError):
        authorize_identity("admin@example.com", False, assignments())


def test_unknown_email_is_rejected():
    with pytest.raises(AuthorizationError):
        authorize_identity("unknown@example.com", True, assignments())


def test_missing_email_is_rejected():
    with pytest.raises(AuthorizationError):
        authorize_identity(None, True, assignments())


def test_manager_must_have_department():
    with pytest.raises(AuthorizationError):
        parse_user_assignments('{"manager@example.com":{"role":"MANAGER"}}')


def test_non_manager_cannot_be_assigned_department():
    with pytest.raises(AuthorizationError):
        parse_user_assignments('{"admin@example.com":{"role":"ADMIN","department_id":"D01"}}')


def test_unknown_role_is_rejected():
    with pytest.raises(AuthorizationError):
        parse_user_assignments('{"x@example.com":{"role":"SUPERUSER"}}')


def test_empty_or_invalid_json_is_rejected():
    for raw in ("", "not-json", "[]", "{}"):
        with pytest.raises(AuthorizationError):
            parse_user_assignments(raw)


def test_no_default_or_wildcard_user_is_supported():
    with pytest.raises(AuthorizationError):
        authorize_identity("someone@example.com", True, assignments())
