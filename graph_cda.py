# Take output of cda_calculations.py, and graph CdA (y) vs mass flow(x) for both venturi and orifice. 

#refer to cda_calculations.py for which variables to be configurable at the top of script.

import csv
import matplotlib.pyplot as plt

# Which test: "test1" (IPA) or "test2" (LOX)
TEST = "test2"

# Flow type label (used for folder name)
FLOW_TYPE = "IPA" if TEST == "test1" else "LOX"

# Input file (output of cda_calculations.py)
INPUT_FILE = f"{TEST} ({FLOW_TYPE})/3_{TEST}_with_cda.csv"

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

    fig, ax = plt.subplots()

    ax.scatter(mf_orifice, cda_orifice, s=5, alpha=0.5, label='Orifice')
    ax.scatter(mf_venturi, cda_venturi, s=5, alpha=0.5, label='Venturi')

    ax.set_xlabel('Mass Flow (kg/s)')
    ax.set_ylabel('CdA (m²)')
    ax.set_title(f'CdA vs Mass Flow — {TEST} ({FLOW_TYPE})')
    ax.legend()

    # Tight margins around data so details are visible
    all_x = mf_orifice + mf_venturi
    all_y = cda_orifice + cda_venturi
    x_margin = (max(all_x) - min(all_x)) * 0.05
    y_margin = (max(all_y) - min(all_y)) * 0.05
    ax.set_xlim(min(all_x) - x_margin, max(all_x) + x_margin)
    ax.set_ylim(min(all_y) - y_margin, max(all_y) + y_margin)

    ax.grid(True, alpha=0.3)

    fig.savefig(f"{TEST} ({FLOW_TYPE})/graph_cda_{TEST}.png", dpi=150, bbox_inches='tight')
    print(f"  Graph saved to {TEST} ({FLOW_TYPE})/graph_cda_{TEST}.png")
    plt.show()