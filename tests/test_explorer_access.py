import pytest

from explorer.access import get_allowed_metrics


def test_admin_has_approved_metrics():
    assert set(get_allowed_metrics("ADMIN")) == {
        "Headcount", "Attendance", "Attrition",
        "Employer cost", "Overtime", "Task completion",
    }


def test_hr_has_only_hr_metrics():
    assert set(get_allowed_metrics("HR")) == {
        "Headcount", "Attendance", "Attrition", "Task completion",
    }


def test_manager_has_restricted_metrics():
    assert set(get_allowed_metrics("MANAGER")) == {
        "Headcount", "Attendance", "Task completion",
    }


def test_executive_has_approved_metrics():
    assert set(get_allowed_metrics("EXECUTIVE")) == {
        "Headcount", "Attendance", "Attrition",
        "Employer cost", "Overtime", "Task completion",
    }


def test_role_matching_is_case_insensitive():
    assert get_allowed_metrics("manager") == get_allowed_metrics("MANAGER")


def test_unsupported_role_is_rejected():
    with pytest.raises(ValueError):
        get_allowed_metrics("SUPERUSER")


@pytest.mark.parametrize("role", [None, 123, "", "   "])
def test_invalid_role_values_are_rejected(role):
    with pytest.raises(ValueError, match="Unsupported role"):
        get_allowed_metrics(role)
