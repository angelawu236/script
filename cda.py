"""
Reads cda.csv and plots CdA (y-axis) vs mass flow rate m (x-axis).

Two CdA formulas per fluid:
  Orifice:  CdA = m / sqrt(2 * rho * dP)
  Venturi:  CdA = m * sqrt(1 - beta^4) / sqrt(2 * rho * dP)

Click any point to see its values. Install mplcursors for richer tooltips:
    pip install mplcursors
"""

import csv
import math
import matplotlib.pyplot as plt

try:
    import mplcursors
    HAS_MPLCURSORS = True
except ImportError:
    HAS_MPLCURSORS = False

# ── CONFIGURATION ─────────────────────────────────────────────────────────────

INPUT_CSV = "cda.csv"

# Each entry: (label, mfr_col, p1_col, p2_col, rho_kg_m3, D_in, d_in)
VENTURIS = [
    ("LOX", "lox_mass_flow_rate_kg_s", "LOX_VENTURI_1_PT", "LOX_VENTURI_2_PT", 1147.0, 0.61, 0.2493),
    ("IPA", "ipa_mass_flow_rate_kg_s", "IPA_VENTURI_1_PT", "IPA_VENTURI_2_PT",  786.0, 0.61, 0.19),
]

# ── END CONFIGURATION ─────────────────────────────────────────────────────────

PSI_TO_PA = 6894.76
IN_TO_M   = 0.0254


def load_series(path, mfr_col, p1_col, p2_col, rho, D_in, d_in):
    beta = d_in / D_in
    d_m  = d_in * IN_TO_M

    m_vals, cda_orifice, cda_venturi, times = [], [], [], []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            mfr = row.get(mfr_col, "").strip()
            p1  = row.get(p1_col,  "").strip()
            p2  = row.get(p2_col,  "").strip()
            ts  = row.get("time_s", "").strip()
            if not mfr or not p1 or not p2:
                continue
            dp_pa = (float(p2) - float(p1)) * PSI_TO_PA
            if dp_pa <= 0:
                continue
            m     = float(mfr)
            denom = math.sqrt(2 * rho * dp_pa)
            m_vals.append(m)
            cda_orifice.append(m / denom)
            cda_venturi.append(m * math.sqrt(1 - beta**4) / denom)
            times.append(float(ts))

    return m_vals, cda_orifice, cda_venturi, times


def add_tooltip(scatter, m_vals, cda_vals, times, label):
    if HAS_MPLCURSORS:
        cursor = mplcursors.cursor(scatter, hover=False)
        @cursor.connect("add")
        def on_add(sel):
            i = sel.index
            sel.annotation.set_text(
                f"{label}\nm = {m_vals[i]:.4f} kg/s\nCdA = {cda_vals[i]:.6f} m²\nt = {times[i]:.2f} s"
            )
    else:
        # Fallback: show annotation on click via pick event
        annot = scatter.axes.annotate(
            "", xy=(0, 0), xytext=(12, 12), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", alpha=0.9),
            arrowprops=dict(arrowstyle="->"),
        )
        annot.set_visible(False)

        def on_pick(event):
            if event.artist is not scatter:
                return
            i = event.ind[0]
            x, y = m_vals[i], cda_vals[i]
            annot.xy = (x, y)
            annot.set_text(f"{label}\nm={x:.4f} kg/s\nCdA={y:.6f} m²\nt={times[i]:.2f} s")
            annot.set_visible(True)
            scatter.figure.canvas.draw_idle()

        scatter.set_picker(8)
        scatter.figure.canvas.mpl_connect("pick_event", on_pick)


def main():
    fig, ax = plt.subplots(figsize=(11, 6))
    colors = {"LOX": "#1f77b4", "IPA": "#ff7f0e"}

    for label, mfr_col, p1_col, p2_col, rho, D_in, d_in in VENTURIS:
        m_vals, cda_ori, cda_ven, times = load_series(
            INPUT_CSV, mfr_col, p1_col, p2_col, rho, D_in, d_in
        )
        if not m_vals:
            print(f"{label}: no valid rows — check column names match cda.csv headers")
            continue

        c = colors[label]

        # Faint connecting lines
        ax.plot(m_vals, cda_ori, color=c, alpha=0.25, linewidth=1)
        ax.plot(m_vals, cda_ven, color=c, alpha=0.25, linewidth=1, linestyle="--")

        # Scatter points (clickable)
        sc_ori = ax.scatter(m_vals, cda_ori, color=c, s=25, label=f"{label} orifice", zorder=3)
        sc_ven = ax.scatter(m_vals, cda_ven, color=c, s=25, marker="^", label=f"{label} venturi",
                            zorder=3, alpha=0.7)

        add_tooltip(sc_ori, m_vals, cda_ori, times, f"{label} orifice")
        add_tooltip(sc_ven, m_vals, cda_ven, times, f"{label} venturi")

        print(f"{label}: {len(m_vals)} points")

    ax.set_xlabel("Mass flow rate  m  [kg/s]")
    ax.set_ylabel("CdA  [m²]")
    ax.set_title("CdA vs mass flow rate\n"
                 "Orifice: CdA = m/√(2ρΔP)    Venturi: CdA = m·√(1−β⁴)/√(2ρΔP)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("cda_plot.png", dpi=150)
    print("Saved cda_plot.png")
    plt.show()


if __name__ == "__main__":
    main()
