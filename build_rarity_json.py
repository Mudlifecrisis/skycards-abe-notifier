# build_rarity_json.py
import csv, json, sys

# Adjust these to match your CSV column headers:
COL_ICAO = "ICAO Code"   # e.g., B738
COL_IATA = None          # Not present in this CSV
COL_RARITY = "Rarity"    # numeric rarity, if present
COL_FTEA = "Observed Aircraft"  # Using observed aircraft count as FTEA

in_csv = sys.argv[1] if len(sys.argv) > 1 else "aircraft_list.csv"
by_rarity, by_ftea = {}, {}

with open(in_csv, newline='', encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        icao = (row.get(COL_ICAO) or "").strip().upper()
        iata = (row.get(COL_IATA) or "").strip().upper() if COL_IATA else ""
        def put(dct, k, v):
            if k: dct[k] = v
            elif iata: dct[iata] = v

        if row.get(COL_RARITY):
            try:
                put(by_rarity, icao, float(row[COL_RARITY]))
            except: pass

        if row.get(COL_FTEA):
            try:
                put(by_ftea, icao, float(row[COL_FTEA]))
            except: pass

with open("rarity.json", "w", encoding="utf-8") as f:
    json.dump(by_rarity, f, indent=2)
with open("ftea.json", "w", encoding="utf-8") as f:
    json.dump(by_ftea, f, indent=2)
print(f"wrote rarity.json ({len(by_rarity)} types) and ftea.json ({len(by_ftea)} types)")