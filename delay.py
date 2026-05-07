# From raw data (both tests) / test1.txt and test2.txt, output a CSV file with this format:
# TIME | VALVE{} STATE | PT READING
#
# VALVE: {IPA_ENGINE = 9, LOX_ENGINE = 10}, PT: {17 = Orifice (ipa if test1, lox if test2)}

import json
import csv

# Which test: "test1" (IPA) or "test2" (LOX)
TEST = "test2"

# Which valve to track (9 = IPA_ENGINE, 10 = LOX_ENGINE)
VALVE_CODE = 9 if TEST == "test1" else 10

# Which PT to track (17 = Orifice)
PT_CODE = 17

# Flow type label (used for folder name)
FLOW_TYPE = "IPA" if TEST == "test1" else "LOX"

# Input and output file paths
INPUT_FILE = f"raw data (both tests)/{TEST}.txt"
OUTPUT_FILE = f"delay/{TEST}_valve{VALVE_CODE}_pt{PT_CODE}.csv"

# ================================================


def parse_raw_data(input_file):
    """Parse raw JSON-lines data and return rows of [time, valve_state, pt_reading]."""
    rows = []
    current_valve_state = None
    current_pt = None

    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)

            # Update valve state when we see a states record
            if 'states' in record:
                valve_key = str(VALVE_CODE)
                if valve_key in record['states']:
                    current_valve_state = record['states'][valve_key]

            # Update PT value when we see the matching pt_code
            elif 'pt_code' in record:
                if record['pt_code'] == PT_CODE:
                    current_pt = record['value']
                    # Record a row each time the target PT is updated
                    if current_valve_state is not None:
                        rows.append([
                            record['ts_s'],
                            1 if current_valve_state else 0,
                            current_pt
                        ])

    return rows


def write_csv(rows, output_file):
    """Write rows to CSV with header."""
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['TIME', f'VALVE{VALVE_CODE} STATE', 'PT READING'])
        writer.writerows(rows)


def trim_before_valve_open(rows, seconds_before=3):
    """Trim data to start `seconds_before` seconds before the valve first opens."""
    # Find when valve first opens
    valve_open_time = None
    for row in rows:
        if row[1] == 1:
            valve_open_time = row[0]
            break

    if valve_open_time is None:
        return rows

    start_time = valve_open_time - seconds_before
    return [row for row in rows if row[0] >= start_time]


if __name__ == '__main__':
    rows = parse_raw_data(INPUT_FILE)
    rows = trim_before_valve_open(rows, seconds_before=3)
    write_csv(rows, OUTPUT_FILE)
    print(f"Written {len(rows)} rows to {OUTPUT_FILE}")

