"""
Live PT logger + mass flow calculator.

Reads out.txt while mosquitto_sub is appending to it.
Writes PT values + mass flow rates to mass_flow_rate_live.csv in real time.

Run:
python3 live_mass_flow.py
"""

import csv
import json
import math
import os
import time

INPUT_FILE = "out.txt"
OUTPUT_CSV = "mass_flow_rate_live.csv"

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

PT_CODES_TO_OUTPUT = [5, 6, 7, 8]

VENTURIS = [
    ("lox_mass_flow_rate_kg_s", "LOX_VENTURI_1_PT", "LOX_VENTURI_2_PT", 1147.0, 0.61, 0.2493),
    ("ipa_mass_flow_rate_kg_s", "IPA_VENTURI_1_PT", "IPA_VENTURI_2_PT",  786.0, 0.61, 0.19),
]
# tuple order: (label, p1_col, p2_col, rho, D_in, d_in)

PSI_TO_PA = 6894.76
IN_TO_M = 0.0254


def venturi_mfr(p1_psi, p2_psi, rho, D_in, d_in):
    """
    Follows the spec sheet formula exactly:
      q = C / sqrt(1 - beta^4) * eps * (pi/4) * d^2 * sqrt(2*(P2-P1)*rho)
    where C=1, eps=1, P2 is downstream (p2), P1 is upstream (p1)
    """
    # P2 - P1: downstream minus upstream (per your equation)
    dp_pa = (p2_psi - p1_psi) * PSI_TO_PA
    if dp_pa <= 0:
        return ""
    
    beta = d_in / D_in
    d_m = d_in * IN_TO_M
    
    q_m = (1 / math.sqrt(1 - beta**4)) * (math.pi / 4) * d_m**2 * math.sqrt(2 * dp_pa * rho)
    return f"{q_m:.6f}"


def follow_file(filename):
    while not os.path.exists(filename):
        print(f"Waiting for {filename}...")
        time.sleep(0.5)

    with open(filename, "r") as f:
        f.seek(0, os.SEEK_END)

        while True:
            line = f.readline()

            if not line:
                time.sleep(0.05)
                continue

            yield line


def main():
    last_known = {}

    pt_columns = [PT_NAMES[c] for c in PT_CODES_TO_OUTPUT]
    mfr_columns = [label for label, *_ in VENTURIS]

    output_exists = os.path.exists(OUTPUT_CSV)

    with open(OUTPUT_CSV, "a", newline="") as f_out:
        writer = csv.writer(f_out)

        if not output_exists or os.path.getsize(OUTPUT_CSV) == 0:
            writer.writerow(["time_s"] + pt_columns + mfr_columns)
            f_out.flush()

        print(f"Reading live from {INPUT_FILE}")
        print(f"Writing live output to {OUTPUT_CSV}")

        for line in follow_file(INPUT_FILE):
            line = line.strip()

            if not line:
                continue

            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            if "pt_code" not in msg:
                continue

            try:
                ts = float(msg["ts_s"])
                code = int(msg["pt_code"])
                val = float(msg["value"])
            except (KeyError, ValueError, TypeError):
                continue

            if code not in PT_NAMES:
                continue

            pt_name = PT_NAMES[code]
            last_known[pt_name] = val

            out_row = [f"{ts:.6f}"]

            # PT values
            for pt_code in PT_CODES_TO_OUTPUT:
                name = PT_NAMES[pt_code]
                out_row.append(last_known.get(name, ""))

            # Mass flow rates
            for label, p1_col, p2_col, rho, D_in, d_in in VENTURIS:
                if p1_col in last_known and p2_col in last_known:
                    mfr = venturi_mfr(
                        last_known[p1_col],
                        last_known[p2_col],
                        rho,
                        D_in,
                        d_in,
                    )
                else:
                    mfr = ""
                out_row.append(mfr)

            writer.writerow(out_row)
            f_out.flush()

            print(out_row)


if __name__ == "__main__":
    main()