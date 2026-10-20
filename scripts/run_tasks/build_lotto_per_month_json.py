import json
from pathlib import Path

GAMES = {
    "539": "今彩539",
    "638": "威力彩",
    "649": "大樂透",
}

# Reads the purchase JSON written by build_{game}_purchases.py, so it must run after those tasks.
IN_JSON = "docs/assets/data/{game}-purchases.json"
OUT_JSON = "docs/assets/data/{game}-per-month.json"
OUT_MD = "docs/_list/{game}-per-month.md"


def build_months(records):
    agg = {}
    for r in records:
        month = r["purchase_date"].replace("/", "-")[:7]
        item = agg.setdefault(
            month,
            {"month": month, "records": 0, "spent": 0, "settled_spent": 0, "prize": 0, "pending_records": 0},
        )
        price = int(r["price"] or 0)
        item["records"] += 1
        item["spent"] += price
        if r["settled"]:
            item["settled_spent"] += price
            item["prize"] += int(r["prize"] or 0)
        else:
            item["pending_records"] += 1
    return [agg[month] for month in sorted(agg)]


def build_description(title, items):
    if not items:
        return f"尚無{title}每月資料。"
    last = items[-1]
    year, month = last["month"].split("-")
    description = f"{int(year)} 年 {int(month)} 月，{last['records']:,} 注，花費 {last['spent']:,} 元，中獎 {last['prize']:,} 元。"
    if last["pending_records"]:
        description += f" 待開獎或未填獎金 {last['pending_records']:,} 筆。"
    return description


def build_markdown(game, title, items):
    return "\n".join(
        [
            "---",
            f"title: {title}每月統計",
            f"permalink: /list/{game}-per-month/",
            f"category: list-{game}",
            f"date: {latest_date(game)}",
            f"description: {build_description(title, items)}",
            "---",
            "",
            f"<!-- 此檔由 scripts/run_tasks/build_lotto_per_month_json.py 從 {IN_JSON.format(game=game)} 自動產生，請勿手改；如需修改請改 raw-data/lotto-purchases/{game}-purchases.csv 後執行 python scripts/run.py -->",
            "",
            f'{{% include lotto/per-month.html game="{game}" %}}',
            "",
        ]
    )


def latest_date(game):
    md = Path(OUT_MD.format(game=game))
    purchases = json.loads(Path(IN_JSON.format(game=game)).read_text(encoding="utf-8"))
    end = purchases["summary"]["date_end"]
    if end:
        return end.replace("/", "-")
    # No purchases yet: keep the date already in the page, if any.
    if md.exists():
        for line in md.read_text(encoding="utf-8").splitlines():
            if line.startswith("date:"):
                return line.split(":", 1)[1].strip()
    return "2026-10-20"


def main():
    for game, title in GAMES.items():
        in_path = Path(IN_JSON.format(game=game))
        if not in_path.exists():
            raise FileNotFoundError(f"Purchase JSON not found: {in_path} (run build_{game}_purchases.py first)")

        purchases = json.loads(in_path.read_text(encoding="utf-8"))
        items = build_months(purchases["records"])

        out_json = Path(OUT_JSON.format(game=game))
        out_md = Path(OUT_MD.format(game=game))
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        out_md.write_text(build_markdown(game, title, items), encoding="utf-8")

        print(f"Updated: {out_json}")
        print(f"Updated: {out_md}")
        print(f"   Months: {len(items)}")


if __name__ == "__main__":
    main()
