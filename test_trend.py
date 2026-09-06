import yfinance as yf
import pandas as pd

from strategy.trend import get_trend


def main():
    df = yf.download("GC=F", period="2y", interval="1d", progress=False)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    result = get_trend(df)

    print("========== TRADINGAI TREND (D1) ==========")
    print("Direction :", result["direction"])
    print("EMA Fast  :", result["ema_fast"])
    print("EMA Slow  :", result["ema_slow"])
    print("ADX       :", result["adx"])
    print("Strength  :", result["strength"])


if __name__ == "__main__":
    main()