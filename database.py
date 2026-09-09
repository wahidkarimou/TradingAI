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
            enabled INTEGER,
            price REAL,
            signal TEXT NOT NULL,
            block_reason TEXT,
            confluence_score INTEGER,
            confluence_breakdown TEXT,
            sl REAL,
            tp1 REAL,
            tp2 REAL,
            invalidation TEXT,
            regime TEXT,
            structure_pattern TEXT,
            bos TEXT,
            d1_direction TEXT,
            h4_direction TEXT,
            h1_trend_direction TEXT,
            h1_momentum_direction TEXT,
            rsi REAL,
            atr REAL
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
        (timestamp, symbol, enabled, price, signal, block_reason, confluence_score, confluence_breakdown,
         sl, tp1, tp2, invalidation, regime, structure_pattern, bos,
         d1_direction, h4_direction, h1_trend_direction, h1_momentum_direction, rsi, atr)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.utcnow().isoformat(timespec="seconds"),
            result["symbol"],
            1 if result.get("enabled") else 0,
            result["price"],
            result["signal"],
            result.get("block_reason"),
            result["confluence_score"],
            json.dumps(result.get("confluence_breakdown", {})),
            result.get("sl"),
            result.get("tp1"),
            result.get("tp2"),
            result.get("invalidation"),
            result.get("regime"),
            result.get("structure_pattern"),
            result.get("bos"),
            result.get("d1_direction"),
            result.get("h4_direction"),
            result.get("h1_trend_direction"),
            result.get("h1_momentum_direction"),
            result.get("rsi"),
            result.get("atr"),
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
            d["confluence_breakdown"] = json.loads(d.get("confluence_breakdown") or "{}")
        except (TypeError, ValueError):
            d["confluence_breakdown"] = {}
        results.append(d)
    return results

def get_last_signal(symbol: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM signals WHERE symbol = ? ORDER BY id DESC LIMIT 1", (symbol,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None