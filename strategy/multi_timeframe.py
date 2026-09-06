from __future__ import annotations

from strategy.trend import get_trend


def get_mtf_context(dataframes: dict) -> dict:

    context = {}
    for label, df in dataframes.items():
        context[label] = get_trend(df)

    return context


def get_mtf_directions(context: dict) -> list:
    return [info["direction"] for info in context.values()]