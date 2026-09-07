from __future__ import annotations


def get_metrics(trades: list) -> dict:

    if not trades:
        return {"total_trades": 0}

    r_values = [t["r_multiple"] for t in trades]
    wins = [r for r in r_values if r > 0]
    losses = [r for r in r_values if r <= 0]

    win_rate = len(wins) / len(r_values) * 100
    expectancy = sum(r_values) / len(r_values)

    if losses and sum(losses) != 0:
        profit_factor = sum(wins) / abs(sum(losses))
    else:
        profit_factor = None

    cumulative = 0
    peak = 0
    max_drawdown = 0
    for r in r_values:
        cumulative += r
        peak = max(peak, cumulative)
        max_drawdown = min(max_drawdown, cumulative - peak)

    max_consecutive_losses = 0
    current_streak = 0
    for r in r_values:
        if r <= 0:
            current_streak += 1
            max_consecutive_losses = max(max_consecutive_losses, current_streak)
        else:
            current_streak = 0

    return {
        "total_trades": len(r_values),
        "win_rate": round(win_rate, 1),
        "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
        "expectancy": round(expectancy, 3),
        "avg_win": round(sum(wins) / len(wins), 2) if wins else None,
        "avg_loss": round(sum(losses) / len(losses), 2) if losses else None,
        "max_drawdown_R": round(max_drawdown, 2),
        "max_consecutive_losses": max_consecutive_losses
    }