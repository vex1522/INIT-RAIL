"""Build the interactive Folium zone map."""

from pathlib import Path
import random

import folium
from folium.plugins import HeatMap


ZONE_COORDS = {
    "Beach": [13.0925, 80.2954],
    "Egmore": [13.0790, 80.2618],
    "Tambaram": [12.9249, 80.1100],
    "Avadi": [13.1166, 80.1009],
    "Chengalpattu": [12.6954, 79.9767],
}

OUTPUT_PATH = Path("outputs") / "railway_mobility_map.html"


def run(df) -> None:
    """Create and save the folium map."""
    m = folium.Map(location=[13.0827, 80.2707], zoom_start=11, tiles="OpenStreetMap")
    folium.TileLayer("CartoDB positron", name="Light Map").add_to(m)
    folium.TileLayer("OpenStreetMap", name="Street Map").add_to(m)

    for zone, coords in ZONE_COORDS.items():
        zone_df = df[df["zone"] == zone]
        if zone_df.empty:
            continue
        avg_pass = zone_df["passengers"].mean()
        avg_delay = zone_df["delay_min"].mean()
        dominant_load = zone_df["peak_load"].mode()[0]
        radius = avg_pass / 200
        color = "green" if avg_pass < 2000 else "orange" if avg_pass <= 3500 else "red"
        popup_html = f"""
<div style="font-family:sans-serif;min-width:200px;padding:8px">
  <h4 style="margin:0 0 8px;color:#d4a373;border-bottom:2px solid #d4a373">{zone}</h4>
  <table style="width:100%;border-collapse:collapse">
    <tr><td style="color:#7a7060">Avg Passengers</td>
        <td><b>{avg_pass:.0f}</b></td></tr>
    <tr><td style="color:#7a7060">Avg Delay</td>
        <td><b>{avg_delay:.1f} min</b></td></tr>
    <tr><td style="color:#7a7060">Dominant Load</td>
        <td><b>{dominant_load}</b></td></tr>
    <tr><td style="color:#7a7060">Route Count</td>
        <td><b>{zone_df['route_id'].nunique()}</b></td></tr>
  </table>
</div>
"""
        folium.CircleMarker(
            location=coords,
            radius=radius,
            color=color,
            fill=True,
            fill_opacity=0.65,
            weight=2,
            tooltip=folium.Tooltip(f"{zone} - {avg_pass:.0f} passengers"),
            popup=folium.Popup(popup_html, max_width=260),
        ).add_to(m)

    heat_data = []
    for _, row in df.iterrows():
        if row["zone"] in ZONE_COORDS:
            lat, lon = ZONE_COORDS[row["zone"]]
            heat_data.append(
                [
                    lat + random.uniform(-0.02, 0.02),
                    lon + random.uniform(-0.02, 0.02),
                    row["passengers"],
                ]
            )
    HeatMap(heat_data, radius=12, blur=15).add_to(m)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    legend_html = """
<div style="position:fixed;bottom:30px;left:30px;z-index:9999;
            background:#fefae0;padding:14px 18px;border-radius:10px;
            border:2px solid #d4a373;font-family:sans-serif;font-size:13px">
  <b style="color:#3b3a2f">Avg Passengers</b><br>
  <span style="color:#6a994e">●</span> Low  &lt; 2000<br>
  <span style="color:#e6a817">●</span> Medium  2000-3500<br>
  <span style="color:#bc4749">●</span> High  &gt; 3500
</div>"""
    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl(collapsed=False).add_to(m)
    m.save(str(OUTPUT_PATH))
    print(f"Total markers placed: {len(ZONE_COORDS)}")
