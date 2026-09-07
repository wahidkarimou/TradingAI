import yfinance as yf
import pandas as pd

from strategy.structure import get_structure
from strategy.trend import get_trend
from strategy.momentum import get_momentum
from strategy.volatility import get_volatility
from strategy.regime import get_regime
from strategy.setups import get_setup


def main():
    daily = yf.download("GC=F", period="2y", interval="1d", progress=False)
    if isinstance(daily.columns, pd.MultiIndex):
        daily.columns = daily.columns.get_level_values(0)

    h1 = yf.download("GC=F", period="60d", interval="1h", progress=False)
    if isinstance(h1.columns, pd.MultiIndex):
        h1.columns = h1.columns.get_level_values(0)

    structure_result = get_structure(daily)
    trend_result = get_trend(daily)
    momentum_result = get_momentum(h1)
    volatility_result = get_volatility(h1)
    regime_result = get_regime(trend_result, volatility_result)
    setup_result = get_setup(regime_result, structure_result, momentum_result)

    print("========== TRADINGAI SETUP ==========")
    print("Structure :", structure_result["structure"])
    print("Regime    :", regime_result["regime"])
    print("Momentum  :", momentum_result["direction"])
    print("Setup     :", setup_result["setup"])
    print("Direction :", setup_result["direction"])


if __name__ == "__main__":
    main()