"""
Reads pt_timeseries.csv and calculates venturi mass flow rate for each row.
Outputs a new CSV with timestamp and mass flow rate column(s).

q_m = C / sqrt(1 - beta^4) * epsilon * (pi/4) * d^2 * sqrt(2 * (P2 - P1) * rho)
C = epsilon = 1

Edit CONFIG below, then run: python3 mass_flow_rate.py
"""

import csv
import math
import matplotlib.pyplot as plt

# ── CONFIGURATION ─────────────────────────────────────────────────────────────

INPUT_CSV  = "pt_timeseries.csv"
OUTPUT_CSV = "mass_flow_rate.csv"

# Each entry defines one venturi calculation:
#   (label, p1_col, p2_col, rho_kg_m3, D_in, d_in)
#   p1_col / p2_col : column names in the input CSV (upstream / downstream)
#   rho             : fluid density kg/m³
#   D_in            : pipe diameter, inches
#   d_in            : throat diameter, inches
VENTURIS = [
    ("lox_mass_flow_rate_kg_s", "LOX_VENTURI_1_PT", "LOX_VENTURI_2_PT", 1147.0, 0.61, 0.2493),
    ("ipa_mass_flow_rate_kg_s", "IPA_VENTURI_1_PT", "IPA_VENTURI_2_PT",  786.0, 0.61, 0.19),
]

# ── END CONFIGURATION ─────────────────────────────────────────────────────────

PSI_TO_PA = 6894.76
IN_TO_M   = 0.0254


def venturi_mfr(p1_psi, p2_psi, rho, D_in, d_in):
    dp_pa = (p2_psi - p1_psi) * PSI_TO_PA   # P2 - P1
    if dp_pa <= 0:
        return ""
    beta = d_in / D_in
    d_m  = d_in * IN_TO_M
    A    = math.pi / 4 * d_m ** 2
    q_m  = (A / math.sqrt(1 - beta ** 4)) * math.sqrt(2 * dp_pa * rho)
    return f"{q_m:.6f}"


def main():
    mfr_cols = [label for label, *_ in VENTURIS]

    with open(INPUT_CSV, newline="") as f_in, open(OUTPUT_CSV, "w", newline="") as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.writer(f_out)
        writer.writerow(["time_s"] + mfr_cols)

        rows = 0
        plot_data = {label: ([], []) for label, *_ in VENTURIS}
        for row in reader:
            ts = row.get("time_s", "").strip()
            if not ts:
                continue
            out_row = [ts]
            for label, p1_col, p2_col, rho, D_in, d_in in VENTURIS:
                p1 = row.get(p1_col, "").strip()
                p2 = row.get(p2_col, "").strip()
                val = venturi_mfr(float(p1), float(p2), rho, D_in, d_in) if p1 and p2 else ""
                out_row.append(val)
                if val:
                    plot_data[label][0].append(float(ts))
                    plot_data[label][1].append(float(val))
            writer.writerow(out_row)
            rows += 1
        plot_data = [(label, t, m) for label, (t, m) in plot_data.items()]

    print(f"Written {rows} rows to {OUTPUT_CSV}")

    # ── Plot ──────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(11, 5))
    for label, times, m_vals in plot_data:
        t0 = times[0] if times else 0
        ax.plot([t - t0 for t in times], m_vals, marker="o", markersize=3, linewidth=1.2, label=label)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Mass flow rate (kg/s)")
    ax.set_title("Venturi mass flow rate vs time")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("mass_flow_rate_plot.png", dpi=150)
    print("Saved mass_flow_rate_plot.png")
    plt.show()


if __name__ == "__main__":
    main()
