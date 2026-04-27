import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
DERIVED_DIR = ROOT / "research" / "derived"
OUTPUT_PATH = ROOT / "docs" / "_data" / "latest_draws.json"


@dataclass(frozen=True)
class GameConfig:
    key: str
    filename: str
    display_name: str
    special_label: Optional[str]
    details_path: str
    recommender_path: str


GAMES = (
    GameConfig(
        key="638",
        filename="638_all_years.csv",
        display_name="威力彩",
        special_label="第二區",
        details_path="/638/",
        recommender_path="/recommender_638/",
    ),
    GameConfig(
        key="649",
        filename="649_all_years.csv",
        display_name="大樂透",
        special_label="特別號",
        details_path="/649/",
        recommender_path="/recommender_649/",
    ),
    GameConfig(
        key="539",
        filename="539_all_years.csv",
        display_name="今彩539",
        special_label=None,
        details_path="/539/",
        recommender_path="/recommender_539/",
    ),
)


def load_latest_row(csv_path: Path) -> Dict[str, str]:
    latest_row = None
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if any((value or "").strip() for value in row.values()):
                latest_row = row
    if latest_row is None:
        raise ValueError("No data rows found in {0}".format(csv_path))
    return latest_row


def extract_main_numbers(row: Dict[str, str]) -> List[str]:
    number_keys = sorted(
        (column for column in row if column.startswith("獎號")),
        key=lambda name: int(name[2:]),
    )
    return [
        (row.get(column) or "").strip().zfill(2)
        for column in number_keys
        if (row.get(column) or "").strip()
    ]


def extract_special(row: Dict[str, str], configured_label: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not configured_label:
        return None, None
    value = (row.get(configured_label) or "").strip()
    if value:
        return configured_label, value.zfill(2)
    return None, None


def build_payload() -> Dict[str, Any]:
    games = []

    for game in GAMES:
        row = load_latest_row(DERIVED_DIR / game.filename)
        special_label, special_number = extract_special(row, game.special_label)
        games.append(
            {
                "key": game.key,
                "name": game.display_name,
                "issue": (row.get("期別") or "").strip(),
                "date": (row.get("開獎日期") or "").strip(),
                "numbers": extract_main_numbers(row),
                "special_label": special_label,
                "special_number": special_number,
                "details_path": game.details_path,
                "recommender_path": game.recommender_path,
            }
        )

    return {"games": games}


def main() -> None:
    payload = build_payload()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Wrote {0}".format(OUTPUT_PATH))


if __name__ == "__main__":
    main()
