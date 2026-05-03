"""
Validates that a query result is usable before further processing.
"""

from __future__ import annotations

import pandas as pd
from typing import Tuple


def check_output(df: pd.DataFrame | None) -> Tuple[bool, str]:
    """Return (is_valid, reason)."""
    if df is None:
        return False, "Query returned no result"
    if df.empty:
        return False, "Query returned an empty table"
    if len(df.columns) == 0:
        return False, "Result has no columns"
    return True, "OK"
