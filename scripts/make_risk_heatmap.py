"""
Generate cascade risk heatmap data for Section 08 Step 0.

Outputs: docs/assets/risk_heatmap.json
  - avg predicted cascade probability by (super-spreader station × hour of day)
  - two scenarios: actual model vs. structural intervention (top-5 isolated)

Usage:
  python scripts/make_risk_heatmap.py           # full run (17 months)
  python scripts/make_risk_heatmap.py --test    # 1 month only for quick validation
"""

import sys
import json
import pickle
import warnings
import numpy as np
import pandas as pd
from pathlib import Path

warnings.filterwarnings('ignore')

TEST_MODE = '--test' in sys.argv

ROOT     = Path(__file__).resolve().parents[1]
PROC_DIR = ROOT / 'data' / 'processed'
OUT_PATH = ROOT / 'docs' / 'assets' / 'risk_heatmap.json'

TEST_YM = ['2025-01'] if TEST_MODE else (
    [f'2025-{m:02d}' for m in range(1, 13)] + [f'2026-{m:02d}' for m in range(1, 6)]
)
print(f'Mode: {"TEST (1 month)" if TEST_MODE else "FULL (17 months)"}')
print(f'Months: {TEST_YM}')

# ── Load model ─────────────────────────────────────────────────────────────────
with open(PROC_DIR / 'cascade_model.pkl', 'rb') as f:
    payload = pickle.load(f)
model        = payload['model']
FEATURE_COLS = payload['feature_cols']
THRESHOLD    = payload['threshold']
print(f'Loaded model: {payload["model_name"]}  threshold={THRESHOLD}')
print(f'Features: {FEATURE_COLS}')

# ── Load raw OTP data ──────────────────────────────────────────────────────────
OTP_COLS = ['route_id', 'line', 'parent_station', 'stop_timestamp',
            'scheduled_arrival_time', 'service_date', 'headway_branch_seconds']
frames = []
for ym in TEST_YM:
    tmp = pd.read_parquet(PROC_DIR / 'strategic' / f'{ym}.parquet', columns=OTP_COLS)
    frames.append(tmp)
raw = pd.concat(frames, ignore_index=True)

raw = raw.dropna(subset=['stop_timestamp', 'scheduled_arrival_time']).copy()
raw['service_date'] = pd.to_datetime(raw['service_date'])

# Vectorized midnight_unix: avoid per-row apply()
unique_dates = raw['service_date'].unique()
tz = 'America/New_York'
date_to_unix = {
    d: pd.Timestamp(d, tz=tz).timestamp()
    for d in pd.to_datetime(unique_dates)
}
raw['midnight_unix'] = raw['service_date'].map(date_to_unix)

raw['scheduled_unix'] = raw['midnight_unix'] + raw['scheduled_arrival_time']
raw['delay_sec']      = raw['stop_timestamp'] - raw['scheduled_unix']
raw = raw[raw['delay_sec'].abs() <= 3600].copy()
raw['hour']        = (raw['scheduled_arrival_time'] // 3600).astype(int).clip(0, 23)
raw['day_of_week'] = raw['service_date'].dt.dayofweek
raw['is_weekend']  = (raw['day_of_week'] >= 5)

station_hour = (
    raw.groupby(['service_date', 'parent_station', 'line', 'hour',
                 'day_of_week', 'is_weekend'])
    .agg(mean_delay=('delay_sec', 'mean'), n_trips=('delay_sec', 'count'))
    .reset_index()
)
station_hour['is_delay_event'] = station_hour['mean_delay'] > 300
station_hour['delay_severity'] = pd.cut(
    station_hour['mean_delay'],
    bins=[-np.inf, 300, 600, 1200, np.inf], labels=[0, 1, 2, 3]
).astype(int)

print(f'Station-hour rows: {len(station_hour):,}')

# ── Feature matrix ─────────────────────────────────────────────────────────────
cascade_scores = pd.read_parquet(
    PROC_DIR / 'station_cascade_score.parquet',
    columns=['parent_station', 'betweenness', 'bunching_rate', 'n_events', 'out_degree']
).rename(columns={'bunching_rate': 'hist_bunching_rate',
                  'n_events': 'station_volume', 'out_degree': 'granger_out_degree'})
cascade_scores['station_volume_norm'] = (
    cascade_scores['station_volume'] / cascade_scores['station_volume'].max())

feat = station_hour[['service_date', 'parent_station', 'line',
                      'hour', 'day_of_week', 'is_weekend',
                      'delay_severity', 'n_trips']].copy()
feat['is_peak']    = ((feat['hour'].between(7, 9)) | (feat['hour'].between(16, 19))).astype(int)
feat['is_weekend'] = feat['is_weekend'].astype(int)
feat['hour_sin']   = np.sin(2 * np.pi * feat['hour'] / 24)
feat['hour_cos']   = np.cos(2 * np.pi * feat['hour'] / 24)
feat = feat.merge(cascade_scores, on='parent_station', how='left')
for c in ['betweenness', 'hist_bunching_rate', 'granger_out_degree', 'station_volume_norm']:
    feat[c] = feat[c].fillna(0)

X_actual = feat[FEATURE_COLS].fillna(0)
feat['prob_actual'] = model.predict_proba(X_actual)[:, 1]

# ── Structural intervention ────────────────────────────────────────────────────
top_spreaders = cascade_scores.nlargest(5, 'granger_out_degree')['parent_station'].tolist()
cent = pd.read_parquet(PROC_DIR / 'station_centrality.parquet',
                       columns=['parent_station', 'stop_name'])
name_map = cent.set_index('parent_station')['stop_name'].to_dict()
spreader_names = [name_map.get(s, s) for s in top_spreaders]
print(f'Top-5 spreaders: {spreader_names}')

X_structural = X_actual.copy()
is_spreader = feat['parent_station'].isin(top_spreaders).values
X_structural.loc[is_spreader, 'granger_out_degree'] = 0
X_structural.loc[is_spreader, 'betweenness']        = 0
feat['prob_structural'] = model.predict_proba(X_structural)[:, 1]
feat['pred_actual']     = (feat['prob_actual']     >= THRESHOLD).astype(int)
feat['pred_structural'] = (feat['prob_structural'] >= THRESHOLD).astype(int)

# ── Build heatmap: avg probability by (station × hour) ────────────────────────
spreader_feat = feat[feat['parent_station'].isin(top_spreaders)].copy()
spreader_feat['stop_name'] = spreader_feat['parent_station'].map(name_map)

# Order stations by out_degree (highest first = rank 1)
ordered = (cascade_scores[cascade_scores['parent_station'].isin(top_spreaders)]
           .nlargest(5, 'granger_out_degree'))
station_order = [name_map.get(s, s) for s in ordered['parent_station']]

HOURS = list(range(5, 24))  # 5am to 11pm

heatmap_actual = []
for sid in ordered['parent_station']:
    sub = spreader_feat[spreader_feat['parent_station'] == sid]
    row = []
    for h in HOURS:
        h_sub = sub[sub['hour'] == h]
        row.append(round(float(h_sub['prob_actual'].mean()), 4) if len(h_sub) > 0 else 0.0)
    heatmap_actual.append(row)

# ── Cascade events prevented per hour-of-day (across all spreader stations) ───
# "Prevented" = model predicted cascade before intervention but not after
prevented_mask = (feat['pred_actual'] == 1) & (feat['pred_structural'] == 0) & feat['parent_station'].isin(top_spreaders)
prevented_by_hour = feat[prevented_mask].groupby('hour').size().reindex(HOURS, fill_value=0).tolist()

print('\nCascade events prevented by hour:')
for h, n in zip(HOURS, prevented_by_hour):
    bar = '█' * (n // 50)
    print(f'  {h:02d}h  {n:5d}  {bar}')

# ── Output ─────────────────────────────────────────────────────────────────────
out = {
    'stations': station_order,
    'hours': HOURS,
    'prob_actual': heatmap_actual,
    'prevented_by_hour': prevented_by_hour,
}

with open(OUT_PATH, 'w') as f:
    json.dump(out, f)

print(f'\nSaved: {OUT_PATH}')
print(f'Stations: {station_order}')
print(f'Hour range: {HOURS[0]}h – {HOURS[-1]}h')
print('\nSample — Kenmore (rank #1) actual prob by hour:')
for h, p in zip(HOURS, heatmap_actual[0]):
    bar = '█' * int(p * 30)
    print(f'  {h:02d}h  {p:.3f}  {bar}')
