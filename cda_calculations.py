# Use outputs of venturi_mass_flow.py (2_test2_with_venturi.csv in test1 (IPA) and in test2 (LOX)). 
# and create a new CSV file with the same columns as the output of venturi_mass_flow.py but with
# an additional 2 columns: 1 for CdA (venturi) and CdA (orifice)
# 
# Format: 1. TIME | PT1 | PT2 | Mass Flow (venturi) | Mass Flow (orifice) | CdA (orifice) | CdA (venturi)

# CdA equation for orifice: CdA = mass flow (orifice) /sqrt(2*999.1*(PT2-0)*6894.8)
# CdA equation for venturi: CdA = mass flow (venturi) /sqrt(2*999.1*(PT2-PT1)*6894.8)

import csv
import math

# Which test: "test1" (IPA) or "test2" (LOX)
TEST = "test2"

# Flow type label (used for folder name)
FLOW_TYPE = "IPA" if TEST == "test1" else "LOX"

# Input file (output of venturi_mass_flow.py)
INPUT_FILE = f"{TEST} ({FLOW_TYPE})/2_{TEST}_with_venturi.csv"

# Output file
OUTPUT_FILE = f"{TEST} ({FLOW_TYPE})/3_{TEST}_with_cda.csv"

# ================================================


def calc_cda_orifice(mass_flow_orifice, pt2):
    """CdA (orifice) = mass_flow_orifice / sqrt(2 * 999.1 * (PT2 - 0) * 6894.8)"""
    if pt2 <= 0:
        return 0.0
    return mass_flow_orifice / math.sqrt(2 * 999.1 * pt2 * 6894.8)


def calc_cda_venturi(mass_flow_venturi, pt1, pt2):
    """CdA (venturi) = mass_flow_venturi / sqrt(2 * 999.1 * (PT2 - PT1) * 6894.8)"""
    delta_p = pt2 - pt1
    if delta_p <= 0:
        return 0.0
    return mass_flow_venturi / math.sqrt(2 * 999.1 * delta_p * 6894.8)


def process(input_file, output_file):
    with open(input_file, 'r') as fin, open(output_file, 'w', newline='') as fout:
        reader = csv.reader(fin)
        writer = csv.writer(fout)

        next(reader)  # skip old header
        writer.writerow(['TIME', 'PT1', 'PT2', 'Mass Flow (venturi)', 'Mass Flow (orifice)', 'CdA (orifice)', 'CdA (venturi)'])

        for row in reader:
            time = row[0]
            pt1 = float(row[1])
            pt2 = float(row[2])
            mass_flow_orifice = float(row[3])
            mass_flow_venturi = float(row[4])

            cda_orifice = calc_cda_orifice(mass_flow_orifice, pt2)
            cda_venturi = calc_cda_venturi(mass_flow_venturi, pt1, pt2)

            writer.writerow([time, pt1, pt2, mass_flow_venturi, mass_flow_orifice, cda_orifice, cda_venturi])


if __name__ == '__main__':
    process(INPUT_FILE, OUTPUT_FILE)
    print(f"  Output written to {OUTPUT_FILE}")