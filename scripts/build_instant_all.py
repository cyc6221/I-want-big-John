import csv
import json
from pathlib import Path
from datetime import datetime

# ====== PATHS ======
CSV_PATH = Path("raw-data/all-instants.csv")
OUT_MD   = Path("docs/_list/instants-all.md")

# ====== 遊戲代碼 -> 中文名稱 ======
GAME_NAMES_PATH = Path("raw-data/instant-games.json")
GAME_NAME = json.loads(GAME_NAMES_PATH.read_text(encoding="utf-8"))

def parse_int(x, default=0):
    s = (x or "").strip()
    if s == "":
        return default
    return int(float(s))

def read_rows():
    rows = []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            date_str = (r.get("date") or "").strip()
            game = (r.get("game") or "").strip()
            price = parse_int(r.get("price"))
            prize = parse_int(r.get("prize"))
            chosen = (r.get("chosen_num") or "").strip()

            # 允許 date 兩種：2026/03/02 或 2026-03-02
            # 用於排序
            dt = None
            for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    pass
            if dt is None:
                raise ValueError(f"Invalid date format: {date_str}")

            rows.append({
                "date": dt.strftime("%Y/%m/%d"),  # 統一輸出格式
                "dt": dt,
                "game": game,
                "price": price,
                "prize": prize,
                "chosen_num": chosen,
            })
    # 依日期排序（同日則照原順序）
    rows.sort(key=lambda x: x["dt"])
    return rows

def build_markdown(rows):
    total_spent = sum(r["price"] for r in rows)
    total_prize = sum(r["prize"] for r in rows)

    start_date = rows[0]["date"] if rows else ""

    description = f"總計花費 {total_spent} 元，中獎 {total_prize} 元。"
    intro = f"從 {start_date} 開始記錄，總計花費 {total_spent} 元，中獎 {total_prize} 元。"

    # 表頭
    lines = []
    lines.append("---")
    lines.append(f"title: 刮刮樂全紀錄")
    lines.append("permalink: /list/instant-all/")
    lines.append("category: list-instant")
    lines.append(f"date: 2026-02-25")
    lines.append(f"description: {description}")
    lines.append("---")
    lines.append("")
    lines.append(intro)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("| i | 日期 | 項目 | 花費 | 中獎 |")
    lines.append("| :-: | :-: | :-: | :-: | :-: |")

    # 表格內容
    for i, r in enumerate(rows, start=1):
        game_id = r["game"]
        name = GAME_NAME.get(game_id, f"#{game_id}")
        href = f"{{ '/all-instants/{game_id}/' | relative_url }}"
        item_html = f'<a class="btn btn--gold" href="{href}">{name}</a>'
        lines.append(f"| {i} | {r['date']} | {item_html} | {r['price']} | {r['prize']} |")

    lines.append("")  # EOF newline
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
    print(f"   Total spent: {sum(r['price'] for r in rows)}")
    print(f"   Total prize: {sum(r['prize'] for r in rows)}")

if __name__ == "__main__":
    main()