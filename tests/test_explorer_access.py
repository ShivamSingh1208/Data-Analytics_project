import pytest

from explorer.access import ROLE_METRICS, METRIC_COLUMNS, get_allowed_metrics


def test_all_four_roles_are_defined():
    assert set(ROLE_METRICS) == {"ADMIN", "HR", "MANAGER", "EXECUTIVE"}


def test_admin_has_all_six_metrics():
    assert len(get_allowed_metrics("ADMIN")) == 6


def test_hr_has_only_four_approved_metrics():
    assert set(get_allowed_metrics("HR")) == {
        "Headcount", "Attendance", "Attrition", "Task completion"
    }


def test_manager_has_only_three_approved_metrics():
    assert set(get_allowed_metrics("MANAGER")) == {
        "Headcount", "Attendance", "Task completion"
    }


def test_executive_has_all_six_metrics():
    assert len(get_allowed_metrics("EXECUTIVE")) == 6


def test_role_lookup_is_case_insensitive():
    assert get_allowed_metrics("manager") == get_allowed_metrics("MANAGER")


def test_unknown_role_is_rejected():
    with pytest.raises(ValueError):
        get_allowed_metrics("GUEST")


def test_every_allowed_metric_has_a_column_policy():
    for metrics in ROLE_METRICS.values():
        for metric in metrics:
            assert metric in METRIC_COLUMNS


def test_attrition_has_stricter_suppression_threshold():
    assert METRIC_COLUMNS["Attrition"][1] == 10
