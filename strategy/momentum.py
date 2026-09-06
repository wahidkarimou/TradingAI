from __future__ import annotations

import pandas as pd
import ta


def get_momentum(
    df: pd.DataFrame,
    rsi_period: int = 14
) -> dict:

    if df.empty or len(df) < rsi_period + 1:
        return {
            "direction": "NEUTRAL",
            "rsi": None,
            "macd": None,
            "macd_signal": None,
            "state": "UNKNOWN"
        }

    data = df.copy()

    data["rsi"] = ta.momentum.RSIIndicator(data["Close"], window=rsi_period).rsi()

    macd_indicator = ta.trend.MACD(data["Close"])
    data["macd"] = macd_indicator.macd()
    data["macd_signal"] = macd_indicator.macd_signal()

    last_rsi = float(data["rsi"].iloc[-1])
    last_macd = float(data["macd"].iloc[-1])
    last_macd_signal = float(data["macd_signal"].iloc[-1])

    macd_bullish = last_macd > last_macd_signal

    if last_rsi > 55 and macd_bullish:
        direction = "BULLISH"
    elif last_rsi < 45 and not macd_bullish:
        direction = "BEARISH"
    else:
        direction = "NEUTRAL"

    if last_rsi >= 70:
        state = "OVERBOUGHT"
    elif last_rsi <= 30:
        state = "OVERSOLD"
    else:
        state = "NORMAL"

    return {
        "direction": direction,
        "rsi": last_rsi,
        "macd": last_macd,
        "macd_signal": last_macd_signal,
        "state": state
    }