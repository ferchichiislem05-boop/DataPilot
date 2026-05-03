"""
SQL safety layer — blocks destructive statements and unknown tables.

Supports:
  - Plain SELECT queries
  - Subqueries and JOINs referencing only allowed tables
"""

from __future__ import annotations

import re
from typing import Tuple

# Any of these as a standalone word is forbidden
_BLOCKED = {
    "DROP", "DELETE", "UPDATE", "INSERT",
    "ALTER", "CREATE", "TRUNCATE", "EXEC", "EXECUTE",
}


def validate_sql(
    query: str,
    allowed_tables: list[str],
    max_length: int = 2_000,
) -> Tuple[bool, str]:
    """
    Return (is_valid, reason).

    A query is valid when:
      - It is a SELECT statement (no CTEs needed; agent prompt forbids them)
      - It contains no forbidden mutation keywords
      - It references only known tables
      - It does not contain multiple statements
    """
    if not query or not query.strip():
        return False, "Query is empty"

    if len(query) > max_length:
        return False, f"Query exceeds {max_length} characters"

    upper = query.upper()

    # ── Block forbidden keywords (word-boundary match) ─────────────────────
    for kw in _BLOCKED:
        if re.search(rf"\b{kw}\b", upper):
            return False, f"Forbidden keyword detected: {kw}"

    # ── Block multiple statements ──────────────────────────────────────────
    clean = query.rstrip().rstrip(";")
    if ";" in clean:
        return False, "Multiple statements are not allowed"

    # ── Must start with SELECT or WITH (CTE, kept for safety) ─────────────
    if not re.match(r"^\s*(WITH|SELECT)\b", upper):
        return False, "Only SELECT statements are allowed"

    # ── Collect CTE-defined names so they don't fail the table allowlist ──
    cte_names: set[str] = set()
    cte_names.update(re.findall(r"\bWITH\s+([A-Z_][A-Z0-9_]*)\s+AS\s*\(", upper))
    cte_names.update(re.findall(r",\s*([A-Z_][A-Z0-9_]*)\s+AS\s*\(", upper))

    # ── Validate real table names referenced after FROM / JOIN ─────────────
    referenced = re.findall(r"\b(?:FROM|JOIN)\s+([A-Z_][A-Z0-9_]*)", upper)
    allowed_upper = {t.upper() for t in allowed_tables}

    for table in referenced:
        if table in cte_names:
            continue  # CTE alias — not a real table
        if table == "SELECT":
            continue  # subquery: FROM (SELECT ...)
        if table not in allowed_upper:
            return False, f"Unknown or disallowed table: '{table.lower()}'"

    return True, "OK"
