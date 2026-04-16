import argparse
import sys
from datetime import datetime
from pathlib import Path

from _utils.lotto_result_downloads import (
    DEFAULT_ARCHIVE_DIRNAME,
    DEFAULT_OUT_DIR,
    FIRST_AVAILABLE_YEAR,
    extract_archive,
    flatten_single_nested_directory,
)


def parse_args() -> argparse.Namespace:
    now = datetime.now()
    parser = argparse.ArgumentParser(
        description="Extract Taiwan Lottery annual result zip files from raw-data."
    )
    parser.add_argument(
        "--from-year",
        type=int,
        default=FIRST_AVAILABLE_YEAR,
        help=f"first Gregorian year to extract (default: {FIRST_AVAILABLE_YEAR})",
    )
    parser.add_argument(
        "--to-year",
        type=int,
        default=now.year,
        help=f"last Gregorian year to extract (default: {now.year})",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help=f"output directory (default: {DEFAULT_OUT_DIR.as_posix()})",
    )
    parser.add_argument(
        "--archive-dirname",
        default=DEFAULT_ARCHIVE_DIRNAME,
        help=f"zip subdirectory name under out-dir (default: {DEFAULT_ARCHIVE_DIRNAME})",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="re-extract even if the target folder already exists",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.from_year > args.to_year:
        print("[error] --from-year cannot be greater than --to-year", file=sys.stderr)
        return 1

    archive_dir = args.out_dir / args.archive_dirname
    extracted_count = 0

    for year in range(args.from_year, args.to_year + 1):
        archive_path = archive_dir / f"{year}.zip"
        extract_dir = args.out_dir / str(year)

        if not archive_path.exists():
            print(f"[skip] archive not found: {archive_path}")
            continue

        if extract_dir.exists() and not args.overwrite:
            print(f"[skip] extracted folder exists: {extract_dir}")
            continue

        if extract_archive(archive_path, extract_dir):
            flatten_single_nested_directory(extract_dir)
            extracted_count += 1

    print(f"[done] extracted={extracted_count} archive_dir={archive_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
