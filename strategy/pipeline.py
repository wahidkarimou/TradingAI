from __future__ import annotations

from strategy.structure import get_structure
from strategy.trend import get_trend
from strategy.momentum import get_momentum
from strategy.volatility import get_volatility
from strategy.regime import get_regime
from strategy.setups import get_setup
from strategy.risk import get_risk
from strategy.confluence import get_confluence


def strategy_signal(history, threshold: int = 60) -> dict | None:

    structure_result = get_structure(history)
    trend_result = get_trend(history)
    momentum_result = get_momentum(history)
    volatility_result = get_volatility(history)
    regime_result = get_regime(trend_result, volatility_result)
    setup_result = get_setup(regime_result, structure_result, momentum_result)

    direction = None
    if trend_result["direction"] == "BULLISH" and momentum_result["direction"] == "BULLISH":
        direction = "BULLISH"
    elif trend_result["direction"] == "BEARISH" and momentum_result["direction"] == "BEARISH":
        direction = "BEARISH"

    if direction is None:
        return None

    entry = float(history["Close"].iloc[-1])
    risk_result = get_risk(entry, structure_result, volatility_result["atr"], direction)

    confluence_result = get_confluence(
        direction, structure_result, trend_result, momentum_result,
        volatility_result, [trend_result["direction"]], setup_result, risk_result
    )

    if confluence_result["score"] < threshold:
        return None
    if risk_result["sl"] is None or risk_result["tp1"] is None:
        return None

    return {
        "direction": direction,
        "entry": entry,
        "sl": risk_result["sl"],
        "tp1": risk_result["tp1"],
        "score": confluence_result["score"]
    }


def strategy_signal_mtf(h1_history, d1_direction: str, h4_direction: str, threshold: int = 60) -> dict | None:

    if d1_direction is None or h4_direction is None:
        return None

    structure_result = get_structure(h1_history)
    trend_result = get_trend(h1_history)
    momentum_result = get_momentum(h1_history)
    volatility_result = get_volatility(h1_history)
    regime_result = get_regime(trend_result, volatility_result)
    setup_result = get_setup(regime_result, structure_result, momentum_result)

    direction = None
    if h4_direction == "BULLISH" and momentum_result["direction"] == "BULLISH":
        direction = "BULLISH"
    elif h4_direction == "BEARISH" and momentum_result["direction"] == "BEARISH":
        direction = "BEARISH"

    if direction is None:
        return None

    entry = float(h1_history["Close"].iloc[-1])
    risk_result = get_risk(entry, structure_result, volatility_result["atr"], direction)

    mtf_directions = [d1_direction, h4_direction, trend_result["direction"]]

    confluence_result = get_confluence(
        direction, structure_result, trend_result, momentum_result,
        volatility_result, mtf_directions, setup_result, risk_result
    )

    if confluence_result["score"] < threshold:
        return None
    if risk_result["sl"] is None or risk_result["tp1"] is None:
        return None

    return {
        "direction": direction,
        "entry": entry,
        "sl": risk_result["sl"],
        "tp1": risk_result["tp1"],
        "score": confluence_result["score"]
    }