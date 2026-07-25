from pathlib import Path
from datetime import datetime, timedelta, timezone
import csv

tle_path = Path("geo.tle")
out_tle = Path("china_clean.tle")
out_csv = Path("china_geo.csv")

keywords = [
    "CHINASAT",
    "ZHONGXING",
    "ZX-",
    "TIANLIAN",
    "APSTAR",
    "FENGYUN",
    "FY-",
    "BEIDOU",
    "COMPASS",
]


def parse_tle_epoch(line1):
    # TLE 1行目 columns 19-32: YYDDD.DDDDDDDD
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


lines = tle_path.read_text(
    encoding="utf-8",
    errors="ignore"
).splitlines()

records = []
clean_lines = []

for i in range(0, len(lines) - 2, 3):

    name = lines[i].strip()
    l1 = lines[i + 1].strip()
    l2 = lines[i + 2].strip()

    if not (
        l1.startswith("1 ")
        and l2.startswith("2 ")
    ):
        continue

    upper = name.upper()

    if any(k in upper for k in keywords):

        norad = l1[2:7].strip()
        epoch = parse_tle_epoch(l1)

        clean_lines.extend([
            name,
            l1,
            l2
        ])

        records.append({
            "name": name,
            "norad": norad,
            "line1": l1,
            "line2": l2,

            "epoch_raw": epoch["epoch_raw"],
            "epoch_day": epoch["epoch_day"],
            "epoch_utc": epoch["epoch_utc"],
            "epoch_iso": epoch["epoch_iso"],
        })


out_tle.write_text(
    "\n".join(clean_lines) + "\n",
    encoding="utf-8"
)


with out_csv.open(
    "w",
    newline="",
    encoding="utf-8"
) as f:

    w = csv.DictWriter(
        f,
        fieldnames=[
            "name",
            "norad",
            "line1",
            "line2",
            "epoch_raw",
            "epoch_day",
            "epoch_utc",
            "epoch_iso",
        ]
    )

    w.writeheader()
    w.writerows(records)


print(f"saved {out_tle} and {out_csv}")
print(f"count: {len(records)}")

for r in records:
    print(
        r["name"],
        r["norad"],
        r["epoch_day"],
        r["epoch_utc"]
    )