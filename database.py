"""Stockage SQLite de l'historique des signaux générés."""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "data" / "signals.db"


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL DEFAULT 'H4',
            signal TEXT NOT NULL,
            confidence INTEGER,
            price REAL,
            sl REAL,
            tp REAL,
            trend TEXT,
            momentum TEXT,
            rsi REAL,
            support REAL,
            resistance REAL
        )
        """
    )
    conn.commit()
    conn.close()


def save_signal(result: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO signals
        (timestamp, symbol, timeframe, signal, confidence, price, sl, tp, trend, momentum, rsi, support, resistance)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.utcnow().isoformat(timespec="seconds"),
            result["symbol"],
            result.get("timeframe", "H4"),
            result["signal"],
            result["confidence"],
            result["price"],
            result["sl"],
            result["tp"],
            result["trend"],
            result["momentum"],
            result["rsi"],
            result["support"],
            result["resistance"],
        ),
    )
    conn.commit()
    conn.close()


def get_all_signals(limit: int = 100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM signals ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
