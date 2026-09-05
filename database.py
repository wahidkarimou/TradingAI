"""Stockage SQLite de l'historique des signaux générés."""

import sqlite3
import json
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
            confluence INTEGER,
            setup_quality TEXT,
            price REAL,
            sl REAL,
            tp1 REAL,
            tp2 REAL,
            invalidation TEXT,
            trend TEXT,
            momentum TEXT,
            rsi REAL,
            support REAL,
            resistance REAL,
            regime TEXT,
            adx REAL,
            structure_pattern TEXT,
            bos TEXT,
            volatility_state TEXT,
            mtf_json TEXT
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
        (timestamp, symbol, timeframe, signal, confluence, setup_quality, price, sl, tp1, tp2,
         invalidation, trend, momentum, rsi, support, resistance, regime, adx,
         structure_pattern, bos, volatility_state, mtf_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.utcnow().isoformat(timespec="seconds"),
            result["symbol"],
            result.get("timeframe", "H4"),
            result["signal"],
            result.get("confluence"),
            result.get("setup_quality"),
            result["price"],
            result["sl"],
            result.get("tp1"),
            result.get("tp2"),
            result.get("invalidation"),
            result["trend"],
            result["momentum"],
            result["rsi"],
            result["support"],
            result["resistance"],
            result.get("regime"),
            result.get("adx"),
            result.get("structure_pattern"),
            result.get("bos"),
            result.get("volatility_state"),
            json.dumps(result.get("mtf", {})),
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
    results = []
    for row in rows:
        d = dict(row)
        try:
            d["mtf"] = json.loads(d.get("mtf_json") or "{}")
        except (TypeError, ValueError):
            d["mtf"] = {}
        results.append(d)
    return results
