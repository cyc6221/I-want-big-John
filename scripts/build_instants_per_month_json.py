import csv, json
from pathlib import Path
from datetime import datetime

CSV_PATH = Path("raw-data/all-instants.csv")
OUT_JSON = Path("docs/assets/data/instants-per-month.json")
OUT_MD = Path("docs/_list/instants-per-month.md")


def parse_int(x, default=0):
    s = (x or "").strip()
    return default if s == "" else int(float(s))


def parse_date(date_str: str) -> datetime:
    s = (date_str or "").strip()
    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(f"Invalid date format: {date_str}")


def month_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


def chars(*codes):
    return "".join(chr(code) for code in codes)


def build_month_description(item):
    if not item:
        return chars(0x5c1a, 0x7121, 0x522e, 0x522e, 0x6a02, 0x6bcf, 0x6708, 0x8cc7, 0x6599, 0x3002)

    year, month_num = item["month"].split("-")
    spent = item["spent"]
    prize = item["prize"]

    return (
        f"{int(year)} {chars(0x5e74)} {int(month_num)} {chars(0x6708, 0xff0c)}"
        f"{chars(0x7e3d, 0x8a08, 0x82b1, 0x8cbb)} {spent} {chars(0x5143, 0xff0c)}"
        f"{chars(0x4e2d, 0x734e)} {prize} {chars(0x5143, 0x3002)}"
    )


def build_month_markdown(items):
    title = chars(0x522e, 0x522e, 0x6a02, 0x6bcf, 0x6708, 0x7d71, 0x8a08)
    description = build_month_description(items[-1] if items else None)

    lines = [
        "---",
        f"title: {title}",
        "permalink: /list/instant-per-month/",
        "category: list-instant",
        "date: 2026-02-25",
        f"description: {description}",
        "---",
        "",
        "{% include instants/per-month-data.html %}",
        "",
        "{% include instants/per-month-chart.html %}",
        "{% include instants/per-month-table.html %}",
        "",
    ]
    return "\n".join(lines)


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    agg = {}

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            dt = parse_date(r.get("date"))
            month = month_key(dt)
            price = parse_int(r.get("price"))
            prize = parse_int(r.get("prize"))

            if month not in agg:
                agg[month] = {"month": month, "spent": 0, "prize": 0}

            agg[month]["spent"] += price
            agg[month]["prize"] += prize

    items = list(agg.values())
    items.sort(key=lambda x: x["month"])

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(build_month_markdown(items), encoding="utf-8")

    print(f"Updated: {OUT_JSON}")
    print(f"Updated: {OUT_MD}")
    print(f"   Months: {len(items)}")


if __name__ == "__main__":
    main()
