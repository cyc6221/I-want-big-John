import math
from datetime import datetime, timedelta

from models.model_mean_reversion_utils import (
    build_state,
    build_training_samples_gap_deficit_recent,
    predict_with_linear_scores,
    sigmoid,
    train_logistic_regression,
)


MODEL = {
    "id": "gap_deficit_recent_time_lr_v2",
    "label": "Gap Deficit Recent Time LR V2",
    "family": "mean_reversion",
    "description": "在 gap、deficit、近期頻率之外，再加入月份、星期、年內期數位置的時間特徵。",
}

PHASE_BIN_WIDTH = 9
TIME_SMOOTHING = 1.0


def parse_date(text: str) -> datetime:
    return datetime.strptime(text, "%Y/%m/%d")


def next_draw_date(latest_date_text: str) -> datetime:
    current = parse_date(latest_date_text)
    candidate = current + timedelta(days=1)
    while candidate.weekday() not in (0, 3):
        candidate += timedelta(days=1)
    return candidate


def phase_bin_from_period(period_text: str) -> int:
    sequence = int(period_text[-6:])
    return min((sequence - 1) // PHASE_BIN_WIDTH, 11)


def build_temporal_counts(history_main: list[str], history_dates: list[str], history_periods: list[str]) -> tuple[dict, dict, dict]:
    month_counts = {month: {number: 0 for number in range(1, 39)} for month in range(1, 13)}
    weekday_counts = {weekday: {number: 0 for number in range(1, 39)} for weekday in range(7)}
    phase_counts = {phase: {number: 0 for number in range(1, 39)} for phase in range(12)}

    for combo_key, date_text, period_text in zip(history_main, history_dates, history_periods):
        dt = parse_date(date_text)
        phase = phase_bin_from_period(period_text)
        for part in combo_key.split(","):
            number = int(part)
            month_counts[dt.month][number] += 1
            weekday_counts[dt.weekday()][number] += 1
            phase_counts[phase][number] += 1

    return month_counts, weekday_counts, phase_counts


def temporal_scores_for_context(month_counts: dict, weekday_counts: dict, phase_counts: dict, month: int, weekday: int, phase: int) -> dict[int, float]:
    scores = {}
    month_total = sum(month_counts[month].values())
    weekday_total = sum(weekday_counts[weekday].values())
    phase_total = sum(phase_counts[phase].values())

    for number in range(1, 39):
        month_rate = (month_counts[month][number] + TIME_SMOOTHING) / (month_total + 38 * TIME_SMOOTHING)
        weekday_rate = (weekday_counts[weekday][number] + TIME_SMOOTHING) / (weekday_total + 38 * TIME_SMOOTHING)
        phase_rate = (phase_counts[phase][number] + TIME_SMOOTHING) / (phase_total + 38 * TIME_SMOOTHING)
        scores[number] = month_rate + weekday_rate + phase_rate
    return scores


def build_training_samples_gap_deficit_recent_time(payload: dict, recent_window: int = 30, deficit_mode: str = "z") -> list[tuple[list[float], int]]:
    history_main = payload["history_main_combos"]
    history_dates = payload["history_dates"]
    history_periods = payload["history_periods"]
    base_samples = build_training_samples_gap_deficit_recent(history_main, recent_window=recent_window, deficit_mode=deficit_mode)

    month_counts = {month: {number: 0 for number in range(1, 39)} for month in range(1, 13)}
    weekday_counts = {weekday: {number: 0 for number in range(1, 39)} for weekday in range(7)}
    phase_counts = {phase: {number: 0 for number in range(1, 39)} for phase in range(12)}

    samples = []
    sample_index = 0
    for index in range(len(history_main) - 1):
        current_numbers = [int(part) for part in history_main[index].split(",")]
        current_dt = parse_date(history_dates[index])
        current_phase = phase_bin_from_period(history_periods[index])
        for number in current_numbers:
            month_counts[current_dt.month][number] += 1
            weekday_counts[current_dt.weekday()][number] += 1
            phase_counts[current_phase][number] += 1

        next_dt = parse_date(history_dates[index + 1])
        next_phase = phase_bin_from_period(history_periods[index + 1])
        temporal_scores = temporal_scores_for_context(month_counts, weekday_counts, phase_counts, next_dt.month, next_dt.weekday(), next_phase)

        for number in range(1, 39):
            features, target = base_samples[sample_index]
            extended = features + [temporal_scores[number]]
            samples.append((extended, target))
            sample_index += 1

    return samples


def generate_predictions_with_config(
    payload: dict,
    *,
    recent_window: int = 30,
    deficit_mode: str = "z",
    epochs: int = 6,
    learning_rate: float = 0.08,
    output_count: int = 6,
) -> list[dict]:
    history_main = payload["history_main_combos"]
    history_dates = payload["history_dates"]
    history_periods = payload["history_periods"]
    state = build_state(payload, recent_window=recent_window)
    samples = build_training_samples_gap_deficit_recent_time(payload, recent_window=recent_window, deficit_mode=deficit_mode)
    weights = train_logistic_regression(samples, epochs=epochs, learning_rate=learning_rate)

    month_counts, weekday_counts, phase_counts = build_temporal_counts(history_main, history_dates, history_periods)
    target_dt = next_draw_date(payload["summary"]["date_end"])
    latest_period = payload["summary"]["latest_period"]
    latest_roc_year = int(latest_period[:3])
    target_roc_year = target_dt.year - 1911
    if target_roc_year != latest_roc_year:
        next_period = f"{target_roc_year:03d}{1:06d}"
    else:
        next_period = f"{latest_roc_year:03d}{int(latest_period[-6:]) + 1:06d}"
    next_phase = phase_bin_from_period(next_period)
    temporal_scores = temporal_scores_for_context(month_counts, weekday_counts, phase_counts, target_dt.month, target_dt.weekday(), next_phase)

    main_scores = {}
    for number in range(1, 39):
        if deficit_mode == "raw":
            deficit_value = state["deficits"][number]
        elif deficit_mode == "ratio":
            expected = (6.0 / 38.0) * state["draw_count"]
            deficit_value = state["deficits"][number] / max(expected, 1e-9)
        else:
            deficit_value = state["z_deficits"][number]

        features = [
            1.0,
            math.log1p(state["gaps"][number]),
            deficit_value,
            state["recent_freq"][number],
            temporal_scores[number],
        ]
        score = sum(weight * feature for weight, feature in zip(weights, features))
        main_scores[number] = sigmoid(score)

    return predict_with_linear_scores(payload, main_scores, output_count)


def generate_predictions(payload: dict, seed: int | None = None, attempts: int = 0, output_count: int = 6) -> list[dict]:
    return generate_predictions_with_config(
        payload,
        recent_window=30,
        deficit_mode="z",
        epochs=6,
        learning_rate=0.08,
        output_count=output_count,
    )
