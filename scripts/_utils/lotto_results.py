import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
DERIVED_DIR = ROOT / "research" / "derived"
MANUAL_RESULTS_PATH = ROOT / "raw-data" / "manual-lotto-results.csv"

BASE_COLUMNS = ["遊戲名稱", "期別", "開獎日期", "銷售總額", "銷售注數", "總獎金"]
MANUAL_COLUMNS = [
    "game",
    "draw_no",
    "draw_date",
    "number1",
    "number2",
    "number3",
    "number4",
    "number5",
    "number6",
    "special",
]


@dataclass(frozen=True)
class LottoGameConfig:
    key: str
    display_name: str
    filename: str
    main_count: int
    main_min: int
    main_max: int
    special_column: str | None = None
    special_min: int | None = None
    special_max: int | None = None

    @property
    def derived_path(self) -> Path:
        return DERIVED_DIR / self.filename

    @property
    def columns(self) -> list[str]:
        main_columns = [f"獎號{i}" for i in range(1, self.main_count + 1)]
        special_columns = [self.special_column] if self.special_column else []
        return BASE_COLUMNS + main_columns + special_columns


GAME_CONFIGS = {
    "638": LottoGameConfig(
        key="638",
        display_name="威力彩",
        filename="638_all_years.csv",
        main_count=6,
        main_min=1,
        main_max=38,
        special_column="第二區",
        special_min=1,
        special_max=8,
    ),
    "649": LottoGameConfig(
        key="649",
        display_name="大樂透",
        filename="649_all_years.csv",
        main_count=6,
        main_min=1,
        main_max=49,
        special_column="特別號",
        special_min=1,
        special_max=49,
    ),
    "539": LottoGameConfig(
        key="539",
        display_name="今彩539",
        filename="539_all_years.csv",
        main_count=5,
        main_min=1,
        main_max=39,
    ),
}

GAME_ALIASES = {
    config.key: config.key
    for config in GAME_CONFIGS.values()
} | {
    config.display_name: config.key
    for config in GAME_CONFIGS.values()
}


def normalize_game_key(raw: str) -> str:
    key = (raw or "").strip()
    normalized = GAME_ALIASES.get(key)
    if not normalized:
        raise ValueError(f"Unsupported lotto game: {raw!r}")
    return normalized


def infer_game_key_from_path(path: Path) -> str | None:
    name = path.name
    for key, config in GAME_CONFIGS.items():
        if name == config.filename:
            return key
    return None


def parse_date(raw: str, *, field: str, source: Path, line_number: int) -> datetime:
    value = (raw or "").strip()
    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError(f"Invalid {field} at {source}:{line_number}: {raw!r}")


def format_date(raw: str, *, source: Path, line_number: int) -> str:
    return parse_date(raw, field="draw_date", source=source, line_number=line_number).strftime("%Y/%m/%d")


def parse_ball(raw: str, *, field: str, low: int, high: int, source: Path, line_number: int) -> str:
    value = (raw or "").strip()
    if not value:
        raise ValueError(f"Missing {field} at {source}:{line_number}")
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {field} at {source}:{line_number}: {raw!r}") from exc
    if parsed < low or parsed > high:
        raise ValueError(f"{field} out of range at {source}:{line_number}: {raw!r}")
    return f"{parsed:02d}"


def has_financial_values(row: dict[str, str]) -> bool:
    return all((row.get(column) or "").strip() for column in ("銷售總額", "銷售注數", "總獎金"))


def normalize_headers(fieldnames: Iterable[str] | None, expected: list[str], source: Path) -> None:
    actual = [name.strip() for name in (fieldnames or [])]
    missing = [name for name in expected if name not in actual]
    if missing:
        raise ValueError(f"Missing CSV columns in {source}: {', '.join(missing)}")


def is_blank_manual_row(row: dict[str, str]) -> bool:
    return all((row.get(column) or "").strip() == "" for column in MANUAL_COLUMNS)


def read_official_rows(config: LottoGameConfig) -> list[dict[str, str]]:
    if not config.derived_path.exists():
        raise FileNotFoundError(f"CSV not found: {config.derived_path}")

    rows = []
    with config.derived_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        normalize_headers(reader.fieldnames, config.columns, config.derived_path)
        for raw in reader:
            if not any((value or "").strip() for value in raw.values()):
                continue
            rows.append({column: (raw.get(column) or "").strip() for column in config.columns})
    return rows


def manual_row_to_official(config: LottoGameConfig, raw: dict[str, str], line_number: int) -> dict[str, str]:
    source = MANUAL_RESULTS_PATH
    draw_no = (raw.get("draw_no") or "").strip()
    if not draw_no:
        raise ValueError(f"Missing draw_no at {source}:{line_number}")

    numbers = [
        parse_ball(
            raw.get(f"number{i}") or "",
            field=f"number{i}",
            low=config.main_min,
            high=config.main_max,
            source=source,
            line_number=line_number,
        )
        for i in range(1, config.main_count + 1)
    ]
    if len(set(numbers)) != len(numbers):
        raise ValueError(f"Duplicate main numbers at {source}:{line_number}")

    row = {
        "遊戲名稱": config.display_name,
        "期別": draw_no,
        "開獎日期": format_date(raw.get("draw_date") or "", source=source, line_number=line_number),
        "銷售總額": "",
        "銷售注數": "",
        "總獎金": "",
    }

    for index, value in enumerate(sorted(numbers), start=1):
        row[f"獎號{index}"] = value

    if config.special_column:
        row[config.special_column] = parse_ball(
            raw.get("special") or "",
            field="special",
            low=config.special_min or 1,
            high=config.special_max or config.main_max,
            source=source,
            line_number=line_number,
        )

    return row


def read_manual_rows(config: LottoGameConfig) -> list[dict[str, str]]:
    if not MANUAL_RESULTS_PATH.exists():
        return []

    rows = []
    seen_draws = set()
    with MANUAL_RESULTS_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        normalize_headers(reader.fieldnames, MANUAL_COLUMNS, MANUAL_RESULTS_PATH)
        for index, raw in enumerate(reader, start=2):
            row = {column: (raw.get(column) or "").strip() for column in MANUAL_COLUMNS}
            if is_blank_manual_row(row):
                continue
            if normalize_game_key(row.get("game") or "") != config.key:
                continue

            converted = manual_row_to_official(config, row, index)
            draw_no = converted["期別"]
            if draw_no in seen_draws:
                raise ValueError(f"Duplicate manual draw_no for {config.key} at {MANUAL_RESULTS_PATH}:{index}: {draw_no}")
            seen_draws.add(draw_no)
            rows.append(converted)
    return rows


def merge_rows(official_rows: list[dict[str, str]], manual_rows: list[dict[str, str]], config: LottoGameConfig) -> list[dict[str, str]]:
    rows_by_draw_no = {row["期別"]: dict(row) for row in official_rows}

    for manual in manual_rows:
        draw_no = manual["期別"]
        existing = rows_by_draw_no.get(draw_no, {})
        merged = dict(existing)
        for column in config.columns:
            manual_value = (manual.get(column) or "").strip()
            if manual_value:
                merged[column] = manual_value
            elif column not in merged:
                merged[column] = ""
        rows_by_draw_no[draw_no] = merged

    rows = list(rows_by_draw_no.values())
    rows.sort(key=lambda row: (parse_date(row["開獎日期"], field="開獎日期", source=config.derived_path, line_number=0), row["期別"]))
    return rows


def load_result_rows(game_key: str, *, include_manual: bool = True, require_financial: bool = False) -> list[dict[str, str]]:
    config = GAME_CONFIGS[normalize_game_key(game_key)]
    rows = read_official_rows(config)
    if include_manual:
        rows = merge_rows(rows, read_manual_rows(config), config)
    if require_financial:
        rows = [row for row in rows if has_financial_values(row)]
    return rows


def load_result_rows_for_path(csv_path: Path, *, include_manual: bool = True, require_financial: bool = False) -> list[dict[str, str]]:
    game_key = infer_game_key_from_path(csv_path)
    if game_key:
        return load_result_rows(game_key, include_manual=include_manual, require_financial=require_financial)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [
            row
            for row in csv.DictReader(handle)
            if any((value or "").strip() for value in row.values())
        ]
