from __future__ import annotations

import pandas as pd


def get_buy_hold_return(df: pd.DataFrame) -> float | None:

    if df.empty or len(df) < 2:
        return None

    start = float(df["Close"].iloc[0])
    end = float(df["Close"].iloc[-1])

    return round((end - start) / start * 100, 2)