"""Rank routes using merge sort and efficiency scoring."""

from __future__ import annotations

from typing import Callable, TypeVar

import pandas as pd

T = TypeVar("T")


def merge_sort(arr: list[T], key_fn: Callable[[T], float], reverse: bool = False) -> list[T]:
    """Sort a list with merge sort."""
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid], key_fn, reverse=reverse)
    right = merge_sort(arr[mid:], key_fn, reverse=reverse)
    merged: list[T] = []
    i = j = 0
    while i < len(left) and j < len(right):
        left_key = key_fn(left[i])
        right_key = key_fn(right[j])
        take_left = left_key >= right_key if reverse else left_key <= right_key
        if take_left:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def run(df: pd.DataFrame) -> list[tuple]:
    """Aggregate route metrics and return efficiency-ranked records."""
    grouped = (
        df.groupby("route_id")
        .agg(avg_passengers=("passengers", "mean"), avg_delay_min=("delay_min", "mean"))
        .reset_index()
    )
    records = [(row.route_id, row.avg_passengers, row.avg_delay_min) for row in grouped.itertuples(index=False)]

    records = merge_sort(records, key_fn=lambda x: x[1], reverse=True)
    print("\nRoutes sorted by average passengers descending:")
    for record in records:
        print(record)

    scored = [
        (route_id, avg_pass, avg_delay, avg_pass / (1 + avg_delay))
        for route_id, avg_pass, avg_delay in records
    ]
    scored = merge_sort(scored, key_fn=lambda x: x[3], reverse=True)

    print("+---------------------------------------------------------------+")
    print("| TOP 5 ROUTES BY EFFICIENCY SCORE                              |")
    print("+--------+--------------+-----------+--------------------+")
    print("| Route  | Avg Pass     | Avg Delay | Efficiency Score   |")
    for route_id, avg_pass, avg_delay, eff_score in scored[:5]:
        print(f"| {route_id:<6} | {avg_pass:>12.2f} | {avg_delay:>9.2f} | {eff_score:>18.4f} |")
    print("| BOTTOM 5 ROUTES BY EFFICIENCY SCORE                          |")
    for route_id, avg_pass, avg_delay, eff_score in scored[-5:]:
        print(f"| {route_id:<6} | {avg_pass:>12.2f} | {avg_delay:>9.2f} | {eff_score:>18.4f} |")
    print("+---------------------------------------------------------------+")

    assert all(scored[i][3] >= scored[i + 1][3] for i in range(len(scored) - 1))
    return scored
