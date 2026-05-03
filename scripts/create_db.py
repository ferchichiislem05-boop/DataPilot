"""
Creates (or re-creates) the sample SQLite database used by DataPilot.

Tables
------
customers    — id, name, country, joined_date
sales        — id, date, product, revenue, units_sold
transactions — id, customer_id, amount, transaction_date

Run directly:   python scripts/create_db.py
Imported by:    app/main.py (auto-creates on first launch)
"""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

# Seed for reproducibility
random.seed(42)

PRODUCTS  = ["Laptop", "Phone", "Tablet", "Monitor", "Keyboard", "Mouse", "Headphones", "Webcam"]
COUNTRIES = ["USA", "Germany", "France", "UK", "Japan", "Canada", "Australia", "Brazil"]

START_DATE       = date(2023, 1, 1)
NUM_CUSTOMERS    = 100
NUM_SALES        = 300
NUM_TRANSACTIONS = 500


def _random_date(start: date = START_DATE, days: int = 364) -> str:
    return (start + timedelta(days=random.randint(0, days))).isoformat()


def create_sample_database(db_path: Path) -> None:
    """Create and populate the sample database at *db_path*."""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()

        # ── Schema ────────────────────────────────────────────────────────
        cur.executescript("""
            DROP TABLE IF EXISTS transactions;
            DROP TABLE IF EXISTS sales;
            DROP TABLE IF EXISTS customers;

            CREATE TABLE customers (
                id          INTEGER PRIMARY KEY,
                name        TEXT    NOT NULL,
                country     TEXT    NOT NULL,
                joined_date TEXT    NOT NULL
            );

            CREATE TABLE sales (
                id          INTEGER PRIMARY KEY,
                date        TEXT    NOT NULL,
                product     TEXT    NOT NULL,
                revenue     REAL    NOT NULL,
                units_sold  INTEGER NOT NULL
            );

            CREATE TABLE transactions (
                id               INTEGER PRIMARY KEY,
                customer_id      INTEGER NOT NULL,
                amount           REAL    NOT NULL,
                transaction_date TEXT    NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            );
        """)

        # ── Seed data ─────────────────────────────────────────────────────
        customers = [
            (i, f"Customer_{i:03d}", random.choice(COUNTRIES), _random_date(date(2022, 1, 1), 364))
            for i in range(1, NUM_CUSTOMERS + 1)
        ]
        cur.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", customers)

        sales = [
            (
                i,
                _random_date(),
                random.choice(PRODUCTS),
                round(random.uniform(50.0, 2_000.0), 2),
                random.randint(1, 50),
            )
            for i in range(1, NUM_SALES + 1)
        ]
        cur.executemany("INSERT INTO sales VALUES (?, ?, ?, ?, ?)", sales)

        transactions = [
            (
                i,
                random.randint(1, NUM_CUSTOMERS),
                round(random.uniform(10.0, 500.0), 2),
                _random_date(),
            )
            for i in range(1, NUM_TRANSACTIONS + 1)
        ]
        cur.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?)", transactions)

        # ── Indexes (speed up common GROUP BY / JOIN patterns) ────────────
        cur.executescript("""
            CREATE INDEX IF NOT EXISTS idx_sales_date        ON sales(date);
            CREATE INDEX IF NOT EXISTS idx_sales_product     ON sales(product);
            CREATE INDEX IF NOT EXISTS idx_txn_customer      ON transactions(customer_id);
            CREATE INDEX IF NOT EXISTS idx_customers_country ON customers(country);
        """)

        conn.commit()

    print(f"[create_db] Database ready: {db_path}")


if __name__ == "__main__":
    target = Path(__file__).parent.parent / "data" / "sample.db"
    create_sample_database(target)
