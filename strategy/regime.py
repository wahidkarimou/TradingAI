from __future__ import annotations


def get_regime(
    trend_result: dict,
    volatility_result: dict
) -> dict:

    direction = trend_result.get("direction")
    strength = trend_result.get("strength")
    vol_regime = volatility_result.get("regime")

    if strength == "UNKNOWN" or vol_regime == "UNKNOWN":
        return {"regime": "UNKNOWN"}

    if strength == "TRENDING" and direction == "BULLISH":
        regime = "BULLISH_TREND"
    elif strength == "TRENDING" and direction == "BEARISH":
        regime = "BEARISH_TREND"
    elif strength == "RANGING" and vol_regime == "COMPRESSION":
        regime = "TIGHT_RANGE"
    elif strength == "RANGING":
        regime = "RANGE"
    elif vol_regime == "EXPANSION":
        regime = "VOLATILE_TRANSITION"
    else:
        regime = "TRANSITION"

    return {
        "regime": regime,
        "trend_direction": direction,
        "trend_strength": strength,
        "volatility_regime": vol_regime
    }