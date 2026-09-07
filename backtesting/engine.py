from __future__ import annotations

import pandas as pd


def generate_trades(
    df: pd.DataFrame,
    signal_fn,
    min_bars: int = 250,
    cost: float = 0.0
) -> list:

    trades = []
    i = min_bars
    n = len(df)

    while i < n - 1:
        history = df.iloc[: i + 1]
        decision = signal_fn(history)

        if decision is None or decision.get("direction") not in ("BULLISH", "BEARISH"):
            i += 1
            continue

        raw_entry = decision["entry"]
        sl = decision["sl"]
        tp1 = decision["tp1"]
        direction = decision["direction"]

        if sl is None or tp1 is None:
            i += 1
            continue

        entry = raw_entry + cost if direction == "BULLISH" else raw_entry - cost

        exit_price = None
        exit_reason = None
        exit_index = None

        for j in range(i + 1, n):
            bar_high = df["High"].iloc[j]
            bar_low = df["Low"].iloc[j]

            if direction == "BULLISH":
                hit_sl = bar_low <= sl
                hit_tp = bar_high >= tp1
            else:
                hit_sl = bar_high >= sl
                hit_tp = bar_low <= tp1

            if hit_sl:
                exit_price, exit_reason = sl, "SL"
            elif hit_tp:
                exit_price, exit_reason = tp1, "TP1"

            if exit_price is not None:
                exit_index = j
                break

        if exit_price is None:
            i += 1
            continue

        adjusted_exit = exit_price - cost if direction == "BULLISH" else exit_price + cost

        risk = abs(entry - sl)
        pnl = (adjusted_exit - entry) if direction == "BULLISH" else (entry - adjusted_exit)
        r_multiple = pnl / risk if risk > 0 else 0

        trades.append({
            "entry_index": i,
            "exit_index": exit_index,
            "direction": direction,
            "entry": round(entry, 5),
            "exit": round(adjusted_exit, 5),
            "exit_reason": exit_reason,
            "r_multiple": round(r_multiple, 2)
        })

        i = exit_index + 1

    return trades