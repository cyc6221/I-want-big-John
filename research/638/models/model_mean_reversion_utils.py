import math

from models.model_historical_frequency import top_predictions_from_scores


RECENT_WINDOW = 30
BASE_PROBABILITY = 6.0 / 38.0


def build_state(payload: dict, recent_window: int = RECENT_WINDOW) -> dict:
    history_main = payload["history_main_combos"]
    draw_count = payload["summary"]["draw_count"]
    counts = {number: 0 for number in range(1, 39)}
    last_seen = {number: None for number in range(1, 39)}
    recent_hits = {number: 0 for number in range(1, 39)}

    for index, combo_key in enumerate(history_main):
        numbers = [int(part) for part in combo_key.split(",")]
        is_recent = (draw_count - index) <= recent_window
        for number in numbers:
            counts[number] += 1
            last_seen[number] = index
            if is_recent:
                recent_hits[number] += 1

    gaps = {}
    deficits = {}
    z_deficits = {}
    recent_freq = {}
    for number in range(1, 39):
        seen_at = last_seen[number]
        gap = draw_count - 1 - seen_at if seen_at is not None else draw_count
        expected = BASE_PROBABILITY * draw_count
        deficit = expected - counts[number]
        variance = max(draw_count * BASE_PROBABILITY * (1.0 - BASE_PROBABILITY), 1e-9)
        z_deficit = deficit / math.sqrt(variance)
        gaps[number] = gap
        deficits[number] = deficit
        z_deficits[number] = z_deficit
        recent_freq[number] = recent_hits[number] / max(1, min(draw_count, recent_window))

    second_scores = {item["number"]: float(item["total_count"]) for item in payload["second_zone_stats"]}
    return {
        "draw_count": draw_count,
        "counts": counts,
        "gaps": gaps,
        "deficits": deficits,
        "z_deficits": z_deficits,
        "recent_hits": recent_hits,
        "recent_freq": recent_freq,
        "second_scores": second_scores,
    }


def build_training_samples(history_main: list[str], recent_window: int = RECENT_WINDOW, deficit_mode: str = "z") -> list[tuple[list[float], int]]:
    counts = {number: 0 for number in range(1, 39)}
    last_seen = {number: None for number in range(1, 39)}
    recent_windows: list[list[int]] = []
    samples: list[tuple[list[float], int]] = []

    for index in range(len(history_main) - 1):
        current_numbers = [int(part) for part in history_main[index].split(",")]
        next_numbers = set(int(part) for part in history_main[index + 1].split(","))

        recent_windows.append(current_numbers)
        if len(recent_windows) > recent_window:
            recent_windows.pop(0)

        for number in current_numbers:
            counts[number] += 1
            last_seen[number] = index

        draw_count = index + 1
        recent_counts = {number: 0 for number in range(1, 39)}
        for window_numbers in recent_windows:
            for number in window_numbers:
                recent_counts[number] += 1

        expected = BASE_PROBABILITY * draw_count
        variance = max(draw_count * BASE_PROBABILITY * (1.0 - BASE_PROBABILITY), 1e-9)
        scale = math.sqrt(variance)

        for number in range(1, 39):
            seen_at = last_seen[number]
            gap = draw_count - 1 - seen_at if seen_at is not None else draw_count
            deficit = expected - counts[number]
            if deficit_mode == "raw":
                deficit_value = deficit
            elif deficit_mode == "ratio":
                deficit_value = deficit / max(expected, 1e-9)
            else:
                deficit_value = deficit / scale
            recent_frequency = recent_counts[number] / max(1, len(recent_windows))
            features = [1.0, math.log1p(gap), deficit_value, recent_frequency]
            target = 1 if number in next_numbers else 0
            samples.append((features, target))

    return samples


def build_training_samples_gap_deficit(history_main: list[str]) -> list[tuple[list[float], int]]:
    full_samples = build_training_samples(history_main)
    return [([features[0], features[1], features[2]], target) for features, target in full_samples]


def build_training_samples_gap_deficit_recent(
    history_main: list[str],
    recent_window: int = RECENT_WINDOW,
    deficit_mode: str = "z",
) -> list[tuple[list[float], int]]:
    return build_training_samples(history_main, recent_window=recent_window, deficit_mode=deficit_mode)


def sigmoid(value: float) -> float:
    if value >= 0:
        exp_term = math.exp(-value)
        return 1.0 / (1.0 + exp_term)
    exp_term = math.exp(value)
    return exp_term / (1.0 + exp_term)


def train_logistic_regression(samples: list[tuple[list[float], int]], epochs: int = 6, learning_rate: float = 0.08, l2: float = 0.001) -> list[float]:
    weights = [0.0] * len(samples[0][0]) if samples else []
    if not samples:
        return weights

    sample_count = len(samples)
    for _ in range(epochs):
        gradients = [0.0] * len(weights)
        for features, target in samples:
            score = sum(weight * feature for weight, feature in zip(weights, features))
            prediction = sigmoid(score)
            error = prediction - target
            for idx, feature in enumerate(features):
                gradients[idx] += error * feature

        for idx in range(len(weights)):
            gradients[idx] = (gradients[idx] / sample_count) + (l2 * weights[idx])
            weights[idx] -= learning_rate * gradients[idx]

    return weights


def predict_with_linear_scores(payload: dict, main_scores: dict[int, float], output_count: int = 6) -> list[dict]:
    state = build_state(payload)
    return top_predictions_from_scores(payload, main_scores, state["second_scores"], output_count)
