from __future__ import annotations


def get_risk(
    entry: float,
    structure_result: dict,
    atr: float,
    direction: str,
    atr_multiplier: float = 0.5,
    tp1_rr: float = 1.5,
    tp2_rr: float = 3.0
) -> dict:

    empty_result = {
        "entry": entry,
        "sl": None,
        "tp1": None,
        "tp2": None,
        "risk_reward_tp2": None,
        "invalidation": None
    }

    if direction not in ("BULLISH", "BEARISH") or atr is None:
        return empty_result

    last_swing_high = structure_result.get("last_swing_high")
    last_swing_low = structure_result.get("last_swing_low")

    if direction == "BULLISH":
        if last_swing_low is None:
            return empty_result

        sl = last_swing_low - atr_multiplier * atr
        risk = entry - sl

        if risk <= 0:
            return {**empty_result, "sl": round(sl, 2), "invalidation": "invalid_risk"}

        tp1 = entry + risk * tp1_rr
        tp2 = entry + risk * tp2_rr
        invalidation = f"close below {round(sl, 2)}"

    else:
        if last_swing_high is None:
            return empty_result

        sl = last_swing_high + atr_multiplier * atr
        risk = sl - entry

        if risk <= 0:
            return {**empty_result, "sl": round(sl, 2), "invalidation": "invalid_risk"}

        tp1 = entry - risk * tp1_rr
        tp2 = entry - risk * tp2_rr
        invalidation = f"close above {round(sl, 2)}"

    return {
        "entry": entry,
        "sl": round(sl, 2),
        "tp1": round(tp1, 2),
        "tp2": round(tp2, 2),
        "risk_reward_tp2": tp2_rr,
        "invalidation": invalidation
    }