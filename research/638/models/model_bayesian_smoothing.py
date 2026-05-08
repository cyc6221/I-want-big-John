from lib_features import pad2
from models.model_historical_frequency import top_predictions_from_scores


MODEL = {
    "id": "bayesian_smoothing_v1",
    "label": "Bayesian Smoothing V1",
    "family": "statistical",
    "description": "在歷史頻率上加入 Laplace smoothing，避免極端估計。",
}

ALPHA = 1.0


def generate_predictions(payload: dict, seed: int | None = None, attempts: int = 0, output_count: int = 6) -> list[dict]:
    draw_count = payload["summary"]["draw_count"]
    main_denominator = (6 * draw_count) + (38 * ALPHA)
    second_denominator = draw_count + (8 * ALPHA)

    main_scores = {
        item["number"]: 6.0 * ((item["total_count"] + ALPHA) / main_denominator)
        for item in payload["number_stats"]
    }
    second_scores = {
        item["number"]: (item["total_count"] + ALPHA) / second_denominator
        for item in payload["second_zone_stats"]
    }
    return top_predictions_from_scores(payload, main_scores, second_scores, output_count)
