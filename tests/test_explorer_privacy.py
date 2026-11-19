import pandas as pd
import pytest

from explorer.privacy import suppress_small_groups


def test_regular_metrics_hide_groups_below_five():
    data = pd.DataFrame({
        "department_id": ["D01", "D02", "D03"],
        "group_size": [5, 4, 1],
        "metric_value": [10, 20, 30],
    })

    visible, hidden = suppress_small_groups(data, 5)

    assert visible["department_id"].tolist() == ["D01"]
    assert hidden == 2


def test_attrition_threshold_is_ten():
    data = pd.DataFrame({
        "department_id": ["D01", "D02"],
        "group_size": [10, 9],
        "metric_value": [2.5, 3.0],
    })

    visible, hidden = suppress_small_groups(data, 10)

    assert visible["department_id"].tolist() == ["D01"]
    assert hidden == 1


def test_missing_group_size_is_suppressed():
    data = pd.DataFrame({
        "department_id": ["D01", "D02"],
        "group_size": [None, 5],
        "metric_value": [10, 20],
    })

    visible, hidden = suppress_small_groups(data, 5)

    assert visible["department_id"].tolist() == ["D02"]
    assert hidden == 1


def test_original_dataframe_is_not_modified():
    data = pd.DataFrame({
        "department_id": ["D01", "D02"],
        "group_size": [5, 2],
    })
    original = data.copy(deep=True)

    suppress_small_groups(data, 5)

    pd.testing.assert_frame_equal(data, original)


def test_invalid_threshold_is_rejected():
    with pytest.raises(ValueError):
        suppress_small_groups(
            pd.DataFrame({"group_size": [5]}), 0
        )


def test_missing_group_size_column_is_rejected():
    with pytest.raises(ValueError):
        suppress_small_groups(
            pd.DataFrame({"department_id": ["D01"]}), 5
        )



def test_non_numeric_group_sizes_are_suppressed():
    data = pd.DataFrame({
        "department_id": ["D01", "D02", "D03"],
        "group_size": ["unknown", "5", "3"],
        "metric_value": [10, 20, 30],
    })

    visible, hidden = suppress_small_groups(data, 5)

    assert visible["department_id"].tolist() == ["D02"]
    assert hidden == 2


def test_group_exactly_at_threshold_is_visible():
    data = pd.DataFrame({
        "department_id": ["D01", "D02"],
        "group_size": [4, 5],
    })

    visible, hidden = suppress_small_groups(data, 5)

    assert visible["department_id"].tolist() == ["D02"]
    assert hidden == 1


def test_non_integer_threshold_is_rejected():
    data = pd.DataFrame({"group_size": [5]})

    with pytest.raises(ValueError):
        suppress_small_groups(data, 2.5)


def test_boolean_threshold_is_rejected():
    data = pd.DataFrame({"group_size": [5]})

    with pytest.raises(ValueError):
        suppress_small_groups(data, True)


def test_explorer_does_not_offer_historical_month_selector():
    from pathlib import Path

    source = Path("explorer/app.py").read_text(encoding="utf-8")

    assert "st.date_input" not in source
    assert "selected_month = cutoff" in source


def test_explorer_query_is_scoped_to_the_latest_month():
    from pathlib import Path

    source = Path("explorer/app.py").read_text(encoding="utf-8")

    assert 'SELECT MAX(month)' in source
    assert 'WHERE month = :month' in source
    assert 'params = {"month": cutoff}' in source


def test_infinite_group_sizes_are_suppressed():
    data = pd.DataFrame({
        "department_id": ["D01", "D02"],
        "group_size": [float("inf"), 5],
    })

    visible, hidden = suppress_small_groups(data, 5)

    assert visible["department_id"].tolist() == ["D02"]
    assert hidden == 1


def test_fractional_group_sizes_are_suppressed():
    data = pd.DataFrame({
        "department_id": ["D01", "D02"],
        "group_size": [5.5, 6.0],
    })

    visible, hidden = suppress_small_groups(data, 5)

    assert visible["department_id"].tolist() == ["D02"]
    assert hidden == 1


def test_negative_group_sizes_are_suppressed():
    data = pd.DataFrame({
        "department_id": ["D01", "D02"],
        "group_size": [-5, 5],
    })

    visible, hidden = suppress_small_groups(data, 5)

    assert visible["department_id"].tolist() == ["D02"]
    assert hidden == 1


def test_invalid_group_sizes_fail_closed():
    data = pd.DataFrame({
        "department_id": ["D01", "D02", "D03", "D04"],
        "group_size": [None, "unknown", float("nan"), float("-inf")],
    })

    visible, hidden = suppress_small_groups(data, 5)

    assert visible.empty
    assert hidden == 4


def test_integer_valued_float_group_size_is_valid():
    data = pd.DataFrame({
        "department_id": ["D01"],
        "group_size": [5.0],
    })

    visible, hidden = suppress_small_groups(data, 5)

    assert visible["department_id"].tolist() == ["D01"]
    assert hidden == 0
