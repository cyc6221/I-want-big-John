import random

from lib_features import circular_run_max, draw_key_of, key_of


MODEL = {
    "id": "uniform_random_v1",
    "label": "Uniform Random V1",
    "family": "baseline",
    "description": "均勻隨機抽號，作為理論隨機基準；遵守不重複歷史整組與禁止3連號以上。",
}

DEFAULT_ATTEMPTS = 4000
DEFAULT_OUTPUT_COUNT = 6


def build_candidate(payload: dict, history_main: set[str], history_draw: set[str], rng: random.Random) -> dict | None:
    rules = payload["rules"]
    numbers = sorted(rng.sample(range(rules["number_min"], rules["number_max"] + 1), rules["main_numbers"]))
    second_zone = rng.randint(rules["second_zone_min"], rules["second_zone_max"])

    if circular_run_max(numbers, rules["number_min"], rules["number_max"]) >= 3:
        return None
    if key_of(numbers) in history_main:
        return None
    if draw_key_of(numbers, second_zone) in history_draw:
        return None

    return {
        "main_numbers": numbers,
        "second_zone": second_zone,
        "score": 0.0,
        "max_run": circular_run_max(numbers, rules["number_min"], rules["number_max"]),
        "top_signals": [],
    }


def generate_predictions(payload: dict, seed: int | None = None, attempts: int = DEFAULT_ATTEMPTS, output_count: int = DEFAULT_OUTPUT_COUNT) -> list[dict]:
    history_main = set(payload["history_main_combos"])
    history_draw = set(payload["history_draw_combos"])
    rng = random.Random(seed)

    best_by_draw = {}
    for _ in range(attempts):
        candidate = build_candidate(payload, history_main, history_draw, rng)
        if not candidate:
            continue
        draw_key = draw_key_of(candidate["main_numbers"], candidate["second_zone"])
        if draw_key not in best_by_draw:
            best_by_draw[draw_key] = candidate

    return list(best_by_draw.values())[:output_count]
