"""
Executes validated SQL against the SQLite database and returns a DataFrame.
Also exposes a helper that reads the live schema for the LLM prompt.
"""

from __future__ import annotations

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Tuple


def execute_query(
    query: str, db_path: Path
) -> Tuple[pd.DataFrame | None, str | None]:
    """
    Run *query* against the SQLite file at *db_path*.
    Returns (DataFrame, None) on success or (None, error_message) on failure.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
        return df, None
    except sqlite3.Error as exc:
        return None, f"SQLite error: {exc}"
    except Exception as exc:
        return None, f"Unexpected error: {exc}"


def get_schema(db_path: Path) -> str:
    """
    Return the database schema as a human-readable string so the LLM
    knows exactly which tables and columns are available.
    """
    if not db_path.exists():
        return "(database not yet created)"

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]

            parts = []
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                cols = cursor.fetchall()
                col_lines = [f"  {c[1]} {c[2]}" for c in cols]
                parts.append(f"Table: {table}\n" + "\n".join(col_lines))

            return "\n\n".join(parts)
    except Exception as exc:
        return f"Error reading schema: {exc}"
