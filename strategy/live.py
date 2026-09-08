from __future__ import annotations

import yfinance as yf
import pandas as pd

from strategy.structure import get_structure
from strategy.trend import get_trend
from strategy.momentum import get_momentum
from strategy.volatility import get_volatility
from strategy.regime import get_regime
from strategy.setups import get_setup
from strategy.risk import get_risk
from strategy.confluence import get_confluence


ASSETS = {
    "XAUUSD": {"yf": "GC=F", "cost": 0.30, "enabled": True},
    "BTCUSD": {"yf": "BTC-USD", "cost": 15.0, "enabled": True},
    "EURUSD": {"yf": "EURUSD=X", "cost": 0.00015, "enabled": False}
}


def _flatten(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    df.index = pd.to_datetime(df.index)
    return df


def _fetch(yf_symbol, period, interval):
    df = yf.download(yf_symbol, period=period, interval=interval, progress=False)
    return _flatten(df)


def get_live_signal(symbol: str, threshold: int = 60) -> dict:

    if symbol not in ASSETS:
        raise ValueError(f"Actif inconnu : {symbol}")

    cfg = ASSETS[symbol]
    yf_symbol = cfg["yf"]

    d1 = _fetch(yf_symbol, "5y", "1d")
    h1 = _fetch(yf_symbol, "730d", "1h")
    h4 = h1.resample("4h").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    ).dropna()

    d1_trend = get_trend(d1)
    h4_trend = get_trend(h4)
    h1_trend = get_trend(h1)
    h1_structure = get_structure(h1)
    h1_momentum = get_momentum(h1)
    h1_volatility = get_volatility(h1)
    regime = get_regime(h1_trend, h1_volatility)
    setup = get_setup(regime, h1_structure, h1_momentum)

    direction = None
    if h4_trend["direction"] == "BULLISH" and h1_momentum["direction"] == "BULLISH":
        direction = "BULLISH"
    elif h4_trend["direction"] == "BEARISH" and h1_momentum["direction"] == "BEARISH":
        direction = "BEARISH"

    entry = float(h1["Close"].iloc[-1])

    if direction is None:
        risk_result = {"entry": entry, "sl": None, "tp1": None, "tp2": None, "invalidation": None}
        confluence_result = {"score": 0, "breakdown": {}}
    else:
        risk_result = get_risk(entry, h1_structure, h1_volatility["atr"], direction)
        mtf_directions = [d1_trend["direction"], h4_trend["direction"], h1_trend["direction"]]
        confluence_result = get_confluence(
            direction, h1_structure, h1_trend, h1_momentum,
            h1_volatility, mtf_directions, setup, risk_result
        )

    if direction and confluence_result["score"] >= threshold and risk_result.get("sl") is not None:
        signal = direction
    else:
        signal = "WAIT"

    return {
        "symbol": symbol,
        "enabled": cfg["enabled"],
        "price": round(entry, 5),
        "signal": signal,
        "confluence_score": confluence_result["score"],
        "confluence_breakdown": confluence_result["breakdown"],
        "sl": risk_result.get("sl"),
        "tp1": risk_result.get("tp1"),
        "tp2": risk_result.get("tp2"),
        "invalidation": risk_result.get("invalidation"),
        "regime": regime.get("regime"),
        "structure_pattern": h1_structure.get("structure"),
        "bos": h1_structure.get("bos"),
        "d1_direction": d1_trend["direction"],
        "h4_direction": h4_trend["direction"],
        "h1_direction": h1_trend["direction"],
        "rsi": round(h1_momentum["rsi"], 2) if h1_momentum.get("rsi") is not None else None,
        "atr": round(h1_volatility["atr"], 5) if h1_volatility.get("atr") is not None else None
    }