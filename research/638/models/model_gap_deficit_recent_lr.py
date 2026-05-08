import math

from models.model_mean_reversion_utils import (
    build_state,
    build_training_samples_gap_deficit_recent,
    predict_with_linear_scores,
    sigmoid,
    train_logistic_regression,
)


MODEL = {
    "id": "gap_deficit_recent_lr_v1",
    "label": "Gap Deficit Recent LR V1",
    "family": "mean_reversion",
    "description": "用 gap、標準化 deficit、近期頻率做輕量 logistic regression。",
}


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
    state = build_state(payload, recent_window=recent_window)
    samples = build_training_samples_gap_deficit_recent(
        history_main,
        recent_window=recent_window,
        deficit_mode=deficit_mode,
    )
    weights = train_logistic_regression(samples, epochs=epochs, learning_rate=learning_rate)

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
            state["recent_freq"][number] if recent_window == 30 else state["recent_hits"].get(number, 0) / max(1, min(state["draw_count"], recent_window)),
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
