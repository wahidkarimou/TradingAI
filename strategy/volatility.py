from __future__ import annotations

import pandas as pd
import ta


def get_volatility(
    df: pd.DataFrame,
    atr_short: int = 10,
    atr_long: int = 50
) -> dict:

    if df.empty or len(df) < atr_long + 1:
        return {
            "atr": None,
            "atr_short": None,
            "atr_long": None,
            "ratio": None,
            "regime": "UNKNOWN"
        }

    data = df.copy()

    atr_short_indicator = ta.volatility.AverageTrueRange(
        data["High"], data["Low"], data["Close"], window=atr_short
    )
    atr_long_indicator = ta.volatility.AverageTrueRange(
        data["High"], data["Low"], data["Close"], window=atr_long
    )

    data["atr_short"] = atr_short_indicator.average_true_range()
    data["atr_long"] = atr_long_indicator.average_true_range()

    last_short = float(data["atr_short"].iloc[-1])
    last_long = float(data["atr_long"].iloc[-1])

    if last_long == 0:
        return {
            "atr": last_short,
            "atr_short": last_short,
            "atr_long": last_long,
            "ratio": None,
            "regime": "UNKNOWN"
        }

    ratio = last_short / last_long

    if ratio > 1.25:
        regime = "EXPANSION"
    elif ratio < 0.75:
        regime = "COMPRESSION"
    else:
        regime = "NORMAL"

    return {
        "atr": last_short,
        "atr_short": last_short,
        "atr_long": last_long,
        "ratio": round(ratio, 2),
        "regime": regime
    }