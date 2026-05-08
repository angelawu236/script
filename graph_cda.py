# Take output of cda_calculations.py, and graph CdA (y) vs mass flow(x) for both venturi and orifice. 

#refer to cda_calculations.py for which variables to be configurable at the top of script.

import csv
import plotly.graph_objects as go

# Which test: "test1" (IPA) or "test2" (LOX)
TEST = "test2"

# Flow type label (used for folder name)
FLOW_TYPE = "IPA" if TEST == "test1" else "LOX"

# Input file (output of cda_calculations.py)
INPUT_FILE = f"{TEST} ({FLOW_TYPE})/3_{TEST}_with_cda.csv"

# Output interactive graph
OUTPUT_FILE = f"{TEST} ({FLOW_TYPE})/graph_cda_{TEST}.html"

# ================================================


def load_data(input_file):
    mass_flow_venturi = []
    mass_flow_orifice = []
    cda_orifice = []
    cda_venturi = []

    with open(input_file, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            mf_venturi = float(row[3])
            mf_orifice = float(row[4])
            cda_o = float(row[5])
            cda_v = float(row[6])

            mass_flow_venturi.append(mf_venturi)
            mass_flow_orifice.append(mf_orifice)
            cda_orifice.append(cda_o)
            cda_venturi.append(cda_v)

    return mass_flow_venturi, mass_flow_orifice, cda_orifice, cda_venturi


if __name__ == '__main__':
    mf_venturi, mf_orifice, cda_orifice, cda_venturi = load_data(INPUT_FILE)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=mf_orifice, y=cda_orifice,
        mode='markers',
        marker=dict(size=4, opacity=0.5),
        name='Orifice',
        hovertemplate='Mass Flow: %{x:.4f} kg/s<br>CdA: %{y:.6f} m²<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=mf_venturi, y=cda_venturi,
        mode='markers',
        marker=dict(size=4, opacity=0.5),
        name='Venturi',
        hovertemplate='Mass Flow: %{x:.4f} kg/s<br>CdA: %{y:.6f} m²<extra></extra>'
    ))

    fig.update_layout(
        title=f'CdA vs Mass Flow — {TEST} ({FLOW_TYPE})',
        xaxis_title='Mass Flow (kg/s)',
        yaxis_title='CdA (m²)',
        hovermode='closest'
    )

    fig.write_html(OUTPUT_FILE)
    print(f"Interactive graph saved to {OUTPUT_FILE}")