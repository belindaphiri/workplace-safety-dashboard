#!/usr/bin/env python3
"""Build aggregate CSVs for the dashboard artifact's datasets."""
import csv, sys
from collections import Counter
from pathlib import Path

CLEAN = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

rows = list(csv.DictReader(CLEAN.open(newline="", encoding="utf-8")))

by_cause = Counter(r["SourceTitle"] for r in rows if r["SourceTitle"])
by_body = Counter(r["Part of Body Title"] for r in rows if r["Part of Body Title"])
by_nature = Counter(r["NatureTitle"] for r in rows if r["NatureTitle"])
top_causes = {k for k, _ in by_cause.most_common(30)}
top_bodies = {k for k, _ in by_body.most_common(30)}
top_natures = {k for k, _ in by_nature.most_common(12)}

monthly = Counter()   # (month, state, industry, severity) -> [n, hosp, amp]
m_h = Counter(); m_a = Counter()
causes = Counter(); causes_amp = Counter()
bodies = Counter()
matrix = Counter()

for r in rows:
    month = r["EventDate"][:7]
    year = r["EventDate"][:4]
    st = r["State"]
    ind = r["Industry"]
    sev = r["Severity"]
    k = (month, st, ind, sev)
    monthly[k] += 1
    m_h[k] += int(r["Hospitalized"])
    m_a[k] += int(r["Amputation"])
    cause = r["SourceTitle"] if r["SourceTitle"] in top_causes else "Other"
    body = r["Part of Body Title"] if r["Part of Body Title"] in top_bodies else "Other"
    nature = r["NatureTitle"] if r["NatureTitle"] in top_natures else "Other"
    causes[(year, ind, cause)] += 1
    if int(r["Amputation"]) > 0:
        causes_amp[(year, ind, cause)] += 1
    bodies[(year, ind, body)] += 1
    matrix[(year, ind, nature)] += 1

def write(name, header, items):
    p = OUT / name
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(items)
    print(name, p.stat().st_size, "bytes,", len(items), "rows")

write("incidents_monthly.csv", ["month", "state", "industry", "severity", "incidents", "hospitalized", "amputations"],
      [(m, s, i, v, n, m_h[(m, s, i, v)], m_a[(m, s, i, v)]) for (m, s, i, v), n in sorted(monthly.items())])
write("causes.csv", ["year", "industry", "cause", "incidents", "amputation_incidents"],
      [(y, i, c, n, causes_amp[(y, i, c)]) for (y, i, c), n in sorted(causes.items())])
write("body_parts.csv", ["year", "industry", "body_part", "incidents"],
      [(y, i, b, n) for (y, i, b), n in sorted(bodies.items())])
write("industry_nature.csv", ["year", "industry", "nature", "incidents"],
      [(y, i, t, n) for (y, i, t), n in sorted(matrix.items())])
