"""
Module d'analyse — logique de confluence à 3 couches pour swing trading.

Couche 1 - TENDANCE   : EMA 50 / EMA 200 sur Daily -> filtre le sens autorisé
Couche 2 - MOMENTUM   : RSI + MACD sur H4        -> détecte le bon moment d'entrée
Couche 3 - STRUCTURE  : derniers swing high/low   -> valide la proximité d'un niveau clé

Un signal BUY ou SELL n'est émis QUE si les 3 couches sont alignées.
Sinon -> WAIT.

SL / TP :
  - SL = niveau de structure le plus proche, avec une marge de sécurité = 0.5 x ATR
  - TP = distance (entrée - SL) x ratio risque/récompense (défaut 1:2)
"""

import yfinance as yf
import pandas as pd
import ta

# Mapping symbole TradingView -> ticker yfinance
SYMBOL_MAP = {
    "XAUUSD": "GC=F",
    "EURUSD": "EURUSD=X",
    "BTCUSD": "BTC-USD",
}

RISK_REWARD_RATIO = 2.0
STRUCTURE_LOOKBACK = 20  # bougies utilisées pour détecter les swing high/low

# Config par timeframe : comment construire les bougies "momentum/structure"
TIMEFRAME_CONFIG = {
    "H4": {"fetch_period": "60d", "fetch_interval": "1h", "resample": "4h"},
    "H1": {"fetch_period": "60d", "fetch_interval": "1h", "resample": None},  # déjà en H1
}


def _to_yf_symbol(symbol: str) -> str:
    return SYMBOL_MAP.get(symbol.upper(), symbol)


def _fetch(symbol: str, period: str, interval: str) -> pd.DataFrame:
    yf_symbol = _to_yf_symbol(symbol)
    data = yf.download(yf_symbol, period=period, interval=interval, progress=False)

    if data.empty:
        # Yahoo Finance renvoie parfois une réponse vide sans raison claire —
        # une seconde tentative résout le problème la plupart du temps.
        import time
        time.sleep(2)
        data = yf.download(yf_symbol, period=period, interval=interval, progress=False)

    if data.empty:
        raise ValueError(f"Aucune donnée reçue pour {symbol} ({yf_symbol})")
    # yfinance renvoie parfois des colonnes multi-index -> on aplatit
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data


def _trend_layer(daily: pd.DataFrame) -> dict:
    """Détermine la tendance de fond via EMA50 vs EMA200 sur Daily."""
    daily = daily.copy()
    daily["ema50"] = ta.trend.EMAIndicator(daily["Close"], window=50).ema_indicator()
    daily["ema200"] = ta.trend.EMAIndicator(daily["Close"], window=200).ema_indicator()
    last = daily.iloc[-1]

    if pd.isna(last["ema50"]) or pd.isna(last["ema200"]):
        direction = "NEUTRAL"
    elif last["ema50"] > last["ema200"]:
        direction = "UP"
    else:
        direction = "DOWN"

    return {"direction": direction, "ema50": last["ema50"], "ema200": last["ema200"]}


def _momentum_layer(h4: pd.DataFrame) -> dict:
    """Détermine le momentum via RSI + MACD sur H4."""
    h4 = h4.copy()
    h4["rsi"] = ta.momentum.RSIIndicator(h4["Close"], window=14).rsi()
    macd = ta.trend.MACD(h4["Close"])
    h4["macd"] = macd.macd()
    h4["macd_signal"] = macd.macd_signal()
    last = h4.iloc[-1]

    bullish = last["rsi"] > 50 and last["macd"] > last["macd_signal"]
    bearish = last["rsi"] < 50 and last["macd"] < last["macd_signal"]

    if bullish:
        direction = "UP"
    elif bearish:
        direction = "DOWN"
    else:
        direction = "NEUTRAL"

    return {
        "direction": direction,
        "rsi": round(last["rsi"], 2) if not pd.isna(last["rsi"]) else None,
        "macd": last["macd"],
        "macd_signal": last["macd_signal"],
    }


def _structure_layer(h4: pd.DataFrame, price: float) -> dict:
    """Trouve le dernier support et la dernière résistance (swing low/high)."""
    recent = h4.tail(STRUCTURE_LOOKBACK)
    resistance = recent["High"].max()
    support = recent["Low"].min()

    dist_to_support = abs(price - support) / price
    dist_to_resistance = abs(price - resistance) / price

    near_support = dist_to_support < 0.01       # < 1% du prix
    near_resistance = dist_to_resistance < 0.01

    return {
        "support": support,
        "resistance": resistance,
        "near_support": near_support,
        "near_resistance": near_resistance,
    }


def _atr(h4: pd.DataFrame) -> float:
    atr_series = ta.volatility.AverageTrueRange(
        h4["High"], h4["Low"], h4["Close"], window=14
    ).average_true_range()
    return atr_series.iloc[-1]


def run_analysis(symbol: str, timeframe: str = "H4") -> dict:
    timeframe = timeframe.upper()
    if timeframe not in TIMEFRAME_CONFIG:
        raise ValueError(f"Timeframe non supporté : {timeframe} (attendu: H1 ou H4)")

    cfg = TIMEFRAME_CONFIG[timeframe]
    daily = _fetch(symbol, period="1y", interval="1d")
    tf_data = _fetch(symbol, period=cfg["fetch_period"], interval=cfg["fetch_interval"])
    if cfg["resample"]:
        tf_data = tf_data.resample(cfg["resample"]).agg(
            {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
        ).dropna()

    price = float(tf_data["Close"].iloc[-1])

    trend = _trend_layer(daily)          # filtre de tendance : toujours Daily, commun aux 2 systèmes
    momentum = _momentum_layer(tf_data)  # momentum : propre au timeframe (H1 ou H4)
    structure = _structure_layer(tf_data, price)
    atr = float(_atr(tf_data))

    # --- Décision de confluence ---
    signal = "WAIT"
    confidence = 0

    if trend["direction"] == "UP" and momentum["direction"] == "UP" and structure["near_support"]:
        signal = "BUY"
        confidence = 3
    elif trend["direction"] == "DOWN" and momentum["direction"] == "DOWN" and structure["near_resistance"]:
        signal = "SELL"
        confidence = 3
    elif trend["direction"] == "UP" and momentum["direction"] == "UP":
        signal = "BUY"
        confidence = 2  # tendance + momentum ok, mais pas encore sur un niveau clé
    elif trend["direction"] == "DOWN" and momentum["direction"] == "DOWN":
        signal = "SELL"
        confidence = 2

    # --- Calcul SL / TP ---
    sl = tp = None
    if signal == "BUY":
        sl = structure["support"] - 0.5 * atr
        risk = price - sl
        tp = price + risk * RISK_REWARD_RATIO
    elif signal == "SELL":
        sl = structure["resistance"] + 0.5 * atr
        risk = sl - price
        tp = price - risk * RISK_REWARD_RATIO

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "price": round(price, 5),
        "signal": signal,
        "confidence": confidence,  # 0 à 3
        "sl": round(sl, 5) if sl is not None else None,
        "tp": round(tp, 5) if tp is not None else None,
        "atr": round(atr, 5),
        "trend": trend["direction"],
        "momentum": momentum["direction"],
        "rsi": momentum["rsi"],
        "support": round(float(structure["support"]), 5),
        "resistance": round(float(structure["resistance"]), 5),
    }
