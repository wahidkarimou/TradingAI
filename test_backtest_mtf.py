import yfinance as yf
import pandas as pd

from strategy.pipeline import strategy_signal_mtf
from backtesting.engine import generate_trades_mtf
from backtesting.walkforward import get_walkforward_report, passes_validation


SYMBOLS = {
    "XAUUSD": {"yf": "GC=F", "cost": 0.30},
    "EURUSD": {"yf": "EURUSD=X", "cost": 0.00015},
    "BTCUSD": {"yf": "BTC-USD", "cost": 15.0}
}

N_FOLDS = 5


def flatten(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    df.index = pd.to_datetime(df.index)
    return df


def load_all_timeframes(yf_symbol):
    h1 = flatten(yf.download(yf_symbol, period="730d", interval="1h", progress=False))
    d1 = flatten(yf.download(yf_symbol, period="5y", interval="1d", progress=False))
    h4 = h1.resample("4h").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    ).dropna()
    return h1, d1, h4


def main():
    for symbol, cfg in SYMBOLS.items():
        try:
            h1, d1, h4 = load_all_timeframes(cfg["yf"])

            if h1.empty or d1.empty or h4.empty:
                print(f"\n=========== {symbol} : donnees indisponibles, ignore ===========")
                continue

            def signal_fn(history, d1_dir, h4_dir):
                return strategy_signal_mtf(history, d1_dir, h4_dir, threshold=60)

            all_trades = generate_trades_mtf(h1, d1, h4, signal_fn, cost=cfg["cost"])
            fold_metrics = get_walkforward_report(all_trades, total_bars=len(h1), n_folds=N_FOLDS)
            validation = passes_validation(fold_metrics)

            print(f"\n=========== {symbol} — WALK-FORWARD ({N_FOLDS} folds) ===========")
            for i, m in enumerate(fold_metrics):
                if m.get("total_trades", 0) == 0:
                    print(f"Fold {i+1}: aucun trade")
                else:
                    print(f"Fold {i+1}: {m['total_trades']} trades, expectancy {m['expectancy']}R, PF {m['profit_factor']}")

            print("---")
            print("Fraction de folds positifs :", validation["positive_fraction"], f"({validation['valid_folds']} folds valides)")
            print("VALIDATION :", "PASSED" if validation["passed"] else "REJECTED")

        except Exception as e:
            print(f"\n=========== {symbol} : erreur ({e}), ignore ===========")
            continue


if __name__ == "__main__":
    main()