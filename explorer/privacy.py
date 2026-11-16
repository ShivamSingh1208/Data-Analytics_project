import pandas as pd


def suppress_small_groups(data: pd.DataFrame, minimum: int):
    if minimum < 1:
        raise ValueError("Minimum group size must be at least 1.")

    if "group_size" not in data.columns:
        raise ValueError("Missing required group_size column.")

    sizes = pd.to_numeric(data["group_size"], errors="coerce").fillna(0)
    visible = data.loc[sizes >= minimum].copy()
    hidden = len(data) - len(visible)

    return visible, hidden
