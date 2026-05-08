import csv
import json
from pathlib import Path

from lib_dataset import RESEARCH_638_DIR, load_draws


OUTPUT_DIR = RESEARCH_638_DIR / "outputs" / "hazard"
RAW_CSV_PATH = OUTPUT_DIR / "gap_hazard_raw.csv"
BIN_CSV_PATH = OUTPUT_DIR / "gap_hazard_binned.csv"
FINE_BIN_CSV_PATH = OUTPUT_DIR / "gap_hazard_fine_binned.csv"
SUMMARY_JSON_PATH = OUTPUT_DIR / "gap_hazard_summary.json"
SUMMARY_MD_PATH = OUTPUT_DIR / "gap_hazard_summary.md"
CHART_HTML_PATH = OUTPUT_DIR / "gap_hazard_chart.html"
BASE_PROBABILITY = 6.0 / 38.0
ALPHA = 25.0


def build_bins(raw_rows: list[dict], bins: list[tuple[str, int, int]]) -> list[dict]:
    rows = []
    for label, start, end in bins:
        obs = sum(row["observations"] for row in raw_rows if start <= row["gap"] <= end)
        hits = sum(row["hits"] for row in raw_rows if start <= row["gap"] <= end)
        empirical = hits / obs if obs else 0.0
        smoothed = ((ALPHA * BASE_PROBABILITY) + hits) / (ALPHA + obs) if obs else BASE_PROBABILITY
        rows.append(
            {
                "gap_bin": label,
                "observations": obs,
                "hits": hits,
                "empirical_hazard": round(empirical, 6),
                "smoothed_hazard": round(smoothed, 6),
                "delta_vs_base": round(empirical - BASE_PROBABILITY, 6),
            }
        )
    return rows


def main() -> None:
    draws = load_draws()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    last_seen = {number: None for number in range(1, 39)}
    gap_counts: dict[int, int] = {}
    gap_hits: dict[int, int] = {}

    for index in range(len(draws) - 1):
        current_numbers = set(draws[index]["numbers"])
        next_numbers = set(draws[index + 1]["numbers"])

        for number in current_numbers:
            last_seen[number] = index

        for number in range(1, 39):
            seen_at = last_seen[number]
            gap = index - seen_at if seen_at is not None else index + 1
            gap_counts[gap] = gap_counts.get(gap, 0) + 1
            gap_hits[gap] = gap_hits.get(gap, 0) + (1 if number in next_numbers else 0)

    raw_rows = []
    for gap in sorted(gap_counts):
        count = gap_counts[gap]
        hits = gap_hits.get(gap, 0)
        empirical = hits / count if count else 0.0
        smoothed = ((ALPHA * BASE_PROBABILITY) + hits) / (ALPHA + count)
        raw_rows.append(
            {
                "gap": gap,
                "observations": count,
                "hits": hits,
                "empirical_hazard": round(empirical, 6),
                "smoothed_hazard": round(smoothed, 6),
                "delta_vs_base": round(empirical - BASE_PROBABILITY, 6),
            }
        )

    bins = [
        ("0", 0, 0),
        ("1", 1, 1),
        ("2", 2, 2),
        ("3", 3, 3),
        ("4-5", 4, 5),
        ("6-8", 6, 8),
        ("9-12", 9, 12),
        ("13-20", 13, 20),
        ("21+", 21, 10**9),
    ]
    fine_bins = [
        ("0", 0, 0), ("1", 1, 1), ("2", 2, 2), ("3", 3, 3), ("4", 4, 4),
        ("5", 5, 5), ("6", 6, 6), ("7", 7, 7), ("8", 8, 8), ("9", 9, 9),
        ("10", 10, 10), ("11-12", 11, 12), ("13-15", 13, 15), ("16-20", 16, 20),
        ("21-30", 21, 30), ("31-50", 31, 50), ("51+", 51, 10**9),
    ]
    binned_rows = build_bins(raw_rows, bins)
    fine_binned_rows = build_bins(raw_rows, fine_bins)

    increasing_pairs = 0
    comparable_pairs = 0
    for prev_row, row in zip(binned_rows, binned_rows[1:]):
        if prev_row["observations"] and row["observations"]:
            comparable_pairs += 1
            if row["smoothed_hazard"] > prev_row["smoothed_hazard"]:
                increasing_pairs += 1

    summary = {
        "base_probability": round(BASE_PROBABILITY, 6),
        "alpha": ALPHA,
        "raw_gap_count": len(raw_rows),
        "binned_rows": binned_rows,
        "fine_binned_rows": fine_binned_rows,
        "increasing_pairs": increasing_pairs,
        "comparable_pairs": comparable_pairs,
        "supports_monotonic_gap_hypothesis": increasing_pairs == comparable_pairs and comparable_pairs > 0,
    }

    with RAW_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(raw_rows[0].keys()))
        writer.writeheader()
        writer.writerows(raw_rows)

    with BIN_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(binned_rows[0].keys()))
        writer.writeheader()
        writer.writerows(binned_rows)

    with FINE_BIN_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fine_binned_rows[0].keys()))
        writer.writeheader()
        writer.writerows(fine_binned_rows)

    SUMMARY_JSON_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Gap Hazard Diagnostic",
        "",
        f"基準機率：`{BASE_PROBABILITY:.6f}`",
        f"平滑參數 alpha：`{ALPHA}`",
        "",
        "| Gap Bin | Obs | Hits | Empirical | Smoothed | Delta vs Base |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in binned_rows:
        lines.append(
            f"| `{row['gap_bin']}` | {row['observations']} | {row['hits']} | "
            f"{row['empirical_hazard']:.6f} | {row['smoothed_hazard']:.6f} | {row['delta_vs_base']:.6f} |"
        )
    lines.extend(
        [
            "",
            f"單調上升檢查：`{increasing_pairs}/{comparable_pairs}` 個相鄰區間呈上升",
            f"是否支持『gap 越大 hazard 越高』：`{summary['supports_monotonic_gap_hypothesis']}`",
        ]
    )
    SUMMARY_MD_PATH.write_text("\n".join(lines), encoding="utf-8")

    chart_payload = {
        "base": BASE_PROBABILITY,
        "raw": raw_rows[:80],
        "fine": fine_binned_rows,
        "coarse": binned_rows,
    }
    chart_html = """<!doctype html>
<html lang="zh-Hant">
<meta charset="utf-8">
<title>Gap Hazard Chart</title>
<style>
body {{ font-family: Segoe UI, sans-serif; margin: 24px; color: #222; }}
svg {{ border: 1px solid #ddd; background: #fff; }}
.axis {{ stroke: #666; stroke-width: 1; }}
.line {{ fill: none; stroke-width: 2; }}
.base {{ stroke: #999; stroke-dasharray: 5 4; }}
.raw {{ stroke: #1f77b4; }}
.fine {{ stroke: #d62728; }}
.label {{ font-size: 12px; fill: #333; }}
</style>
<body>
<h1>Gap Hazard Chart</h1>
<p>Base probability: __BASE__</p>
<svg id="chart" width="960" height="420" viewBox="0 0 960 420"></svg>
<script>
const payload = __PAYLOAD__;
const svg = document.getElementById('chart');
const width = 960, height = 420, left = 60, right = 20, top = 20, bottom = 50;
const plotW = width - left - right, plotH = height - top - bottom;
const raw = payload.raw.map(d => [d.gap, d.smoothed_hazard]);
const fine = payload.fine.map((d, i) => [i, d.smoothed_hazard]);
const maxY = Math.max(...raw.map(d => d[1]), ...fine.map(d => d[1]), payload.base) * 1.05;
const xRawMax = Math.max(...raw.map(d => d[0]), 1);
const xFineMax = Math.max(fine.length - 1, 1);
function xRaw(v) {{ return left + (v / xRawMax) * plotW; }}
function xFine(v) {{ return left + (v / xFineMax) * plotW; }}
function y(v) {{ return top + plotH - (v / maxY) * plotH; }}
function path(points, xf) {{
  return points.map((p, i) => `${{i===0?'M':'L'}}${{xf(p[0]).toFixed(2)}},${{y(p[1]).toFixed(2)}}`).join(' ');
}}
svg.innerHTML = `
  <line class="axis" x1="${{left}}" y1="${{top}}" x2="${{left}}" y2="${{top+plotH}}"></line>
  <line class="axis" x1="${{left}}" y1="${{top+plotH}}" x2="${{left+plotW}}" y2="${{top+plotH}}"></line>
  <line class="line base" x1="${{left}}" y1="${{y(payload.base)}}" x2="${{left+plotW}}" y2="${{y(payload.base)}}}"></line>
  <path class="line raw" d="${{path(raw, xRaw)}}"></path>
  <path class="line fine" d="${{path(fine, xFine)}}"></path>
  <text class="label" x="${{left}}" y="${{top+plotH+30}}">Raw gap (blue) / Fine bins (red)</text>
  <text class="label" x="${{left+plotW-150}}" y="${{y(payload.base)-6}}">Base</text>
`;
</script>
</body>
</html>"""
    chart_html = chart_html.replace("__BASE__", f"{BASE_PROBABILITY:.6f}")
    chart_html = chart_html.replace("__PAYLOAD__", json.dumps(chart_payload, ensure_ascii=False))
    CHART_HTML_PATH.write_text(chart_html, encoding="utf-8")

    print(f"Gap hazard raw CSV: {RAW_CSV_PATH}")
    print(f"Gap hazard binned CSV: {BIN_CSV_PATH}")
    print(f"Gap hazard fine binned CSV: {FINE_BIN_CSV_PATH}")
    print(f"Gap hazard summary JSON: {SUMMARY_JSON_PATH}")
    print(f"Gap hazard summary MD: {SUMMARY_MD_PATH}")
    print(f"Gap hazard chart HTML: {CHART_HTML_PATH}")


if __name__ == "__main__":
    main()
