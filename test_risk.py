import yfinance as yf
import pandas as pd

from strategy.structure import get_structure
from strategy.trend import get_trend
from strategy.momentum import get_momentum
from strategy.volatility import get_volatility
from strategy.risk import get_risk


def main():
    daily = yf.download("GC=F", period="2y", interval="1d", progress=False)
    if isinstance(daily.columns, pd.MultiIndex):
        daily.columns = daily.columns.get_level_values(0)

    structure_result = get_structure(daily)
    trend_result = get_trend(daily)
    volatility_result = get_volatility(daily)

    entry = float(daily["Close"].iloc[-1])
    direction = trend_result["direction"]
    atr = volatility_result["atr"]

    risk_result = get_risk(entry, structure_result, atr, direction)

    print("========== TRADINGAI RISK (D1) ==========")
    print("Entry        :", risk_result["entry"])
    print("Direction    :", direction)
    print("SL           :", risk_result["sl"])
    print("TP1          :", risk_result["tp1"])
    print("TP2          :", risk_result["tp2"])
    print("R:R (TP2)    :", risk_result["risk_reward_tp2"])
    print("Invalidation :", risk_result["invalidation"])


if __name__ == "__main__":
    main()