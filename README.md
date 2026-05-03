# 🚀 DataPilot — AI Data Analysis Agent

DataPilot is a production-ready AI agent that accepts natural-language questions, converts them to SQL, executes them against a SQLite database, and returns charts, statistics, and plain-English explanations — all through a clean Streamlit interface.

---

## Architecture

```
DataPilot/
├── app/
│   ├── main.py              # Streamlit UI — entry point
│   ├── agent.py             # Orchestration loop (NL → SQL → analysis → explanation)
│   ├── config.py            # Central config (paths, model, limits)
│   │
│   ├── tools/
│   │   ├── sql_tool.py      # SQLite execution + schema reader
│   │   ├── python_tool.py   # Pandas aggregations & summaries
│   │   └── viz_tool.py      # Plotly chart builder (bar / line / histogram)
│   │
│   └── guardrails/
│       ├── sql_validator.py  # Blocks dangerous keywords, unknown tables
│       └── output_checker.py # Rejects empty or malformed results
│
├── data/
│   └── sample.db            # Auto-created on first run
│
├── scripts/
│   └── create_db.py         # DB seed script (100 customers, 300 sales, 500 txns)
│
├── .streamlit/
│   ├── config.toml          # Theme + server config
│   └── secrets.toml.example # Template for secrets
│
├── requirements.txt
├── runtime.txt              # Python version for Streamlit Cloud
└── .env.example
```

### Agent pipeline

```
User question
     │
     ▼
[Claude] Generate SQL
     │
     ▼
[sql_validator] Block dangerous / unknown tables
     │
     ▼
[sql_tool] Execute on SQLite → DataFrame
     │ empty or error?
     ├──yes──► [Claude] Retry with hint → re-validate → re-execute
     │
     ▼
[output_checker] Confirm result is usable
     │
     ▼
[python_tool] Pandas stats & summaries
     │
     ▼
[viz_tool] Build Plotly chart (auto-detected type)
     │
     ▼
[Claude] Generate plain-English explanation
     │
     ▼
Streamlit UI — Chart | Data | SQL | Explanation
```

---

## Quick Start (local)

### 1. Clone and install

```bash
git clone https://github.com/ferchichiislem05-boop/DataPilot.git
cd DataPilot
pip install -r requirements.txt
```

### 2. Configure your API key

```bash
cp .env.example .env
# Edit .env and set your key:
# ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Run

```bash
streamlit run app/main.py
```

The sample database is created automatically on first launch.

---

## Deploy on Streamlit Community Cloud (free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select this repo → set **Main file path** to `app/main.py`
4. Open **Advanced settings → Secrets** and add:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
5. Click **Deploy**

---

## Example Queries

| Question | Chart type |
|---|---|
| What are the top 5 products by total revenue? | Bar |
| Which country has the most customers? | Bar |
| Show total revenue per month in 2023 | Line |
| What is the average transaction amount by country? | Bar |
| Which product sold the most units? | Bar |
| Show me revenue distribution across products | Histogram |

---

## Sample Database

| Table | Columns | Rows |
|---|---|---|
| `customers` | id, name, country, joined_date | 100 |
| `sales` | id, date, product, revenue, units_sold | 300 |
| `transactions` | id, customer_id, amount, transaction_date | 500 |

Dates are stored as `TEXT` in `YYYY-MM-DD` format (ISO-8601).

---

## Security

| Rule | Detail |
|---|---|
| Blocked keywords | DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE, EXEC |
| Only SELECT | Any non-SELECT statement is rejected |
| Table allowlist | Only `sales`, `customers`, `transactions` can be queried |
| No multi-statement | Semicolons inside queries are blocked |
| Query length cap | 2,000 characters max |
| API key | Never rendered in the browser DOM |

---

## Tech Stack

| Layer | Library | Version |
|---|---|---|
| LLM | Anthropic Claude | claude-sonnet-4-6 |
| UI | Streamlit | 1.57.0 |
| Data | pandas | 3.0.2 |
| Charts | Plotly | 6.7.0 |
| Database | SQLite | built-in |
| Config | python-dotenv | 1.2.2 |

---

## Limitations

- Single-file SQLite only (no PostgreSQL / MySQL)
- No conversation memory — each question is independent
- Chart type is auto-detected; complex multi-series charts need manual override
- Retry runs at most once

## Future Improvements

- [ ] Multi-turn conversation with chat history
- [ ] Upload your own CSV / Excel file
- [ ] PostgreSQL / DuckDB connectors
- [ ] Streaming LLM responses
- [ ] Export results to CSV
