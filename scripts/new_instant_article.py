"""Generate a new instants (刮刮樂) article from official Taiwan Lottery data.

官網 (www.taiwanlottery.com) 是 JS SPA，直接抓公告網址只會拿到空殼；
這支腳本改走官網背後的公開 JSON API 取得上市公告與遊戲資料，
由程式計算所有期望值數學，再依現有文章格式產出：

- docs/_articles/all-instants/{期別}.md（文章）
- raw-data/instant-prize-structures/{期別}.json（獎金結構資料源）
- docs/_data/instants_compare.yml（比較表條目，自動新增/更新）
- raw-data/instant-games.json（期別 -> 名稱對照，自動新增）

Usage:
    python scripts/new_instant_article.py 5156
    python scripts/new_instant_article.py 5156 --news-url https://www.taiwanlottery.com/news/news/{newsId}#5156
    python scripts/new_instant_article.py 5156 --from-json raw-data/instant-prize-structures/5156.json
    python scripts/new_instant_article.py 5156 --output out.md   # 只產文章到指定路徑，不動 repo 其他檔案
"""

import argparse
import json
import re
import ssl
import sys
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from html import unescape
from pathlib import Path
from urllib.request import Request, urlopen

API_BASE = "https://api.taiwanlottery.com/TLCAPIWeB"
NEWS_PAGE_URL = "https://www.taiwanlottery.com/news/news/{news_id}"
USER_AGENT = "Mozilla/5.0 (compatible; IWBJ-instant-article/1.0)"
NEWS_SEARCH_MAX_PAGES = 10
NEWS_SEARCH_PAGE_SIZE = 50

ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = ROOT / "docs" / "_articles" / "all-instants"
PRIZE_DIR = ROOT / "raw-data" / "instant-prize-structures"
COMPARE_YML = ROOT / "docs" / "_data" / "instants_compare.yml"
GAMES_JSON = ROOT / "raw-data" / "instant-games.json"

WEEKDAY_NAMES = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
SECTION_HEADING_RE = re.compile(r"^[一二三四五六七八九十]+、")
ROC_DATE_RE = re.compile(r"(\d{2,3})年(\d{1,2})月(\d{1,2})日(?:（(星期.)）)?")


class ParseError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def build_ssl_context() -> ssl.SSLContext:
    # 台彩憑證缺 Subject Key Identifier，Python 3.13 起預設的
    # VERIFY_X509_STRICT 會拒絕；只放寬 strict 檢查，保留一般憑證驗證。
    context = ssl.create_default_context()
    context.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return context


SSL_CONTEXT = build_ssl_context()


def fetch_api(path: str) -> dict:
    url = f"{API_BASE}/{path}"
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(req, timeout=30, context=SSL_CONTEXT) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if payload.get("rtCode") != 0:
        raise RuntimeError(f"API error {payload.get('rtCode')} for {url}: {payload.get('rtMsg')}")
    return payload["content"]


def fetch_news_detail(news_id: str) -> dict:
    return fetch_api(f"News/Detail/{news_id}")


def find_announcement(issue: int) -> tuple[str, dict]:
    """Search News/List for the 上市公告 that covers the issue."""
    # 舊公告不一定有 <a id="{期數}"> 錨點，改以「期數：{期數}」為主要依據。
    issue_re = re.compile(rf'(?:id="{issue}"|期數：\s*{issue}\b)')
    for page in range(1, NEWS_SEARCH_MAX_PAGES + 1):
        listing = fetch_api(f"News/List?PageNo={page}&PageSize={NEWS_SEARCH_PAGE_SIZE}")
        for item in listing.get("newsListRes", []):
            title = item.get("newsTitle") or ""
            if "上市公告" not in title:
                continue
            detail = fetch_news_detail(item["newsId"])
            if issue_re.search(detail.get("content") or ""):
                return item["newsId"], detail
        if page >= int(listing.get("totalPages") or 1):
            break
    raise RuntimeError(
        f"在最近 {NEWS_SEARCH_MAX_PAGES * NEWS_SEARCH_PAGE_SIZE} 則公告中找不到第 {issue} 期的上市公告；"
        "可改用 --news-url 直接指定公告網址。"
    )


# ---------------------------------------------------------------------------
# Announcement parsing
# ---------------------------------------------------------------------------

def strip_tags(fragment: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "\n", fragment)).replace("\xa0", " ")


def html_head_lines(html: str) -> list[str]:
    """Text lines of the announcement body before the per-issue prize blocks."""
    cut = html.find('<div class="table_area')
    head = html[:cut] if cut >= 0 else html
    head = re.sub(r"<style[\s\S]*?</style>", "", head)
    return [line.strip() for line in strip_tags(head).split("\n") if line.strip()]


def split_sections(lines: list[str]) -> dict[str, list[str]]:
    """Group announcement lines under their numbered headings (一、二、...)."""
    sections: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in lines:
        if SECTION_HEADING_RE.match(line):
            current = sections.setdefault(line, [])
        elif current is not None:
            current.append(line)
    return sections


def section_lines(sections: dict[str, list[str]], keyword_re: str) -> list[str]:
    pattern = re.compile(keyword_re)
    for heading, lines in sections.items():
        if pattern.search(heading):
            return [heading] + lines
    return []


def parse_int(raw: str) -> int:
    return int(raw.replace(",", ""))


def parse_roc_date(text: str) -> dict:
    match = ROC_DATE_RE.search(text)
    if not match:
        raise ParseError(f"找不到民國日期：{text!r}")
    roc_year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
    iso = date(roc_year + 1911, month, day)
    weekday = match.group(4) or WEEKDAY_NAMES[iso.weekday()]
    if weekday != WEEKDAY_NAMES[iso.weekday()]:
        print(f"[warn] 公告星期 ({weekday}) 與日期 {iso.isoformat()} 實際星期 "
              f"({WEEKDAY_NAMES[iso.weekday()]}) 不符，以公告為準。")
    return {
        "iso": iso.isoformat(),
        "roc": f"{roc_year}年{month}月{day}日",
        "weekday": weekday,
    }


def pick_dated_line(lines: list[str], name: str) -> str:
    """Prefer the per-game line; fall back to the first line carrying a date."""
    dated = [line for line in lines if ROC_DATE_RE.search(line)]
    if not dated:
        raise ParseError(f"段落中沒有日期資訊：{lines!r}")
    for line in dated:
        if f"「{name}」" in line:
            return line
    return dated[0]


def parse_issue_block(html: str, issue: int) -> dict:
    """Extract name / prize tiers / total / announced odds from the issue's prize block."""
    blocks = list(re.finditer(r"<h1[^>]*>[^<]*期數：(\d+)", html))
    if not blocks:
        raise ParseError("公告內找不到任何「彩券期數」區塊")
    target = None
    for idx, match in enumerate(blocks):
        if int(match.group(1)) == issue:
            end = blocks[idx + 1].start() if idx + 1 < len(blocks) else len(html)
            target = html[match.start():end]
            break
    if target is None:
        raise ParseError(f"公告內找不到第 {issue} 期的獎金結構區塊")

    name_match = re.search(r"主題：\s*([^<]+?)\s*</h2>", target)
    if not name_match:
        raise ParseError(f"第 {issue} 期區塊內找不到「彩券主題」")
    name = unescape(name_match.group(1)).strip()

    tiers: list[dict] = []
    total = None
    announced_rate = None
    for table_match in re.finditer(r'<table class="([^"]*)">([\s\S]*?)</table>', target):
        klass, body = table_match.group(1), table_match.group(2)
        cells = re.findall(r"<td[^>]*>([\s\S]*?)</td>", body)
        if "summy" in klass:
            if len(cells) != 2:
                raise ParseError(f"摘要表格格式不符（{len(cells)} 欄）")
            label, value = strip_tags(cells[0]).strip(), strip_tags(cells[1]).strip()
            if "發行張數" in label:
                total = parse_int(value)
            elif "中獎率" in label:
                announced_rate = value.rstrip("%")
            continue
        if len(cells) != 2:
            raise ParseError(f"獎金結構表格應有 2 欄，實際 {len(cells)} 欄")
        def list_items(cell: str) -> list[str]:
            # 部分公告用 &nbsp; 的空 <li> 對齊兩欄，過濾掉再配對。
            items = [strip_tags(item).strip() for item in re.findall(r"<li[^>]*>([\s\S]*?)</li>", cell)]
            return [item for item in items if item]

        prizes = list_items(cells[0])
        counts = list_items(cells[1])
        if len(prizes) != len(counts) or not prizes:
            raise ParseError(f"獎項與張數數量不符：{prizes!r} / {counts!r}")
        for prize_label, count_label in zip(prizes, counts):
            prize_match = re.fullmatch(r"NT\$([\d,]+)", strip_tags(prize_label).strip())
            if not prize_match:
                raise ParseError(f"無法解析獎項金額：{prize_label!r}")
            tiers.append({
                "prize": parse_int(prize_match.group(1)),
                "count": parse_int(strip_tags(count_label).strip()),
            })

    if not tiers:
        raise ParseError(f"第 {issue} 期區塊內沒有解析到任何獎項")
    if total is None:
        raise ParseError(f"第 {issue} 期區塊內找不到「發行張數」")
    if announced_rate is None:
        raise ParseError(f"第 {issue} 期區塊內找不到「中獎率」")
    tiers.sort(key=lambda tier: tier["prize"], reverse=True)
    return {"name": name, "tiers": tiers, "total": total, "announced_rate": announced_rate}


def parse_announcement(html: str, issue: int, news_id: str) -> dict:
    block = parse_issue_block(html, issue)
    name = block["name"]
    sections = split_sections(html_head_lines(html))

    price_lines = section_lines(sections, r"售價")
    price_match = None
    for line in price_lines:
        if f"「{name}」" in line:
            price_match = re.search(r"每張新臺幣([\d,]+)元[^、，]*[、，]每本([\d,]+)張", line)
            break
    if not price_match:
        raise ParseError(f"售價段落找不到「{name}」的售價與包裝：{price_lines!r}")
    price, per_book = parse_int(price_match.group(1)), parse_int(price_match.group(2))

    qty_lines = section_lines(sections, r"發行數量")
    for line in qty_lines:
        if f"「{name}」" in line:
            qty_match = re.search(r"總計([\d,]+)張", line)
            if qty_match and parse_int(qty_match.group(1)) != block["total"]:
                raise ParseError(
                    f"發行數量不一致：公告段落 {qty_match.group(1)} vs 獎金結構表 {block['total']:,}"
                )

    dates = {}
    for key, keyword_re in (
        ("launch", r"發行日期"),
        ("off_sale", r"下[市巿]日期"),
        ("claim_deadline", r"兌獎截止"),
    ):
        lines = section_lines(sections, keyword_re)
        if not lines:
            raise ParseError(f"公告內找不到段落：{keyword_re}")
        dates[key] = parse_roc_date(pick_dated_line(lines[1:] or lines, name))

    return {
        "issue": issue,
        "name": name,
        "price": price,
        "tickets_per_book": per_book,
        "total_tickets": block["total"],
        "dates": dates,
        "announced_win_rate_percent": block["announced_rate"],
        "prize_tiers": block["tiers"],
        "source": {
            "news_id": news_id,
            "official_url": NEWS_PAGE_URL.format(news_id=news_id),
            "scratch_id": None,
            "fetched_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        },
    }


# ---------------------------------------------------------------------------
# Cross validation with Instant/List + Instant/Detail
# ---------------------------------------------------------------------------

def cross_validate_with_api(data: dict) -> None:
    listing = fetch_api("Instant/List")
    match = next(
        (g for g in listing.get("scratchListInfos", []) if g.get("scratchName") == data["name"]),
        None,
    )
    if match is None:
        print(f"[warn] Instant/List 沒有「{data['name']}」（可能已下市或尚未上架），跳過 API 交叉驗證。")
        return

    detail = fetch_api(f"Instant/Detail?ScratchId={match['scratchId']}")
    data["source"]["scratch_id"] = match["scratchId"]

    problems = []
    if detail.get("money") != data["price"]:
        problems.append(f"售價：公告 {data['price']} vs API {detail.get('money')}")
    if detail.get("issuedCount") != data["total_tickets"]:
        problems.append(f"發行張數：公告 {data['total_tickets']:,} vs API {detail.get('issuedCount'):,}")
    for key, field in (
        ("launch", "listingDate"),
        ("off_sale", "downDate"),
        ("claim_deadline", "exchangeLastDate"),
    ):
        api_date = (detail.get(field) or "")[:10]
        if api_date != data["dates"][key]["iso"]:
            problems.append(f"{field}：公告 {data['dates'][key]['iso']} vs API {api_date}")
    api_odds = (detail.get("oddsOfWinning") or "").strip()
    if api_odds and Decimal(api_odds) != Decimal(data["announced_win_rate_percent"]):
        problems.append(f"中獎率：公告 {data['announced_win_rate_percent']}% vs API {api_odds}%")
    if problems:
        raise RuntimeError("公告與官方 API 資料不一致：\n  - " + "\n  - ".join(problems))
    print("[ok] Instant/Detail 交叉驗證通過（售價、張數、日期、中獎率）。")


# ---------------------------------------------------------------------------
# Math (Decimal, ROUND_HALF_UP — LLM 不得手算，一律由這裡計算)
# ---------------------------------------------------------------------------

def quantize(value: Decimal, exp: str) -> Decimal:
    return value.quantize(Decimal(exp), rounding=ROUND_HALF_UP)


def compute_stats(data: dict) -> dict:
    total = data["total_tickets"]
    tiers = data["prize_tiers"]
    price = data["price"]
    n = Decimal(total)

    win_count = sum(tier["count"] for tier in tiers)
    lose_count = total - win_count
    if lose_count < 0:
        raise ParseError(f"中獎張數總和 ({win_count:,}) 超過發行張數 ({total:,})")

    def pct6(count: int) -> Decimal:
        return quantize(Decimal(count) * 100 / n, "0.000001")

    profit_count = sum(t["count"] for t in tiers if t["prize"] > price)
    break_even_count = sum(t["count"] for t in tiers if t["prize"] == price)

    total_prize_sum = sum(t["prize"] * t["count"] for t in tiers)
    expected_value = quantize(Decimal(total_prize_sum) / n, "0.0001")
    average_loss = Decimal(price) - expected_value
    return_rate = quantize(expected_value * 100 / Decimal(price), "0.01")
    win_rate_2dp = quantize(Decimal(win_count) * 100 / n, "0.01")

    announced = Decimal(data["announced_win_rate_percent"])
    if win_rate_2dp != announced:
        raise ParseError(
            f"計算中獎率 {win_rate_2dp}% 與公告 {announced}% 不符，獎金結構資料可能有誤"
        )

    return {
        "tiers": [
            {
                "prize": t["prize"],
                "count": t["count"],
                "pct6": pct6(t["count"]),
                "contribution": quantize(Decimal(t["prize"] * t["count"]) / n, "0.0001"),
                "prize_sum": t["prize"] * t["count"],
            }
            for t in tiers
        ],
        "lose_count": lose_count,
        "lose_pct6": pct6(lose_count),
        "win_count": win_count,
        "win_pct6": pct6(win_count),
        "profit_count": profit_count,
        "profit_pct6": pct6(profit_count),
        "break_even_count": break_even_count,
        "break_even_pct6": pct6(break_even_count),
        "total_prize_sum": total_prize_sum,
        "expected_value": expected_value,
        "average_loss": average_loss,
        "return_rate": return_rate,
        "win_rate_2dp": win_rate_2dp,
        "win_rate_4dp": quantize(Decimal(profit_count) * 100 / n, "0.0001"),
        "break_even_rate_4dp": quantize(Decimal(break_even_count) * 100 / n, "0.0001"),
        "no_loss_rate_4dp": quantize(Decimal(win_count) * 100 / n, "0.0001"),
    }


# ---------------------------------------------------------------------------
# Rendering (格式基準：docs/_articles/all-instants/5155.md、5156.md)
# ---------------------------------------------------------------------------

def render_article(data: dict, stats: dict) -> str:
    issue = data["issue"]
    name = data["name"]
    price = data["price"]
    total = data["total_tickets"]
    dates = data["dates"]
    top = stats["tiers"][0]
    url = f"{data['source']['official_url']}#{issue}"

    lines = [
        "---",
        f"title: 刮刮樂-第{issue}期：{name}",
        f"permalink: /all-instants/{issue}/",
        "category: all-instants",
        f"date: {dates['launch']['iso']}",
        f"published: {dates['launch']['iso']}",
        f"num: {issue}",
        f"description: 每張{price}元，總計{total:,}張，頭獎NT${top['prize']:,}"
        f"，中獎機率{stats['win_rate_2dp']:.2f}%",
        "---",
        "",
        "## 基本資料",
        "",
        "| 項目 | 資料 |",
        "| :-: | :-: |",
        f"| 期別 | 第{issue}期 |",
        f"| 名稱 | {name} |",
        f"| 售價 | 每張{price}元，每本{data['tickets_per_book']}張 |",
        f"| 發行張數 | 總計{total:,}張 |",
        f"| 日期 | 發行：{dates['launch']['roc']}（{dates['launch']['weekday']}）"
        f"<br>下巿：{dates['off_sale']['roc']}（{dates['off_sale']['weekday']}）"
        f"<br>兌獎截止：{dates['claim_deadline']['roc']}（{dates['claim_deadline']['weekday']}） |",
        f"| 官方資料 | [台灣彩券公告]({url}) |",
        "",
        "## 獎金結構",
        "",
        "| 獎項 | 中獎張數 | 中獎機率 |",
        "| :-: | :-: | :-: |",
    ]
    for tier in stats["tiers"]:
        lines.append(f"| NT${tier['prize']:,} | {tier['count']:,} | {tier['pct6']:.6f}% |")
    lines += [
        f"| NT$0 | {stats['lose_count']:,} | {stats['lose_pct6']:.6f}% |",
        f"| **總計** | **{total:,}** | **100.000000%** |",
        "",
        "| 統計 | 張數 | 機率 |",
        "| :-: | :-: | :-: |",
        f"| 總發行張數 | {total:,} | |",
        f"| 中獎張數（有賺） | {stats['profit_count']:,} | {stats['profit_pct6']:.6f}% |",
        f"| 中獎張數（沒賠） | {stats['break_even_count']:,} | {stats['break_even_pct6']:.6f}% |",
        f"| 中獎張數（加總） | {stats['win_count']:,} | {stats['win_pct6']:.6f}% |",
        f"| 烏龜張數 | {stats['lose_count']:,} | {stats['lose_pct6']:.6f}% |",
        "",
        "## 期望值計算",
        "",
        f"總發行張數 $N={total:,}$。",
        "",
        "### 計算表",
        "",
        r"| 單張獎金 $x_i$ | 中獎張數 $n_i$ | 機率 $p_i=\frac{n_i}{N}$ | 貢獻值 $x_i p_i$ | 總獎金 $x_i n_i$ |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for tier in stats["tiers"]:
        frac = rf"\frac{{{tier['count']:,}}}{{{total:,}}}"
        lines.append(
            f"| {tier['prize']:,} | {tier['count']:,} | ${frac}$ "
            f"| ${tier['prize']:,}\\cdot{frac}={tier['contribution']:.4f}$ "
            f"| {tier['prize_sum']:,} |"
        )
    lose_frac = rf"\frac{{{stats['lose_count']:,}}}{{{total:,}}}"
    lines += [
        f"| 0 | {stats['lose_count']:,} | ${lose_frac}$ | $0$ | 0 |",
        f"| **總和** | **{total:,}** | **1** "
        f"| **{stats['expected_value']:.4f}** | **{stats['total_prize_sum']:,}** |",
        "",
        "### 結論",
        "",
        f"- 每張售價：**{price} 元**",
        f"- 單張期望值：**{stats['expected_value']:.4f} 元**",
        f"- 平均虧損：**{price} - {stats['expected_value']:.4f} = {stats['average_loss']:.4f} 元**",
        rf"- 期望值回收率：$\frac{{{stats['expected_value']:.4f}}}{{{price}}}\approx$"
        f" **{stats['return_rate']:.2f}%**",
        "",
        "## 親自實測",
        "",
    ]
    return "\n".join(lines)


def format_jackpot(prize: int) -> str:
    if prize >= 1_000_000:
        return f"{prize / 1_000_000:g}M"
    return f"{prize / 1_000:g}K"


def render_compare_entry(data: dict, stats: dict) -> str:
    top = stats["tiers"][0]
    launch = data["dates"]["launch"]["iso"].replace("-", "/")
    end = data["dates"]["off_sale"]["iso"].replace("-", "/")
    lines = [
        f"  - id: {data['issue']}",
        f"    name: {data['name']}",
        f"    launch: {launch}",
        f"    end: {end}",
        f"    price: {data['price']}",
        f"    jackpot: {format_jackpot(top['prize'])}",
        f"    jackpot_count: {top['count']}",
        f"    win_rate: {stats['win_rate_4dp']:.4f}%",
        f"    break_even_rate: {stats['break_even_rate_4dp']:.4f}%",
        f"    no_loss_rate: {stats['no_loss_rate_4dp']:.4f}%",
        f"    expected_value: \"{stats['expected_value']:.4f}\"",
        f"    expected_loss: \"{stats['average_loss']:.4f}\"",
        f"    roi: {stats['return_rate']:.2f}%",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# File IO（一律 UTF-8 無 BOM；換行沿用 repo 工作區慣例 CRLF）
# ---------------------------------------------------------------------------

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(text.replace("\r\n", "\n").replace("\n", "\r\n"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def update_compare_yml(data: dict, stats: dict) -> str:
    text = read_text(COMPARE_YML)
    entry = render_compare_entry(data, stats)
    block_re = re.compile(rf"(?m)^  - id: {data['issue']}\n(?:    .*\n)*")
    if block_re.search(text):
        text = block_re.sub(entry, text, count=1)
        action = "updated"
    else:
        if not text.endswith("\n"):
            text += "\n"
        text += entry
        action = "added"
    write_text(COMPARE_YML, text.rstrip("\n") + "\n")
    return action


def update_games_json(data: dict) -> str:
    games = json.loads(GAMES_JSON.read_text(encoding="utf-8"))
    key = str(data["issue"])
    if games.get(key) == data["name"]:
        return "unchanged"
    if key in games:
        games[key] = data["name"]
        action = "updated"
    else:
        games = {key: data["name"], **games}
        action = "added"
    write_text(GAMES_JSON, json.dumps(games, ensure_ascii=False, indent=4) + "\n")
    return action


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def extract_news_id(url: str) -> str:
    match = re.search(r"([0-9a-f]{32})", url)
    if not match:
        raise ValueError(f"無法從網址解析 newsId：{url}")
    return match.group(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("issue", type=int, help="刮刮樂期別，例如 5156")
    parser.add_argument("--news-url", help="上市公告網址（不給則自動從 News/List 搜尋）")
    parser.add_argument("--from-json", type=Path,
                        help="改用既有的 raw-data JSON（跳過網路抓取與 API 驗證）")
    parser.add_argument("--output", type=Path,
                        help="只把文章寫到指定路徑，不寫 raw-data / yml / games json（黃金比對用）")
    parser.add_argument("--force", action="store_true", help="覆寫既有文章")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if args.from_json:
        data = json.loads(args.from_json.read_text(encoding="utf-8"))
        if data.get("issue") != args.issue:
            raise SystemExit(f"JSON 內 issue={data.get('issue')} 與參數 {args.issue} 不符")
        print(f"[ok] 從 {args.from_json} 載入資料（跳過網路抓取）。")
    else:
        if args.news_url:
            news_id = extract_news_id(args.news_url)
            detail = fetch_news_detail(news_id)
        else:
            print("[..] 搜尋上市公告 ...")
            news_id, detail = find_announcement(args.issue)
        print(f"[ok] 公告：{(detail.get('newsTitle') or '').strip()} (newsId={news_id})")
        try:
            data = parse_announcement(detail["content"], args.issue, news_id)
        except ParseError as exc:
            draft = PRIZE_DIR / f"{args.issue}.draft.json"
            write_text(draft, json.dumps({
                "issue": args.issue,
                "error": str(exc),
                "news_id": news_id,
                "announcement_text": [
                    line for line in strip_tags(detail["content"]).split("\n") if line.strip()
                ],
            }, ensure_ascii=False, indent=2) + "\n")
            print(f"[error] 公告解析失敗：{exc}")
            print(f"[hint] 原始內容已存到 {draft.relative_to(ROOT).as_posix()}，"
                  "可手動整理成正式 JSON 後用 --from-json 重跑。")
            return 1
        cross_validate_with_api(data)

    stats = compute_stats(data)
    article = render_article(data, stats)

    if args.output:
        write_text(args.output, article)
        print(f"[ok] 文章已寫到 {args.output}（未動 repo 其他檔案）。")
        return 0

    article_path = ARTICLES_DIR / f"{args.issue}.md"
    if article_path.exists() and not args.force:
        raise SystemExit(f"{article_path.relative_to(ROOT).as_posix()} 已存在；要覆寫請加 --force")

    prize_path = PRIZE_DIR / f"{args.issue}.json"
    write_text(prize_path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    write_text(article_path, article)
    yml_action = update_compare_yml(data, stats)
    games_action = update_games_json(data)

    for path, action in (
        (prize_path, "written"),
        (article_path, "written"),
        (COMPARE_YML, yml_action),
        (GAMES_JSON, games_action),
    ):
        print(f"[ok] {path.relative_to(ROOT).as_posix()} ({action})")
    print("[next] 請執行 python scripts/run.py 更新產生檔，並用 jekyll build 驗證。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
