import argparse
import sys
from datetime import datetime
from pathlib import Path

from _utils.lotto_result_downloads import (
    DEFAULT_OUT_DIR,
    FIRST_AVAILABLE_YEAR,
    flatten_single_nested_directory,
)


def parse_args() -> argparse.Namespace:
    now = datetime.now()
    parser = argparse.ArgumentParser(
        description="Flatten nested single-folder lotto result directories."
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.from_year > args.to_year:
        print("[error] --from-year cannot be greater than --to-year", file=sys.stderr)
        return 1

    fixed_count = 0

    for year in range(args.from_year, args.to_year + 1):
        year_dir = args.out_dir / str(year)
        if flatten_single_nested_directory(year_dir):
            fixed_count += 1

    print(f"[done] fixed={fixed_count} out_dir={args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
