import csv
import json
import sys
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from _utils.lotto_results import load_result_rows


CSV_PATH = Path("raw-data/lotto-purchases/638.csv")
RESULTS_PATH = Path("research/derived/638_all_years.csv")
OUT_JSON = Path("docs/assets/data/638-purchases.json")
OUT_MD = Path("docs/_list/638-purchases.md")

GAME_KEY = "638"
GAME_TITLE = "威力彩"
RESULT_SOURCE_PATH_COLUMN = "__source_path"
RESULT_SOURCE_LINE_COLUMN = "__source_line"

PRIZE_RULES = {
    (6, True): {"rank": "頭獎", "prize": None, "variable": True},
    (6, False): {"rank": "貳獎", "prize": None, "variable": True},
    (5, True): {"rank": "參獎", "prize": 150000, "variable": False},
    (5, False): {"rank": "肆獎", "prize": 20000, "variable": False},
    (4, True): {"rank": "伍獎", "prize": 4000, "variable": False},
    (4, False): {"rank": "陸獎", "prize": 800, "variable": False},
    (3, True): {"rank": "柒獎", "prize": 400, "variable": False},
    (2, True): {"rank": "捌獎", "prize": 200, "variable": False},
    (3, False): {"rank": "玖獎", "prize": 100, "variable": False},
    (1, True): {"rank": "普獎", "prize": 100, "variable": False},
}

EXPECTED_HEADERS = [
    "purchase_date",
    "draw_no",
    "line_no",
    "price",
    "number1",
    "number2",
    "number3",
    "number4",
    "number5",
    "number6",
    "special",
]


def parse_date(raw: str, *, field: str, line_number: int, required: bool = True) -> datetime | None:
    value = (raw or "").strip()
    if not value:
        if required:
            raise ValueError(f"Missing {field} at line {line_number}")
        return None

    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError(f"Invalid {field} at line {line_number}: {raw!r}")


def format_date(value: datetime | None) -> str:
    return value.strftime("%Y/%m/%d") if value else ""


def parse_money(raw: str, *, field: str, line_number: int, required: bool) -> int | None:
    value = (raw or "").strip().replace(",", "")
    if not value:
        if required:
            raise ValueError(f"Missing {field} at line {line_number}")
        return None

    if not value.isdecimal():
        raise ValueError(f"Invalid {field} at line {line_number}: {raw!r}")

    parsed = int(value)
    if parsed < 0:
        raise ValueError(f"{field} cannot be negative at line {line_number}: {raw!r}")
    return parsed


def parse_required_text(raw: str, *, field: str, line_number: int) -> str:
    value = (raw or "").strip()
    if not value:
        raise ValueError(f"Missing {field} at line {line_number}")
    return value


def parse_positive_int(raw: str, *, field: str, line_number: int) -> int:
    value = (raw or "").strip()
    if not value:
        raise ValueError(f"Missing {field} at line {line_number}")
    if not value.isdecimal():
        raise ValueError(f"Invalid {field} at line {line_number}: {raw!r}")
    parsed = int(value)
    if parsed <= 0:
        raise ValueError(f"{field} must be positive at line {line_number}: {raw!r}")
    return parsed


def parse_ball(raw: str, *, field: str, line_number: int, low: int, high: int) -> int:
    value = (raw or "").strip()
    if not value:
        raise ValueError(f"Missing {field} at line {line_number}")

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {field} at line {line_number}: {raw!r}") from exc

    if parsed < low or parsed > high:
        raise ValueError(f"{field} out of range at line {line_number}: {raw!r}")
    return parsed


def ball_label(value: int) -> str:
    return f"{value:02d}"


def normalize_headers(fieldnames: list[str] | None) -> None:
    actual = [name.strip() for name in (fieldnames or [])]
    missing = [name for name in EXPECTED_HEADERS if name not in actual]
    if missing:
        raise ValueError(f"Missing CSV columns in {CSV_PATH}: {', '.join(missing)}")


def is_blank_row(row: dict[str, str]) -> bool:
    return all((row.get(key) or "").strip() == "" for key in EXPECTED_HEADERS)


def result_source_line(row: dict[str, str], fallback: int) -> int:
    value = (row.get(RESULT_SOURCE_LINE_COLUMN) or "").strip()
    if not value:
        return fallback
    try:
        return int(value)
    except ValueError:
        return fallback


def result_source_label(row: dict[str, str], fallback: int) -> tuple[str, int]:
    source = (row.get(RESULT_SOURCE_PATH_COLUMN) or "").strip() or RESULTS_PATH.as_posix()
    line_number = result_source_line(row, fallback)
    return source, line_number


def parse_result_date(row: dict[str, str], *, field: str, fallback: int) -> datetime:
    source, line_number = result_source_label(row, fallback)
    draw_no = (row.get("期別") or "<missing>").strip() or "<missing>"
    try:
        parsed = parse_date(row.get(field) or "", field=field, line_number=line_number)
    except ValueError as exc:
        raise ValueError(f"Invalid 638 draw result at {source}:{line_number} draw_no={draw_no}: {exc}") from exc
    if parsed is None:
        raise ValueError(f"Missing 638 draw result {field} at {source}:{line_number} draw_no={draw_no}")
    return parsed


def parse_result_ball(row: dict[str, str], *, field: str, fallback: int, low: int, high: int) -> int:
    source, line_number = result_source_label(row, fallback)
    draw_no = (row.get("期別") or "<missing>").strip() or "<missing>"
    try:
        return parse_ball(row.get(field) or "", field=field, line_number=line_number, low=low, high=high)
    except ValueError as exc:
        raise ValueError(f"Invalid 638 draw result at {source}:{line_number} draw_no={draw_no}: {exc}") from exc

def resolve_prize(primary_hits: int, special_hit: bool, result_known: bool) -> dict[str, Any]:
    if not result_known:
        return {
            "rank": "待開獎",
            "prize": None,
            "source": "pending",
            "settled": False,
        }

    rule = PRIZE_RULES.get((primary_hits, special_hit))
    rank = rule["rank"] if rule else "未中獎"

    if rule is None:
        return {
            "rank": rank,
            "prize": 0,
            "source": "auto",
            "settled": True,
        }

    if rule["variable"]:
        return {
            "rank": rank,
            "prize": None,
            "source": "variable",
            "settled": False,
        }

    return {
        "rank": rank,
        "prize": rule["prize"],
        "source": "auto",
        "settled": True,
    }


def load_draw_results() -> dict[str, dict[str, Any]]:
    by_draw_no: dict[str, dict[str, Any]] = {}

    if not RESULTS_PATH.exists():
        return by_draw_no

    for index, row in enumerate(load_result_rows(GAME_KEY, include_manual=True, require_financial=False), start=1):
        draw_no = (row.get("期別") or "").strip()
        draw_date = parse_result_date(row, field="開獎日期", fallback=index)
        numbers = [
            parse_result_ball(row, field=f"獎號{i}", fallback=index, low=1, high=38)
            for i in range(1, 7)
        ]
        result = {
            "draw_no": draw_no,
            "draw_date": format_date(draw_date),
            "numbers": [ball_label(number) for number in numbers],
            "special": ball_label(parse_result_ball(row, field="第二區", fallback=index, low=1, high=8)),
            "number_set": set(numbers),
        }
        if draw_no:
            by_draw_no[draw_no] = result

    return by_draw_no


def read_purchase_rows(results_by_draw_no: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    rows: list[dict[str, Any]] = []

    with CSV_PATH.open(newline="", encoding="utf-8") as file_obj:
        reader = csv.DictReader(file_obj)
        normalize_headers(reader.fieldnames)

        for index, raw_row in enumerate(reader):
            line_number = index + 2
            row = {key: (raw_row.get(key) or "").strip() for key in EXPECTED_HEADERS}
            if is_blank_row(row):
                continue

            purchase_date = parse_date(row["purchase_date"], field="purchase_date", line_number=line_number)
            draw_no = parse_required_text(row["draw_no"], field="draw_no", line_number=line_number)
            line_no_sort = parse_positive_int(row["line_no"], field="line_no", line_number=line_number)
            price = parse_money(row["price"], field="price", line_number=line_number, required=True)
            numbers = [
                parse_ball(row[f"number{i}"], field=f"number{i}", line_number=line_number, low=1, high=38)
                for i in range(1, 7)
            ]

            if len(set(numbers)) != 6:
                raise ValueError(f"Duplicate first-area numbers at line {line_number}")

            numbers = sorted(numbers)
            special = parse_ball(row["special"], field="special", line_number=line_number, low=1, high=8)
            result = results_by_draw_no.get(draw_no)

            primary_hits = 0
            special_hit = False
            if result is not None:
                primary_hits = sum(1 for number in numbers if number in result["number_set"])
                special_hit = ball_label(special) == result["special"]
            prize_result = resolve_prize(primary_hits, special_hit, result is not None)

            rows.append(
                {
                    "index": index,
                    "purchase_date": format_date(purchase_date),
                    "draw_no": draw_no,
                    "line_no": row["line_no"],
                    "line_no_sort": line_no_sort,
                    "price": price,
                    "prize": prize_result["prize"],
                    "prize_rank": prize_result["rank"],
                    "prize_source": prize_result["source"],
                    "settled": prize_result["settled"],
                    "numbers": [ball_label(number) for number in numbers],
                    "special": ball_label(special),
                    "primary_hits": primary_hits,
                    "special_hit": special_hit,
                    "result_known": result is not None,
                    "result": {
                        "draw_no": result["draw_no"],
                        "draw_date": result["draw_date"],
                        "numbers": result["numbers"],
                        "special": result["special"],
                    }
                    if result is not None
                    else None,
                }
            )

    rows.sort(key=lambda item: (item["purchase_date"], item["draw_no"], item["line_no_sort"], item["index"]))
    return rows


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_spent = sum(int(row["price"] or 0) for row in rows)
    settled_spent = sum(int(row["price"] or 0) for row in rows if row["settled"])
    pending_spent = total_spent - settled_spent
    total_prize = sum(int(row["prize"] or 0) for row in rows if row["settled"])
    pending_records = sum(1 for row in rows if not row["settled"])
    settled_records = len(rows) - pending_records
    winning_records = sum(1 for row in rows if row["settled"] and (row["prize"] or 0) > 0)

    return {
        "game": GAME_KEY,
        "title": GAME_TITLE,
        "total_records": len(rows),
        "settled_records": settled_records,
        "pending_records": pending_records,
        "winning_records": winning_records,
        "total_spent": total_spent,
        "settled_spent": settled_spent,
        "pending_spent": pending_spent,
        "known_prize": total_prize,
        "known_net": total_prize - settled_spent,
        "date_start": rows[0]["purchase_date"] if rows else "",
        "date_end": rows[-1]["purchase_date"] if rows else "",
    }


def format_amount(value: int | None) -> str:
    if value is None:
        return "待開獎"
    return f"{value:,}"


def format_prize_amount(row: dict[str, Any]) -> str:
    if row["prize"] is not None:
        return format_amount(row["prize"])
    if row["prize_source"] == "variable":
        return "待填獎金"
    return "待開獎"


def build_description(summary: dict[str, Any]) -> str:
    if summary["total_records"] == 0:
        return "尚無威力彩購買紀錄。"

    description = f"總計花費 {summary['total_spent']:,} 元，已結算中獎 {summary['known_prize']:,} 元。"
    if summary["pending_records"]:
        description += f" 待開獎或未填獎金 {summary['pending_records']} 筆。"
    return description


def front_matter_date(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return datetime.now().strftime("%Y-%m-%d")
    latest = max(parse_date(row["purchase_date"], field="purchase_date", line_number=0) for row in rows)
    return latest.strftime("%Y-%m-%d")


def ball_items(values: list[str], row: dict[str, Any], *, special: bool = False) -> str:
    if not row["result_known"]:
        return " ".join(f"{value}:pending" for value in values)

    if special:
        return " ".join(f"{value}:{'pick' if row['special_hit'] else 'miss'}" for value in values)

    result_numbers = set(row["result"]["numbers"])
    return " ".join(f"{value}:{'pick' if value in result_numbers else 'miss'}" for value in values)


def small_balls_include(items: str, label: str) -> str:
    return "{% include small-balls.html items=\"" + items + "\" label=\"" + label + "\" %}"


def table_cell(value: object) -> str:
    return escape(str(value or ""))


def build_markdown(rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    description = build_description(summary)
    lines = [
        "---",
        "title: 威力彩購買紀錄",
        "permalink: /list/638-purchases/",
        "category: list-638",
        f"date: {front_matter_date(rows)}",
        f"description: {description}",
        "---",
        "",
    ]

    if not rows:
        lines.extend(["尚無威力彩購買紀錄。", ""])
        return "\n".join(lines)

    lines.extend(
        [
            (
                f"從 {summary['date_start']} 開始記錄，總計花費 {summary['total_spent']:,} 元，"
                f"已結算 {summary['settled_records']:,} 筆，已結算中獎 {summary['known_prize']:,} 元，"
                f"已結算淨額 {summary['known_net']:,} 元。"
            ),
            "",
        ]
    )
    if summary["pending_records"]:
        lines.extend(
            [
                f"另有 {summary['pending_records']:,} 筆待開獎或尚未填入中獎金額，花費 {summary['pending_spent']:,} 元。",
                "",
            ]
        )

    lines.extend(
        [
            '<table class="buy-table">',
            "  <thead>",
            "    <tr>",
            '      <th style="text-align:center;">i</th>',
            '      <th style="text-align:center;">購買日</th>',
            '      <th style="text-align:center;">期別</th>',
            '      <th style="text-align:center;">第一區</th>',
            '      <th style="text-align:center;">第二區</th>',
            '      <th style="text-align:center;">獎別</th>',
            '      <th style="text-align:center;">花費</th>',
            '      <th style="text-align:center;">中獎</th>',
            '      <th style="text-align:center;">備註</th>',
            "    </tr>",
            "  </thead>",
            "  <tbody>",
        ]
    )

    for display_index, row in enumerate(rows, start=1):
        draw_label = row["draw_no"]
        note_parts = []
        if row["line_no"]:
            note_parts.append(f"第 {row['line_no']} 注")
        note = " / ".join(note_parts)
        primary = small_balls_include(ball_items(row["numbers"], row), "威力彩第一區選號")
        special = small_balls_include(ball_items([row["special"]], row, special=True), "威力彩第二區選號")

        lines.extend(
            [
                "    <tr>",
                f'      <td style="text-align:center;">{display_index}</td>',
                f'      <td style="text-align:center;">{table_cell(row["purchase_date"])}</td>',
                f'      <td style="text-align:center;">{table_cell(draw_label)}</td>',
                f'      <td style="text-align:center;">{primary}</td>',
                f'      <td style="text-align:center;">{special}</td>',
                f'      <td style="text-align:center;">{table_cell(row["prize_rank"])}</td>',
                f'      <td style="text-align:center;">{format_amount(row["price"])}</td>',
                f'      <td style="text-align:center;">{format_prize_amount(row)}</td>',
                f'      <td style="text-align:center;">{table_cell(note)}</td>',
                "    </tr>",
            ]
        )

    lines.extend(["  </tbody>", "</table>", ""])
    return "\n".join(lines)


def build_payload(rows: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    records = []
    for row in rows:
        records.append({key: value for key, value in row.items() if key not in {"index", "line_no_sort"}})

    return {
        "game": GAME_KEY,
        "title": GAME_TITLE,
        "source": CSV_PATH.as_posix(),
        "summary": summary,
        "records": records,
    }


def main() -> None:
    results_by_draw_no = load_draw_results()
    rows = read_purchase_rows(results_by_draw_no)
    summary = build_summary(rows)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(build_payload(rows, summary), ensure_ascii=False, indent=2), encoding="utf-8")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(build_markdown(rows, summary), encoding="utf-8")

    print(f"Updated: {OUT_JSON}")
    print(f"Updated: {OUT_MD}")
    print(f"   Records: {summary['total_records']}")
    print(f"   Total spent: {summary['total_spent']}")
    print(f"   Known prize: {summary['known_prize']}")


if __name__ == "__main__":
    main()
