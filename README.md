<div align="center">

# 🚀 DataPilot

### AI-Powered Data Analysis Agent

*Ask a question in plain English. Get SQL, a chart, and an explanation — instantly.*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.57-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Claude](https://img.shields.io/badge/Claude-Sonnet%204.6-orange?style=flat-square)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## What is DataPilot?

DataPilot is an AI agent that sits between you and your database. You ask a business question in natural language — it figures out the SQL, runs it, and comes back with a chart and a clear explanation.

No SQL knowledge required. No BI tool license needed.

```
You:  "What are the top 5 products by revenue?"

DataPilot:  → generates SQL
            → runs it on the database
            → builds a bar chart
            → explains the result in plain English
```

---

## How it works

```
┌─────────────────────────────────────────────────────────────┐
│                        User question                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  Claude Sonnet  │  Converts question → SQL
              └────────┬────────┘
                       │
                       ▼
           ┌────────────────────────┐
           │    SQL Validator       │  Blocks DROP / DELETE /
           │    (Security layer)    │  UPDATE / unknown tables
           └──────────┬─────────────┘
                      │
                      ▼
           ┌────────────────────────┐
           │    SQLite Database     │  Executes the query
           │    (3 tables, 900 rows)│  Returns a DataFrame
           └──────────┬─────────────┘
                      │ Empty result?
                      ├──────────────► Retry once with a smarter query
                      │
                      ▼
         ┌──────────────────────────┐
         │   Pandas + Plotly        │  Analyzes + builds chart
         └──────────┬───────────────┘
                    │
                    ▼
         ┌──────────────────────────┐
         │   Claude Sonnet          │  Writes plain-English explanation
         └──────────┬───────────────┘
                    │
                    ▼
         ┌──────────────────────────────────────────────┐
         │  Streamlit UI                                │
         │  📊 Chart  │  📋 Data  │  🔍 SQL  │  💡 Why │
         └──────────────────────────────────────────────┘
```

---

## Features

| Feature | Detail |
|---|---|
| **Natural language → SQL** | Powered by Claude Sonnet 4.6 |
| **Auto-retry** | If first query returns nothing, agent reformulates and retries once |
| **Security guardrails** | Blocks all mutation queries (DROP, DELETE, UPDATE, INSERT…) |
| **Smart charts** | Auto-selects bar / line / histogram based on data shape |
| **Plain-English explanation** | Results explained without technical jargon |
| **Cloud-ready** | Deploys to Streamlit Community Cloud in 3 clicks |

---

## Project structure

```
DataPilot/
│
├── app/
│   ├── main.py              ← Streamlit UI
│   ├── agent.py             ← Orchestration pipeline
│   ├── config.py            ← Settings (model, paths, limits)
│   │
│   ├── tools/
│   │   ├── sql_tool.py      ← Runs SQL, reads schema
│   │   ├── python_tool.py   ← Pandas stats & summaries
│   │   └── viz_tool.py      ← Builds Plotly charts
│   │
│   └── guardrails/
│       ├── sql_validator.py ← Security: blocks dangerous SQL
│       └── output_checker.py← Rejects empty / malformed results
│
├── data/
│   └── sample.db            ← Auto-created SQLite database
│
├── scripts/
│   └── create_db.py         ← Seeds database with sample data
│
├── .streamlit/
│   └── config.toml          ← Theme + server config
│
├── requirements.txt
└── runtime.txt
```

---

## Sample database

Three tables, automatically created on first launch:

| Table | Columns | Rows |
|---|---|---|
| `sales` | id, date, product, revenue, units_sold | 300 |
| `customers` | id, name, country, joined_date | 100 |
| `transactions` | id, customer_id, amount, transaction_date | 500 |

---

## Example queries to try

```
"What are the top 5 products by total revenue?"
"Which country has the most customers?"
"Show total revenue per month in 2023"
"What is the average transaction amount by country?"
"Which product sold the most units?"
"Show me the revenue distribution across products"
```

---

## Run locally

**1 — Clone the repo**
```bash
git clone https://github.com/ferchichiislem05-boop/DataPilot.git
cd DataPilot
```

**2 — Install dependencies**
```bash
pip install -r requirements.txt
```

**3 — Add your Anthropic API key**
```bash
cp .env.example .env
# Open .env and set:
# ANTHROPIC_API_KEY=sk-ant-...
```
Get a free key at [console.anthropic.com](https://console.anthropic.com)

**4 — Launch**
```bash
streamlit run app/main.py
```

Open [http://localhost:8501](http://localhost:8501) — the database is created automatically.

---

## Deploy to Streamlit Cloud (free, 3 steps)

1. Go to **[share.streamlit.io](https://share.streamlit.io)** → sign in with GitHub

2. Click **New app** and fill in:
   ```
   Repository  : ferchichiislem05-boop/DataPilot
   Branch      : main
   Main file   : app/main.py
   ```

3. In **Advanced settings → Secrets**, paste:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```

Click **Deploy** — live in ~2 minutes.

---

## Security

The agent only allows read operations. Every query is validated before execution:

```
✅ SELECT  — allowed
❌ DROP    — blocked
❌ DELETE  — blocked
❌ UPDATE  — blocked
❌ INSERT  — blocked
❌ ALTER   — blocked
❌ Unknown tables — blocked
❌ Multiple statements — blocked
❌ API key in browser DOM — never exposed
```

---

## Tech stack

| Layer | Tool |
|---|---|
| LLM | Anthropic Claude Sonnet 4.6 |
| UI | Streamlit 1.57 |
| Data processing | pandas 3.0 |
| Charts | Plotly 6.7 |
| Database | SQLite (built-in, zero config) |
| Config | python-dotenv |

---

## Limitations & roadmap

**Current limitations**
- Single SQLite file (no external databases yet)
- No conversation memory — each question is independent
- Max 1 retry on failed queries

**Planned improvements**
- [ ] PostgreSQL / DuckDB support
- [ ] Upload your own CSV or Excel file
- [ ] Multi-turn conversation (memory across questions)
- [ ] Streaming LLM responses
- [ ] Export results to CSV / Excel

---

## Author

Built by **ferchichiislem05-boop** as a portfolio project demonstrating:
- LLM integration (Anthropic Claude)
- Secure agentic pipelines
- Clean Python architecture
- Production deployment

---

<div align="center">

*If this project helped you, leave a ⭐ on GitHub*

</div>
