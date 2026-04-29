import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "docs" / "assets" / "data"
PAGES_DIR = ROOT / "docs" / "pages"
VENDOR_CHART = ROOT / "docs" / "assets" / "vendor" / "chart.umd.min.js"

GAMES = ("539", "638", "649")
SERIES_KEYS = ("daily", "weekly", "monthly", "yearly")


def require(condition: bool, message: str):
    if not condition:
        raise SystemExit(message)


def validate_json(game: str):
    json_path = DATA_DIR / f"{game}-stats.json"
    require(json_path.exists(), f"Missing stats JSON: {json_path}")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), f"Invalid payload shape: {json_path}")

    summary = payload.get("summary")
    series = payload.get("series")
    require(isinstance(summary, dict), f"Missing summary object: {json_path}")
    require(isinstance(series, dict), f"Missing series object: {json_path}")

    for key in SERIES_KEYS:
        values = series.get(key)
        require(isinstance(values, list), f"Series '{key}' is not a list: {json_path}")
        require(len(values) > 0, f"Series '{key}' is empty: {json_path}")

    print(f"Validated stats JSON: {json_path.name}")


def validate_page(game: str):
    page_path = PAGES_DIR / f"{game}.md"
    require(page_path.exists(), f"Missing page: {page_path}")
    content = page_path.read_text(encoding="utf-8")
    include_tag = f'{{% include lotto/stats.html game="{game}" %}}'
    require(include_tag in content, f"Missing stats include in page: {page_path.name}")
    print(f"Validated page include: {page_path.name}")


def main():
    require(VENDOR_CHART.exists(), f"Missing vendored Chart.js file: {VENDOR_CHART}")
    print(f"Validated vendor asset: {VENDOR_CHART.name}")

    for game in GAMES:
        validate_json(game)
        validate_page(game)

    print("Lotto stats validation passed.")


if __name__ == "__main__":
    main()
