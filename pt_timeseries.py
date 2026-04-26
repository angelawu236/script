"""
Reads a mosquitto_sub log and writes a CSV with one row per PT reading.
Every PT column is filled using the last known value for that PT.

Edit CONFIG below, then run: python3 pt_timeseries.py
"""

import csv
import json

# ── CONFIGURATION ─────────────────────────────────────────────────────────────

INPUT_FILE = "out.txt"
OUTPUT_CSV = "pt_timeseries.csv"

PT_NAMES = {
    0:  "NITROGEN_TANK_PT",
    1:  "IPA_TANK_PT",
    2:  "LOX_TANK_PT",
    3:  "LOX_LINE_PT",
    4:  "IPA_LINE_PT",
    5:  "LOX_VENTURI_1_PT",
    6:  "LOX_VENTURI_2_PT",
    7:  "IPA_VENTURI_1_PT",
    8:  "IPA_VENTURI_2_PT",
    9:  "CHAMBER_PT",
    10: "IGNITER_PT",
    11: "PFM_PT",
    12: "POM_PT",
}

# PT codes to include in the output (must be keys in PT_NAMES above).
INCLUDE_PT_CODES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

# ── END CONFIGURATION ─────────────────────────────────────────────────────────


def main():
    pt_codes = sorted(INCLUDE_PT_CODES)
    last_known = {}   # pt_code -> most recent value

    with open(INPUT_FILE) as f_in, open(OUTPUT_CSV, "w", newline="") as f_out:
        header = ["time_s"] + [PT_NAMES[c] for c in pt_codes]
        w = csv.writer(f_out)
        w.writerow(header)
        rows = 0

        for line in f_in:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "pt_code" not in msg:
                continue
            ts   = msg["ts_s"]
            code = int(msg["pt_code"])
            val  = float(msg["value"])
            if code not in PT_NAMES:
                continue
            last_known[code] = val
            row = [f"{ts:.6f}"] + [last_known.get(c, "") for c in pt_codes]
            w.writerow(row)
            rows += 1

    print(f"Written {rows} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
