import csv
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import DefaultDict, List, TypedDict


CSV_PATH = Path("raw-data/all-instants.csv")
ARTICLES_DIR = Path("docs/_articles/all-instants")

PUBLISHED_RE = re.compile(r"^published:\s*(\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE)
DATE_RE = re.compile(r"^date:\s*(\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE)
MANUAL_TEST_RE = re.compile(r"^## 親自實測\s*\n(?:.*\n?)*\Z", re.MULTILINE)


class ManualTestRow(TypedDict):
    index: int
    date: datetime
    price: int
    prize: int


def parse_date(raw: str) -> datetime:
    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw.strip(), fmt)
        except ValueError:
            pass
    raise ValueError(f"Invalid date format: {raw!r}")


def detect_newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def load_rows_by_game() -> DefaultDict[str, List[ManualTestRow]]:
    rows_by_game: DefaultDict[str, List[ManualTestRow]] = defaultdict(list)
    with CSV_PATH.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for idx, row in enumerate(reader):
            game = (row.get("game") or "").strip()
            if not game:
                continue

            try:
                parsed_date = parse_date((row.get("date") or "").strip())
                parsed_price = int((row.get("price") or "0").strip())
                parsed_prize = int((row.get("prize") or "0").strip())
            except (TypeError, ValueError) as exc:
                line_number = idx + 2
                raise ValueError(
                    f"Failed to parse CSV row index {idx} "
                    f"(line {line_number}, game={game!r})"
                ) from exc

            rows_by_game[game].append(
                {
                    "index": idx,
                    "date": parsed_date,
                    "price": parsed_price,
                    "prize": parsed_prize,
                }
            )

    for items in rows_by_game.values():
        items.sort(key=lambda item: (item["date"], item["index"]))

    return rows_by_game


def build_test_note(price: int, prize: int) -> str:
    if prize <= 0:
        return f"打龜（-${price}）"
    if prize < price:
        return f"中獎，倒虧（+${prize}）"
    if prize == price:
        return f"中獎，沒賠（+${prize}）"
    return f"中獎，有賺（+${prize}）"


def build_manual_test_section(rows: List[ManualTestRow]) -> str:
    lines = ["## 親自實測", ""]
    for row in rows:
        date_str = row["date"].strftime("%Y/%m/%d")
        lines.append(f"- {date_str}: {build_test_note(row['price'], row['prize'])}")
    return "\n".join(lines)


def update_article(path: Path, rows_by_game: DefaultDict[str, List[ManualTestRow]]) -> bool:
    original = path.read_text(encoding="utf-8")
    newline = detect_newline(original)
    had_trailing_newline = original.endswith(("\r\n", "\n"))
    normalized_original = original.replace("\r\n", "\n")
    issue = path.stem
    rows = rows_by_game.get(issue, [])

    date_match = DATE_RE.search(normalized_original)
    if not date_match:
        raise ValueError(f"Missing date in front matter: {path}")
    published_value = rows[-1]["date"].strftime("%Y-%m-%d") if rows else date_match.group(1)

    updated = PUBLISHED_RE.sub(f"published: {published_value}", normalized_original, count=1)
    manual_test_section = build_manual_test_section(rows)
    if not MANUAL_TEST_RE.search(updated):
        raise ValueError(f"Missing manual test section: {path}")
    updated = MANUAL_TEST_RE.sub(manual_test_section, updated)
    if had_trailing_newline and not updated.endswith("\n"):
        updated += "\n"
    if newline == "\r\n":
        updated = updated.replace("\n", "\r\n")

    if updated == original:
        return False

    path.write_text(updated, encoding="utf-8", newline="")
    return True


def main() -> None:
    rows_by_game = load_rows_by_game()
    updated_paths: List[Path] = []

    for path in sorted(ARTICLES_DIR.glob("*.md")):
        if update_article(path, rows_by_game):
            updated_paths.append(path)

    print(f"Updated {len(updated_paths)} article(s).")
    for path in updated_paths:
        print(path.as_posix())


if __name__ == "__main__":
    main()
