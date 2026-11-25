#!/usr/bin/env python3
"""Compute the plan's 8 DAX-equivalent measures + build the dashboard dataset.

Outputs:
  data_clean/measures.json        – headline numbers (whole dataset)
  dashboard/data.json             – columnar per-incident dataset + dictionaries
"""
import csv, json, sys
from collections import Counter, defaultdict
from pathlib import Path

CLEAN = Path(sys.argv[1])
OUTDIR = Path(sys.argv[2])
DASH = Path(sys.argv[3])
DASH.mkdir(parents=True, exist_ok=True)

rows = list(csv.DictReader(CLEAN.open(newline="", encoding="utf-8")))

def month_index(d):  # months since 2015-01
    y, m = int(d[:4]), int(d[5:7])
    return (y - 2015) * 12 + (m - 1)

# ---------- measures ----------
total = len(rows)
hosp = sum(int(r["Hospitalized"]) for r in rows)
amp = sum(int(r["Amputation"]) for r in rows)
amp_rate = amp / total

by_year = Counter(r["EventDate"][:4] for r in rows)
# data ends Nov 2025 -> compare Jan-Nov 2025 vs Jan-Nov 2024 (like-for-like)
jan_nov = lambda y: sum(1 for r in rows if r["EventDate"][:4] == y and int(r["EventDate"][5:7]) <= 11)
cur, prev = jan_nov("2025"), jan_nov("2024")
yoy = (cur - prev) / prev

by_month = Counter(month_index(r["EventDate"]) for r in rows)
last_m = max(by_month)
avg3m = sum(by_month.get(m, 0) for m in (last_m, last_m - 1, last_m - 2)) / 3

by_industry = Counter(r["Industry"] for r in rows)
top_ind, top_ind_n = by_industry.most_common(1)[0]

by_state = Counter(r["State"] for r in rows)
amp_causes = Counter(r["SourceTitle"] for r in rows if int(r["Amputation"]) > 0 and r["SourceTitle"])
by_sev = Counter(r["Severity"] for r in rows)
by_cause = Counter(r["SourceTitle"] for r in rows if r["SourceTitle"])
by_body = Counter(r["Part of Body Title"] for r in rows if r["Part of Body Title"])

measures = {
    "total_incidents": total,
    "total_hospitalised": hosp,
    "total_amputations": amp,
    "amputation_rate_pct": round(amp_rate * 100, 1),
    "incidents_2025_jan_nov": cur,
    "incidents_2024_jan_nov": prev,
    "yoy_change_pct_like_for_like": round(yoy * 100, 1),
    "incidents_3m_avg_latest": round(avg3m, 1),
    "top_industry": top_ind,
    "top_industry_incidents": top_ind_n,
    "top_industry_share_pct": round(top_ind_n / total * 100, 1),
    "top_state": by_state.most_common(1)[0],
    "severity_split": dict(by_sev),
    "top_cause_overall": by_cause.most_common(1)[0],
    "top_amputation_causes": amp_causes.most_common(5),
    "top_body_parts": by_body.most_common(5),
    "incidents_by_year": dict(sorted(by_year.items())),
    "rows_by_industry_top10": by_industry.most_common(10),
}
(OUTDIR / "measures.json").write_text(json.dumps(measures, indent=2))

# ---------- dashboard dataset (columnar) ----------
def dict_top(counter, n):
    names = [k for k, _ in counter.most_common(n)]
    idx = {k: i for i, k in enumerate(names)}
    return names + ["Other"], idx, len(names)

states = sorted({r["State"] for r in rows if r["State"]})
state_idx = {s: i for i, s in enumerate(states)}
industries = [k for k, _ in by_industry.most_common()]
ind_idx = {k: i for i, k in enumerate(industries)}
sevs = ["Hospitalisation", "Amputation", "Loss of Eye"]
sev_idx = {s: i for i, s in enumerate(sevs)}
causes, cause_idx, nc = dict_top(by_cause, 30)
bodies, body_idx, nb = dict_top(by_body, 30)
by_nature = Counter(r["NatureTitle"] for r in rows if r["NatureTitle"])
natures, nature_idx, nn = dict_top(by_nature, 12)

cols = defaultdict(list)
for r in rows:
    cols["m"].append(month_index(r["EventDate"]))
    cols["st"].append(state_idx.get(r["State"], -1))
    cols["in"].append(ind_idx[r["Industry"]])
    cols["sv"].append(sev_idx[r["Severity"]])
    cols["h"].append(int(r["Hospitalized"]))
    cols["a"].append(int(r["Amputation"]))
    cols["ca"].append(cause_idx.get(r["SourceTitle"], nc))
    cols["bp"].append(body_idx.get(r["Part of Body Title"], nb))
    cols["na"].append(nature_idx.get(r["NatureTitle"], nn))

data = {
    "meta": {"rows": total, "start": "2015-01", "end": "2025-11",
             "source": "OSHA Severe Injury Reports (osha.gov/severe-injury-reports)"},
    "dims": {"states": states, "industries": industries, "severities": sevs,
             "causes": causes, "bodyParts": bodies, "natures": natures},
    "cols": cols,
}
out = DASH / "data.json"
out.write_text(json.dumps(data, separators=(",", ":")))
print("data.json bytes:", out.stat().st_size)
print(json.dumps(measures, indent=2))
