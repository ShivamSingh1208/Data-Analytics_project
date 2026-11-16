import numpy as np
import pandas as pd


def suppress_small_groups(data: pd.DataFrame, minimum: int):
    """Suppress groups with small or invalid group sizes."""

    if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 1:
        raise ValueError("Minimum group size must be a positive integer.")

    if "group_size" not in data.columns:
        raise ValueError("Missing required group_size column.")

    sizes = pd.to_numeric(data["group_size"], errors="coerce")

    # Fail closed: missing, infinite, negative and fractional sizes
    # must never be treated as publishable group sizes.
    valid = (
        sizes.notna()
        & np.isfinite(sizes)
        & sizes.ge(0)
        & sizes.mod(1).eq(0)
    )

    visible_mask = valid & sizes.ge(minimum)
    visible = data.loc[visible_mask].copy()
    hidden = len(data) - len(visible)

    return visible, hidden
