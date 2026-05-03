"""
DataPilot — Streamlit front-end.

Run locally:  streamlit run app/main.py
Deploy:       Streamlit Community Cloud (share.streamlit.io)
              Set ANTHROPIC_API_KEY in App Settings → Secrets
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so all `app.*` imports resolve
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from app.agent import DataPilotAgent
from app.config import ANTHROPIC_API_KEY, DB_PATH
from scripts.create_db import create_sample_database

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataPilot — AI Data Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Bootstrap database ─────────────────────────────────────────────────────
if not DB_PATH.exists():
    with st.spinner("Creating sample database…"):
        create_sample_database(DB_PATH)


# ── API key resolution: Streamlit Secrets (cloud) → .env (local) ──────────
def _resolve_api_key() -> str:
    """Returns the API key without ever putting it in the DOM."""
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return ANTHROPIC_API_KEY


_env_key = _resolve_api_key()


# ── Cached agent (one instance per API key, avoids rebuilding schema) ──────
@st.cache_resource
def get_agent(api_key: str) -> DataPilotAgent:
    return DataPilotAgent(api_key=api_key)


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    if _env_key:
        # Key already configured — confirm without exposing the value
        st.success("API key loaded", icon="🔑")
        api_key = _env_key
    else:
        # No key configured → user must paste one (field starts empty)
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-...",
            help="Set ANTHROPIC_API_KEY in .env (local) or Streamlit Secrets (cloud)",
        )

    st.markdown("---")
    st.markdown("## 💡 Example Queries")
    examples = [
        "What are the top 5 products by total revenue?",
        "Which country has the most customers?",
        "Show total revenue per month in 2023",
        "What is the average transaction amount by country?",
        "Which product sold the most units?",
        "Show me revenue distribution across products",
    ]
    for example in examples:
        if st.button(example, use_container_width=True, key=f"ex_{example}"):
            # Write directly into the text-area session-state key
            st.session_state["query_input"] = example

    st.markdown("---")
    st.markdown("### Database Tables")
    st.markdown(
        "- **sales** — date, product, revenue, units_sold\n"
        "- **customers** — id, name, country, joined_date\n"
        "- **transactions** — id, customer_id, amount, transaction_date"
    )

# ── Header ─────────────────────────────────────────────────────────────────
st.title("🚀 DataPilot")
st.caption("Ask a question in plain English — get SQL, a chart, and an explanation instantly.")
st.divider()

# ── Input ──────────────────────────────────────────────────────────────────
MAX_QUESTION_LEN = 500

query = st.text_area(
    "Your question",
    key="query_input",
    placeholder="e.g. What are the top 5 products by revenue?",
    height=80,
    label_visibility="collapsed",
)

col_btn, col_hint = st.columns([1, 5])
with col_btn:
    run = st.button("Analyze ▶", type="primary", use_container_width=True)
with col_hint:
    remaining = MAX_QUESTION_LEN - len(query or "")
    st.caption(
        f"{remaining} characters remaining — "
        "click a suggestion in the sidebar or type your own question above."
    )

# ── Run agent ──────────────────────────────────────────────────────────────
if run:
    q = (query or "").strip()

    if not q:
        st.warning("Please enter a question first.")
    elif len(q) > MAX_QUESTION_LEN:
        st.warning(f"Question is too long ({len(q)} chars). Keep it under {MAX_QUESTION_LEN}.")
    elif not api_key:
        st.error("Add your Anthropic API key in the sidebar to continue.")
    else:
        agent = get_agent(api_key)

        with st.spinner("Thinking…"):
            result = agent.run(q)

        if result.error:
            st.error(f"**Error:** {result.error}")
            if result.sql:
                with st.expander("Generated SQL (failed — shown for debugging)"):
                    st.code(result.sql, language="sql")
        else:
            if result.retry_attempted:
                st.info(
                    "The first attempt returned no data — "
                    "a refined query was generated automatically."
                )

            tab_chart, tab_data, tab_sql, tab_explain = st.tabs(
                ["📊 Chart", "📋 Data", "🔍 SQL", "💡 Explanation"]
            )

            with tab_chart:
                if result.chart is not None:
                    st.plotly_chart(result.chart, use_container_width=True)
                else:
                    st.info(
                        "No chart available for this result. "
                        "Check the Data tab for the raw numbers."
                    )

            with tab_data:
                st.dataframe(result.dataframe, use_container_width=True)
                rows, cols = result.dataframe.shape
                st.caption(
                    f"{rows:,} row{'s' if rows != 1 else ''} "
                    f"× {cols} column{'s' if cols != 1 else ''}"
                )

            with tab_sql:
                st.code(result.sql, language="sql")
                st.caption("Generated by Claude and validated before execution.")

            with tab_explain:
                st.markdown(result.explanation)

                num_stats = result.analysis.get("numeric_stats")
                if num_stats:
                    with st.expander("Numeric statistics"):
                        st.json(num_stats)

                top_vals = result.analysis.get("top_values")
                if top_vals:
                    with st.expander("Top values per column"):
                        st.json(top_vals)
