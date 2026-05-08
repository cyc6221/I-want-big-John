import math

from models.model_mean_reversion_utils import build_state, predict_with_linear_scores


MODEL = {
    "id": "gap_only_v1",
    "label": "Gap Only V1",
    "family": "mean_reversion",
    "description": "只使用 gap = 距離上次出現多久，gap 越大分數越高。",
}


def generate_predictions(payload: dict, seed: int | None = None, attempts: int = 0, output_count: int = 6) -> list[dict]:
    state = build_state(payload)
    main_scores = {number: math.log1p(state["gaps"][number]) for number in range(1, 39)}
    return predict_with_linear_scores(payload, main_scores, output_count)
