import yfinance as yf
import pandas as pd

from strategy.volatility import get_volatility


def main():
    df = yf.download("GC=F", period="60d", interval="1h", progress=False)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    result = get_volatility(df)

    print("========== TRADINGAI VOLATILITY (H1) ==========")
    print("ATR short :", result["atr_short"])
    print("ATR long  :", result["atr_long"])
    print("Ratio     :", result["ratio"])
    print("Regime    :", result["regime"])


if __name__ == "__main__":
    main()