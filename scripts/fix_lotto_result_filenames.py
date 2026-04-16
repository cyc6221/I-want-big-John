import argparse
import sys
from datetime import datetime
from pathlib import Path

from _utils.lotto_result_downloads import DEFAULT_OUT_DIR, FIRST_AVAILABLE_YEAR


def parse_args() -> argparse.Namespace:
    now = datetime.now()
    parser = argparse.ArgumentParser(
        description="Rename lotto result files to {Game}_{Year}.csv."
    )
    parser.add_argument(
        "--from-year",
        type=int,
        default=FIRST_AVAILABLE_YEAR,
        help=f"first Gregorian year to process (default: {FIRST_AVAILABLE_YEAR})",
    )
    parser.add_argument(
        "--to-year",
        type=int,
        default=now.year,
        help=f"last Gregorian year to process (default: {now.year})",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help=f"output directory (default: {DEFAULT_OUT_DIR.as_posix()})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show planned renames without changing files",
    )
    return parser.parse_args()


def normalize_year_dir(year_dir: Path, year: int, dry_run: bool) -> int:
    if not year_dir.exists():
        print(f"[skip] folder not found: {year_dir}")
        return 0

    renamed_count = 0
    for csv_path in sorted(year_dir.glob("*.csv")):
        game_name = csv_path.stem.split("_", 1)[0].strip()
        if not game_name:
            print(f"[skip] cannot derive game name: {csv_path}")
            continue

        target_path = csv_path.with_name(f"{game_name}_{year}.csv")
        if csv_path == target_path:
            continue

        if target_path.exists():
            print(f"[skip] target already exists: {target_path}")
            continue

        print(f"[rename] {csv_path.name} -> {target_path.name}")
        if not dry_run:
            csv_path.rename(target_path)
        renamed_count += 1

    return renamed_count


def main() -> int:
    args = parse_args()

    if args.from_year > args.to_year:
        print("[error] --from-year cannot be greater than --to-year", file=sys.stderr)
        return 1

    renamed_total = 0
    for year in range(args.from_year, args.to_year + 1):
        year_dir = args.out_dir / str(year)
        renamed_total += normalize_year_dir(year_dir, year, args.dry_run)

    mode = "planned" if args.dry_run else "renamed"
    print(f"[done] {mode}={renamed_total} out_dir={args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
