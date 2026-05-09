# Use outputs of process_raw.py (2 csv files, one in test1 (IPA) and other in test2 (LOX)) to calculate mass flow rate for venturi
# and create a new CSV file with the same columns as the output of process_raw.py but with
# an additional column of venturi mass flow. 

# Format: TIME | PT1 | PT2 | PT3 | PT4 | Mass Flow (orifice) | Mass Flow (venturi) 

# Mass Flow (IPA venturi) = 1.76310132e-5 * sqrt(2 * (PT2 - PT1) * 6894.8 * 999.1)
# Mass Flow (LOX venturi) = 2.34674906e-5* sqrt(2 * (PT2 - PT1) * 6894.8 * 999.1)

import csv
import math

# Which test: "test1" (IPA) or "test2" (LOX)
TEST = "test2"

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


def process(input_file, output_file):
    with open(input_file, 'r') as fin, open(output_file, 'w', newline='') as fout:
        reader = csv.reader(fin)
        writer = csv.writer(fout)

        header = next(reader)
        writer.writerow(header + ['Mass Flow (venturi)'])

        for row in reader:
            time, pt1, pt2, pt3, pt4, orifice_flow = row[0], float(row[1]), float(row[2]), row[3], row[4], row[5]
            venturi_flow = calc_venturi_mass_flow(pt1, pt2)
            writer.writerow([time, pt1, pt2, pt3, pt4, orifice_flow, venturi_flow])


if __name__ == '__main__':
    process(INPUT_FILE, OUTPUT_FILE)
    print(f"  Output written to {OUTPUT_FILE}")