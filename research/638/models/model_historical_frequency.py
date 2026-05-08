from itertools import combinations

from lib_features import circular_run_max, draw_key_of, key_of, pad2


MODEL = {
    "id": "historical_frequency_v1",
    "label": "Historical Frequency V1",
    "family": "statistical",
    "description": "使用全歷史出現次數作為機率分數，直接取 Top-6。",
}


def top_predictions_from_scores(payload: dict, main_scores: dict[int, float], second_scores: dict[int, float], output_count: int) -> list[dict]:
    rules = payload["rules"]
    history_main = set(payload["history_main_combos"])
    history_draw = set(payload["history_draw_combos"])
    max_run_allowed = rules["max_circular_run_allowed"]
    main_rank = sorted(main_scores.items(), key=lambda item: (-item[1], item[0]))
    second_rank = sorted(second_scores.items(), key=lambda item: (-item[1], item[0]))
    predictions = []
    used_draws = set()
    pool_size = min(12, len(main_rank))
    candidate_numbers = [number for number, _ in main_rank[:pool_size]]
    candidate_main_sets = []

    for combo in combinations(candidate_numbers, rules["main_numbers"]):
        numbers = sorted(combo)
        numbers_key = key_of(numbers)
        if circular_run_max(numbers, rules["number_min"], rules["number_max"]) > max_run_allowed:
            continue
        if numbers_key in history_main:
            continue
        main_score = sum(main_scores[n] for n in numbers)
        top_signals = [pad2(n) for n in sorted(numbers, key=lambda n: (-main_scores[n], n))[:3]]
        candidate_main_sets.append((main_score, numbers, top_signals))

    candidate_main_sets.sort(key=lambda item: (-item[0], item[1]))

    for main_score, numbers, top_signals in candidate_main_sets:
        for second_zone, second_score in second_rank:
            draw_key = draw_key_of(numbers, second_zone)
            if draw_key in history_draw or draw_key in used_draws:
                continue
            predictions.append(
                {
                    "main_numbers": numbers,
                    "second_zone": second_zone,
                    "score": main_score + second_score,
                    "max_run": circular_run_max(numbers, rules["number_min"], rules["number_max"]),
                    "top_signals": top_signals,
                }
            )
            used_draws.add(draw_key)
            break
        if len(predictions) >= output_count:
            break

    return predictions


def generate_predictions(payload: dict, seed: int | None = None, attempts: int = 0, output_count: int = 6) -> list[dict]:
    main_scores = {item["number"]: float(item["total_count"]) for item in payload["number_stats"]}
    second_scores = {item["number"]: float(item["total_count"]) for item in payload["second_zone_stats"]}
    return top_predictions_from_scores(payload, main_scores, second_scores, output_count)
