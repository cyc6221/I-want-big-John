from models.model_mean_reversion_utils import build_state, predict_with_linear_scores


MODEL = {
    "id": "deficit_only_v1",
    "label": "Deficit Only V1",
    "family": "mean_reversion",
    "description": "只使用標準化 deficit，越低於理論平均的號碼分數越高。",
}


def build_main_scores(payload: dict, normalize_mode: str = "z", window: int | None = None) -> dict[int, float]:
    state = build_state(payload)
    draw_count = payload["summary"]["draw_count"]
    history_main = payload["history_main_combos"]

    if window is None or window >= draw_count:
        counts = state["counts"]
        effective_draws = draw_count
    else:
        counts = {number: 0 for number in range(1, 39)}
        for combo_key in history_main[-window:]:
            for part in combo_key.split(","):
                counts[int(part)] += 1
        effective_draws = window

    expected = (6.0 / 38.0) * effective_draws
    variance = max(effective_draws * (6.0 / 38.0) * (1.0 - (6.0 / 38.0)), 1e-9)

    main_scores = {}
    for number in range(1, 39):
        deficit = expected - counts[number]
        if normalize_mode == "raw":
            score = deficit
        elif normalize_mode == "ratio":
            score = deficit / max(expected, 1e-9)
        else:
            score = deficit / (variance ** 0.5)
        main_scores[number] = score

    return main_scores


def generate_predictions_with_config(
    payload: dict,
    *,
    normalize_mode: str = "z",
    window: int | None = None,
    output_count: int = 6,
) -> list[dict]:
    main_scores = build_main_scores(payload, normalize_mode=normalize_mode, window=window)
    return predict_with_linear_scores(payload, main_scores, output_count)


def generate_predictions(payload: dict, seed: int | None = None, attempts: int = 0, output_count: int = 6) -> list[dict]:
    return generate_predictions_with_config(payload, normalize_mode="z", window=None, output_count=output_count)
