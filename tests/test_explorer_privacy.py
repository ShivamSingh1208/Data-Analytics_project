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
