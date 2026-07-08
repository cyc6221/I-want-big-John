"""Sync lotto result downloads into research/by-game and research/derived.

raw-data/lotto-result-downloads/{Year}/{官方檔名}_{Year}.csv
  -> research/by-game/{game}/{game}_{Year}.csv   (獎號補零成兩位數)
  -> research/derived/{game}_all_years.csv       (逐年串接、單一檔頭)

The derived CSVs are what scripts/run.py reads (stats, purchases, latest
draws), so run this after extract_lotto_results.py and before run.py.
"""

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS_DIR = ROOT / "raw-data" / "lotto-result-downloads"
BY_GAME_DIR = ROOT / "research" / "by-game"
DERIVED_DIR = ROOT / "research" / "derived"

# game key -> official download filename stem
GAME_SOURCES = {
    "539": "今彩539",
    "638": "威力彩",
    "649": "大樂透",
    "649-extra": "大樂透加開獎項",
}

# games aggregated into research/derived/{game}_all_years.csv
DERIVED_GAMES = ["539", "638", "649"]

# Games that must have at least one source CSV in the requested year range.
# A missing source here means the download/extract step failed (or the
# official filename changed); failing loudly prevents run.py from quietly
# publishing stale draw data. 649-extra only exists in years with 加碼活動,
# so it stays optional.
REQUIRED_GAMES = {"539", "638", "649"}

BASE_COLUMNS = ["遊戲名稱", "期別", "開獎日期", "銷售總額", "銷售注數", "總獎金"]


def read_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = [name.strip() for name in next(reader)]
        # Some official annual files carry a trailing empty column; drop it.
        while header and not header[-1]:
            header.pop()
        rows = []
        for row in reader:
            if not any(cell.strip() for cell in row):
                continue
            rows.append([cell.strip() for cell in row[: len(header)]])
    return header, rows


def write_rows(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\r\n")
        writer.writerow(header)
        writer.writerows(rows)


def pad_ball_columns(header: list[str], rows: list[list[str]]) -> list[list[str]]:
    ball_indexes = [i for i, name in enumerate(header) if name not in BASE_COLUMNS]
    padded = []
    for row in rows:
        row = list(row)
        for i in ball_indexes:
            value = row[i].strip()
            if value.isdigit():
                row[i] = f"{int(value):02d}"
        padded.append(row)
    return padded


def sync_by_game(game: str, years: list[int]) -> list[int]:
    source_stem = GAME_SOURCES[game]
    synced = []
    for year in years:
        source = DOWNLOADS_DIR / str(year) / f"{source_stem}_{year}.csv"
        if not source.exists():
            continue
        header, rows = read_rows(source)
        rows = pad_ball_columns(header, rows)
        target = BY_GAME_DIR / game / f"{game}_{year}.csv"
        write_rows(target, header, rows)
        synced.append(year)
    return synced


def rebuild_derived(game: str) -> Path:
    year_files = sorted(
        (BY_GAME_DIR / game).glob(f"{game}_*.csv"),
        key=lambda path: int(path.stem.split("_")[1]),
    )
    if not year_files:
        raise FileNotFoundError(f"No by-game files found for {game}")

    header: list[str] | None = None
    all_rows: list[list[str]] = []
    for path in year_files:
        file_header, rows = read_rows(path)
        if header is None:
            header = file_header
        elif file_header != header:
            raise ValueError(f"Header mismatch in {path}: {file_header} != {header}")
        all_rows.extend(rows)

    target = DERIVED_DIR / f"{game}_all_years.csv"
    assert header is not None
    write_rows(target, header, all_rows)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync downloaded lotto results into research/by-game and research/derived."
    )
    current_year = date.today().year
    parser.add_argument(
        "--from-year", type=int, default=current_year,
        help="first Gregorian year to sync (default: current year; historical files normally stay untouched)",
    )
    parser.add_argument(
        "--to-year", type=int, default=current_year,
        help="last Gregorian year to sync (default: current year)",
    )
    args = parser.parse_args()

    years = list(range(args.from_year, args.to_year + 1))

    missing_required = []
    for game in GAME_SOURCES:
        synced = sync_by_game(game, years)
        if synced:
            print(f"[synced] by-game/{game}: {synced[0]}-{synced[-1]} ({len(synced)} year files)")
        elif game in REQUIRED_GAMES:
            missing_required.append(game)
        else:
            print(f"[skip] by-game/{game}: no download files in range")

    if missing_required:
        for game in missing_required:
            source_stem = GAME_SOURCES[game]
            print(
                f"[error] no source CSV for required game {game} "
                f"({source_stem}_{{year}}.csv) in {args.from_year}-{args.to_year}; "
                "check download_lotto_results.py / extract_lotto_results.py output",
                file=sys.stderr,
            )
        print("[error] aborting before rebuilding research/derived", file=sys.stderr)
        return 1

    for game in DERIVED_GAMES:
        target = rebuild_derived(game)
        print(f"[rebuilt] {target.relative_to(ROOT).as_posix()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
