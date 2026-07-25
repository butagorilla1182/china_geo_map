import csv
import json

from skyfield.api import load, EarthSatellite, wgs84


# =========================================================
# CSV読み込み
# =========================================================

with open(
    "china_geo.csv",
    encoding="utf-8"
) as f:

    rows = list(
        csv.DictReader(f)
    )


# =========================================================
# 現在位置を計算
# =========================================================

ts = load.timescale()
t = ts.now()

satellite_data = []


for r in rows:

    try:

        name = r["name"]
        line1 = r["line1"]
        line2 = r["line2"]

        sat = EarthSatellite(
            line1,
            line2,
            name,
            ts
        )

        geocentric = sat.at(t)

        subpoint = wgs84.subpoint(
            geocentric
        )


        satellite_data.append({

            "name":
                name,

            "norad":
                r.get(
                    "norad",
                    ""
                ),

            "lat":
                round(
                    subpoint.latitude.degrees,
                    4
                ),

            "lon":
                round(
                    subpoint.longitude.degrees,
                    4
                ),

            "alt_km":
                round(
                    subpoint.elevation.km,
                    1
                ),


            # SATCAT
            "launch_date":
                r.get(
                    "launch_date",
                    ""
                ),

            "launch_site":
                r.get(
                    "launch_site",
                    ""
                ),


            # TLE Epoch
            "epoch_raw":
                r.get(
                    "epoch_raw",
                    ""
                ),

            "epoch_day":
                r.get(
                    "epoch_day",
                    ""
                ),

            "epoch_utc":
                r.get(
                    "epoch_utc",
                    ""
                ),

            "epoch_iso":
                r.get(
                    "epoch_iso",
                    ""
                ),
        })


    except Exception as e:

        print(
            "Satellite calculation skip:",
            r.get(
                "name",
                "UNKNOWN"
            ),
            e
        )


markers = json.dumps(
    satellite_data,
    ensure_ascii=False
)


# =========================================================
# HTML
# =========================================================

template = r'''
<html>

<head>

<meta charset="utf-8">

<title>China GEO Map</title>

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
>

<script
    src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
</script>


<style>

body {
    margin: 0;
    font-family: sans-serif;
}

.bar {
    padding: 12px;
    background: #f7f3ea;
}

.search-box {
    display: flex;
    gap: 7px;
    margin-top: 10px;
}

#satSearch {
    flex: 1;
    min-width: 0;
    padding: 10px;
    font-size: 16px;
    border: 1px solid #999;
    border-radius: 8px;
}

#searchButton {
    padding: 10px 15px;
    border: 0;
    border-radius: 8px;
    background: #2378d3;
    color: white;
    font-size: 15px;
    font-weight: bold;
}

#searchResult {
    min-height: 20px;
    margin-top: 6px;
    font-size: 13px;
}


/* 地図を広く表示 */
#map {
    height: 82vh;
    width: 100%;
}


/* =========================================================
   詳細ポップアップ

   ポップアップ全体を巨大化させず
   中身だけスクロール
   ========================================================= */

.leaflet-popup {
    max-width: 92vw;
}

.leaflet-popup-content-wrapper {
    max-width: 420px;
}

.leaflet-popup-content {
    max-height: 300px;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
    overscroll-behavior: contain;
    margin: 12px 18px;
}

.leaflet-popup-content::-webkit-scrollbar {
    width: 5px;
}

.leaflet-popup-content::-webkit-scrollbar-thumb {
    background: #999;
    border-radius: 5px;
}

</style>

</head>


<body>


<div class="bar">

    <b>China GEO Map</b><br>

    CelesTrak GEO + GPZから抽出した中国系GEO衛星<br>

    表示衛星数：__COUNT__ 機


    <div class="search-box">

        <input
            id="satSearch"
            type="text"
            placeholder="衛星名 または NORAD ID"
            autocomplete="off"
        >

        <button id="searchButton">
            🔍 検索
        </button>

    </div>


    <div id="searchResult"></div>

</div>


<div id="map"></div>


<script>


const data = __MARKERS__;



/* =========================================================
   地図
   ========================================================= */

const map =
    L.map(
        "map"
    ).setView(
        [0, 110],
        2
    );


L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 6,
        attribution: "OpenStreetMap"
    }
).addTo(map);



/* =========================================================
   発射場コード → 日本語
   ========================================================= */

const LAUNCH_SITES = {

    "WSC":
        "文昌衛星発射場",

    "XICLF":
        "西昌衛星発射センター",

    "JSC":
        "酒泉衛星発射センター",

    "TAISC":
        "太原衛星発射センター",

    "SCSLA":
        "南シナ海打上げ区域",

    "YSLA":
        "黄海打上げ区域",

    "SEAL":
        "シーローンチ海上発射施設",

    "UNK":
        "不明"
};



function launchSiteName(code) {

    if (!code) {
        return "不明";
    }


    const key =
        String(
            code
        )
        .trim()
        .toUpperCase();


    const name =
        LAUNCH_SITES[key];


    if (name) {

        return (
            name +
            "（" +
            key +
            "）"
        );
    }


    /*
     * 未登録コードは
     * 略号をそのまま表示
     */
    return key;
}



/* =========================================================
   衛星カテゴリ
   ========================================================= */

function catOf(r) {

    const n =
        String(
            r.name || ""
        ).toUpperCase();


    const lat =
        Math.abs(
            parseFloat(
                r.lat || "0"
            )
        );


    /*
     * GEOから南北に大きく外れている
     */
    if (lat > 3) {

        return [
            "#dd6b20",
            "移動中・傾斜大",
            "GEO付近だが南北方向の変動が大きい衛星"
        ];
    }


    /*
     * TIANLIAN
     */
    if (
        n.includes(
            "TIANLIAN"
        )
    ) {

        return [
            "#2b6cb0",
            "データ中継",
            "天鏈データ中継衛星系"
        ];
    }


    /*
     * 中国通信衛星
     */
    if (
        n.includes("CHINASAT") ||
        n.includes("ZHONGXING") ||
        n.includes("ZX-") ||
        n.includes("APSTAR")
    ) {

        return [
            "#c53030",
            "通信",
            "中国系静止通信衛星"
        ];
    }


    /*
     * 気象
     */
    if (
        n.includes("FENGYUN") ||
        n.includes("FY-")
    ) {

        return [
            "#2f855a",
            "気象・観測",
            "風雲系気象・地球観測衛星"
        ];
    }


    /*
     * BeiDou
     */
    if (
        n.includes("BEIDOU") ||
        n.includes("COMPASS")
    ) {

        return [
            "#6b46c1",
            "測位・航法",
            "北斗衛星測位システム"
        ];
    }


    return [
        "#718096",
        "未整理",
        "用途未整理"
    ];
}



/* =========================================================
   打上げ情報
   ========================================================= */

function formatLaunchDate(date) {

    if (!date) {
        return "不明";
    }


    return date.replaceAll(
        "-",
        "/"
    );
}



function launchAgeOf(date) {

    if (!date) {
        return "不明";
    }


    const launch =
        new Date(
            date +
            "T00:00:00Z"
        );


    if (
        Number.isNaN(
            launch.getTime()
        )
    ) {

        return "不明";
    }


    const diff =
        Date.now() -
        launch.getTime();


    if (diff < 0) {

        return "未打上げ";
    }


    const days =
        Math.floor(
            diff /
            86400000
        );


    if (days < 365) {

        return (
            days +
            "日"
        );
    }


    const years =
        Math.floor(
            days /
            365.2425
        );


    const remainDays =
        Math.floor(
            days -
            years *
            365.2425
        );


    return (
        years +
        "年 " +
        remainDays +
        "日"
    );
}



/* =========================================================
   TLE経過時間
   ========================================================= */

function ageOf(epochIso) {

    const epoch =
        new Date(
            epochIso
        );


    if (
        Number.isNaN(
            epoch.getTime()
        )
    ) {

        return "不明";
    }


    let diff =
        Date.now() -
        epoch.getTime();


    const future =
        diff < 0;


    diff =
        Math.abs(
            diff
        );


    const totalMinutes =
        Math.floor(
            diff /
            60000
        );


    const days =
        Math.floor(
            totalMinutes /
            1440
        );


    const hours =
        Math.floor(
            (
                totalMinutes %
                1440
            ) /
            60
        );


    const minutes =
        totalMinutes %
        60;


    let text = "";


    if (days > 0) {

        text +=
            days +
            "日 ";
    }


    text +=
        hours +
        "時間" +
        minutes +
        "分";


    return future
        ? "未来 " + text
        : text;
}



/* =========================================================
   TLE鮮度
   ========================================================= */

function freshnessOf(epochIso) {

    const epoch =
        new Date(
            epochIso
        );


    if (
        Number.isNaN(
            epoch.getTime()
        )
    ) {

        return {
            color: "#718096",
            icon: "⚪",
            text: "不明"
        };
    }


    const ageHours =
        (
            Date.now() -
            epoch.getTime()
        ) /
        3600000;


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



/* =========================================================
   ポップアップ
   ========================================================= */

function popOf(r) {

    const c =
        catOf(r);


    const fresh =
        freshnessOf(
            r.epoch_iso
        );


    return (

        "<b>" +
        r.name +
        "</b><br>" +


        "<span style='" +

        "display:inline-block;" +
        "margin:4px 0;" +
        "padding:2px 8px;" +
        "border-radius:10px;" +

        "background:" +
        c[0] +
        ";" +

        "color:white;" +
        "font-size:12px;" +

        "'>" +

        c[1] +

        "</span><br>" +


        "<b>NORAD ID：</b>" +
        r.norad +
        "<br>" +


        "<b>緯度：</b>" +
        r.lat +
        "°<br>" +


        "<b>経度：</b>" +
        r.lon +
        "°<br>" +


        "<b>高度：</b>" +
        r.alt_km +
        " km<br>" +


        "<hr>" +


        "🚀 <b>打上げ日：</b>" +

        formatLaunchDate(
            r.launch_date
        ) +

        "<br>" +


        "📍 <b>打上げ場所：</b>" +

        launchSiteName(
            r.launch_site
        ) +

        "<br>" +


        "🛰 <b>打上げから：</b>" +

        launchAgeOf(
            r.launch_date
        ) +

        "<br>" +


        "<hr>" +


        "<b>TLEエポック：</b>" +
        r.epoch_day +
        "<br>" +


        "<b>エポック日時：</b>" +
        r.epoch_utc +
        "<br>" +


        "<b>経過時間：</b>" +

        ageOf(
            r.epoch_iso
        ) +

        "<br>" +


        "<b>TLE鮮度：</b>" +


        "<span style='" +

        "font-weight:bold;" +

        "color:" +
        fresh.color +
        ";" +

        "'>" +

        fresh.icon +
        " " +
        fresh.text +

        "</span><br>" +


        "<hr>" +


        "<b>分類：</b>" +
        c[1] +
        "<br>" +


        "<b>任務メモ：</b>" +
        c[2]
    );
}



/* =========================================================
   マーカー
   ========================================================= */

const satelliteMarkers = [];


data.forEach(r => {

    const c =
        catOf(r);


    const marker =
        L.circleMarker(

            [
                parseFloat(
                    r.lat
                ),

                parseFloat(
                    r.lon
                )
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

        .bindPopup(
            popOf(r),
            {
                maxWidth: 420
            }
        );


    satelliteMarkers.push({

        data: r,

        marker: marker
    });
});



/* =========================================================
   検索文字列正規化

   ZHONGXING-19
   zhongxing19
   Zhongxing 19

   全部同じ扱い
   ========================================================= */

function normalizeSearch(value) {

    return String(
        value || ""
    )

    .toUpperCase()

    .replace(
        /[^A-Z0-9]/g,
        ""
    );
}



/* =========================================================
   衛星検索
   ========================================================= */

function searchSatellite() {

    const input =
        document.getElementById(
            "satSearch"
        );


    const result =
        document.getElementById(
            "searchResult"
        );


    const query =
        normalizeSearch(
            input.value.trim()
        );


    if (!query) {

        result.textContent =
            "衛星名かNORAD IDを入力してください";

        return;
    }



    /*
     * 完全一致
     */
    let found =
        satelliteMarkers.find(
            item => {

                const name =
                    normalizeSearch(
                        item.data.name
                    );


                const norad =
                    normalizeSearch(
                        item.data.norad
                    );


                return (
                    name === query ||
                    norad === query
                );
            }
        );



    /*
     * 部分一致
     */
    if (!found) {

        found =
            satelliteMarkers.find(
                item => {

                    const name =
                        normalizeSearch(
                            item.data.name
                        );


                    const norad =
                        normalizeSearch(
                            item.data.norad
                        );


                    return (
                        name.includes(
                            query
                        ) ||

                        norad.includes(
                            query
                        )
                    );
                }
            );
    }



    if (!found) {

        result.textContent =
            "❌ 該当する衛星がありません";

        return;
    }



    const r =
        found.data;


    const marker =
        found.marker;



    /* 衛星位置へ移動 */

    map.setView(

        [
            parseFloat(
                r.lat
            ),

            parseFloat(
                r.lon
            )
        ],

        5,

        {
            animate: true
        }
    );



    /* 詳細を開く */

    marker.openPopup();



    /* 一時的に強調 */

    marker.setRadius(
        14
    );


    setTimeout(

        function() {

            marker.setRadius(
                8
            );
        },

        2500
    );



    result.textContent =
        "✅ " +
        r.name +
        " / NORAD " +
        r.norad;
}



/* =========================================================
   検索ボタン
   ========================================================= */

document
    .getElementById(
        "searchButton"
    )
    .addEventListener(

        "click",

        searchSatellite
    );



/* =========================================================
   Enterでも検索
   ========================================================= */

document
    .getElementById(
        "satSearch"
    )
    .addEventListener(

        "keydown",

        function(event) {

            if (
                event.key ===
                "Enter"
            ) {

                event.preventDefault();

                searchSatellite();
            }
        }
    );



/* =========================================================
   衛星カテゴリ
   ========================================================= */

const legend =
    L.control({
        position:
            "bottomleft"
    });



legend.onAdd =
    function() {

        const div =
            L.DomUtil.create(
                "div",
                "info legend"
            );


        div.id =
            "satLegend";


        div.style.background =
            "white";

        div.style.padding =
            "10px";

        div.style.borderRadius =
            "8px";

        div.style.boxShadow =
            "0 1px 5px rgba(0,0,0,0.3)";

        div.style.fontSize =
            "13px";


        div.innerHTML =

            "<b>衛星カテゴリ</b><br>" +

            "<div>🔵 データ中継</div>" +

            "<div>🔴 通信</div>" +

            "<div>🟢 気象・観測</div>" +

            "<div>🟣 測位・航法</div>" +

            "<div>⚫ 未整理</div>" +

            "<div>🟠 移動中・傾斜大</div>";


        return div;
    };


legend.addTo(map);



/* =========================================================
   詳細表示中はカテゴリを消す
   ========================================================= */

map.on(
    "popupopen",

    function() {

        const legendBox =
            document.getElementById(
                "satLegend"
            );


        if (legendBox) {

            legendBox.style.display =
                "none";
        }
    }
);



/* =========================================================
   詳細を閉じたらカテゴリ復活
   ========================================================= */

map.on(
    "popupclose",

    function() {

        const legendBox =
            document.getElementById(
                "satLegend"
            );


        if (legendBox) {

            legendBox.style.display =
                "block";
        }
    }
);


</script>

</body>

</html>
'''


# =========================================================
# プレースホルダ置換
# =========================================================

html = (
    template
    .replace(
        "__COUNT__",
        str(
            len(
                satellite_data
            )
        )
    )
    .replace(
        "__MARKERS__",
        markers
    )
)


# =========================================================
# 保存
# =========================================================

with open(
    "china_map.html",
    "w",
    encoding="utf-8"
) as f:

    f.write(
        html
    )


print(
    "saved china_map.html"
)

print(
    "count:",
    len(
        satellite_data
    )
)