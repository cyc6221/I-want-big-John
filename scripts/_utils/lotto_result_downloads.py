import json
import shutil
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
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


def build_opener(*, insecure: bool = False) -> urllib.request.OpenerDirector:
    ssl_context = (
        ssl._create_unverified_context() if insecure else ssl.create_default_context()
    )
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


def fetch_download_info(year: int, *, insecure: bool = False) -> dict | None:
    opener = build_opener(insecure=insecure)
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
        if isinstance(exc.reason, ssl.SSLCertVerificationError) and not insecure:
            print(
                f"[error] failed to query {year}: {exc}. "
                "Retry with --insecure if the remote certificate chain is broken.",
                file=sys.stderr,
            )
            return None
        print(f"[error] failed to query {year}: {exc}", file=sys.stderr)
        return None

    if payload.get("rtCode") != 0 or not payload.get("content"):
        message = payload.get("rtMsg") or "no data"
        print(f"[skip] {year}: {message}")
        return None

    return payload["content"]


def download_archive(
    url: str, destination: Path, overwrite: bool, *, insecure: bool = False
) -> bool:
    if destination.exists() and not overwrite:
        print(f"[skip] archive exists: {destination}")
        return False

    opener = build_opener(insecure=insecure)
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        with opener.open(url, timeout=120) as response, destination.open("wb") as fh:
            shutil.copyfileobj(response, fh)
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLCertVerificationError) and not insecure:
            print(
                f"[error] failed to download {destination.name}: {exc}. "
                "Retry with --insecure if the remote certificate chain is broken.",
                file=sys.stderr,
            )
            return False
        print(f"[error] failed to download {destination.name}: {exc}", file=sys.stderr)
        return False

    print(f"[saved] {destination}")
    return True


def open_zipfile(archive_path: Path) -> zipfile.ZipFile:
    try:
        return zipfile.ZipFile(archive_path, metadata_encoding="cp950")
    except TypeError:
        return zipfile.ZipFile(archive_path)


def validate_member_path(member_name: str, temp_dir: Path) -> Path | None:
    normalized = member_name.rstrip("/")
    if not normalized:
        return None

    if normalized.startswith(("/", "\\")):
        raise ValueError(f"unsafe absolute archive path: {member_name}")

    parts = [part for part in normalized.split("/") if part not in ("", ".")]
    if any(part == ".." for part in parts):
        raise ValueError(f"unsafe parent traversal in archive path: {member_name}")
    if not parts:
        return None

    target_path = temp_dir.joinpath(*parts)
    resolved_target = target_path.resolve(strict=False)
    resolved_root = temp_dir.resolve(strict=False)
    try:
        resolved_target.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"unsafe archive path outside target dir: {member_name}") from exc
    return target_path


def extract_archive(archive_path: Path, output_dir: Path) -> bool:
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_output_dir = output_dir.parent / f"{output_dir.name}.tmp-{uuid.uuid4().hex[:8]}"
    temp_output_dir.mkdir(parents=True, exist_ok=False)
    backup_dir = None

    try:
        with open_zipfile(archive_path) as zip_file:
            members = zip_file.infolist()

            top_level_parts = []
            for member in members:
                normalized = member.filename.rstrip("/")
                if not normalized:
                    continue
                parts = [part for part in normalized.split("/") if part not in ("", ".")]
                if any(part == ".." for part in parts):
                    raise ValueError(f"unsafe parent traversal in archive path: {member.filename}")
                if normalized.startswith(("/", "\\")):
                    raise ValueError(f"unsafe absolute archive path: {member.filename}")
                if parts:
                    top_level_parts.append(parts[0])

            flatten_root = None
            unique_top_levels = set(top_level_parts)
            if len(unique_top_levels) == 1:
                flatten_root = next(iter(unique_top_levels))

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

                target_path = validate_member_path("/".join(parts), temp_output_dir)
                if target_path is None:
                    continue

                if member.is_dir():
                    target_path.mkdir(parents=True, exist_ok=True)
                    continue

                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zip_file.open(member) as src, target_path.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
        if output_dir.exists():
            backup_dir = output_dir.with_name(f"{output_dir.name}.backup-{uuid.uuid4().hex[:8]}")
            output_dir.replace(backup_dir)
        temp_output_dir.replace(output_dir)
        if backup_dir and backup_dir.exists():
            shutil.rmtree(backup_dir)
    except (zipfile.BadZipFile, OSError, ValueError) as exc:
        if temp_output_dir.exists():
            shutil.rmtree(temp_output_dir, ignore_errors=True)
        if backup_dir and backup_dir.exists() and not output_dir.exists():
            backup_dir.replace(output_dir)
        if isinstance(exc, zipfile.BadZipFile):
            print(f"[error] invalid zip archive: {archive_path}", file=sys.stderr)
        else:
            print(f"[error] failed to extract {archive_path}: {exc}", file=sys.stderr)
        return False
    finally:
        if temp_output_dir.exists():
            shutil.rmtree(temp_output_dir, ignore_errors=True)
        if backup_dir and backup_dir.exists():
            shutil.rmtree(backup_dir, ignore_errors=True)

    if not output_dir.exists():
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
