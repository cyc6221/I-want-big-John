from lib_dataset import MAX_NUMBER, SECOND_ZONE_MAX
from models.model_historical_frequency import top_predictions_from_scores


MODEL = {
    "id": "markov_transition_v1",
    "label": "Markov Transition V1",
    "family": "statistical",
    "description": "估計上一期號碼到下一期號碼的轉移強度，並以轉移分數排序。",
}

ALPHA = 0.1


def generate_predictions(payload: dict, seed: int | None = None, attempts: int = 0, output_count: int = 6) -> list[dict]:
    history_main = payload["history_main_combos"]
    history_draw = payload["history_draw_combos"]
    main_scores = {number: ALPHA for number in range(1, MAX_NUMBER + 1)}
    second_scores = {number: ALPHA for number in range(1, SECOND_ZONE_MAX + 1)}

    if len(history_main) < 2:
        return []

    transitions = {
        prev_number: {next_number: ALPHA for next_number in range(1, MAX_NUMBER + 1)}
        for prev_number in range(1, MAX_NUMBER + 1)
    }
    second_transitions = {
        prev_number: {next_number: ALPHA for next_number in range(1, SECOND_ZONE_MAX + 1)}
        for prev_number in range(1, SECOND_ZONE_MAX + 1)
    }

    for index in range(len(history_main) - 1):
        prev_numbers = [int(part) for part in history_main[index].split(",")]
        next_numbers = [int(part) for part in history_main[index + 1].split(",")]
        for prev_number in prev_numbers:
            for next_number in next_numbers:
                transitions[prev_number][next_number] += 1.0

        prev_second = int(history_draw[index].split("|")[1])
        next_second = int(history_draw[index + 1].split("|")[1])
        second_transitions[prev_second][next_second] += 1.0

    latest_numbers = [int(part) for part in history_main[-1].split(",")]
    latest_second = int(history_draw[-1].split("|")[1])

    for next_number in range(1, MAX_NUMBER + 1):
        main_scores[next_number] += sum(transitions[prev_number][next_number] for prev_number in latest_numbers)
    for next_second in range(1, SECOND_ZONE_MAX + 1):
        second_scores[next_second] += second_transitions[latest_second][next_second]

    return top_predictions_from_scores(payload, main_scores, second_scores, output_count)
