from __future__ import annotations


def get_confluence(
    direction: str,
    structure_result: dict,
    trend_result: dict,
    momentum_result: dict,
    volatility_result: dict,
    mtf_directions: list,
    setup_result: dict,
    risk_result: dict
) -> dict:

    if direction not in ("BULLISH", "BEARISH"):
        return {"score": 0, "breakdown": {}}

    breakdown = {}

    structure = structure_result.get("structure")
    if structure == direction:
        breakdown["structure"] = 25
    elif structure == "RANGE":
        breakdown["structure"] = 10
    else:
        breakdown["structure"] = 0

    trend_direction = trend_result.get("direction")
    trend_strength = trend_result.get("strength")
    if trend_direction == direction and trend_strength == "TRENDING":
        breakdown["trend"] = 20
    elif trend_direction == direction and trend_strength == "TRANSITION":
        breakdown["trend"] = 10
    else:
        breakdown["trend"] = 0

    breakdown["momentum"] = 15 if momentum_result.get("direction") == direction else 0

    volatility_regime = volatility_result.get("regime")
    if volatility_regime == "NORMAL":
        breakdown["volatility"] = 10
    elif volatility_regime in ("EXPANSION", "COMPRESSION"):
        breakdown["volatility"] = 5
    else:
        breakdown["volatility"] = 0

    if mtf_directions:
        matches = sum(1 for d in mtf_directions if d == direction)
        breakdown["multi_timeframe"] = round(15 * matches / len(mtf_directions))
    else:
        breakdown["multi_timeframe"] = 0

    if setup_result.get("setup") != "NONE" and setup_result.get("direction") == direction:
        breakdown["setup"] = 10
    else:
        breakdown["setup"] = 0

    if risk_result.get("invalidation") not in (None, "invalid_risk"):
        breakdown["risk_reward"] = 5
    else:
        breakdown["risk_reward"] = 0

    score = sum(breakdown.values())

    return {"score": score, "breakdown": breakdown}