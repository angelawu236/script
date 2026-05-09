# Extract all PT readings over time from raw data into a CSV.
# Format: TIME | PT0 | PT1 | PT2 | ... | PT17

import json
import csv
import plotly.graph_objects as go

# Which test: "test1" (IPA) or "test2" (LOX)
TEST = "test1"

# Flow type label (used for folder name)
FLOW_TYPE = "IPA" if TEST == "test1" else "LOX"

# Input and output file paths
INPUT_FILE = f"raw data (both tests)/{TEST}.txt"
OUTPUT_FILE = f"{TEST} ({FLOW_TYPE})/pt_timeseries_{TEST}.csv"
GRAPH_FILE = f"{TEST} ({FLOW_TYPE})/pt_timeseries_{TEST}.html"

# All PT codes (0–17)
PT_CODES = list(range(18))
VALVE_CODES = list(range(18))

# Valve name mapping
VALVE_NAMES = {
    0: "Pneumatic DLR",
    1: "Propellant DLR",
    2: "N2 Fill",
    3: "LOX ISO",
    4: "N2 Vent",
    5: "IPA Vent",
    6: "LOX Vent",
    7: "IPA Fill",
    8: "LOX Fill",
    9: "IPA Main (Engine)",
    10: "LOX Main (Engine)",
    11: "IPA Igniter",
    12: "LOX Igniter",
    13: "LOX Purge",
    14: "UNUSED (X)",
    15: "IPA Purge",
    16: "IPA ISO",
    17: "EMATCH",
}

# ================================================


def parse_raw_data(input_file):
    """Parse raw JSON-lines data and return rows with all PT readings and valve states per scan cycle."""
    rows = []
    current_pts = {pt: None for pt in PT_CODES}
    current_valves = {v: 0 for v in VALVE_CODES}
    current_ts = None

    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)

            # Update valve states
            if 'states' in record:
                for valve_id, state in record['states'].items():
                    vid = int(valve_id)
                    if vid in current_valves:
                        current_valves[vid] = 1 if state else 0
                continue

            if 'pt_code' not in record:
                continue

            pt_code = record['pt_code']
            if pt_code not in current_pts:
                continue

            # Detect new scan cycle when we see PT0 again
            if pt_code == 0 and current_ts is not None and all(v is not None for v in current_pts.values()):
                rows.append([current_ts] + [current_pts[pt] for pt in PT_CODES] + [current_valves[v] for v in VALVE_CODES])

            current_pts[pt_code] = record['value']
            current_ts = record['ts_s']

        # Append last cycle
        if current_ts is not None and all(v is not None for v in current_pts.values()):
            rows.append([current_ts] + [current_pts[pt] for pt in PT_CODES] + [current_valves[v] for v in VALVE_CODES])

    return rows


def parse_valve_events(input_file):
    """Find all valve open/close events and return list of (timestamp, valve_id, opened)."""
    events = []
    prev_states = {}

    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)

            if 'states' not in record:
                continue

            ts = record['ts_s']
            for valve_id, state in record['states'].items():
                prev = prev_states.get(valve_id)
                if prev is not None and state != prev:
                    events.append((ts, int(valve_id), state))
                prev_states[valve_id] = state

    return events


def write_csv(rows, output_file):
    """Write rows to CSV with header."""
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['TIME'] + [f'PT{pt}' for pt in PT_CODES] + [VALVE_NAMES.get(v, f'Valve{v}') for v in VALVE_CODES]
        writer.writerow(header)
        writer.writerows(rows)


if __name__ == '__main__':
    rows = parse_raw_data(INPUT_FILE)
    write_csv(rows, OUTPUT_FILE)
    print(f"Written {len(rows)} rows to {OUTPUT_FILE}")

    # Graph all PTs vs time
    times = [row[0] for row in rows]
    t0 = times[0]
    times_s = [t - t0 for t in times]

    fig = go.Figure()
    for i, pt in enumerate(PT_CODES):
        pt_values = [row[i + 1] for row in rows]
        fig.add_trace(go.Scatter(
            x=times_s, y=pt_values,
            mode='lines',
            name=f'PT{pt}',
            hovertemplate='Time: %{x:.3f} s<br>Pressure: %{y:.3f} psi<extra></extra>'
        ))

    # Add valve open/close events as vertical lines
    events = parse_valve_events(INPUT_FILE)
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'brown', 'pink', 'gray',
              'olive', 'cyan', 'magenta', 'teal', 'navy', 'maroon', 'lime', 'coral', 'indigo', 'gold']
    for ts, valve_id, opened in events:
        t_s = ts - t0
        action = "Open" if opened else "Close"
        name = VALVE_NAMES.get(valve_id, f"Valve {valve_id}")
        color = colors[valve_id % len(colors)]
        fig.add_vline(
            x=t_s, line_dash='dash' if opened else 'dot', line_color=color,
            annotation_text=f'{name} {action}',
            annotation_position='top left',
            annotation_font_size=9
        )

    fig.update_layout(
        title=f'PT Timeseries — {TEST} ({FLOW_TYPE})',
        xaxis_title='Time (s)',
        yaxis_title='PT Reading (psi)',
        hovermode='x unified'
    )

    fig.write_html(GRAPH_FILE)
    print(f"Interactive graph saved to {GRAPH_FILE}")
