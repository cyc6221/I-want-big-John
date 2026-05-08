import json

from lib_dataset import PREDICTOR_DATA_PATH
from lib_features import pad2
from models.model_basic_heuristic import MODEL, generate_predictions


def main() -> None:
    payload = json.loads(PREDICTOR_DATA_PATH.read_text(encoding="utf-8"))
    predictions = generate_predictions(payload)

    print(f"模型: {MODEL['id']} - {MODEL['label']}")
    print(f"資料期間: {payload['summary']['date_start']} -> {payload['summary']['date_end']}")
    print("規則: 不重複歷史整組、禁止 3 連號以上、1 與 38 視為相連")
    print()

    for index, item in enumerate(predictions, start=1):
        main_text = " ".join(pad2(n) for n in item["main_numbers"])
        second_text = pad2(item["second_zone"])
        print(
            f"{index}. 第一區: {main_text}  第二區: {second_text}  "
            f"分數: {item['score']:.2f}  最大連號: {item['max_run']}  "
            f"訊號: {', '.join(item['top_signals'])}"
        )


if __name__ == "__main__":
    main()
