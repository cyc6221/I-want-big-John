import csv
from pathlib import Path
from datetime import datetime

# ====== PATHS ======
CSV_PATH = Path("raw-data/all-instants.csv")
OUT_MD   = Path("docs/_list/instants-per-month.md")

def parse_int(x, default=0):
    s = (x or "").strip()
    if s == "":
        return default
    return int(float(s))

def parse_date(date_str: str) -> datetime:
    s = (date_str or "").strip()
    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: {date_str}")

def read_rows():
    rows = []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            dt = parse_date(r.get("date"))
            price = parse_int(r.get("price"))
            prize = parse_int(r.get("prize"))
            rows.append({"dt": dt, "price": price, "prize": prize})
    rows.sort(key=lambda x: x["dt"])
    return rows

def build_markdown(rows):
    # 沒資料也照樣輸出固定頁首 + 空表格
    month_map = {}
    for r in rows:
        month = r["dt"].strftime("%Y/%m")
        if month not in month_map:
            month_map[month] = {"spent": 0, "prize": 0}
        month_map[month]["spent"] += r["price"]
        month_map[month]["prize"] += r["prize"]

    months_sorted = sorted(month_map.keys())

    lines = []
    lines.append("---")
    lines.append("title: 刮刮樂每月花費紀錄")
    lines.append("permalink: /list/instant-per-month/")
    lines.append("category: list-instant")
    lines.append(f"date: 2026-02-25")
    lines.append(f"description: 從 2026 年 2 月 25 日 開始記錄。")
    lines.append("---")
    lines.append("")
    lines.append("從 2026 年 2 月 25 日 開始記錄。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("| 月份 | 花費 | 中獎 |")
    lines.append("| :-: | :-: | :-: |")

    # 有資料才填月份列，沒資料就只保留表頭
    for m in months_sorted:
        spent = month_map[m]["spent"]
        prize = month_map[m]["prize"]
        lines.append(f"| {m} | {spent} | {prize} |")

    lines.append("")
    return "\n".join(lines)

def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    rows = read_rows()
    md = build_markdown(rows)

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")

    print(f"✅ Updated: {OUT_MD}")
    print(f"   Records: {len(rows)}")

if __name__ == "__main__":
    main()