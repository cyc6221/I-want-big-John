import math

from models.model_mean_reversion_utils import (
    build_state,
    build_training_samples_gap_deficit,
    predict_with_linear_scores,
    sigmoid,
    train_logistic_regression,
)


MODEL = {
    "id": "gap_deficit_lr_v1",
    "label": "Gap Deficit LR V1",
    "family": "mean_reversion",
    "description": "用 gap、標準化 deficit 做輕量 logistic regression。",
}


def generate_predictions(payload: dict, seed: int | None = None, attempts: int = 0, output_count: int = 6) -> list[dict]:
    history_main = payload["history_main_combos"]
    state = build_state(payload)
    samples = build_training_samples_gap_deficit(history_main)
    weights = train_logistic_regression(samples)

    main_scores = {}
    for number in range(1, 39):
        features = [
            1.0,
            math.log1p(state["gaps"][number]),
            state["z_deficits"][number],
        ]
        score = sum(weight * feature for weight, feature in zip(weights, features))
        main_scores[number] = sigmoid(score)

    return predict_with_linear_scores(payload, main_scores, output_count)
