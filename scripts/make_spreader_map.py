"""
Generate an interactive Folium map showing:
- All MBTA stations (small dots, colored by line)
- Top 5 Green Line super-spreaders (large pulsing markers)
- Orange Line key stations: North Station + Haymarket
- Red Line key station: Park Street
- Network edges (faint lines)

Output: docs/assets/spreader_map.html
"""

import pandas as pd
import folium
from pathlib import Path

ROOT     = Path(__file__).resolve().parents[1]
PROC_DIR = ROOT / 'data' / 'processed'
OUT_PATH = ROOT / 'docs' / 'assets' / 'spreader_map.html'

# ── Load data ─────────────────────────────────────────────────────────────────
sc   = pd.read_parquet(PROC_DIR / 'station_cascade_score.parquet',
       columns=['parent_station','stop_name','out_degree','betweenness','super_spreader_score'])
cent = pd.read_parquet(PROC_DIR / 'station_centrality.parquet',
       columns=['parent_station','lat','lon','lines'])
edges = pd.read_parquet(PROC_DIR / 'network_edges.parquet',
        columns=['from_station','to_station','route_id'])

merged = sc.merge(cent, on='parent_station', how='left').dropna(subset=['lat','lon'])

# Green Line top-5 super-spreaders
TOP5_IDS = ['place-kencl','place-coecl','place-gover','place-bcnfd','place-hymnl']
top5 = merged[merged['parent_station'].isin(TOP5_IDS)].copy()

# Orange Line key stations
ORANGE_IDS = ['place-north','place-haecl']
orange_key = merged[merged['parent_station'].isin(ORANGE_IDS)].copy()

# Red Line key station
RED_IDS = ['place-pktrm']
red_key = merged[merged['parent_station'].isin(RED_IDS)].copy()

ALL_KEY_IDS = TOP5_IDS + ORANGE_IDS + RED_IDS

# Line colors
EDGE_COLOR = {
    'Red':     '#DA291C',
    'Orange':  '#ED8B00',
    'Blue':    '#003DA5',
    'Green-B': '#00843D',
    'Green-C': '#00843D',
    'Green-D': '#00843D',
    'Green-E': '#00843D',
}

# ── Build map ─────────────────────────────────────────────────────────────────
m = folium.Map(
    location=[42.355, -71.080],
    zoom_start=13,
    tiles='CartoDB.DarkMatter',
    prefer_canvas=True,
)

# Draw network edges (faint)
station_coords = merged.set_index('parent_station')[['lat','lon']].to_dict('index')
for _, row in edges.iterrows():
    src = row['from_station']
    dst = row['to_station']
    if src not in station_coords or dst not in station_coords:
        continue
    route = row['route_id']
    color = EDGE_COLOR.get(route, '#888888')
    folium.PolyLine(
        locations=[
            [station_coords[src]['lat'], station_coords[src]['lon']],
            [station_coords[dst]['lat'], station_coords[dst]['lon']],
        ],
        color=color, weight=2.5, opacity=0.45,
    ).add_to(m)

# Draw all stations (small circles)
for _, row in merged.iterrows():
    if row['parent_station'] in ALL_KEY_IDS:
        continue
    lines_str = str(row.get('lines', ''))
    if 'Red' in lines_str:       color = '#DA291C'
    elif 'Orange' in lines_str:  color = '#ED8B00'
    elif 'Blue' in lines_str:    color = '#003DA5'
    elif 'Green' in lines_str:   color = '#00843D'
    else:                        color = '#888888'

    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=4,
        color=color, fill=True, fill_color=color,
        fill_opacity=0.7, opacity=0.8, weight=1,
        tooltip=folium.Tooltip(f"<b>{row['stop_name']}</b><br>out_degree: {int(row['out_degree'])}"),
    ).add_to(m)

# ── Draw Green Line top-5 super-spreaders ─────────────────────────────────────
RANK_COLORS = ['#FF4444', '#FF6B00', '#FFA500', '#FFD700', '#FFEE88']
top5_sorted = top5.sort_values('out_degree', ascending=False).reset_index(drop=True)

for i, row in top5_sorted.iterrows():
    rank = i + 1
    color = RANK_COLORS[i]
    radius = 8 + row['out_degree'] * 0.3

    # Outer pulse ring
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=radius + 6,
        color=color, fill=False,
        opacity=0.4, weight=2,
    ).add_to(m)

    # Main marker
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=radius,
        color='white', fill=True, fill_color=color,
        fill_opacity=0.95, opacity=1, weight=2,
        tooltip=folium.Tooltip(
            f"<div style='font-family:Inter,sans-serif;font-size:13px;'>"
            f"<b style='color:{color}'>🟢 #{rank} Green Line Super-Spreader</b><br>"
            f"<b>{row['stop_name']}</b><br>"
            f"Granger out-degree: <b>{int(row['out_degree'])}</b> downstream stations<br>"
            f"Betweenness: {row['betweenness']:.3f}"
            f"</div>",
            sticky=True
        ),
        popup=folium.Popup(
            f"<div style='font-family:Inter,sans-serif;min-width:180px'>"
            f"<div style='font-size:11px;font-weight:700;color:{color};text-transform:uppercase;letter-spacing:1px;margin-bottom:4px'>🟢 #{rank} Green Line Super-Spreader</div>"
            f"<div style='font-size:16px;font-weight:800;margin-bottom:8px'>{row['stop_name']}</div>"
            f"<div style='font-size:12px;color:#444;margin-bottom:4px'>Cascades to <b>{int(row['out_degree'])} downstream stations</b></div>"
            f"<div style='font-size:12px;color:#444'>Lines: {row.get('lines','').replace(',', ', ')}</div>"
            f"</div>",
            max_width=220
        ),
    ).add_to(m)

    # Label
    folium.Marker(
        location=[row['lat'] + 0.0015, row['lon']],
        icon=folium.DivIcon(
            html=f"""<div style="
                font-family:Inter,sans-serif;
                font-size:11px;font-weight:700;
                color:{color};
                text-shadow:0 0 6px #000, 0 0 10px #000;
                white-space:nowrap;pointer-events:none;
            ">#{rank} {row['stop_name']}<br>
            <span style='font-size:10px;font-weight:400;color:rgba(255,255,255,0.8)'>→ {int(row['out_degree'])} stations</span>
            </div>""",
            icon_size=(160, 35), icon_anchor=(0, 0),
        )
    ).add_to(m)

# ── Draw Orange Line key stations ─────────────────────────────────────────────
ORANGE_COLOR = '#ED8B00'
orange_sorted = orange_key.sort_values('out_degree', ascending=False).reset_index(drop=True)

for i, row in orange_sorted.iterrows():
    rank_label = ['North Station', 'Haymarket'][i]

    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=14,
        color=ORANGE_COLOR, fill=False,
        opacity=0.4, weight=2,
    ).add_to(m)

    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=10,
        color='white', fill=True, fill_color=ORANGE_COLOR,
        fill_opacity=0.95, opacity=1, weight=2,
        tooltip=folium.Tooltip(
            f"<div style='font-family:Inter,sans-serif;font-size:13px;'>"
            f"<b style='color:{ORANGE_COLOR}'>🟠 Orange Line Key Station</b><br>"
            f"<b>{row['stop_name']}</b><br>"
            f"Granger out-degree: <b>{int(row['out_degree'])}</b> downstream stations<br>"
            f"Betweenness: {row['betweenness']:.3f}"
            f"</div>",
            sticky=True
        ),
        popup=folium.Popup(
            f"<div style='font-family:Inter,sans-serif;min-width:180px'>"
            f"<div style='font-size:11px;font-weight:700;color:{ORANGE_COLOR};text-transform:uppercase;letter-spacing:1px;margin-bottom:4px'>🟠 Orange Line Key Station</div>"
            f"<div style='font-size:16px;font-weight:800;margin-bottom:8px'>{row['stop_name']}</div>"
            f"<div style='font-size:12px;color:#444;margin-bottom:4px'>Cascades to <b>{int(row['out_degree'])} downstream stations</b></div>"
            f"<div style='font-size:12px;color:#444'>Shared with Green Line</div>"
            f"</div>",
            max_width=220
        ),
    ).add_to(m)

    folium.Marker(
        location=[row['lat'] + 0.0015, row['lon']],
        icon=folium.DivIcon(
            html=f"""<div style="
                font-family:Inter,sans-serif;font-size:11px;font-weight:700;
                color:{ORANGE_COLOR};
                text-shadow:0 0 6px #000,0 0 10px #000;
                white-space:nowrap;pointer-events:none;
            ">{row['stop_name']}<br>
            <span style='font-size:10px;font-weight:400;color:rgba(255,255,255,0.8)'>Orange · → {int(row['out_degree'])} stations</span>
            </div>""",
            icon_size=(160, 30), icon_anchor=(0, 0),
        )
    ).add_to(m)

# ── Draw Red Line key station ─────────────────────────────────────────────────
RED_COLOR = '#DA291C'
for _, row in red_key.iterrows():
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=14,
        color=RED_COLOR, fill=False,
        opacity=0.4, weight=2,
    ).add_to(m)

    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=10,
        color='white', fill=True, fill_color=RED_COLOR,
        fill_opacity=0.95, opacity=1, weight=2,
        tooltip=folium.Tooltip(
            f"<div style='font-family:Inter,sans-serif;font-size:13px;'>"
            f"<b style='color:{RED_COLOR}'>🔴 Red Line Key Station</b><br>"
            f"<b>{row['stop_name']}</b><br>"
            f"Granger out-degree: <b>{int(row['out_degree'])}</b> downstream stations<br>"
            f"Betweenness: {row['betweenness']:.3f} (highest in system)"
            f"</div>",
            sticky=True
        ),
        popup=folium.Popup(
            f"<div style='font-family:Inter,sans-serif;min-width:180px'>"
            f"<div style='font-size:11px;font-weight:700;color:{RED_COLOR};text-transform:uppercase;letter-spacing:1px;margin-bottom:4px'>🔴 Red Line Key Station</div>"
            f"<div style='font-size:16px;font-weight:800;margin-bottom:8px'>{row['stop_name']}</div>"
            f"<div style='font-size:12px;color:#444;margin-bottom:4px'>Granger out-degree: <b>{int(row['out_degree'])} stations</b></div>"
            f"<div style='font-size:12px;color:#444;margin-bottom:4px'>Betweenness: <b>{row['betweenness']:.3f}</b> — highest in system</div>"
            f"<div style='font-size:12px;color:#444'>Shared with Green Line</div>"
            f"</div>",
            max_width=220
        ),
    ).add_to(m)

    folium.Marker(
        location=[row['lat'] + 0.0015, row['lon']],
        icon=folium.DivIcon(
            html=f"""<div style="
                font-family:Inter,sans-serif;font-size:11px;font-weight:700;
                color:{RED_COLOR};
                text-shadow:0 0 6px #000,0 0 10px #000;
                white-space:nowrap;pointer-events:none;
            ">{row['stop_name']}<br>
            <span style='font-size:10px;font-weight:400;color:rgba(255,255,255,0.8)'>Red · betweenness 0.560</span>
            </div>""",
            icon_size=(160, 30), icon_anchor=(0, 0),
        )
    ).add_to(m)

# ── Legend ────────────────────────────────────────────────────────────────────
legend_html = """
<div style="
    position:fixed; bottom:24px; left:50%; transform:translateX(-50%);
    background:rgba(10,14,20,0.92);
    border:1px solid rgba(255,255,255,0.15);
    border-radius:12px; padding:14px 20px;
    font-family:Inter,sans-serif; font-size:11px; color:white;
    z-index:9999; display:flex; gap:20px; align-items:center;
    backdrop-filter:blur(8px);
    box-shadow:0 4px 24px rgba(0,0,0,0.5);
">
  <div>
    <div style='font-weight:700;font-size:12px;margin-bottom:6px;color:rgba(255,255,255,0.9)'>System-Wide Cascade Risk Stations</div>
    <div style='display:flex;gap:12px;'>
      <span style='color:#FF4444;font-weight:700'>● Green Line Top 5</span>
      <span style='color:#ED8B00;font-weight:700'>● Orange Line</span>
      <span style='color:#DA291C;font-weight:700'>● Red Line</span>
    </div>
  </div>
  <div style='color:rgba(255,255,255,0.5);font-size:10px;border-left:1px solid rgba(255,255,255,0.1);padding-left:16px;'>
    Click any station for details<br>
    Granger out-degree = downstream stations affected
  </div>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# Save
m.save(str(OUT_PATH))
print(f'Saved: {OUT_PATH}')
print('\nGreen Line top-5:')
for i, row in top5_sorted.iterrows():
    print(f'  #{i+1} {row["stop_name"]:30s} out_degree={int(row["out_degree"])}')
print('\nOrange Line key stations:')
for _, row in orange_sorted.iterrows():
    print(f'  {row["stop_name"]:30s} out_degree={int(row["out_degree"])}')
print('\nRed Line key station:')
for _, row in red_key.iterrows():
    print(f'  {row["stop_name"]:30s} out_degree={int(row["out_degree"])}  betweenness={row["betweenness"]:.3f}')
