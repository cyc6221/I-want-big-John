import random

from lib_features import circular_run_max, draw_key_of, key_of, mean, std, z_score, pad2


MODEL = {
    "id": "basic_heuristic_v1",
    "label": "Basic Heuristic V1",
    "family": "heuristic",
    "description": "歷史頻率 + 近30/60期熱度 + 遺漏期數加權，並加上形狀分數。",
}

DEFAULT_ATTEMPTS = 4000
DEFAULT_OUTPUT_COUNT = 6


def enrich_stats(stats: list[dict], weights: dict[str, float]) -> list[dict]:
    total_counts = [item["total_count"] for item in stats]
    recent30_counts = [item["recent_30_count"] for item in stats]
    recent60_counts = [item["recent_60_count"] for item in stats]
    overdue_counts = [item["last_seen_draws_ago"] for item in stats]

    avg_total = mean(total_counts)
    avg_recent30 = mean(recent30_counts)
    avg_recent60 = mean(recent60_counts)
    avg_overdue = mean(overdue_counts)

    std_total = std(total_counts, avg_total)
    std_recent30 = std(recent30_counts, avg_recent30)
    std_recent60 = std(recent60_counts, avg_recent60)
    std_overdue = std(overdue_counts, avg_overdue)

    scored = []
    for item in stats:
        score = (
            z_score(item["total_count"], avg_total, std_total) * weights["total"]
            + z_score(item["recent_30_count"], avg_recent30, std_recent30) * weights["recent30"]
            + z_score(item["recent_60_count"], avg_recent60, std_recent60) * weights["recent60"]
            + z_score(item["last_seen_draws_ago"], avg_overdue, std_overdue) * weights["overdue"]
        )
        scored.append({**item, "score": score})

    min_score = min(item["score"] for item in scored)
    return [{**item, "weight": max(0.05, item["score"] - min_score + 0.2)} for item in scored]


def weighted_sample(stats: list[dict], count: int, rng: random.Random) -> list[dict]:
    pool = [dict(item) for item in stats]
    chosen = []

    while len(chosen) < count and pool:
        weights = [item["weight"] for item in pool]
        picked = rng.choices(pool, weights=weights, k=1)[0]
        chosen.append(picked)
        pool = [item for item in pool if item["number"] != picked["number"]]

    return chosen


def combo_score(main_pick: list[dict], second_pick: dict, rules: dict) -> tuple[float, int]:
    numbers = sorted(item["number"] for item in main_pick)
    max_run = circular_run_max(numbers, rules["number_min"], rules["number_max"])
    odd_count = sum(1 for n in numbers if n % 2 == 1)
    low_count = sum(1 for n in numbers if n <= 19)
    spread = numbers[-1] - numbers[0]
    decade_count = len({(n - 1) // 10 for n in numbers})
    sum_score = sum(item["score"] for item in main_pick)

    bonus = 0.0
    bonus += 0.18 if max_run == 2 else 0.10
    bonus += 0.10 if 2 <= odd_count <= 4 else 0.0
    bonus += 0.10 if 2 <= low_count <= 4 else 0.0
    bonus += 0.12 if 16 <= spread <= 30 else 0.0
    bonus += 0.08 if decade_count >= 4 else 0.0
    bonus += second_pick["score"] * 0.35
    return sum_score + bonus, max_run


def build_candidate(payload: dict, main_stats: list[dict], second_stats: list[dict], history_main: set[str], history_draw: set[str], rng: random.Random) -> dict | None:
    rules = payload["rules"]
    pick_count = rules["main_numbers"]
    main_pick = sorted(weighted_sample(main_stats, pick_count, rng), key=lambda item: item["number"])
    if len(main_pick) != pick_count:
        return None

    numbers = [item["number"] for item in main_pick]
    second_pick = weighted_sample(second_stats, 1, rng)[0]
    main_key = key_of(numbers)

    if circular_run_max(numbers, rules["number_min"], rules["number_max"]) >= 3:
        return None
    if main_key in history_main:
        return None
    if draw_key_of(numbers, second_pick["number"]) in history_draw:
        return None

    score, max_run = combo_score(main_pick, second_pick, rules)
    return {
        "main_numbers": numbers,
        "second_zone": second_pick["number"],
        "score": score,
        "max_run": max_run,
        "top_signals": [pad2(item["number"]) for item in sorted(main_pick, key=lambda item: item["score"], reverse=True)[:3]],
    }


def generate_predictions(payload: dict, seed: int | None = None, attempts: int = DEFAULT_ATTEMPTS, output_count: int = DEFAULT_OUTPUT_COUNT) -> list[dict]:
    history_main = set(payload["history_main_combos"])
    history_draw = set(payload["history_draw_combos"])
    rng = random.Random(seed)
    main_stats = enrich_stats(payload["number_stats"], {"total": 0.42, "recent30": 0.12, "recent60": 0.18, "overdue": 0.28})
    second_stats = enrich_stats(payload["second_zone_stats"], {"total": 0.40, "recent30": 0.15, "recent60": 0.15, "overdue": 0.30})

    best_by_draw = {}
    for _ in range(attempts):
        candidate = build_candidate(payload, main_stats, second_stats, history_main, history_draw, rng)
        if not candidate:
            continue
        draw_key = draw_key_of(candidate["main_numbers"], candidate["second_zone"])
        current = best_by_draw.get(draw_key)
        if current is None or candidate["score"] > current["score"]:
            best_by_draw[draw_key] = candidate

    return sorted(best_by_draw.values(), key=lambda item: item["score"], reverse=True)[:output_count]
