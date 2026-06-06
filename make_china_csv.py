from pathlib import Path
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

lines = tle_path.read_text(errors="ignore").splitlines()

records = []
clean_lines = []

for i in range(0, len(lines) - 2, 3):
    name = lines[i].strip()
    l1 = lines[i + 1].strip()
    l2 = lines[i + 2].strip()

    upper = name.upper()

    if any(k in upper for k in keywords):
        norad = l1[2:7].strip()
        clean_lines.extend([name, l1, l2])
        records.append({
            "name": name,
            "norad": norad,
            "line1": l1,
            "line2": l2,
        })

out_tle.write_text("\n".join(clean_lines) + "\n", encoding="utf-8")

with out_csv.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["name", "norad", "line1", "line2"])
    w.writeheader()
    w.writerows(records)

print(f"saved {out_tle} and {out_csv}")
print(f"count: {len(records)}")
