# Project Progress Log

**Project:** Beyond On-Time Performance — MBTA Hidden Failures Analysis  
**Dashboard:** [shanelin0107.github.io/MBTA](https://shanelin0107.github.io/MBTA/)  
**Last updated:** 2026-06-16

---

## Current Status: All 8 Sections Complete ✅

The full analysis pipeline — from raw data acquisition through ML prediction and prescriptive recommendations — is built, deployed, and live on GitHub Pages.

---

## Section Completion

| Section | Title | Status |
|---|---|---|
| 01 | Official OTP by line (Jan 2024 – May 2026) | ✅ Done |
| 02 | Bunching rate + station × hour heatmap | ✅ Done |
| 03 | Headway gap → dwell time crowding signal | ✅ Done |
| 04 | Official OTP vs Rider Experience Score | ✅ Done |
| 05 | Cascade case study — Aug 10, 2022 | ✅ Done |
| 06 | Super-spreader stations (Granger causality) | ✅ Done |
| 07 | Research hypotheses summary | ✅ Done |
| 08 | ML cascade risk model + structural intervention backtest | ✅ Done |

---

## Key Technical Milestones

### Data Pipeline
- Downloaded and processed MBTA LAMP Parquet files: Jan 2024 – May 2026 (OTP), Jan 2025 – May 2026 (ML backtest)
- Vectorized date→unix conversion — reduced 17-month processing from 30+ min hang to 17 seconds

### ML Model (Section 08)
- **Model:** Gradient Boosting (threshold = 0.4), saved as `data/processed/cascade_model.pkl`
- **Features:** `hour_sin`, `hour_cos`, `is_peak`, `is_weekend`, `delay_severity`, `betweenness`, `hist_bunching_rate`, `granger_out_degree`, `station_volume_norm`, `n_trips`
- **Structural intervention backtest:** sets `granger_out_degree=0`, `betweenness=0` for top-5 stations → simulates network isolation
- **Result:** 23,556 cascade events preventable over 17 months across Green B/C/D/E + Blue lines

### Section 08 Visualizations
- **Step 0** — Cascade risk heatmap by station × hour (actual model predictions); peak window (16–19h) highlighted in MBTA yellow; Kenmore peaks at P=0.93
- **Step 1** — Structural vs. operational risk sensitivity (delay_severity has near-zero effect; structural features dominate)
- **Step 2** — Case study before/after heatmap (Aug 10, 2022)
- **Step 3** — Preventable cascade events by line (Green B: 7,093 / C: 4,646 / D: 7,298 / E: 2,757 / Blue: 1,762)

### Scripts Created
| Script | Purpose |
|---|---|
| `scripts/make_risk_heatmap.py` | Generates `docs/assets/risk_heatmap.json` — ML risk by station × hour |
| `scripts/backtest_intervention.py` | Generates `docs/assets/backtest_data.json` — structural intervention results |
| `scripts/make_spreader_map.py` | Generates `docs/assets/station_risk_map.html` — Folium super-spreader map |

---

## Key Findings (Confirmed)

1. **No MBTA line passes 57% on-time.** Blue Line best (58.8%); Green D worst (29.6%).
2. **Green D rider score drops to 19.2%** after bunching + cascade penalties (−10.4 pt hidden gap).
3. **51.9% of Blue Line bunching events are classified "on-time"** — invisible to official metrics.
4. **Longwood Medical** is a persistent choke-point (10–13% bunching rate all day).
5. **1 Kenmore delay → 32 downstream stations** affected within 5 hours.
6. **Headway gap ↑ → dwell time ↑:** 1-min gap = 48s dwell; 25-min gap = 67s dwell (+40%).
7. **5 super-spreaders drive 19.7% of all cascade events:** Kenmore, Copley, Government Center, Beaconsfield, Hynes Convention Center.
8. **Cascade risk is structural, not operational** — delay_severity (operational) has near-zero model effect; betweenness + Granger out-degree (structural) dominate.
9. **Red/Orange/Blue have 0 internal cascade edges** — simple linear topology, no branching = no propagation network. All their "preventable" events occur at Government Center (Green+Blue shared station).

---

## Key Decisions Made

### Architecture
- **Orange/Red preventable = 0** in backtest (not 1,104 — that was from a buggy targeted run). Only Green branches and Blue (via Government Center) show preventable events.
- **"After" heatmap removed** — setting structural features to 0 drops all super-spreader probabilities to near zero, making the "after" chart all-white and uninformative. Replaced with single "before" heatmap + peak annotation.
- **prevented_by_hour not visualized** — model predicts ALL station-hours at super-spreaders as high risk, so hourly prevented counts are flat (~480 every hour). Not informative as a chart.

### Recommendations (Bottom Line section)
Chose **conservative, feasibility-focused framing** over ambitious claims:
- "real-time alerts" / "1–4 hours before impact" → removed (model is historical schedule, not live feed)
- Short-turn framed as **reactive → proactive shift**, not a new capability
- Kenmore (Kenmore Loop) + Government Center (westbound turnback track) = only 2 of 5 with physical short-turn infrastructure
- Copley / Hynes / Beaconsfield = headway spacing management only (no short-turn infrastructure)
- OTP reform split into: bunching frequency (feasible now) + cascade rate (longer-term target)

### Infrastructure Research
- **Kenmore Loop:** existing track loop; trains can reverse without entering B/C/D/E trunk
- **Government Center turnback track:** westbound track allowing Green Line trains to reverse before entering tunnel
- **Copley, Hynes, Beaconsfield:** no short-turn infrastructure confirmed
- None of the 5 stations serve as backup train storage locations (yards are at Reservoir, Riverside, etc.)

---

## Hypotheses Final Verdicts

| Hypothesis | Verdict |
|---|---|
| H1 — Bunching clusters at transfer stations | Partial — outer Green D (6.33%) higher than transfer stations (~3.4%) |
| H2 — Larger headway gap → longer dwell (crowding signal) | ✅ Supported |
| H3 — Surface stops shorter dwell (fare evasion proxy) | ❌ Rejected — surface 48s vs underground 46s (reversed) |
| H4 — High-centrality stations cascade delays | ✅ Supported |
| H5 — Official OTP overestimates service quality | ✅ Supported |

---

## Analytics Framework

This project covers all four analytics types:
- **Descriptive** — Sections 01–02 (what happened: OTP, bunching rates)
- **Diagnostic** — Sections 03–06 (why it happened: crowding signal, cascade structure, Granger causality)
- **Predictive** — Section 08 Step 0 (what will happen: cascade risk by station × hour)
- **Prescriptive** — Section 08 Bottom Line (what to do: pre-scheduled short-turns, headway management)

---

## Repo Stats
- **Total commits:** 41
- **Live URL:** https://shanelin0107.github.io/MBTA/
- **Branch:** `main`
