import csv
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_cjk_font

# ====== PATHS ======
CSV_PATH = Path("raw-data/all-instants.csv")
OUT_MD   = Path("docs/_list/instants-per-month.md")

OUT_PNG  = Path("docs/assets/img/instants/instants-per-month.png")
PNG_MD_PATH = "/assets/img/instants/instants-per-month.png"

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

def build_month_map(rows):
    month_map = {}
    for r in rows:
        month = r["dt"].strftime("%Y/%m")
        if month not in month_map:
            month_map[month] = {"spent": 0, "prize": 0}
        month_map[month]["spent"] += r["price"]
        month_map[month]["prize"] += r["prize"]
    return month_map

def plot_monthly(months, spent_list, prize_list):
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)

    x = list(range(len(months)))
    width = 0.42

    plt.figure(figsize=(10, 4.8))

    bars_spent = plt.bar(
        [i - width/2 for i in x],
        spent_list,
        width=width,
        color="blue",
        label="花費",
    )
    bars_prize = plt.bar(
        [i + width/2 for i in x],
        prize_list,
        width=width,
        color="red",
        label="中獎",
    )

    plt.title("刮刮樂每月花費與中獎")
    plt.xlabel("月份")
    plt.ylabel("金額")
    plt.grid(True, axis="y", alpha=0.25)
    plt.legend()

    plt.xticks(x, months, rotation=45, ha="right")

    # ✅ 柱子上加數字（0 也會顯示）
    plt.bar_label(bars_spent, labels=[str(v) for v in spent_list], padding=3, fontsize=9)
    plt.bar_label(bars_prize, labels=[str(v) for v in prize_list], padding=3, fontsize=9)

    # 讓上方留點空間，避免標籤被切到
    ymax = max(spent_list + prize_list) if (spent_list or prize_list) else 0
    plt.ylim(0, ymax * 1.15 + 1)

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=200)
    plt.close()

def build_markdown(months, month_map):
    lines = []
    lines.append("---")
    lines.append("title: 刮刮樂每月花費紀錄")
    lines.append("permalink: /list/instant-per-month/")
    lines.append("category: list-instant")
    lines.append("date: 2026-02-25")
    lines.append("description: 從 2026 年 2 月 25 日開始記錄。")
    lines.append("---")
    lines.append("")
    lines.append("從 2026 年 2 月 25 日開始記錄。")
    lines.append("")
    lines.append(f"![刮刮樂每月花費與中獎]({PNG_MD_PATH})")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("| 月份 | 花費 | 中獎 |")
    lines.append("| :-: | :-: | :-: |")

    for m in months:
        spent = month_map[m]["spent"]
        prize = month_map[m]["prize"]
        lines.append(f"| {m} | {spent} | {prize} |")

    lines.append("")
    return "\n".join(lines)

def main():
    setup_cjk_font()
    
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    rows = read_rows()
    month_map = build_month_map(rows)
    months_sorted = sorted(month_map.keys())

    spent_list = [month_map[m]["spent"] for m in months_sorted]
    prize_list = [month_map[m]["prize"] for m in months_sorted]

    if months_sorted:
        plot_monthly(months_sorted, spent_list, prize_list)
        print(f"🖼️  Saved chart: {OUT_PNG}")
    else:
        print("⚠️ No data rows; skip chart.")

    md = build_markdown(months_sorted, month_map)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")

    print(f"✅ Updated: {OUT_MD}")
    print(f"   Records: {len(rows)}")

if __name__ == "__main__":
    main()