import csv
import json
from datetime import datetime, timedelta, timezone

from skyfield.api import load, EarthSatellite


def parse_tle_epoch(line1):
    raw = line1[18:32].strip()

    yy = int(raw[:2])
    day = float(raw[2:])
    year = 2000 + yy if yy < 57 else 1900 + yy

    epoch_dt = (
        datetime(year, 1, 1, tzinfo=timezone.utc)
        + timedelta(days=day - 1)
    )

    return {
        "epoch_raw": raw,
        "epoch_day": f"{year}年{int(day):03d}日目",
        "epoch_utc": epoch_dt.strftime("%Y/%m/%d %H:%M:%S UTC"),
        "epoch_iso": epoch_dt.isoformat().replace("+00:00", "Z"),
    }


ts = load.timescale()
t = ts.now()

rows = []

with open("china_geo.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for r in reader:
        name = r["name"]
        line1 = r["line1"]
        line2 = r["line2"]

        sat = EarthSatellite(
            line1,
            line2,
            name,
            ts
        )

        sp = sat.at(t).subpoint()

        # CSV側にエポックが無い場合にも動くように保険
        epoch = parse_tle_epoch(line1)

        rows.append({
            "name": name,
            "norad": r["norad"],
            "lat": f"{sp.latitude.degrees:.4f}",
            "lon": f"{sp.longitude.degrees:.4f}",
            "alt_km": f"{sp.elevation.km:.1f}",

            "epoch_raw": r.get("epoch_raw") or epoch["epoch_raw"],
            "epoch_day": r.get("epoch_day") or epoch["epoch_day"],
            "epoch_utc": r.get("epoch_utc") or epoch["epoch_utc"],
            "epoch_iso": r.get("epoch_iso") or epoch["epoch_iso"],
        })


markers = json.dumps(
    rows,
    ensure_ascii=False
)


html = """<!doctype html>
<html lang="ja">

<head>

<meta charset="utf-8">

<title>中国 GEO 衛星マップ</title>

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0">

<link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">

<script
    src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
</script>

<style>

body {
    margin: 0;
    font-family: sans-serif;
    background: #f7f3ea;
}

.header {
    padding: 16px;
}

#map {
    height: 75vh;
    width: 100%;
}

</style>

</head>


<body>

<div class="header">

<h2>中国 GEO 衛星マップ</h2>

<div>
表示衛星数：__COUNT__ 機
</div>

</div>


<div id="map"></div>


<script>

const data = __MARKERS__;

const map =
    L.map("map").setView([0, 120], 2);


L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 6,
        attribution: "OpenStreetMap"
    }
).addTo(map);



function catOf(r) {

    const n =
        String(r.name || "").toUpperCase();

    const lat =
        Math.abs(parseFloat(r.lat || "0"));


    if (lat > 3)
        return [
            "#dd6b20",
            "移動中・傾斜軌道",
            "南北方向への移動が大きい衛星です。傾斜軌道または軌道変更中の可能性があります。"
        ];


    if (n.includes("TIANLIAN"))
        return [
            "#2b6cb0",
            "データ中継",
            "天鏈（Tianlian）系列のデータ中継衛星候補です。"
        ];


    if (
        n.includes("CHINASAT") ||
        n.includes("ZHONGXING") ||
        n.includes("ZX-") ||
        n.includes("APSTAR")
    )
        return [
            "#c53030",
            "中国通信衛星",
            "中国系の通信衛星候補です。"
        ];


    if (
        n.includes("FENGYUN") ||
        n.includes("FY-")
    )
        return [
            "#2f855a",
            "気象・観測",
            "風雲（Fengyun）系列の気象・観測衛星候補です。"
        ];


    if (
        n.includes("BEIDOU") ||
        n.includes("COMPASS")
    )
        return [
            "#6b46c1",
            "測位・航法",
            "北斗（BeiDou）系列の測位衛星候補です。"
        ];


    return [
        "#718096",
        "未分類",
        "現在の分類条件では未分類の衛星です。"
    ];
}



function ageOf(epochIso) {

    const epoch = new Date(epochIso);

    if (Number.isNaN(epoch.getTime())) {
        return "不明";
    }

    let diff =
        Date.now() - epoch.getTime();

    const future =
        diff < 0;

    diff =
        Math.abs(diff);

    const totalMinutes =
        Math.floor(diff / 60000);

    const days =
        Math.floor(totalMinutes / 1440);

    const hours =
        Math.floor((totalMinutes % 1440) / 60);

    const minutes =
        totalMinutes % 60;

    let text = "";

    if (days > 0) {
        text += days + "日 ";
    }

    text +=
        hours + "時間" +
        minutes + "分";

    return future
        ? "未来 " + text
        : text;
}



function freshnessOf(epochIso) {

    const epoch = new Date(epochIso);

    if (Number.isNaN(epoch.getTime())) {
        return {
            color: "#718096",
            icon: "⚪",
            text: "不明"
        };
    }

    const ageHours =
        (Date.now() - epoch.getTime())
        / 3600000;


    if (ageHours < 24) {
        return {
            color: "#16a34a",
            icon: "🟢",
            text: "新鮮"
        };
    }


    if (ageHours < 72) {
        return {
            color: "#ca8a04",
            icon: "🟡",
            text: "やや古い"
        };
    }


    if (ageHours < 168) {
        return {
            color: "#ea580c",
            icon: "🟠",
            text: "古い"
        };
    }


    return {
        color: "#dc2626",
        icon: "🔴",
        text: "要注意"
    };
}



function popupOf(r) {

    const c = catOf(r);

    const fresh =
        freshnessOf(r.epoch_iso);

    return (
        "<b>" + r.name + "</b><br>" +

        "<span style='" +
        "display:inline-block;" +
        "margin:4px 0;" +
        "padding:2px 8px;" +
        "border-radius:10px;" +
        "background:" + c[0] + ";" +
        "color:white;" +
        "font-size:12px;" +
        "'>" +

        c[1] +

        "</span><br>" +

        "<b>NORAD ID：</b>" +
        r.norad + "<br>" +

        "<b>緯度：</b>" +
        r.lat + "°<br>" +

        "<b>経度：</b>" +
        r.lon + "°<br>" +

        "<b>高度：</b>" +
        r.alt_km + " km<br>" +

        "<hr>" +

        "<b>TLEエポック：</b>" +
        r.epoch_day + "<br>" +

        "<b>エポック日時：</b>" +
        r.epoch_utc + "<br>" +

        "<b>経過時間：</b>" +
        ageOf(r.epoch_iso) + "<br>" +

        "<b>TLE鮮度：</b>" +

        "<span style='" +
        "font-weight:bold;" +
        "color:" + fresh.color + ";" +
        "'>" +

        fresh.icon + " " +
        fresh.text +

        "</span><br>" +

        "<hr>" +

        "<b>国・地域：</b>中国系候補<br>" +

        "<b>分類：</b>" +
        c[1] + "<br>" +

        "<b>任務メモ：</b>" +
        c[2]
    );
}



data.forEach(r => {

    const c = catOf(r);

    L.circleMarker(
        [
            parseFloat(r.lat),
            parseFloat(r.lon)
        ],
        {
            radius: 8,
            color: "#1a202c",
            weight: 1,
            fillColor: c[0],
            fillOpacity: 0.9
        }
    )
    .addTo(map)
    .bindPopup(popupOf(r));

});



const legend =
    L.control({
        position: "bottomleft"
    });


legend.onAdd = function() {

    const div =
        L.DomUtil.create(
            "div",
            "info legend"
        );

    div.style.background = "white";
    div.style.padding = "10px";
    div.style.borderRadius = "8px";
    div.style.boxShadow =
        "0 1px 5px rgba(0,0,0,0.3)";
    div.style.fontSize = "13px";

    div.innerHTML =

        "<b>衛星カテゴリ</b><br>" +

        "<div><span style='display:inline-block;width:12px;height:12px;background:#2b6cb0;border-radius:50%;margin-right:6px;'></span>データ中継</div>" +

        "<div><span style='display:inline-block;width:12px;height:12px;background:#c53030;border-radius:50%;margin-right:6px;'></span>中国通信衛星</div>" +

        "<div><span style='display:inline-block;width:12px;height:12px;background:#2f855a;border-radius:50%;margin-right:6px;'></span>気象・観測</div>" +

        "<div><span style='display:inline-block;width:12px;height:12px;background:#6b46c1;border-radius:50%;margin-right:6px;'></span>測位・航法</div>" +

        "<div><span style='display:inline-block;width:12px;height:12px;background:#dd6b20;border-radius:50%;margin-right:6px;'></span>移動中・傾斜軌道</div>" +

        "<div><span style='display:inline-block;width:12px;height:12px;background:#718096;border-radius:50%;margin-right:6px;'></span>未分類</div>";

    return div;
};


legend.addTo(map);

</script>

</body>
</html>
"""


html = html.replace(
    "__COUNT__",
    str(len(rows))
)

html = html.replace(
    "__MARKERS__",
    markers
)


with open(
    "china_map.html",
    "w",
    encoding="utf-8"
) as f:

    f.write(html)


print("saved china_map.html")
print(f"count: {len(rows)}")