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
from strategy.multi_timeframe import get_mtf_context, get_mtf_directions


def load(symbol, period, interval):
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def main():
    symbol = "GC=F"

    d1 = load(symbol, "2y", "1d")
    h1 = load(symbol, "60d", "1h")
    h4_raw = load(symbol, "60d", "1h")
    h4 = h4_raw.resample("4h").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    ).dropna()

    structure_result = get_structure(d1)
    trend_result = get_trend(d1)
    momentum_result = get_momentum(h1)
    volatility_result = get_volatility(h1)
    regime_result = get_regime(trend_result, volatility_result)
    setup_result = get_setup(regime_result, structure_result, momentum_result)

    entry = float(h1["Close"].iloc[-1])
    direction = trend_result["direction"]
    risk_result = get_risk(entry, structure_result, volatility_result["atr"], direction)

    mtf_context = get_mtf_context({"D1": d1, "H4": h4, "H1": h1})
    mtf_directions = get_mtf_directions(mtf_context)
    
    confluence_result = get_confluence(
        direction, structure_result, trend_result, momentum_result,
        volatility_result, mtf_directions, setup_result, risk_result
    )

    print("========== TRADINGAI CONFLUENCE ==========")
    print("Direction testee :", direction)
    print("Score            :", confluence_result["score"], "/ 100")
    print("MTF Context      :", mtf_context)
    print("Detail           :", confluence_result["breakdown"])
    print("Setup            :", setup_result["setup"])
    print("Entry            :", entry)
    print("SL               :", risk_result["sl"])
    print("TP1              :", risk_result["tp1"])
    print("TP2              :", risk_result["tp2"])


if __name__ == "__main__":
    main()