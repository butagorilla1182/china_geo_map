from pathlib import Path
import json
from skyfield.api import load, EarthSatellite

tle_path = Path("china_clean.tle")
out_html = Path("china_map.html")
index_html = Path("index.html")

lines = tle_path.read_text(encoding="utf-8", errors="ignore").splitlines()

ts = load.timescale()
t = ts.now()

rows = []
for i in range(0, len(lines) - 2, 3):
    name = lines[i].strip()
    l1 = lines[i + 1].strip()
    l2 = lines[i + 2].strip()

    if not (l1.startswith("1 ") and l2.startswith("2 ")):
        continue

    sat = EarthSatellite(l1, l2, name, ts)
    sp = sat.at(t).subpoint()

    lat = float(sp.latitude.degrees)
    lon = float(sp.longitude.degrees)
    alt_km = float(sp.elevation.km)
    norad = l1[2:7].strip()

    rows.append({
        "name": name,
        "norad": norad,
        "lat": f"{lat:.4f}",
        "lon": f"{lon:.4f}",
        "alt_km": f"{alt_km:.1f}",
    })

markers = json.dumps(rows, ensure_ascii=False)

html = f'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>China GEO Map</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
body {{ margin:0; font-family:sans-serif; background:#f7f3ea; }}
.header {{ padding:16px; }}
.btn {{ display:block; margin:10px 16px; padding:14px; background:#2f6f5b; color:white; text-align:center; border-radius:10px; text-decoration:none; font-size:20px; }}
#map {{ height:75vh; width:100%; }}
</style>
</head>
<body>
<div class="header">
<h2>China GEO Map</h2>
<div>Satellites: {len(rows)}</div>
</div>
<div id="map"></div>
<script>
const data = {markers};

const map = L.map("map").setView([0, 120], 2);
L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
  maxZoom: 6,
  attribution: "OpenStreetMap"
}}).addTo(map);

function catOf(r) {{
  const n = String(r.name || "").toUpperCase();
  const lat = Math.abs(parseFloat(r.lat || "0"));

  if (lat > 3) return ["#dd6b20", "Moving / inclined", "Large north-south movement. Possibly inclined orbit or relocation."];
  if (n.includes("TIANLIAN")) return ["#2b6cb0", "Data relay", "Tianlian data relay satellite candidate."];
  if (n.includes("CHINASAT") || n.includes("ZHONGXING") || n.includes("ZX-") || n.includes("APSTAR")) return ["#c53030", "PRC communications", "Chinese communications satellite candidate."];
  if (n.includes("FENGYUN") || n.includes("FY-")) return ["#2f855a", "Weather / observation", "Fengyun weather or observation satellite candidate."];
  if (n.includes("BEIDOU") || n.includes("COMPASS")) return ["#6b46c1", "Navigation", "BeiDou navigation satellite candidate."];
  return ["#718096", "Unsorted", "Not classified yet."];
}}

function popupOf(r) {{
  const c = catOf(r);
  return "<b>" + r.name + "</b><br>"
    + "<span style='display:inline-block;margin:4px 0;padding:2px 8px;border-radius:10px;background:" + c[0] + ";color:white;font-size:12px;'>" + c[1] + "</span><br>"
    + "NORAD " + r.norad + "<br>"
    + "Lat " + r.lat + "<br>"
    + "Lon " + r.lon + "<br>"
    + "Alt km " + r.alt_km + "<br><hr>"
    + "<b>Country:</b> China candidate<br>"
    + "<b>Category:</b> " + c[1] + "<br>"
    + "<b>Mission note:</b> " + c[2];
}}

data.forEach(r => {{
  const c = catOf(r);
  L.circleMarker([parseFloat(r.lat), parseFloat(r.lon)], {{
    radius: 8,
    color: "#1a202c",
    weight: 1,
    fillColor: c[0],
    fillOpacity: 0.9
  }}).addTo(map).bindPopup(popupOf(r));
}});

const legend = L.control({{position:"bottomleft"}});
legend.onAdd = function() {{
  const div = L.DomUtil.create("div", "info legend");
  div.style.background = "white";
  div.style.padding = "10px";
  div.style.borderRadius = "8px";
  div.style.boxShadow = "0 1px 5px rgba(0,0,0,0.3)";
  div.style.fontSize = "13px";
  div.innerHTML =
    "<b>Satellite category</b><br>" +
    "<div><span style='display:inline-block;width:12px;height:12px;background:#2b6cb0;border-radius:50%;margin-right:6px;'></span>Data relay</div>" +
    "<div><span style='display:inline-block;width:12px;height:12px;background:#c53030;border-radius:50%;margin-right:6px;'></span>PRC communications</div>" +
    "<div><span style='display:inline-block;width:12px;height:12px;background:#2f855a;border-radius:50%;margin-right:6px;'></span>Weather / observation</div>" +
    "<div><span style='display:inline-block;width:12px;height:12px;background:#6b46c1;border-radius:50%;margin-right:6px;'></span>Navigation</div>" +
    "<div><span style='display:inline-block;width:12px;height:12px;background:#dd6b20;border-radius:50%;margin-right:6px;'></span>Moving / inclined</div>" +
    "<div><span style='display:inline-block;width:12px;height:12px;background:#718096;border-radius:50%;margin-right:6px;'></span>Unsorted</div>";
  return div;
}};
legend.addTo(map);
</script>
</body>
</html>
'''

out_html.write_text(html, encoding="utf-8")
index_html.write_text('<meta http-equiv="refresh" content="0; url=china_map.html">\n', encoding="utf-8")

print(f"saved {out_html}")
print(f"count: {len(rows)}")
