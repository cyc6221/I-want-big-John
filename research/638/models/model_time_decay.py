from lib_dataset import MAX_NUMBER, SECOND_ZONE_MAX
from models.model_historical_frequency import top_predictions_from_scores


MODEL = {
    "id": "time_decay_v1",
    "label": "Time Decay V1",
    "family": "statistical",
    "description": "對較近期資料給較高權重的指數衰減模型。",
}

LAMBDA = 0.97
ALPHA = 0.2


def generate_predictions(payload: dict, seed: int | None = None, attempts: int = 0, output_count: int = 6) -> list[dict]:
    history_main = payload["history_main_combos"]
    history_draw = payload["history_draw_combos"]
    main_scores = {number: ALPHA for number in range(1, MAX_NUMBER + 1)}
    second_scores = {number: ALPHA for number in range(1, SECOND_ZONE_MAX + 1)}

    for offset, combo_key in enumerate(reversed(history_main)):
        weight = LAMBDA ** offset
        for part in combo_key.split(","):
            main_scores[int(part)] += weight

    for offset, draw_key in enumerate(reversed(history_draw)):
        weight = LAMBDA ** offset
        second_zone = int(draw_key.split("|")[1])
        second_scores[second_zone] += weight

    return top_predictions_from_scores(payload, main_scores, second_scores, output_count)
