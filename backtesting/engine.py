from __future__ import annotations

import pandas as pd
import numpy as np
import ta

from strategy.trend import get_trend


def generate_trades(df: pd.DataFrame, signal_fn, min_bars: int = 250, cost: float = 0.0) -> list:

    trades = []
    i = min_bars
    n = len(df)

    while i < n - 1:
        history = df.iloc[max(0, i - 300) : i + 1]
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

        exit_price, exit_reason, exit_index = None, None, None

        for j in range(i + 1, n):
            bar_high, bar_low = df["High"].iloc[j], df["Low"].iloc[j]

            if direction == "BULLISH":
                hit_sl, hit_tp = bar_low <= sl, bar_high >= tp1
            else:
                hit_sl, hit_tp = bar_high >= sl, bar_low <= tp1

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
            "entry_index": i, "exit_index": exit_index, "direction": direction,
            "entry": round(entry, 5), "exit": round(adjusted_exit, 5),
            "exit_reason": exit_reason, "r_multiple": round(r_multiple, 2)
        })

        i = exit_index + 1

    return trades


def _precompute_trend_series(df: pd.DataFrame, min_bars: int, available_offset) -> pd.DataFrame:

    if df.empty or len(df) < min_bars:
        empty = pd.to_datetime([])
        return pd.DataFrame({"timestamp": empty, "direction": [], "available_from": empty})

    ema_fast = ta.trend.EMAIndicator(df["Close"], window=50).ema_indicator()
    ema_slow = ta.trend.EMAIndicator(df["Close"], window=200).ema_indicator()

    direction = np.full(len(df), "NEUTRAL", dtype=object)
    valid = ema_fast.notna() & ema_slow.notna()
    direction[(valid & (ema_fast > ema_slow)).to_numpy()] = "BULLISH"
    direction[(valid & (ema_fast < ema_slow)).to_numpy()] = "BEARISH"

    series = pd.DataFrame({"timestamp": df.index, "direction": direction})
    series = series.iloc[min_bars:].reset_index(drop=True)

    series["timestamp"] = pd.to_datetime(series["timestamp"]).astype("datetime64[ns]")
    series["available_from"] = (series["timestamp"] + available_offset).astype("datetime64[ns]")

    return series

def generate_trades_mtf(
    h1_df: pd.DataFrame,
    d1_df: pd.DataFrame,
    h4_df: pd.DataFrame,
    signal_fn,
    min_bars_h1: int = 250,
    min_bars_d1: int = 250,
    min_bars_h4: int = 250,
    cost: float = 0.0
) -> list:

    d1_series = _precompute_trend_series(d1_df, min_bars_d1, pd.Timedelta(days=1))
    h4_series = _precompute_trend_series(h4_df, min_bars_h4, pd.Timedelta(hours=4))

    h1_reset = h1_df.reset_index().rename(columns={h1_df.index.name or "index": "timestamp"})
    h1_reset["timestamp"] = pd.to_datetime(h1_reset["timestamp"]).astype("datetime64[ns]")

    merged = pd.merge_asof(
        h1_reset.sort_values("timestamp"),
        d1_series[["available_from", "direction"]].sort_values("available_from").rename(columns={"direction": "d1_direction"}),
        left_on="timestamp", right_on="available_from", direction="backward"
    )
    merged = pd.merge_asof(
        merged.sort_values("timestamp"),
        h4_series[["available_from", "direction"]].sort_values("available_from").rename(columns={"direction": "h4_direction"}),
        left_on="timestamp", right_on="available_from", direction="backward"
    )

    trades = []
    i = min_bars_h1
    n = len(h1_df)

    while i < n - 1:
        d1_direction = merged["d1_direction"].iloc[i]
        h4_direction = merged["h4_direction"].iloc[i]

        if pd.isna(d1_direction) or pd.isna(h4_direction):
            i += 1
            continue

        history = h1_df.iloc[max(0, i - 300) : i + 1]
        h4_slice = h4_df[h4_df.index <= history.index[-1]].iloc[-300:]
        decision = signal_fn(history, d1_direction, h4_direction, h4_slice)

        if decision is None or decision.get("direction") not in ("BULLISH", "BEARISH"):
            i += 1
            continue

        raw_entry, sl, tp1, direction = decision["entry"], decision["sl"], decision["tp1"], decision["direction"]

        if sl is None or tp1 is None:
            i += 1
            continue

        entry = raw_entry + cost if direction == "BULLISH" else raw_entry - cost

        exit_price, exit_reason, exit_index = None, None, None

        for j in range(i + 1, n):
            bar_high, bar_low = h1_df["High"].iloc[j], h1_df["Low"].iloc[j]

            if direction == "BULLISH":
                hit_sl, hit_tp = bar_low <= sl, bar_high >= tp1
            else:
                hit_sl, hit_tp = bar_high >= sl, bar_low <= tp1

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
            "entry_index": i, "exit_index": exit_index, "direction": direction,
            "entry": round(entry, 5), "exit": round(adjusted_exit, 5),
            "exit_reason": exit_reason, "r_multiple": round(r_multiple, 2),
            "signal_type": decision.get("signal_type")
        })

        i = exit_index + 1

    return trades