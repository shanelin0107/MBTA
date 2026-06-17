# Beyond On-Time Performance — MBTA Hidden Failures Analysis

**A system-wide analysis of train bunching, crowding inference, and delay cascade propagation across the MBTA subway network.**

🔗 **[Live Dashboard → shanelin0107.github.io/MBTA](https://shanelin0107.github.io/MBTA/)**

[🚇 MBTA Subway Animation](https://shanelin0107.github.io/MBTA/MBTA-Animation-standalone.html)

---

## The Problem

The MBTA publishes an official on-time percentage for each line. No line passes 57%.  
But the real problem isn't just lateness — it's two hidden failure modes the metric never captures:

1. **Train Bunching** — Trains arrive in clusters. Each one counts as "on-time," while riders in the preceding gap endure severe, unmeasured overcrowding.
2. **Cascade Failures** — A single delayed train at the wrong station can propagate across 32+ downstream stations within hours.

This project quantifies both — and builds a **Rider Experience Score** that reflects what passengers actually experience.

---

## Live Dashboard

> 8 interactive sections built with Plotly — no server required.

| Section | Content |
|---|---|
| 01 | Official OTP by line (Jan 2024 – May 2026) |
| 02 | Bunching rate + station × hour heatmap |
| 03 | Headway gap → dwell time crowding signal (H2) |
| 04 | Official OTP vs Rider Experience Score |
| 05 | Cascade case study — Aug 10, 2022 |
| 06 | Super-spreader stations (Granger causality) |
| 07 | Research hypotheses summary |
| 08 | ML cascade risk model: predictions + structural intervention backtest |

---

## Key Findings

- **No line passes 57% on-time.** Blue Line leads at 58.8%; Green D is worst at 29.6%.
- **Green D drops to 19.2%** after bunching (5.45%) and cascade penalties — a **−10.4 pt hidden gap**.
- **Blue Line: 51.9% of bunching events are still classified as "on-time"** — more than 1 in 2 bunched trains officially don't exist.
- **Longwood Medical stays hot all day** (10–13% bunching), a persistent choke-point invisible to OTP.
- **1 Kenmore delay → 32 downstream stations** affected within 5 hours (Aug 10, 2022).
- **At busy stations, a 25-min headway gap → 67s dwell time** (+40% vs normal), a direct crowding signal.
- **5 super-spreader stations drive 19.7% of all cascade events** — Kenmore, Copley, Government Center, Beaconsfield, Hynes Convention Center (identified via Granger causality out-degree).
- **Gradient Boosting cascade model** predicts evening rush risk at Kenmore peaks at P=0.93 (16–19h); structural intervention backtest shows isolating top-5 stations prevents **23,556 cascade events** across Green B/C/D/E and Blue lines over 17 months.

---

## Research Hypotheses

| Hypothesis | Result | Key Number |
|---|---|---|
| H1 — Bunching clusters at transfer stations | Partial | Outer Green D 6.33% vs transfer stations ~3.4% |
| H2 — Larger headway gap → longer dwell (crowding) | ✅ Supported | 1-min gap: 48s dwell → 25-min gap: 67s dwell (+40%) |
| H3 — Surface stops shorter dwell (fare evasion proxy) | ❌ Rejected | Surface 48s vs Underground 46s — reversed |
| H4 — High-centrality stations cascade delays | ✅ Supported | Kenmore causes delays at 32 downstream stations |
| H5 — Official OTP overestimates service quality | ✅ Supported | Green D: 29.6% official → 19.2% rider score |

---

## Project Structure

```
MBTA/
├── docs/                        # Static dashboard (GitHub Pages)
│   ├── index.html               # Main interactive dashboard
│   └── assets/
│       ├── network_map.html     # Interactive network graph (pyvis)
│       ├── station_risk_map.html# Folium choropleth map
│       ├── risk_heatmap.json    # ML cascade risk by station × hour
│       ├── backtest_data.json   # Structural intervention backtest results
│       └── charts/              # ML model charts
├── notebooks/
│   ├── 01_data_acquisition.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_bunching_analysis.ipynb
│   ├── 04_network_analysis.ipynb
│   ├── 05_cascade_analysis.ipynb
│   ├── 06_synthesis.ipynb
│   └── 07_cascade_prediction.ipynb
├── scripts/
│   ├── make_spreader_map.py     # Folium super-spreader map generator
│   ├── make_risk_heatmap.py     # ML cascade risk heatmap (Section 08 Step 0)
│   └── backtest_intervention.py # Structural intervention backtest
├── requirements.txt
└── CLAUDE.md                    # Project specification
```

---

## Data Source

All data from **[MBTA LAMP Public Data](https://performancedata.mbta.com)** — no API key required.

- **Subway On-Time Performance v1** — Jan 2024 – May 2026 (Sections 01–07)
- **ML model backtest** — Jan 2025 – May 2026 (17 months, Section 08)
- **GTFS Static** — stops, routes, trips metadata
- Lines: Red, Orange, Blue, Green (B/C/D/E branches)

> Raw data files are not included in this repo (gitignored). Re-download via `notebooks/01_data_acquisition.ipynb`.

---

## How to Run

```bash
# Clone and set up
git clone https://github.com/shanelin0107/MBTA.git
cd MBTA
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run notebooks in order
jupyter lab
# 01 → 02 → 03 → 04 → 05 → 06 → 07

# Regenerate Section 08 assets
python scripts/make_risk_heatmap.py       # cascade risk heatmap
python scripts/backtest_intervention.py   # intervention backtest
python scripts/make_spreader_map.py       # super-spreader map
```

---

## Tech Stack

| Category | Tools |
|---|---|
| Data processing | `pandas`, `pyarrow` |
| Network analysis | `networkx`, `pyvis` |
| Statistical analysis | `scipy`, `statsmodels` (Granger causality) |
| Machine learning | `scikit-learn` (Gradient Boosting, Isolation Forest) |
| Visualization | `plotly`, `folium` |
| Dashboard | Static HTML + Plotly.js |

---

## Author

**Shawn Lin** · [GitHub](https://github.com/shanelin0107)

> Independent research, not affiliated with the MBTA.  
> Data: MBTA LAMP Public Data (performancedata.mbta.com)
