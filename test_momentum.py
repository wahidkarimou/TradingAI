import yfinance as yf
import pandas as pd

from strategy.momentum import get_momentum


def main():
    df = yf.download("GC=F", period="60d", interval="1h", progress=False)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    result = get_momentum(df)

    print("========== TRADINGAI MOMENTUM (H1) ==========")
    print("Direction    :", result["direction"])
    print("RSI          :", result["rsi"])
    print("MACD         :", result["macd"])
    print("MACD Signal  :", result["macd_signal"])
    print("State        :", result["state"])


if __name__ == "__main__":
    main()