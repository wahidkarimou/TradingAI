from __future__ import annotations


def get_setup(
    regime_result: dict,
    structure_result: dict,
    momentum_result: dict
) -> dict:

    regime = regime_result.get("regime")
    structure = structure_result.get("structure")
    momentum_direction = momentum_result.get("direction")

    if regime == "UNKNOWN" or structure is None or momentum_direction is None:
        return {"setup": "NONE", "direction": None}

    if regime == "BULLISH_TREND" and structure == "BULLISH" and momentum_direction == "BULLISH":
        return {"setup": "TREND_CONTINUATION", "direction": "BULLISH"}

    if regime == "BEARISH_TREND" and structure == "BEARISH" and momentum_direction == "BEARISH":
        return {"setup": "TREND_CONTINUATION", "direction": "BEARISH"}

    return {"setup": "NONE", "direction": None}