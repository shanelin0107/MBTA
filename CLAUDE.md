# MBTA Hidden Failures: Bunching & Cascade Analysis

## Project Overview

**Title:** Beyond On-Time Performance: Detecting Hidden Service Failures in the MBTA Network
**Subtitle:** A System-Wide Analysis of Train Bunching, Crowding Inference, and Delay Propagation

This project challenges the MBTA's official on-time performance metric by exposing two hidden failure modes that riders experience daily but official KPIs fail to capture:

1. **Train Bunching & Crowding** — When trains arrive in clusters, official "on-time" counts look fine, but the preceding gap creates severe overcrowding on the next train.
2. **Cascade Failures** — A single delay at a critical station propagates through the network, affecting unrelated lines and stations downstream.

A secondary insight focuses on the **Green Line B Branch**: surface-level stops show abnormally short dwell times, which we hypothesize is partially explained by fare evasion (no fare gates → no payment friction → faster boarding).

**Target Audience:** Data science recruiters, transit advocates, urban planning researchers.

---

## Research Questions

1. Where and when does train bunching cluster in the MBTA system?
2. Can we infer station-level crowding from headway gaps and dwell time patterns?
3. Which stations act as "super-spreaders" — single points of failure that cascade delays across the network?
4. Does the official on-time percentage meaningfully represent the actual rider experience?
5. (B Line) Is the shorter dwell time at surface stops consistent with reduced fare-payment friction?

---

## Data Sources

All data from [MBTA LAMP Public Data](https://performancedata.mbta.com) — no API key required, direct Parquet file downloads.

| Dataset | URL Pattern | Usage |
|---------|-------------|-------|
| Subway On-Time Performance | `lamp/subway-on-time-performance-v1/YYYY-MM-DD-*.parquet` | Main analysis data |
| Index file (all dates) | `lamp/subway-on-time-performance-v1/index.csv` | Batch download reference |
| GTFS Stops | `lamp/tableau/.../LAMP_static_stops.parquet` | Station metadata & coordinates |
| GTFS Routes | `lamp/tableau/.../LAMP_static_routes.parquet` | Route classification |
| GTFS Trips | `lamp/tableau/.../LAMP_static_trips.parquet` | Trip-to-route mapping |
| RT Alerts | `lamp/tableau/.../LAMP_RT_ALERTS.parquet` | Real incident validation |
| All RT Fields | `lamp/tableau/.../LAMP_ALL_RT_fields.parquet` | Fine-grained timestamps |

**Time Range:** 2022-01-01 to 2026-05-31 (4+ years; avoids COVID anomaly period of 2020-2021)

**Lines in scope:** All rapid transit — Red, Orange, Blue, Green (B/C/D/E branches)

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│         Layer 5: Web Presentation               │
│   Interactive network map + charts (website)    │
├─────────────────────────────────────────────────┤
│         Layer 4: Synthesis & KPI Critique       │
│   Bunching hotspots → Cascade triggers          │
│   Official OTP vs. Rider Experience Score       │
├──────────────────────┬──────────────────────────┤
│   Layer 3A           │   Layer 3B               │
│   Bunching &         │   Network &              │
│   Crowding Analysis  │   Cascade Analysis       │
├──────────────────────┴──────────────────────────┤
│         Layer 2: Feature Engineering            │
│   Headway gaps / Dwell time / Event flags       │
├─────────────────────────────────────────────────┤
│         Layer 1: Data Acquisition & EDA         │
│   LAMP Parquet downloads + GTFS static          │
└─────────────────────────────────────────────────┘
```

---

## File Structure

```
MBTA/
├── CLAUDE.md                    # This file
├── data/
│   ├── raw/                     # Downloaded Parquet files (gitignored)
│   │   ├── subway_perf/         # Daily subway-on-time-performance files
│   │   └── gtfs_static/         # GTFS static tables
│   └── processed/               # Cleaned & feature-engineered data
│       ├── bunching_events.parquet
│       ├── station_crowding.parquet
│       └── network_edges.parquet
├── notebooks/
│   ├── 01_data_acquisition.ipynb    # Download & cache LAMP data
│   ├── 02_eda.ipynb                 # Exploratory analysis, distributions
│   ├── 03_bunching_analysis.ipynb   # Bunching detection & crowding inference
│   ├── 04_network_analysis.ipynb    # Graph construction & centrality
│   ├── 05_cascade_analysis.ipynb    # Delay propagation modeling
│   └── 06_synthesis.ipynb           # Combine findings, KPI critique
├── src/
│   ├── data_loader.py           # Parquet download & caching utilities
│   ├── bunching.py              # Bunching detection logic
│   ├── crowding.py              # Dwell time → crowding inference
│   ├── network.py               # Graph construction (NetworkX)
│   ├── cascade.py               # Cascade propagation analysis
│   └── viz.py                   # Shared visualization helpers (Plotly)
└── web/
    ├── index.html               # Main landing page
    ├── app.py                   # Streamlit app (or static site generator)
    └── assets/
        ├── network_map.html     # Exported interactive network graph
        └── charts/              # Exported Plotly charts
```

---

## Tech Stack

| Category | Tools |
|----------|-------|
| Data processing | `pandas`, `pyarrow` (Parquet) |
| Network analysis | `networkx`, `pyvis` |
| Statistical analysis | `scipy`, `statsmodels` (Granger causality) |
| ML (lightweight) | `scikit-learn` (Isolation Forest, Logistic Regression) |
| Visualization | `plotly`, `folium` (map), `pyvis` (network) |
| Notebooks | `jupyter` |
| Web presentation | `streamlit` or static HTML with embedded Plotly |

---

## Analysis Detail

### Layer 3A: Bunching & Crowding Analysis

**Bunching Detection**
- Flag events where `headway_branch_seconds < 120` (2 min) as bunching
- Severity tiers: mild (2-4 min gap), moderate (1-2 min), severe (<1 min)
- Aggregate by: line, stop, hour-of-day, day-of-week

**Crowding Inference**
- Hypothesis: large headway gap preceding a train → more accumulated passengers → longer dwell time
- Method: Linear regression of `prior_headway_gap → dwell_time_seconds`, controlling for stop, time-of-day
- Output: "Crowding Score" per station per trip

**B Line Surface Stop Analysis**
- Compare `dwell_time_seconds` at surface stops (BU West, Packard's Corner, etc.) vs. underground stations
- Hypothesis: shorter dwell at surface stops = no fare gate friction
- Frame as: official metrics treat this as "efficiency" but it masks fare evasion

### Layer 3B: Network & Cascade Analysis

**Graph Construction**
- Nodes: stations (`parent_station`)
- Edges: route segments between consecutive stops
- Edge weight: median `travel_time_seconds` (baseline) + delay frequency

**Key Metrics**
- Betweenness Centrality: which stations are on the most "paths"?
- Delay Correlation Matrix: for each pair of stations, lagged correlation of delay events
- Cascade Detection: if station A delays, do downstream stations show elevated delays within N minutes?

**Cascade Modeling**
- Method: Granger causality test between station-level delay time series
- Output: directed graph of "who delays whom"
- Identify top 5 "super-spreader" stations

### Layer 4: Synthesis

**Rider Experience Score (vs. Official OTP)**
- Combine: bunching frequency + estimated crowding + downstream cascade impact
- Show side-by-side: Official on-time % vs. Rider Experience Score by line
- Key finding: lines with similar official OTP can have very different rider experience

**Bunching → Cascade Link**
- Do bunching hotspots overlap with cascade trigger stations?
- Hypothesis: bunching at transfer stations (e.g., Park St, Kenmore) is more likely to cascade

---

## ML Components

| Component | Method | Purpose |
|-----------|--------|---------|
| Anomaly Detection | Isolation Forest on `(headway, dwell_time, travel_time)` | Flag statistically abnormal service events without manual thresholds |
| Cascade Classifier | Logistic Regression | Given delay at station X (features: hour, line, delay severity, centrality), predict cascade probability |

ML is supplementary — the core value is the diagnostic framework.

---

## Web Presentation Plan

**Target:** A single-page website that tells the story with interactive visuals.

**Sections:**
1. **Hook** — "MBTA says X% on time. Here's what that hides." (headline stat)
2. **Bunching Map** — Heatmap of bunching hotspots by station/time
3. **Crowding Inference** — Headway gap vs. dwell time scatter, by line
4. **Network Graph** — Interactive graph colored by cascade centrality score
5. **Cascade Stories** — 2-3 specific delay events traced through the network
6. **B Line Spotlight** — Dwell time comparison, surface vs. underground (fare evasion angle)
7. **KPI Critique** — Side-by-side: Official OTP vs. Rider Experience Score

**Tech:** Streamlit (primary), or static HTML with Plotly JS if deploying to GitHub Pages.

---

## Timeline (2 Weeks)

| Days | Focus | Deliverable |
|------|-------|-------------|
| 1–2 | Data acquisition, caching, EDA | `01_data_acquisition.ipynb`, `02_eda.ipynb` |
| 3–4 | Bunching detection + crowding inference | `03_bunching_analysis.ipynb` |
| 5–6 | Network graph + centrality analysis | `04_network_analysis.ipynb` |
| 7–8 | Cascade analysis + Granger causality | `05_cascade_analysis.ipynb` |
| 9–10 | Synthesis, KPI critique, ML components | `06_synthesis.ipynb` |
| 11–12 | Web presentation build | `web/` folder |
| 13–14 | Polish, QA, deploy | Final website live |

---

## Key Hypotheses to Validate

- [ ] H1: Bunching events cluster at transfer stations (Park St, Downtown Crossing, Kenmore)
- [ ] H2: Larger headway gaps are positively correlated with longer dwell times (crowding signal)
- [ ] H3: Green Line B surface stops have systematically shorter dwell times than underground stops
- [ ] H4: Delays at high-centrality stations cascade to other lines within 15 minutes
- [ ] H5: Official on-time percentage overestimates service quality by masking bunching effects

---

## Potential Findings & Story Hooks

- "The MBTA doesn't track bunching — it's literally the forbidden word"
- "Park Street is the most dangerous station in the network (for cascades)"
- "B Line trains look faster on paper because riders don't pay"
- "X% of officially 'on-time' trips followed a bunching event that caused severe crowding"

---

## Notes & Decisions

- **No API key needed** — all data is public Parquet files on performancedata.mbta.com
- **GitHub repo**: keep `data/raw/` in `.gitignore` (files can be large); include download scripts
- **COVID exclusion**: 2020-2021 data excluded due to abnormal ridership patterns
- **Fare evasion**: treat as qualitative insight layer; LAMP data has no direct fare records, inference only from dwell time anomalies
- **Cloud strategy**: No cloud needed during development. Read raw data directly from MBTA public URLs via pandas (`pd.read_parquet(url)`). Only processed/aggregated outputs saved locally. Cloud (GCP / Streamlit Cloud) introduced only at final deployment stage.
