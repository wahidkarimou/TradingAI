import yfinance as yf
import pandas as pd

from strategy.pipeline import strategy_signal
from backtesting.engine import generate_trades
from backtesting.metrics import get_metrics
from backtesting.report import print_report
from backtesting.baseline import get_buy_hold_return


SYMBOLS = {
    "XAUUSD": {"yf": "GC=F", "cost": 0.30},
    "EURUSD": {"yf": "EURUSD=X", "cost": 0.00015},
    "BTCUSD": {"yf": "BTC-USD", "cost": 15.0}
}


def load_h4(yf_symbol):
    df = yf.download(yf_symbol, period="730d", interval="1h", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.resample("4h").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    ).dropna()
    return df


def main():
    for symbol, cfg in SYMBOLS.items():
        df = load_h4(cfg["yf"])
        split = int(len(df) * 0.7)

        all_trades = generate_trades(df, strategy_signal, min_bars=250, cost=cfg["cost"])

        train_trades = [t for t in all_trades if t["entry_index"] < split]
        test_trades = [t for t in all_trades if t["entry_index"] >= split]

        train_bh = get_buy_hold_return(df.iloc[:split])
        test_bh = get_buy_hold_return(df.iloc[split:])

        print(f"\n=========== {symbol} (H4, {len(df)} bougies) ===========")
        print_report(f"{symbol} - TRAIN (in-sample)", get_metrics(train_trades), train_bh)
        print_report(f"{symbol} - TEST (hors echantillon)", get_metrics(test_trades), test_bh)


if __name__ == "__main__":
    main()