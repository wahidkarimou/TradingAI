from __future__ import annotations


def print_report(title: str, metrics: dict, buy_hold_pct: float | None = None) -> None:

    print(f"---------- {title} ----------")

    if buy_hold_pct is not None:
        print("Buy & hold periode  :", f"{buy_hold_pct}%")

    if metrics.get("total_trades", 0) == 0:
        print("Aucun trade genere.")
        return

    print("Trades              :", metrics["total_trades"],
          f"(BULLISH: {metrics['bullish_trades']} / BEARISH: {metrics['bearish_trades']})")
    print("Win rate            :", f"{metrics['win_rate']}%")
    print("Profit factor       :", metrics["profit_factor"])
    print("Expectancy (R)      :", metrics["expectancy"])
    print("Avg win (R)         :", metrics["avg_win"])
    print("Avg loss (R)        :", metrics["avg_loss"])
    print("Max drawdown (R)    :", metrics["max_drawdown_R"])
    print("Max pertes de suite :", metrics["max_consecutive_losses"])