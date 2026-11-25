#!/usr/bin/env python3
"""Clean the OSHA Severe Injury Reports CSV per the build plan (Step 2).

Steps mirror the Power Query recipe so the numbers match what the user
will later reproduce in Power BI:
 1. remove unused columns
 2. set data types (EventDate=date, counts=int, NAICS=text)
 3. replace null counts with 0
 4. trim + clean text
 5. capitalize each word on Employer and City
 6. remove duplicates (across all kept columns, ID excluded)
 7. add Industry from first 2 NAICS digits + lookup
 8. add Severity (Amputation > Loss of Eye > Hospitalisation)
Outputs: data_clean/injuries_clean.csv, data_clean/naics_lookup.csv,
         data_clean/cleaning_stats.json
"""
import csv, json, re, sys, unicodedata
from datetime import datetime
from pathlib import Path

RAW = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

NAICS_SECTORS = [
    ("11", "Agriculture, Forestry & Fishing"),
    ("21", "Mining, Oil & Gas"),
    ("22", "Utilities"),
    ("23", "Construction"),
    ("31", "Manufacturing"), ("32", "Manufacturing"), ("33", "Manufacturing"),
    ("42", "Wholesale Trade"),
    ("44", "Retail Trade"), ("45", "Retail Trade"),
    ("48", "Transportation & Warehousing"), ("49", "Transportation & Warehousing"),
    ("51", "Information"),
    ("52", "Finance & Insurance"),
    ("53", "Real Estate & Leasing"),
    ("54", "Professional & Technical Services"),
    ("55", "Management of Companies"),
    ("56", "Admin, Support & Waste Services"),
    ("61", "Educational Services"),
    ("62", "Health Care & Social Assistance"),
    ("71", "Arts, Entertainment & Recreation"),
    ("72", "Accommodation & Food Services"),
    ("81", "Other Services"),
    ("92", "Public Administration"),
]
SECTOR = dict(NAICS_SECTORS)

KEEP = ["EventDate", "Employer", "City", "State", "Zip", "Latitude", "Longitude",
        "Primary NAICS", "Hospitalized", "Amputation", "Loss of Eye",
        "NatureTitle", "Part of Body Title", "EventTitle", "SourceTitle",
        "Final Narrative"]

ctrl = re.compile(r"[\x00-\x1f\x7f]")

def clean_text(s):
    if s is None:
        return ""
    s = unicodedata.normalize("NFC", s)
    s = ctrl.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()

def to_int(s):
    s = (s or "").strip()
    if not s:
        return 0
    try:
        return int(float(s))
    except ValueError:
        return 0

def parse_date(s):
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            continue
    return None

stats = {"rows_raw": 0, "bad_date": 0, "null_counts_fixed": 0, "duplicates_removed": 0}
seen = set()
rows = []

with RAW.open(newline="", encoding="utf-8-sig", errors="replace") as f:
    for rec in csv.DictReader(f):
        stats["rows_raw"] += 1
        d = parse_date(rec.get("EventDate"))
        if d is None:
            stats["bad_date"] += 1
            continue
        out = {}
        out["EventDate"] = d.isoformat()
        for col in ("Hospitalized", "Amputation", "Loss of Eye"):
            raw = (rec.get(col) or "").strip()
            if raw == "":
                stats["null_counts_fixed"] += 1
            out[col] = to_int(raw)
        for col in ("Employer", "City"):
            out[col] = clean_text(rec.get(col)).title()
        for col in ("State", "Zip", "Latitude", "Longitude", "Primary NAICS",
                    "NatureTitle", "Part of Body Title", "EventTitle",
                    "SourceTitle", "Final Narrative"):
            out[col] = clean_text(rec.get(col))
        out["State"] = out["State"].upper()
        naics2 = out["Primary NAICS"][:2]
        out["Industry Code"] = naics2
        out["Industry"] = SECTOR.get(naics2, "Unknown")
        if out["Amputation"] > 0:
            out["Severity"] = "Amputation"
        elif out["Loss of Eye"] > 0:
            out["Severity"] = "Loss of Eye"
        else:
            out["Severity"] = "Hospitalisation"
        key = tuple(out[c] for c in KEEP)
        if key in seen:
            stats["duplicates_removed"] += 1
            continue
        seen.add(key)
        rows.append(out)

stats["rows_clean"] = len(rows)
stats["date_min"] = min(r["EventDate"] for r in rows)
stats["date_max"] = max(r["EventDate"] for r in rows)

cols = KEEP + ["Industry Code", "Industry", "Severity"]
with (OUT / "injuries_clean.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

lookup = sorted({(c, n) for c, n in NAICS_SECTORS})
with (OUT / "naics_lookup.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Code", "Industry"])
    w.writerows(lookup)

(OUT / "cleaning_stats.json").write_text(json.dumps(stats, indent=2))
print(json.dumps(stats, indent=2))
