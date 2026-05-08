# Use output of delay.py and plotly to graph out TIME (x) vs PT Reading (y), in MILLISECONDS.
# Add a vertical line from when the valve was opened (state = 1).
# TIME from delay.py output is in seconds — convert to ms and start from 0.
# Save interactive HTML graph to delay folder (viewable in any browser, no Python needed).

import csv
import plotly.graph_objects as go

# Which test: "test1" (IPA) or "test2" (LOX)
TEST = "test2"

# Which valve (9 = IPA_ENGINE, 10 = LOX_ENGINE)
VALVE_CODE = 9 if TEST == "test1" else 10

valve_dct = {9: "IPA Engine", 10: "LOX Engine"}

# Which PTs
PT_CODES = [17, 9]

FLOW_TYPE = "IPA" if TEST == "test1" else "LOX"

# Input file (single CSV output of delay.py)
INPUT_FILE = f"delay/{TEST}_{FLOW_TYPE}_delay.csv"

# Output interactive graph
OUTPUT_FILE = f"delay/{TEST}_{FLOW_TYPE}_delay.html"

# ================================================


def load_data(input_file):
    times = []
    valve_states = []
    pt1_readings = []
    pt2_readings = []

    with open(input_file, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            times.append(float(row[0]))
            valve_states.append(int(row[1]))
            pt1_readings.append(float(row[2]))
            pt2_readings.append(float(row[3]))

    return times, valve_states, pt1_readings, pt2_readings


if __name__ == '__main__':
    times, valve_states, pt1_readings, pt2_readings = load_data(INPUT_FILE)

    # Convert to ms starting from 0
    t0 = times[0]
    times_ms = [(t - t0) * 1000 for t in times]

    # Find when valve first opens (state = 1)
    valve_open_ms = None
    for i, state in enumerate(valve_states):
        if state == 1:
            valve_open_ms = times_ms[i]
            break

    fig = go.Figure()

    pt_label_1 = "IPA Orifice" if TEST == "test1" else "LOX Orifice"
    pt_label_2 = "IPA Tank" if TEST == "test1" else "LOX Tank"

    fig.add_trace(go.Scatter(
        x=times_ms, y=pt1_readings,
        mode='lines',
        name=f'PT {PT_CODES[0]} ({pt_label_1})',
        hovertemplate='Time: %{x:.2f} ms<br>Pressure: %{y:.3f} psi<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=times_ms, y=pt2_readings,
        mode='lines',
        name=f'PT {PT_CODES[1]} ({pt_label_2})',
        hovertemplate='Time: %{x:.2f} ms<br>Pressure: %{y:.3f} psi<extra></extra>'
    ))

    if valve_open_ms is not None:
        fig.add_vline(x=valve_open_ms, line_dash='dash', line_color='red',
                      annotation_text=f'Valve Opened ({valve_open_ms:.2f} ms)',
                      annotation_position='top right')

    title = "IPA" if TEST == "test1" else "LOX" 
    fig.update_layout(
        title=f'Delay — {title} (Valve {valve_dct[VALVE_CODE]})',
        xaxis_title='Time (ms)',
        yaxis_title='PT Reading (psi)',
        hovermode='x unified'
    )

    fig.write_html(OUTPUT_FILE)
    print(f"Interactive graph saved to {OUTPUT_FILE}")