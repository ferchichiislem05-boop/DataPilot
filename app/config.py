import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH  = DATA_DIR / "sample.db"

# ── Anthropic ──────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL      = "claude-sonnet-4-6"
MAX_TOKENS = 1024

# ── Agent behaviour ────────────────────────────────────────────────────────
MAX_RETRIES      = 1          # retry once on empty / error result
MAX_QUERY_LENGTH = 2_000      # characters

# ── Security ───────────────────────────────────────────────────────────────
ALLOWED_TABLES = ["sales", "customers", "transactions"]
