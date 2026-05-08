from models.model_historical_frequency import top_predictions_from_scores


MODEL = {
    "id": "recent_window_v1",
    "label": "Recent Window V1",
    "family": "statistical",
    "description": "使用最近 30 期窗口頻率作為分數，較重視短期活躍度。",
}


def generate_predictions(payload: dict, seed: int | None = None, attempts: int = 0, output_count: int = 6) -> list[dict]:
    main_scores = {item["number"]: float(item["recent_30_count"]) for item in payload["number_stats"]}
    second_scores = {item["number"]: float(item["recent_30_count"]) for item in payload["second_zone_stats"]}
    return top_predictions_from_scores(payload, main_scores, second_scores, output_count)
