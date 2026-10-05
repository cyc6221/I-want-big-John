"""Fetch BINGO BINGO draw results from the official Taiwan Lottery API.

Pure I/O + validation: no files are read or written here. Any network, HTTP,
JSON or data-shape problem raises BingoFetchError so the calling Action fails
loudly instead of writing bad data.
"""

import json
import ssl
import time
from datetime import date, datetime, timedelta, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen

API_URL = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/BingoResult"
USER_AGENT = "Mozilla/5.0 (compatible; IWBJ-bingo/1.0)"
PAGE_SIZE = 300  # one day has at most 203 draws, so a single page covers it
TIMEOUT_SECONDS = 30
RETRIES = 3

TAIPEI = timezone(timedelta(hours=8))  # Taiwan has no DST
FIRST_DRAW_TIME = (7, 5)  # first draw of each day is 07:05, then every 5 minutes
DRAW_INTERVAL = timedelta(minutes=5)

NUMBER_COUNT = 20
NUMBER_MIN, NUMBER_MAX = 1, 80
TIE = "和"


class BingoFetchError(RuntimeError):
    pass


def build_ssl_context() -> ssl.SSLContext:
    # 台彩憑證缺 Subject Key Identifier，Python 3.13 起預設的
    # VERIFY_X509_STRICT 會拒絕；只放寬 strict 檢查，保留一般憑證驗證。
    # (same workaround as scripts/new_instant_article.py)
    context = ssl.create_default_context()
    context.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return context


SSL_CONTEXT = build_ssl_context()


def today_taipei() -> date:
    return datetime.now(TAIPEI).date()


def _request_json(url: str) -> dict:
    last_error: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urlopen(req, timeout=TIMEOUT_SECONDS, context=SSL_CONTEXT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < RETRIES:
                time.sleep(2 * attempt)
    raise BingoFetchError(f"request failed after {RETRIES} attempts: {url}: {last_error!r}")


def _classify(qualifies: bool, other_qualifies: bool, names: tuple[str, str]) -> str:
    if qualifies:
        return names[0]
    if other_qualifies:
        return names[1]
    return TIE


def classify_big_small(numbers: list[int]) -> str:
    """大 if >=13 of the 20 numbers are 41-80, 小 if >=13 are 1-40, else 和."""
    big = sum(1 for n in numbers if n >= 41)
    return _classify(big >= 13, NUMBER_COUNT - big >= 13, ("大", "小"))


def classify_odd_even(numbers: list[int]) -> str:
    """單 if >=13 of the 20 numbers are odd, 雙 if >=13 are even, else 和."""
    odd = sum(1 for n in numbers if n % 2 == 1)
    return _classify(odd >= 13, NUMBER_COUNT - odd >= 13, ("單", "雙"))


def _normalize_label(value: object) -> str:
    # The API uses a full-width dash when neither side reaches 13.
    return TIE if value in (None, "", "－", "-") else str(value)


def _parse_numbers(raw: object, field: str, draw_no: int) -> list[int]:
    try:
        numbers = [int(n) for n in raw]  # type: ignore[union-attr]
    except (TypeError, ValueError) as exc:
        raise BingoFetchError(f"draw {draw_no}: bad {field}: {raw!r}") from exc
    if len(numbers) != NUMBER_COUNT:
        raise BingoFetchError(f"draw {draw_no}: {field} has {len(numbers)} numbers, expected {NUMBER_COUNT}")
    if len(set(numbers)) != NUMBER_COUNT:
        raise BingoFetchError(f"draw {draw_no}: {field} has duplicate numbers: {numbers}")
    if not all(NUMBER_MIN <= n <= NUMBER_MAX for n in numbers):
        raise BingoFetchError(f"draw {draw_no}: {field} has numbers outside {NUMBER_MIN}-{NUMBER_MAX}: {numbers}")
    return numbers


def _parse_draw(item: dict, draw_time: datetime) -> dict:
    try:
        draw_no = int(item["drawTerm"])
    except (KeyError, TypeError, ValueError) as exc:
        raise BingoFetchError(f"missing/invalid drawTerm in {item!r}") from exc

    numbers = _parse_numbers(item.get("bigShowOrder"), "bigShowOrder", draw_no)
    draw_order = _parse_numbers(item.get("openShowOrder"), "openShowOrder", draw_no)
    if sorted(draw_order) != sorted(numbers):
        raise BingoFetchError(f"draw {draw_no}: openShowOrder and bigShowOrder differ")

    try:
        super_number = int(item["bullEyeTop"])
    except (KeyError, TypeError, ValueError) as exc:
        raise BingoFetchError(f"draw {draw_no}: missing/invalid bullEyeTop") from exc
    if super_number not in numbers:
        raise BingoFetchError(f"draw {draw_no}: super number {super_number} is not among the drawn numbers")

    big_small = _normalize_label(item.get("highLowTop"))
    odd_even = _normalize_label(item.get("oddEvenTop"))
    # The official value is authoritative; a mismatch with the 13-of-20 rule is
    # worth a warning (rules may have changed) but must not block the update.
    for label, api_value, computed in (
        ("big_small", big_small, classify_big_small(numbers)),
        ("odd_even", odd_even, classify_odd_even(numbers)),
    ):
        if api_value != computed:
            print(f"warning: draw {draw_no}: {label} API={api_value} but 13-of-20 rule gives {computed}")

    return {
        "draw_no": str(draw_no),
        "draw_time": draw_time.isoformat(),
        "draw_time_derived": True,  # the API gives no time; derived from the 5-minute schedule
        "numbers": sorted(numbers),
        "draw_order": draw_order,
        "super_number": super_number,
        "big_small": big_small,
        "odd_even": odd_even,
    }


def fetch_day(day: date) -> list[dict]:
    """Return all draws of `day`, oldest first. Empty list when no draws exist yet."""
    url = f"{API_URL}?openDate={day.isoformat()}&pageNum=1&pageSize={PAGE_SIZE}"
    payload = _request_json(url)
    if payload.get("rtCode") != 0:
        raise BingoFetchError(f"API error {payload.get('rtCode')} for {url}: {payload.get('rtMsg')}")
    content = payload.get("content")
    if not isinstance(content, dict):
        raise BingoFetchError(f"unexpected API content for {url}: {content!r}")

    items = content.get("bingoQueryResult") or []
    total = content.get("totalSize") or 0
    if len(items) != total:
        raise BingoFetchError(f"{day}: API returned {len(items)} of {total} draws (page size too small?)")

    # Items are newest first; the k-th draw of the day (1-based) happens at
    # 07:05 + 5 min * (k - 1), and the newest item is draw number `total`.
    first_draw = datetime(day.year, day.month, day.day, *FIRST_DRAW_TIME, tzinfo=TAIPEI)
    draws = []
    for index, item in enumerate(items):
        k = total - index
        draws.append(_parse_draw(item, first_draw + DRAW_INTERVAL * (k - 1)))
    draws.reverse()

    ids = [int(d["draw_no"]) for d in draws]
    if ids != sorted(set(ids)):
        raise BingoFetchError(f"{day}: draw numbers are not unique/ascending")
    return draws
