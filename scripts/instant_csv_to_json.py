import csv, json, re
from pathlib import Path
from datetime import datetime

CSV_PATH = Path("raw-data/all-instants.csv")
OUT_JSON = Path("docs/assets/data/instants-chosen-number.json")

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

def chosen_sort_key(s: str):
    nums = [int(x) for x in re.findall(r"\d+", (s or "").strip())]
    return tuple(nums) if nums else (10**9,)

def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    agg = {}

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            _ = parse_date(r.get("date"))  # 只是確保日期格式合法

            chosen = (r.get("chosen_num") or "").strip()
            if chosen == "":
                continue

            price = parse_int(r.get("price"))
            prize = parse_int(r.get("prize"))

            if chosen not in agg:
                agg[chosen] = {
                    "chosen_number": chosen,
                    "times": 0,
                    "win_times": 0,
                    "spent": 0,
                    "prize_amount": 0,
                }

            agg[chosen]["times"] += 1
            agg[chosen]["spent"] += price
            agg[chosen]["prize_amount"] += prize
            if prize > 0:
                agg[chosen]["win_times"] += 1

    items = list(agg.values())
    items.sort(key=lambda x: chosen_sort_key(x["chosen_number"]))

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ Updated: {OUT_JSON}")
    print(f"   Unique chosen numbers: {len(items)}")

if __name__ == "__main__":
    main()