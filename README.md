# Workplace Safety Dashboard

A two-page interactive dashboard built from real US workplace injury records, answering the
questions a safety manager would ask: how many severe injuries, where, in which industries,
what caused them and which body parts were hurt.

**Live dashboard:** built from the cleaned data in this repository.
**Power BI:** `data_clean/injuries_clean.csv` + `data_clean/naics_lookup.csv` import directly;
the DAX measures and page layouts are listed under Process.

## Problem

US employers must report every amputation, in-patient hospitalisation and loss of an eye to
OSHA within days of the incident. A safety manager needs to know whether severe injuries are
rising, which industries and states carry the most risk, and what actually causes them, so
prevention effort goes where it matters.

## Data

- Source: [OSHA Severe Injury Reports](https://osha.gov/severe-injury-reports), full data set
  download (January 2015 – November 2025).
- 105,996 incident records after cleaning (12 blank severity counts set to 0, 0 exact
  duplicates found, 0 unparseable dates).
- Key fields: event date, employer, city, state, NAICS industry code, hospitalisation /
  amputation / loss-of-eye counts, nature of injury, body part, event, source (cause) and a
  free-text narrative.

## Process

1. **Clean** – removed unused columns; set data types; replaced null counts with 0; trimmed
   and cleaned text; capitalised employer and city names; removed duplicates.
2. **Enrich** – derived a 2-digit NAICS sector lookup (`naics_lookup.csv`) and a Severity
   column (Amputation → Loss of Eye → Hospitalisation, in that precedence).
3. **Model** – star schema: an Injuries fact table linked one-to-many to a Date table and an
   Industry lookup table.
4. **Measures** – 8 measures: Total Incidents, Total Hospitalised, Total Amputations,
   Amputation Rate %, Incidents LY, YoY Change %, Incidents 3M Avg, Top Industry.
5. **Design** – Page 1 *Safety Overview*: 4 KPI cards, monthly trend with 3-month average,
   top 10 industries, severity split, top 10 states, with year / industry / state filters.
   Page 2 *Causes & Injuries*: top 10 causes, top 10 body parts, an industry × injury-type
   matrix with conditional formatting, and three written insights.

## Key insights

- **Manufacturing accounts for 32.5% of all severe injuries** (34,472 of 105,996) — more than
  the next two industries (Construction 19,021 and Transportation & Warehousing 9,381)
  combined.
- **26.4% of incidents involve an amputation.** Machinery is the leading amputation source,
  and fingers and fingertips are by far the most injured body parts.
- **Texas leads all states with 17,491 reports.** Monthly reports fell sharply in 2020
  (11,071 in 2019 → 8,915 in 2020) and have stayed below the 2018–2019 peak; Jan–Nov 2025 is
  up 4.5% on the same months of 2024.

## Repository contents

| Path | What it is |
| --- | --- |
| `data_raw/` | Original OSHA download (never edited) |
| `data_clean/injuries_clean.csv` | Cleaned incident table (import this into Power BI) |
| `data_clean/naics_lookup.csv` | 2-digit NAICS → industry sector lookup |
| `data_clean/measures.json` | The 8 headline measures computed on the full data |
| `scripts/` | Cleaning and aggregation scripts (Python, standard library only) |
| `dashboard/` | Claude dashboard page and the aggregate datasets behind it |
| `docs/` | Standalone static dashboard (GitHub Pages-ready; serve locally with `python3 -m http.server` from `docs/`) |
