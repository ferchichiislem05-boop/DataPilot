"""
Pandas-based analysis utilities.
Keeps logic simple: counts, numeric stats, and top-value summaries.
"""

from __future__ import annotations

import pandas as pd
from typing import Any


def analyze_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """
    Return a flat summary dict that is both human-readable and
    easy to serialise into an LLM prompt.
    """
    analysis: dict[str, Any] = {
        "row_count":    len(df),
        "column_count": len(df.columns),
        "columns":      list(df.columns),
        "dtypes":       {col: str(dt) for col, dt in df.dtypes.items()},
    }

    # Numeric statistics
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        analysis["numeric_stats"] = {
            col: {
                "mean": _round(df[col].mean()),
                "min":  _round(df[col].min()),
                "max":  _round(df[col].max()),
                "sum":  _round(df[col].sum()),
            }
            for col in numeric_cols
        }

    # Top values for categorical / text columns (max 3 cols, top 5 each)
    cat_cols = df.select_dtypes(include="object").columns.tolist()
    if cat_cols:
        analysis["top_values"] = {
            col: df[col].value_counts().head(5).to_dict()
            for col in cat_cols[:3]
        }

    return analysis


def _round(value: Any, decimals: int = 2) -> float:
    """Safely round a value; return 0.0 on error."""
    try:
        return round(float(value), decimals)
    except (TypeError, ValueError):
        return 0.0
