from __future__ import annotations

import pandas as pd


def detect_swings(
    df: pd.DataFrame,
    left: int = 3,
    right: int = 3
) -> pd.DataFrame:

    if df.empty:
        return df.copy()

    required = {"High", "Low"}
    if not required.issubset(df.columns):
        raise ValueError("DataFrame must contain High and Low columns")

    data = df.copy()

    data["swing_high"] = False
    data["swing_low"] = False

    for i in range(left, len(data) - right):

        high = data["High"].iloc[i]
        low = data["Low"].iloc[i]

        left_highs = data["High"].iloc[i - left:i]
        right_highs = data["High"].iloc[i + 1:i + right + 1]

        left_lows = data["Low"].iloc[i - left:i]
        right_lows = data["Low"].iloc[i + 1:i + right + 1]

        if high > left_highs.max() and high > right_highs.max():
            data.iloc[i, data.columns.get_loc("swing_high")] = True

        if low < left_lows.min() and low < right_lows.min():
            data.iloc[i, data.columns.get_loc("swing_low")] = True

    return data
def enforce_alternation(df: pd.DataFrame) -> pd.DataFrame:

    data = df.copy()
    n = len(data)

    pivots = []
    for i in range(n):
        if data["swing_high"].iloc[i]:
            pivots.append([i, "H", float(data["High"].iloc[i])])
        elif data["swing_low"].iloc[i]:
            pivots.append([i, "L", float(data["Low"].iloc[i])])

    filtered = []
    for p in pivots:
        if filtered and filtered[-1][1] == p[1]:
            if p[1] == "H" and p[2] > filtered[-1][2]:
                filtered[-1] = p
            elif p[1] == "L" and p[2] < filtered[-1][2]:
                filtered[-1] = p
        else:
            filtered.append(p)

    new_high = [False] * n
    new_low = [False] * n
    for pos, kind, _ in filtered:
        if kind == "H":
            new_high[pos] = True
        else:
            new_low[pos] = True

    data["swing_high"] = new_high
    data["swing_low"] = new_low

    return data

def classify_swings(df: pd.DataFrame) -> pd.DataFrame:

    data = df.copy()

    data["swing_type"] = None

    previous_high = None
    previous_low = None

    for i in range(len(data)):

        if data["swing_high"].iloc[i]:
            current_high = data["High"].iloc[i]

            if previous_high is not None:
                if current_high > previous_high:
                    data.iloc[i, data.columns.get_loc("swing_type")] = "HH"
                else:
                    data.iloc[i, data.columns.get_loc("swing_type")] = "LH"

            previous_high = current_high

        elif data["swing_low"].iloc[i]:
            current_low = data["Low"].iloc[i]

            if previous_low is not None:
                if current_low > previous_low:
                    data.iloc[i, data.columns.get_loc("swing_type")] = "HL"
                else:
                    data.iloc[i, data.columns.get_loc("swing_type")] = "LL"

            previous_low = current_low

    return data


def get_structure(df: pd.DataFrame) -> dict:

    if df.empty:
        return {
            "structure": "NEUTRAL",
            "last_swing_high": None,
            "last_swing_low": None,
            "last_swing_type": None,
            "bos": None,
            "swings": []
        }

    data = detect_swings(df)
    data = enforce_alternation(data)
    data = classify_swings(data)

    swings = data[data["swing_type"].notna()].copy()

    if swings.empty:
        return {
            "structure": "NEUTRAL",
            "last_swing_high": None,
            "last_swing_low": None,
            "last_swing_type": None,
            "bos": None,
            "swings": []
        }

    swing_types = swings["swing_type"].tolist()

    bullish_count = sum(
        1 for x in swing_types[-6:]
        if x in ("HH", "HL")
    )

    bearish_count = sum(
        1 for x in swing_types[-6:]
        if x in ("LH", "LL")
    )

    if bullish_count >= 3 and bullish_count > bearish_count:
        structure = "BULLISH"
    elif bearish_count >= 3 and bearish_count > bullish_count:
        structure = "BEARISH"
    else:
        structure = "RANGE"

    last_high = data[data["swing_high"]]
    last_low = data[data["swing_low"]]

    last_swing_high = (
        float(last_high["High"].iloc[-1])
        if not last_high.empty
        else None
    )

    last_swing_low = (
        float(last_low["Low"].iloc[-1])
        if not last_low.empty
        else None
    )

    last_swing_type = swings["swing_type"].iloc[-1]

    close = float(data["Close"].iloc[-1])

    bos = None

    if last_swing_high is not None and close > last_swing_high:
        bos = "BULLISH"

    elif last_swing_low is not None and close < last_swing_low:
        bos = "BEARISH"

    return {
        "structure": structure,
        "last_swing_high": last_swing_high,
        "last_swing_low": last_swing_low,
        "last_swing_type": last_swing_type,
        "bos": bos,
        "swings": swings[
            ["High", "Low", "swing_type"]
        ].to_dict("records")
    }