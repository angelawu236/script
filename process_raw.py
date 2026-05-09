# process raw data (no calculations) into a CSV file with format, 
# and trim off all rows of CSV from the beginning when orifice flow rate reads 14.84, 
# and from the end when the orifice flow rate starts reading 14.84 again.

# Format: TIME | PT1 | PT2 | PT3 (tank) | PT4 (orifice) | Mass Flow (orifice). Output: 1_test{}_trimmed.csv


import json
import csv

# Which test: "test1" (IPA) or "test2" (LOX)
TEST = "test1"

# Whether to include the given orifice mass flow from the raw data in the output.
# When False, the orifice flow is still used internally for trimming but not output.
USE_GIVEN_ORIFICE = False

PT1_CODE = 7
PT2_CODE = 8
PT3_CODE = 9
PT4_CODE = 17

# Flow type for the orifice mass flow reading
ORIFICE_FLOW_TYPE = "IPA Orifice" if TEST == "test1" else "LOX Orifice"

# Orifice baseline value (readings at this value = no flow)
ORIFICE_BASELINE = 14.848

# Input and output file paths
INPUT_FILE = f"raw data (both tests)/{TEST}.txt"
OUTPUT_FILE = f"{TEST} ({'IPA' if 'IPA' in ORIFICE_FLOW_TYPE else 'LOX'})/1_{TEST}_trimmed.csv"

# ================================================


def parse_raw_data(input_file):
    """Parse raw JSON-lines data and return rows of [time, pt1, pt2, pt3, pt4, orifice_flow]."""
    rows = []
    current_pt1 = None
    current_pt2 = None
    current_pt3 = None
    current_pt4 = None

    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)

            # Update PT values when we see them
            if 'pt_code' in record:
                if record['pt_code'] == PT1_CODE:
                    current_pt1 = record['value']
                elif record['pt_code'] == PT2_CODE:
                    current_pt2 = record['value']
                elif record['pt_code'] == PT3_CODE:
                    current_pt3 = record['value']
                elif record['pt_code'] == PT4_CODE:
                    current_pt4 = record['value']

            # When we see the orifice flow reading, record a row
            elif 'flow_type' in record and record['flow_type'] == ORIFICE_FLOW_TYPE:
                if all(v is not None for v in [current_pt1, current_pt2, current_pt3, current_pt4]):
                    rows.append([
                        record['ts_s'],
                        current_pt1,
                        current_pt2,
                        current_pt3,
                        current_pt4,
                        record['value']
                    ])

    return rows


def trim_data(rows):
    """Trim rows from the beginning/end where orifice flow is at baseline (14.848)."""
    # Find first index where orifice flow departs from baseline
    start = 0
    for i, row in enumerate(rows):
        if row[5] != ORIFICE_BASELINE:
            start = i
            break

    # Find last index where orifice flow departs from baseline
    end = len(rows) - 1
    for i in range(len(rows) - 1, -1, -1):
        if rows[i][5] != ORIFICE_BASELINE:
            end = i
            break

    return rows[start:end + 1]


def write_csv(rows, output_file):
    """Write rows to CSV with header."""
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        if USE_GIVEN_ORIFICE:
            writer.writerow(['TIME', 'PT1', 'PT2', 'PT3', 'PT4', 'Mass Flow (orifice)'])
            writer.writerows(rows)
        else:
            writer.writerow(['TIME', 'PT1', 'PT2', 'PT3', 'PT4'])
            for row in rows:
                writer.writerow(row[:5])  # exclude orifice column


if __name__ == '__main__':
    rows = parse_raw_data(INPUT_FILE)

    trimmed = trim_data(rows)

    write_csv(trimmed, OUTPUT_FILE)
    print(f"  Output written to {OUTPUT_FILE}")

