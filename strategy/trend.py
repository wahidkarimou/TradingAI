from __future__ import annotations

import pandas as pd
import ta


def get_trend(
    df: pd.DataFrame,
    ema_fast: int = 50,
    ema_slow: int = 200
) -> dict:

    if df.empty or len(df) < ema_slow:
        return {
            "direction": "NEUTRAL",
            "ema_fast": None,
            "ema_slow": None,
            "adx": None,
            "strength": "UNKNOWN"
        }

    data = df.copy()

    data["ema_fast"] = ta.trend.EMAIndicator(data["Close"], window=ema_fast).ema_indicator()
    data["ema_slow"] = ta.trend.EMAIndicator(data["Close"], window=ema_slow).ema_indicator()

    adx_indicator = ta.trend.ADXIndicator(data["High"], data["Low"], data["Close"], window=14)
    data["adx"] = adx_indicator.adx()

    last_fast = float(data["ema_fast"].iloc[-1])
    last_slow = float(data["ema_slow"].iloc[-1])
    last_adx = float(data["adx"].iloc[-1])

    if last_fast > last_slow:
        direction = "BULLISH"
    elif last_fast < last_slow:
        direction = "BEARISH"
    else:
        direction = "NEUTRAL"

    if last_adx >= 25:
        strength = "TRENDING"
    elif last_adx <= 20:
        strength = "RANGING"
    else:
        strength = "TRANSITION"

    return {
        "direction": direction,
        "ema_fast": last_fast,
        "ema_slow": last_slow,
        "adx": last_adx,
        "strength": strength
    }