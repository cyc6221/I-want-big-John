import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

CSV_PATH = Path("research/derived/649_all_years.csv")
OUT_JSON = Path("docs/assets/data/649-stats.json")


def parse_int(value, default=0):
    text = str(value or "").strip().replace(",", "")
    if text == "":
        return default
    return int(float(text))


def parse_date(value: str) -> datetime:
    return datetime.strptime((value or "").strip(), "%Y/%m/%d")


def iso_week_start(dt: datetime) -> datetime:
    return dt - timedelta(days=dt.weekday())


def aggregate(rows, key_func, label_func):
    buckets = {}

    for row in rows:
        key = key_func(row["date"])
        if key not in buckets:
            buckets[key] = {
                "label": label_func(key),
                "date": key.strftime("%Y-%m-%d"),
                "draws": 0,
                "sales": 0,
                "bets": 0,
                "prize": 0,
            }

        bucket = buckets[key]
        bucket["draws"] += 1
        bucket["sales"] += row["sales"]
        bucket["bets"] += row["bets"]
        bucket["prize"] += row["prize"]

    items = [buckets[key] for key in sorted(buckets.keys())]
    for item in items:
        draws = item["draws"] or 1
        item["avg_sales"] = round(item["sales"] / draws)
        item["avg_bets"] = round(item["bets"] / draws)
        item["avg_prize"] = round(item["prize"] / draws)
        item["prize_rate"] = round(item["prize"] / item["sales"], 4) if item["sales"] else 0

    return items


def build_stats(rows):
    if not rows:
        return {
            "summary": {},
            "series": {"daily": [], "weekly": [], "monthly": [], "yearly": []},
        }

    rows = sorted(rows, key=lambda row: row["date"])
    total_draws = len(rows)
    total_sales = sum(row["sales"] for row in rows)
    total_bets = sum(row["bets"] for row in rows)
    total_prize = sum(row["prize"] for row in rows)

    latest = rows[-1]
    recent_30 = rows[-30:] if len(rows) >= 30 else rows

    daily = [
        {
            "label": row["date"].strftime("%Y-%m-%d"),
            "date": row["date"].strftime("%Y-%m-%d"),
            "draws": 1,
            "sales": row["sales"],
            "bets": row["bets"],
            "prize": row["prize"],
            "avg_sales": row["sales"],
            "avg_bets": row["bets"],
            "avg_prize": row["prize"],
            "prize_rate": round(row["prize"] / row["sales"], 4) if row["sales"] else 0,
        }
        for row in rows
    ]

    weekly = aggregate(
        rows,
        lambda dt: iso_week_start(dt),
        lambda dt: f"{dt.strftime('%Y-%m-%d')} 週",
    )
    monthly = aggregate(
        rows,
        lambda dt: datetime(dt.year, dt.month, 1),
        lambda dt: dt.strftime("%Y-%m"),
    )
    yearly = aggregate(
        rows,
        lambda dt: datetime(dt.year, 1, 1),
        lambda dt: dt.strftime("%Y"),
    )

    return {
        "summary": {
            "total_draws": total_draws,
            "date_start": rows[0]["date"].strftime("%Y-%m-%d"),
            "date_end": latest["date"].strftime("%Y-%m-%d"),
            "total_sales": total_sales,
            "total_bets": total_bets,
            "total_prize": total_prize,
            "avg_sales": round(total_sales / total_draws),
            "avg_bets": round(total_bets / total_draws),
            "avg_prize": round(total_prize / total_draws),
            "overall_prize_rate": round(total_prize / total_sales, 4) if total_sales else 0,
            "latest_draw": {
                "date": latest["date"].strftime("%Y-%m-%d"),
                "sales": latest["sales"],
                "bets": latest["bets"],
                "prize": latest["prize"],
            },
            "recent_30_avg": {
                "sales": round(sum(row["sales"] for row in recent_30) / len(recent_30)),
                "bets": round(sum(row["bets"] for row in recent_30) / len(recent_30)),
                "prize": round(sum(row["prize"] for row in recent_30) / len(recent_30)),
            },
        },
        "series": {
            "daily": daily,
            "weekly": weekly,
            "monthly": monthly,
            "yearly": yearly,
        },
    }


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    rows = []
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            rows.append(
                {
                    "date": parse_date(raw.get("開獎日期", "")),
                    "sales": parse_int(raw.get("銷售總額")),
                    "bets": parse_int(raw.get("銷售注數")),
                    "prize": parse_int(raw.get("總獎金")),
                }
            )

    payload = build_stats(rows)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Updated: {OUT_JSON}")
    print(f"   Draws: {payload['summary'].get('total_draws', 0)}")


if __name__ == "__main__":
    main()
