"""
Plotly chart generation.
Auto-selects the best chart type based on column dtypes and result size,
or accepts an explicit chart_type override.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Literal

ChartType = Literal["auto", "bar", "line", "histogram"]

_PALETTE  = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"]
_TEMPLATE = "plotly_dark"


def create_chart(
    df: pd.DataFrame,
    chart_type: ChartType = "auto",
) -> go.Figure | None:
    """
    Build a Plotly figure from *df*.
    Returns None when the DataFrame cannot be meaningfully charted.
    """
    if df is None or df.empty:
        return None

    numeric_cols  = df.select_dtypes(include="number").columns.tolist()
    date_cols     = _detect_date_columns(df)
    category_cols = [
        c for c in df.select_dtypes(include="object").columns
        if c not in date_cols
    ]

    if not numeric_cols:
        return None

    resolved_type = _resolve_chart_type(
        chart_type, df, numeric_cols, date_cols, category_cols
    )

    try:
        fig = _build_figure(resolved_type, df, numeric_cols, date_cols, category_cols)
    except Exception:
        return None

    fig.update_layout(
        template=_TEMPLATE,
        margin=dict(l=20, r=20, t=50, b=30),
        font=dict(size=13),
    )
    return fig


# ── helpers ────────────────────────────────────────────────────────────────

def _detect_date_columns(df: pd.DataFrame) -> list[str]:
    """Identify columns that look like dates by name convention."""
    keywords = ("date", "time", "month", "year", "day", "period", "week")
    return [c for c in df.columns if any(k in c.lower() for k in keywords)]


def _resolve_chart_type(
    chart_type: ChartType,
    df: pd.DataFrame,
    numeric_cols: list[str],
    date_cols: list[str],
    category_cols: list[str],
) -> str:
    if chart_type != "auto":
        return chart_type
    if date_cols and numeric_cols:
        return "line"
    if category_cols and numeric_cols and len(df) <= 30:
        return "bar"
    return "histogram"


def _build_figure(
    chart_type: str,
    df: pd.DataFrame,
    numeric_cols: list[str],
    date_cols: list[str],
    category_cols: list[str],
) -> go.Figure:
    y = numeric_cols[0]

    if chart_type == "line":
        x = date_cols[0] if date_cols else (
            category_cols[0] if category_cols else df.columns[0]
        )
        # Sort by x-axis so the line is chronologically correct
        plot_df = df.sort_values(by=x).reset_index(drop=True)
        return px.line(
            plot_df, x=x, y=y,
            title=f"{y} over {x}",
            markers=True,
            color_discrete_sequence=_PALETTE,
        )

    if chart_type == "bar":
        x = category_cols[0] if category_cols else df.columns[0]
        # Sort bars by value descending (most useful for ranking queries)
        plot_df = df.sort_values(by=y, ascending=False).reset_index(drop=True)
        return px.bar(
            plot_df, x=x, y=y,
            title=f"{y} by {x}",
            color_discrete_sequence=_PALETTE,
        )

    # histogram (fallback / distribution queries)
    return px.histogram(
        df, x=y,
        title=f"Distribution of {y}",
        color_discrete_sequence=[_PALETTE[2]],
        nbins=min(30, max(5, len(df) // 3)),
    )
