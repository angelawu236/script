# Use outputs of process_raw.py (2 csv files, one in test1 (IPA) and other in test2 (LOX)) to calculate mass flow rate for venturi
# and create a new CSV file with the same columns as the output of process_raw.py but with
# an additional column of venturi mass flow. 

# Format: TIME | PT1 | PT2 | PT3 | PT4 | Mass Flow (orifice) | Mass Flow (venturi) 

# Venturi Mass Flow (IPA venturi) = 1.76310132e-5 * sqrt(2 * (PT2 - PT1) * 6894.8 * 999.1)
# Venturi Mass Flow (LOX venturi) = 2.31233144e-5* sqrt(2 * (PT2 - PT1) * 6894.8 * 999.1)

# IPA Orifice Mass Flow (Orifice, PT 4) = 0.62 * 2.129e-5 * sqrt(2*PT4*6894.8*999.1)
# LOX Orifice Mass Flow (Orifice, PT 4) = 0.62 * 2.425e-5 * sqrt(2*PT4*6894.8*999.1)

import csv
import math
import os

# Which test: "test1" (IPA) or "test2" (LOX)
TEST = os.environ.get("TEST", "test1")

# Whether to use the given orifice mass flow from process_raw.py output,
# or calculate it from PT4. Must match the setting in process_raw.py.
USE_GIVEN_ORIFICE = False

# Flow type label (used for folder name)
FLOW_TYPE = "IPA" if TEST == "test1" else "LOX"

# Input file (output of process_raw.py)
INPUT_FILE = f"{TEST} ({FLOW_TYPE})/1_{TEST}_trimmed.csv"

# Output file
OUTPUT_FILE = f"{TEST} ({FLOW_TYPE})/2_{TEST}_with_venturi.csv"

# ================================================


def calc_venturi_mass_flow(pt1, pt2):
    """Calculate venturi mass flow rate from pressure transducer readings."""
    delta_p = pt2 - pt1
    if delta_p <= 0:
        return 0.0
    if FLOW_TYPE == "LOX":
        return 2.31233144e-5 * math.sqrt(2 * delta_p * 6894.8 * 999.1)
    else:
        return 1.76310132e-5 * math.sqrt(2 * delta_p * 6894.8 * 999.1)


def calc_orifice_mass_flow(pt4):
    """Calculate orifice mass flow rate from PT4 reading."""
    if pt4 <= 0:
        return 0.0
    if FLOW_TYPE == "LOX":
        return 0.62 * 2.425e-5 * math.sqrt(2 * pt4 * 6894.8 * 999.1)
    else:
        return 0.62 * 2.129e-5 * math.sqrt(2 * pt4 * 6894.8 * 999.1)


def process(input_file, output_file):
    with open(input_file, 'r') as fin, open(output_file, 'w', newline='') as fout:
        reader = csv.reader(fin)
        writer = csv.writer(fout)

        next(reader)  # skip header
        writer.writerow(['TIME', 'PT1', 'PT2', 'PT3', 'PT4', 'Mass Flow (orifice)', 'Mass Flow (venturi)'])

        for row in reader:
            time = row[0]
            pt1 = float(row[1])
            pt2 = float(row[2])
            pt3 = row[3]
            pt4 = float(row[4])

            if USE_GIVEN_ORIFICE:
                orifice_flow = float(row[5])
            else:
                orifice_flow = calc_orifice_mass_flow(pt4)

            venturi_flow = calc_venturi_mass_flow(pt1, pt2)
            writer.writerow([time, pt1, pt2, pt3, pt4, orifice_flow, venturi_flow])


if __name__ == '__main__':
    process(INPUT_FILE, OUTPUT_FILE)
    print(f"  Output written to {OUTPUT_FILE}")