"""
DataPilot core agent.

Loop:
  1. Receive natural-language question
  2. Generate SQL via Claude
  3. Validate SQL (security guardrail)
  4. Execute query → DataFrame
  5. If empty / error → retry once with a hint
  6. Analyse DataFrame (pandas)
  7. Build chart (Plotly)
  8. Generate explanation via Claude
  9. Return AgentResult
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional

import anthropic
import pandas as pd
import plotly.graph_objects as go

from app.config import (
    ALLOWED_TABLES,
    DB_PATH,
    MAX_QUERY_LENGTH,
    MAX_TOKENS,
    MODEL,
)
from app.guardrails.output_checker import check_output
from app.guardrails.sql_validator import validate_sql
from app.tools.python_tool import analyze_dataframe
from app.tools.sql_tool import execute_query, get_schema
from app.tools.viz_tool import create_chart


# ── Result container ───────────────────────────────────────────────────────

@dataclass
class AgentResult:
    sql:             str                    = ""
    dataframe:       Optional[pd.DataFrame] = None
    chart:           Optional[go.Figure]    = None
    analysis:        dict                   = field(default_factory=dict)
    explanation:     str                    = ""
    error:           str                    = ""
    retry_attempted: bool                   = False


# ── Agent ──────────────────────────────────────────────────────────────────

class DataPilotAgent:
    """Orchestrates the full NL → SQL → analysis → explanation pipeline."""

    def __init__(self, api_key: str) -> None:
        self.client = anthropic.Anthropic(api_key=api_key)
        self.schema = get_schema(DB_PATH)

    # ── Public entry-point ─────────────────────────────────────────────────

    def run(self, question: str) -> AgentResult:
        result = AgentResult()

        # 1. Generate SQL
        sql, err = self._generate_sql(question)
        if err:
            result.error = err
            return result
        result.sql = sql

        # 2. Validate
        valid, reason = validate_sql(sql, ALLOWED_TABLES, MAX_QUERY_LENGTH)
        if not valid:
            result.error = f"SQL validation failed: {reason}"
            return result

        # 3. Execute
        df, err = execute_query(sql, DB_PATH)

        # 4. Retry once on failure / empty result
        if err or df is None or df.empty:
            result.retry_attempted = True
            hint = err or "The query returned an empty result. Try a broader or different query."
            retry_sql, retry_err = self._generate_sql(question, hint=hint)

            if not retry_err:
                valid, reason = validate_sql(retry_sql, ALLOWED_TABLES, MAX_QUERY_LENGTH)
                if valid:
                    df, err = execute_query(retry_sql, DB_PATH)
                    result.sql = retry_sql

        if err:
            result.error = err
            return result

        ok, reason = check_output(df)
        if not ok:
            result.error = reason
            return result

        result.dataframe = df

        # 5. Analyse
        result.analysis = analyze_dataframe(df)

        # 6. Visualise
        result.chart = create_chart(df)

        # 7. Explain
        result.explanation = self._generate_explanation(
            question, result.sql, result.analysis
        )

        return result

    # ── Private helpers ────────────────────────────────────────────────────

    def _generate_sql(self, question: str, hint: str = "") -> tuple[str, str]:
        """Ask Claude to write a SQLite SELECT for *question*."""
        hint_block = f"\nHint from previous attempt: {hint}" if hint else ""
        prompt = f"""You are a SQL expert for SQLite. Convert the user question into a valid SQL query.

Database schema:
{self.schema}

Important notes about the data:
- Dates are stored as TEXT in ISO-8601 format: YYYY-MM-DD (e.g. "2023-06-15")
- Use strftime('%Y-%m', date) to group by month
- Use strftime('%Y', date) to group by year
- Do NOT use CTEs (WITH ... AS) — write simple, flat SELECT queries

Rules:
- Return ONLY the raw SQL query — no explanation, no markdown fences
- Use only SELECT statements (no DROP, DELETE, UPDATE, INSERT, ALTER, CREATE)
- Reference only the tables listed in the schema
- Always include an ORDER BY when the question asks for "top", "most", or ranking
- Keep the query correct and efficient{hint_block}

User question: {question}

SQL:"""

        try:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )

            # Guard: empty or unexpected response shape
            if not response.content or not hasattr(response.content[0], "text"):
                return "", "Claude returned an empty response — please try again."

            raw = response.content[0].text.strip()
            if not raw:
                return "", "Claude returned an empty SQL string — please rephrase your question."

            # Strip markdown fences if the model adds them anyway
            sql = raw.replace("```sql", "").replace("```", "").strip()
            return sql, ""

        except anthropic.RateLimitError:
            return "", "API rate limit reached — wait a moment and try again."
        except anthropic.AuthenticationError:
            return "", "Invalid API key — check your key in the sidebar."
        except anthropic.APIError as exc:
            return "", f"Anthropic API error: {exc}"
        except Exception as exc:
            return "", f"Unexpected error generating SQL: {exc}"

    def _generate_explanation(
        self, question: str, sql: str, analysis: dict
    ) -> str:
        """Ask Claude to explain the results in plain English."""
        numeric_summary = json.dumps(analysis.get("numeric_stats", {}), indent=2)
        prompt = f"""You are a friendly data analyst. Explain the query results clearly and concisely.

User question: {question}

SQL used:
{sql}

Result summary:
- Rows returned: {analysis.get("row_count", 0)}
- Columns: {", ".join(analysis.get("columns", []))}
- Numeric stats:
{numeric_summary}

Write 2-3 sentences in plain English. Be specific — use actual numbers from the stats.
Do NOT mention SQL, DataFrames, or technical terms."""

        try:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )

            if not response.content or not hasattr(response.content[0], "text"):
                return "Results retrieved successfully."

            return response.content[0].text.strip()

        except Exception as exc:
            return f"Results retrieved. (Explanation unavailable: {exc})"
