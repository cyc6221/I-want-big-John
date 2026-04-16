import argparse
import sys
from datetime import datetime
from pathlib import Path

from _utils.lotto_result_downloads import (
    DEFAULT_ARCHIVE_DIRNAME,
    DEFAULT_OUT_DIR,
    FIRST_AVAILABLE_YEAR,
    download_archive,
    fetch_download_info,
)


def parse_args() -> argparse.Namespace:
    now = datetime.now()
    parser = argparse.ArgumentParser(
        description="Download Taiwan Lottery annual result zip files into raw-data."
    )
    parser.add_argument(
        "--from-year",
        type=int,
        default=FIRST_AVAILABLE_YEAR,
        help=f"first Gregorian year to fetch (default: {FIRST_AVAILABLE_YEAR})",
    )
    parser.add_argument(
        "--to-year",
        type=int,
        default=now.year,
        help=f"last Gregorian year to fetch (default: {now.year})",
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
        help="re-download archives even if they already exist",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show which files are available without downloading",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.from_year > args.to_year:
        print("[error] --from-year cannot be greater than --to-year", file=sys.stderr)
        return 1

    available_count = 0
    downloaded_count = 0
    archive_dir = args.out_dir / args.archive_dirname

    for year in range(args.from_year, args.to_year + 1):
        info = fetch_download_info(year)
        if not info:
            continue

        available_count += 1
        archive_url = info["path"]
        archive_path = archive_dir / f"{year}.zip"

        if args.dry_run:
            print(f"[available] {year}: {archive_url}")
            continue

        if download_archive(archive_url, archive_path, args.overwrite):
            downloaded_count += 1

    if args.dry_run:
        print(f"[done] found {available_count} available year(s)")
    else:
        print(
            f"[done] available={available_count} downloaded={downloaded_count} "
            f"archive_dir={archive_dir}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
