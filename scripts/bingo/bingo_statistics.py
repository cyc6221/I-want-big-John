"""Descriptive BINGO statistics built from the full draw history.

These numbers only describe past results; they say nothing about the next draw.
"""

from collections import Counter

NUMBER_MIN, NUMBER_MAX = 1, 80
WINDOW_SIZES = (10, 50, 100)
DISCLAIMER = "僅描述歷史開獎結果，不代表對下一期的預測。"


def build_stats(draws: list[dict]) -> dict:
    """`draws` may be in any order; each needs draw_no, numbers, big_small, odd_even."""
    ordered = sorted(draws, key=lambda d: int(d["draw_no"]), reverse=True)  # newest first
    all_numbers = range(NUMBER_MIN, NUMBER_MAX + 1)

    totals = Counter(n for d in ordered for n in d["numbers"])
    window_counts = {
        size: Counter(n for d in ordered[:size] for n in d["numbers"]) for size in WINDOW_SIZES
    }

    draws_since_last: dict[int, int | None] = {n: None for n in all_numbers}
    for index, d in enumerate(ordered):
        for n in d["numbers"]:
            if draws_since_last[n] is None:
                draws_since_last[n] = index
        if all(v is not None for v in draws_since_last.values()):
            break

    numbers = {}
    for n in all_numbers:
        entry = {"total": totals[n]}
        for size in WINDOW_SIZES:
            entry[f"last_{size}"] = window_counts[size][n]
        entry["draws_since_last"] = draws_since_last[n]  # 0 = drawn in the latest draw; null = never seen
        numbers[str(n)] = entry

    repeat = None
    if len(ordered) >= 2:
        repeat = len(set(ordered[0]["numbers"]) & set(ordered[1]["numbers"]))

    return {
        "as_of_draw_no": ordered[0]["draw_no"] if ordered else None,
        "total_draws": len(ordered),
        "window_sizes": list(WINDOW_SIZES),
        "numbers": numbers,
        "repeat_with_previous": repeat,
        "odd_even": _label_counts(ordered, "odd_even", ("單", "雙", "和")),
        "big_small": _label_counts(ordered, "big_small", ("大", "小", "和")),
        "disclaimer": DISCLAIMER,
    }


def _label_counts(ordered: list[dict], field: str, labels: tuple[str, ...]) -> dict:
    counts = Counter(d[field] for d in ordered)
    return {label: counts[label] for label in labels}
