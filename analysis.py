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


def _market_regime(daily: pd.DataFrame) -> dict:
    """Classifie le régime de marché via ADX (force) + EMA50/200 (direction).
    ADX > 25 : marché qui tend clairement. ADX < 20 : range.
    """
    adx_ind = ta.trend.ADXIndicator(daily["High"], daily["Low"], daily["Close"], window=14)
    adx_val = adx_ind.adx().iloc[-1]
    plus_di = adx_ind.adx_pos().iloc[-1]
    minus_di = adx_ind.adx_neg().iloc[-1]

    ema50 = ta.trend.EMAIndicator(daily["Close"], window=50).ema_indicator().iloc[-1]
    ema200 = ta.trend.EMAIndicator(daily["Close"], window=200).ema_indicator().iloc[-1]

    if pd.isna(adx_val) or pd.isna(ema200):
        return {"regime": "Indéterminé", "adx": None}

    if adx_val >= 25:
        if plus_di > minus_di and ema50 > ema200:
            regime = "Bullish Trend"
        elif minus_di > plus_di and ema50 < ema200:
            regime = "Bearish Trend"
        else:
            regime = "Tendance indécise"
    else:
        regime = "Range"

    return {"regime": regime, "adx": round(float(adx_val), 1)}


def _swing_points(df: pd.DataFrame, lookback: int = 5):
    """Détecte les swing highs/lows : un pivot local sur `lookback` bougies de chaque côté."""
    highs, lows = df["High"], df["Low"]
    swing_highs, swing_lows = [], []
    for i in range(lookback, len(df) - lookback):
        window_h = highs.iloc[i - lookback : i + lookback + 1]
        if highs.iloc[i] == window_h.max():
            swing_highs.append(float(highs.iloc[i]))
        window_l = lows.iloc[i - lookback : i + lookback + 1]
        if lows.iloc[i] == window_l.min():
            swing_lows.append(float(lows.iloc[i]))
    return swing_highs, swing_lows


def _structure_bos(df: pd.DataFrame, lookback: int = 5) -> dict:
    """Détecte le pattern de structure (HH/HL ou LH/LL) et un BOS confirmé par CLÔTURE
    (pas par simple mèche) au-delà du dernier swing high/low.
    """
    swing_highs, swing_lows = _swing_points(df, lookback)
    last_close = float(df["Close"].iloc[-1])

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return {"pattern": "Indéterminé", "bos": None, "last_swing_high": None, "last_swing_low": None}

    last_sh, prev_sh = swing_highs[-1], swing_highs[-2]
    last_sl, prev_sl = swing_lows[-1], swing_lows[-2]

    if last_sh > prev_sh and last_sl > prev_sl:
        pattern = "HH/HL (haussier)"
    elif last_sh < prev_sh and last_sl < prev_sl:
        pattern = "LH/LL (baissier)"
    else:
        pattern = "Mixte"

    bos = None
    if last_close > last_sh:
        bos = "bullish"
    elif last_close < last_sl:
        bos = "bearish"

    return {"pattern": pattern, "bos": bos, "last_swing_high": last_sh, "last_swing_low": last_sl}


def _mtf_alignment(symbol: str) -> dict:
    """Évalue le biais directionnel sur D1, H4 et H1 indépendamment (EMA50 vs EMA200 + position du prix)."""
    tf_specs = {
        "D1": {"period": "2y", "interval": "1d", "resample": None},
        "H4": {"period": "60d", "interval": "1h", "resample": "4h"},
        "H1": {"period": "60d", "interval": "1h", "resample": None},
    }
    results = {}
    for label, spec in tf_specs.items():
        df = _fetch(symbol, spec["period"], spec["interval"])
        if spec["resample"]:
            df = df.resample(spec["resample"]).agg(
                {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
            ).dropna()

        if len(df) < 200:
            results[label] = {"bias": "Données insuffisantes", "score": 40}
            continue

        ema50 = ta.trend.EMAIndicator(df["Close"], window=50).ema_indicator().iloc[-1]
        ema200 = ta.trend.EMAIndicator(df["Close"], window=200).ema_indicator().iloc[-1]
        price = float(df["Close"].iloc[-1])

        if pd.isna(ema50) or pd.isna(ema200):
            results[label] = {"bias": "Neutre", "score": 40}
        elif ema50 > ema200 and price > ema50:
            results[label] = {"bias": "Bullish", "score": 90}
        elif ema50 > ema200:
            results[label] = {"bias": "Pullback (dans tendance haussière)", "score": 65}
        elif ema50 < ema200 and price < ema50:
            results[label] = {"bias": "Bearish", "score": 90}
        elif ema50 < ema200:
            results[label] = {"bias": "Pullback (dans tendance baissière)", "score": 65}
        else:
            results[label] = {"bias": "Neutre", "score": 40}

    return results


def _volatility_state(tf_data: pd.DataFrame) -> dict:
    """Compare l'ATR court terme (10) vs long terme (50) pour détecter un régime de volatilité."""
    atr_short = ta.volatility.AverageTrueRange(
        tf_data["High"], tf_data["Low"], tf_data["Close"], window=10
    ).average_true_range().iloc[-1]
    atr_long = ta.volatility.AverageTrueRange(
        tf_data["High"], tf_data["Low"], tf_data["Close"], window=50
    ).average_true_range().iloc[-1]

    if pd.isna(atr_short) or pd.isna(atr_long) or atr_long == 0:
        return {"state": "Indéterminé", "ratio": None}

    ratio = float(atr_short / atr_long)
    if ratio > 1.25:
        state = "Élevée"
    elif ratio < 0.75:
        state = "Compressée"
    else:
        state = "Normale"
    return {"state": state, "ratio": round(ratio, 2)}


def _confluence_score(regime: dict, mtf: dict, momentum_dir: str, structure_bos: dict, direction: str) -> int:
    """Score pondéré 0-100 qui évalue à quel point tout converge dans la direction `direction` (UP/DOWN)."""
    score = 0.0

    # Regime (30 pts) : le régime doit correspondre au sens du trade
    wanted_regime = "Bullish Trend" if direction == "UP" else "Bearish Trend"
    if regime["regime"] == wanted_regime:
        score += 30
    elif regime["regime"] == "Range":
        score += 10

    # Alignement multi-timeframe (30 pts) : moyenne des scores TF pondérée par cohérence de biais
    wanted_bias_keywords = ["Bullish"] if direction == "UP" else ["Bearish"]
    tf_scores = []
    for tf_info in mtf.values():
        if any(k in tf_info["bias"] for k in wanted_bias_keywords):
            tf_scores.append(tf_info["score"])
        else:
            tf_scores.append(0)
    if tf_scores:
        score += 30 * (sum(tf_scores) / (len(tf_scores) * 90))  # normalisé sur score max 90/TF

    # Momentum (20 pts)
    if momentum_dir == direction:
        score += 20

    # Structure / BOS (20 pts)
    wanted_bos = "bullish" if direction == "UP" else "bearish"
    wanted_pattern = "HH/HL (haussier)" if direction == "UP" else "LH/LL (baissier)"
    if structure_bos.get("bos") == wanted_bos:
        score += 12
    if structure_bos.get("pattern") == wanted_pattern:
        score += 8

    return round(min(100, max(0, score)))



def run_analysis(symbol: str, timeframe: str = "H4") -> dict:
    timeframe = timeframe.upper()
    if timeframe not in TIMEFRAME_CONFIG:
        raise ValueError(f"Timeframe non supporté : {timeframe} (attendu: H1 ou H4)")

    cfg = TIMEFRAME_CONFIG[timeframe]
    daily = _fetch(symbol, period="2y", interval="1d")
    tf_data = _fetch(symbol, period=cfg["fetch_period"], interval=cfg["fetch_interval"])
    if cfg["resample"]:
        tf_data = tf_data.resample(cfg["resample"]).agg(
            {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
        ).dropna()

    price = float(tf_data["Close"].iloc[-1])

    trend = _trend_layer(daily)             # filtre simple EMA50/200 (legacy, gardé pour compat)
    momentum = _momentum_layer(tf_data)      # RSI + MACD sur le timeframe demandé
    structure = _structure_layer(tf_data, price)  # support/résistance simples (pour le SL/TP)
    atr = float(_atr(tf_data))

    regime = _market_regime(daily)
    structure_bos = _structure_bos(tf_data)
    mtf = _mtf_alignment(symbol)
    volatility = _volatility_state(tf_data)

    # --- Décision directionnelle (avant score) ---
    direction = None
    if trend["direction"] == "UP" and momentum["direction"] == "UP":
        direction = "UP"
    elif trend["direction"] == "DOWN" and momentum["direction"] == "DOWN":
        direction = "DOWN"

    # --- Score de confluence 0-100, calculé seulement si une direction candidate existe ---
    confluence = 0
    if direction:
        confluence = _confluence_score(regime, mtf, momentum["direction"], structure_bos, direction)

    # --- Décision finale de signal, basée sur le score ---
    signal = "WAIT"
    if direction == "UP" and confluence >= 60:
        signal = "BUY"
    elif direction == "DOWN" and confluence >= 60:
        signal = "SELL"

    if confluence >= 80:
        setup_quality = "A"
    elif confluence >= 65:
        setup_quality = "B"
    elif confluence >= 50:
        setup_quality = "C"
    else:
        setup_quality = "D"

    # --- Calcul SL / TP1 / TP2 ---
    sl = tp1 = tp2 = invalidation = None
    if signal == "BUY":
        sl = structure["support"] - 0.5 * atr
        risk = price - sl
        tp1 = price + risk * 1.5
        tp2 = price + risk * RISK_REWARD_RATIO
        invalidation = f"Clôture {timeframe} sous {round(sl, 5)}"
    elif signal == "SELL":
        sl = structure["resistance"] + 0.5 * atr
        risk = sl - price
        tp1 = price - risk * 1.5
        tp2 = price - risk * RISK_REWARD_RATIO
        invalidation = f"Clôture {timeframe} au-dessus de {round(sl, 5)}"

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "price": round(price, 5),
        "signal": signal,
        "confluence": confluence,       # score 0-100
        "setup_quality": setup_quality,  # A / B / C / D
        "sl": round(sl, 5) if sl is not None else None,
        "tp1": round(tp1, 5) if tp1 is not None else None,
        "tp2": round(tp2, 5) if tp2 is not None else None,
        "invalidation": invalidation,
        "atr": round(atr, 5),
        "trend": trend["direction"],
        "momentum": momentum["direction"],
        "rsi": momentum["rsi"],
        "support": round(float(structure["support"]), 5),
        "resistance": round(float(structure["resistance"]), 5),
        "regime": regime["regime"],
        "adx": regime["adx"],
        "structure_pattern": structure_bos["pattern"],
        "bos": structure_bos["bos"],
        "volatility_state": volatility["state"],
        "mtf": mtf,  # {"D1": {"bias":..., "score":...}, "H4": {...}, "H1": {...}}
    }

