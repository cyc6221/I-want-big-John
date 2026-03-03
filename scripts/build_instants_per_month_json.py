import csv, json
from pathlib import Path
from datetime import datetime

CSV_PATH = Path("raw-data/all-instants.csv")
OUT_JSON = Path("docs/assets/data/instants-per-month.json")

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

def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    agg = {}

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            dt = parse_date(r.get("date"))
            m = month_key(dt)

            price = parse_int(r.get("price"))
            prize = parse_int(r.get("prize"))

            if m not in agg:
                agg[m] = {"month": m, "spent": 0, "prize": 0}

            agg[m]["spent"] += price
            agg[m]["prize"] += prize

    items = list(agg.values())
    items.sort(key=lambda x: x["month"])  # YYYY-MM 字串排序即可

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ Updated: {OUT_JSON}")
    print(f"   Months: {len(items)}")

if __name__ == "__main__":
    main()