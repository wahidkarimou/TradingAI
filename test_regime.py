import yfinance as yf
import pandas as pd

from strategy.trend import get_trend
from strategy.volatility import get_volatility
from strategy.regime import get_regime


def main():
    daily = yf.download("GC=F", period="2y", interval="1d", progress=False)
    if isinstance(daily.columns, pd.MultiIndex):
        daily.columns = daily.columns.get_level_values(0)

    trend_result = get_trend(daily)
    volatility_result = get_volatility(daily)
    regime_result = get_regime(trend_result, volatility_result)

    print("========== TRADINGAI REGIME (D1) ==========")
    print("Regime            :", regime_result["regime"])
    print("Trend direction   :", regime_result.get("trend_direction"))
    print("Trend strength    :", regime_result.get("trend_strength"))
    print("Volatility regime :", regime_result.get("volatility_regime"))


if __name__ == "__main__":
    main()