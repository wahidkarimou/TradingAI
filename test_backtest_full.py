import yfinance as yf
import pandas as pd

from strategy.pipeline import strategy_signal
from backtesting.engine import generate_trades
from backtesting.metrics import get_metrics
from backtesting.report import print_report


SYMBOLS = {
    "XAUUSD": {"yf": "GC=F", "cost": 0.30},
    "EURUSD": {"yf": "EURUSD=X", "cost": 0.00015},
    "BTCUSD": {"yf": "BTC-USD", "cost": 15.0}
}


def load(yf_symbol):
    df = yf.download(yf_symbol, period="5y", interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def main():
    for symbol, cfg in SYMBOLS.items():
        df = load(cfg["yf"])
        split = int(len(df) * 0.7)
        train_df = df.iloc[:split]
        test_df = df.iloc[split:]

        train_trades = generate_trades(train_df, strategy_signal, min_bars=250, cost=cfg["cost"])
        test_trades = generate_trades(test_df, strategy_signal, min_bars=250, cost=cfg["cost"])

        print(f"\n=========== {symbol} ===========")
        print_report(f"{symbol} - TRAIN (70%)", get_metrics(train_trades))
        print_report(f"{symbol} - TEST (30%, hors echantillon)", get_metrics(test_trades))


if __name__ == "__main__":
    main()