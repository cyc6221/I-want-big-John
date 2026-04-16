import json
import shutil
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


API_URL = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/ResultDownload"
REFERER_URL = "https://www.taiwanlottery.com/lotto/history/result_download/"
DEFAULT_OUT_DIR = Path("raw-data/lotto-result-downloads")
DEFAULT_ARCHIVE_DIRNAME = "zip"
FIRST_AVAILABLE_YEAR = 2007
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
)


def build_opener() -> urllib.request.OpenerDirector:
    ssl_context = ssl._create_unverified_context()
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl_context),
    )
    opener.addheaders = [
        ("User-Agent", USER_AGENT),
        ("Accept", "application/json, text/plain, */*"),
        ("Accept-Language", "zh-TW,zh;q=0.9,en;q=0.8"),
        ("Origin", "https://www.taiwanlottery.com"),
        ("Referer", REFERER_URL),
    ]
    return opener


def fetch_download_info(year: int) -> dict | None:
    opener = build_opener()
    query = urllib.parse.urlencode({"year": year})
    url = f"{API_URL}?{query}"
    try:
        with opener.open(url, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"[error] failed to query {year}: HTTP {exc.code} {detail}", file=sys.stderr)
        return None
    except urllib.error.URLError as exc:
        print(f"[error] failed to query {year}: {exc}", file=sys.stderr)
        return None

    if payload.get("rtCode") != 0 or not payload.get("content"):
        message = payload.get("rtMsg") or "no data"
        print(f"[skip] {year}: {message}")
        return None

    return payload["content"]


def download_archive(url: str, destination: Path, overwrite: bool) -> bool:
    if destination.exists() and not overwrite:
        print(f"[skip] archive exists: {destination}")
        return False

    opener = build_opener()
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        with opener.open(url, timeout=120) as response, destination.open("wb") as fh:
            shutil.copyfileobj(response, fh)
    except urllib.error.URLError as exc:
        print(f"[error] failed to download {destination.name}: {exc}", file=sys.stderr)
        return False

    print(f"[saved] {destination}")
    return True


def extract_archive(archive_path: Path, output_dir: Path) -> bool:
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(archive_path, metadata_encoding="cp950") as zip_file:
            members = zip_file.infolist()

            top_level_parts = []
            for member in members:
                normalized = member.filename.rstrip("/")
                if not normalized:
                    continue
                parts = [part for part in normalized.split("/") if part not in ("", ".")]
                if parts:
                    top_level_parts.append(parts[0])

            flatten_root = None
            unique_top_levels = set(top_level_parts)
            if len(unique_top_levels) == 1:
                flatten_root = next(iter(unique_top_levels))

            for child in list(output_dir.iterdir()):
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()

            for member in members:
                normalized = member.filename.rstrip("/")
                if not normalized:
                    continue

                parts = [part for part in normalized.split("/") if part not in ("", ".")]
                if not parts:
                    continue
                if flatten_root and parts[0] == flatten_root:
                    parts = parts[1:]
                if not parts:
                    continue

                relative_path = Path(*parts)
                target_path = output_dir / relative_path

                if member.is_dir():
                    target_path.mkdir(parents=True, exist_ok=True)
                    continue

                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zip_file.open(member) as src, target_path.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
    except zipfile.BadZipFile:
        print(f"[error] invalid zip archive: {archive_path}", file=sys.stderr)
        return False

    print(f"[extracted] {output_dir}")
    return True


def flatten_single_nested_directory(target_dir: Path) -> bool:
    if not target_dir.exists() or not target_dir.is_dir():
        print(f"[skip] target folder not found: {target_dir}")
        return False

    entries = list(target_dir.iterdir())
    directories = [entry for entry in entries if entry.is_dir()]
    files = [entry for entry in entries if entry.is_file()]

    if files or len(directories) != 1:
        print(f"[skip] no single nested folder to flatten: {target_dir}")
        return False

    nested_dir = directories[0]
    nested_entries = list(nested_dir.iterdir())

    for entry in nested_entries:
        shutil.move(str(entry), target_dir / entry.name)

    nested_dir.rmdir()
    print(f"[fixed] flattened {nested_dir} -> {target_dir}")
    return True
