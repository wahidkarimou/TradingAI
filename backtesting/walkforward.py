from __future__ import annotations

from backtesting.metrics import get_metrics


def walk_forward_folds(trades: list, total_bars: int, n_folds: int = 5) -> list:

    boundaries = [int(total_bars * i / n_folds) for i in range(n_folds + 1)]
    folds = []

    for k in range(n_folds):
        lo, hi = boundaries[k], boundaries[k + 1]
        fold_trades = [t for t in trades if lo <= t["entry_index"] < hi]
        folds.append(fold_trades)

    return folds


def get_walkforward_report(trades: list, total_bars: int, n_folds: int = 5) -> list:

    folds = walk_forward_folds(trades, total_bars, n_folds)
    return [get_metrics(f) for f in folds]


def passes_validation(
    fold_metrics: list,
    min_expectancy: float = 0.0,
    min_positive_fraction: float = 0.6
) -> dict:

    valid_folds = [m for m in fold_metrics if m.get("total_trades", 0) > 0]

    if not valid_folds:
        return {"passed": False, "positive_fraction": 0.0, "valid_folds": 0}

    positive = sum(1 for m in valid_folds if m["expectancy"] > min_expectancy)
    fraction = positive / len(valid_folds)

    return {
        "passed": fraction >= min_positive_fraction,
        "positive_fraction": round(fraction, 2),
        "valid_folds": len(valid_folds)
    }