"""
Reads out.txt in real-time (tail -f style), calculates CdA, appends to a CSV,
and updates the live plot as new data arrives.

Two CdA formulas per fluid:
  Orifice:  CdA = m / sqrt(2 * rho * dP)
  Venturi:  CdA = m * sqrt(1 - beta^4) / sqrt(2 * rho * dP)

Click any point to see its values (pip install mplcursors for rich tooltips).
Edit CONFIG below, then run: python3 cda.py
"""

import csv
import json
import math
import os
import threading
import time

import matplotlib.pyplot as plt
import matplotlib.animation as animation

try:
    import mplcursors
    HAS_MPLCURSORS = True
except ImportError:
    HAS_MPLCURSORS = False

# ── CONFIGURATION ─────────────────────────────────────────────────────────────

INPUT_FILE = "out.txt"
OUTPUT_CSV = "cda_live.csv"

# Each entry: (label, p1_col_code, p2_col_code, rho_kg_m3, D_in, d_in)
VENTURIS = [
    ("LOX", 5, 6, 1147.0, 0.61, 0.2493),
    ("IPA", 7, 8,  786.0, 0.61, 0.19),
]

POLL_INTERVAL_MS = 500   # how often to check for new lines (milliseconds)

# ── END CONFIGURATION ─────────────────────────────────────────────────────────

PSI_TO_PA = 6894.76
IN_TO_M   = 0.0254


def venturi_mfr(p1_psi, p2_psi, rho, D_in, d_in):
    dp_pa = (p2_psi - p1_psi) * PSI_TO_PA
    if dp_pa <= 0:
        return None
    beta = d_in / D_in
    d_m  = d_in * IN_TO_M
    A    = math.pi / 4 * d_m ** 2
    return (A / math.sqrt(1 - beta ** 4)) * math.sqrt(2 * dp_pa * rho)


# ── Shared state (written by reader thread, read by plot thread) ──────────────

lock = threading.Lock()

# { label: {"m": [], "cda_ori": [], "cda_ven": [], "times": []} }
series = {label: {"m": [], "cda_ori": [], "cda_ven": [], "times": []}
          for label, *_ in VENTURIS}

last_known = {}   # pt_code -> latest psi value


def compute_and_store(ts, csv_writer):
    """Recompute CdA for every venturi using current last_known values."""
    for label, p1_code, p2_code, rho, D_in, d_in in VENTURIS:
        p1 = last_known.get(p1_code)
        p2 = last_known.get(p2_code)
        if p1 is None or p2 is None:
            continue
        m = venturi_mfr(p1, p2, rho, D_in, d_in)
        if m is None:
            continue
        beta  = d_in / D_in
        dp_pa = (p2 - p1) * PSI_TO_PA
        denom = math.sqrt(2 * rho * dp_pa)
        cda_ori = m / denom
        cda_ven = m * math.sqrt(1 - beta ** 4) / denom
        with lock:
            series[label]["m"].append(m)
            series[label]["cda_ori"].append(cda_ori)
            series[label]["cda_ven"].append(cda_ven)
            series[label]["times"].append(ts)
        csv_writer.writerow([f"{ts:.6f}", label, f"{m:.6f}", f"{cda_ori:.8f}", f"{cda_ven:.8f}"])


def reader_thread():
    """Tail INPUT_FILE, parse PT readings, update shared state, write CSV rows."""
    # Wait for file to exist
    while not os.path.exists(INPUT_FILE):
        print(f"Waiting for {INPUT_FILE}...")
        time.sleep(1)

    with open(OUTPUT_CSV, "w", newline="") as f_out:
        csv_writer = csv.writer(f_out)
        csv_writer.writerow(["time_s", "label", "mass_flow_rate_kg_s", "cda_orifice_m2", "cda_venturi_m2"])
        f_out.flush()

        with open(INPUT_FILE) as f_in:
            f_in.seek(0, 2)   # jump to end — remove this line to reprocess from start
            print(f"Tailing {INPUT_FILE} ...")

            while True:
                line = f_in.readline()
                if not line:
                    time.sleep(POLL_INTERVAL_MS / 1000)
                    continue
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "pt_code" not in msg:
                    continue
                ts   = float(msg["ts_s"])
                code = int(msg["pt_code"])
                val  = float(msg["value"])
                last_known[code] = val
                compute_and_store(ts, csv_writer)
                f_out.flush()


# ── Plot ──────────────────────────────────────────────────────────────────────

COLORS   = {"LOX": "#1f77b4", "IPA": "#ff7f0e"}
plot_objs = {}   # label -> {sc_ori, sc_ven, line_ori, line_ven}


def init_plot(ax):
    for label, *_ in VENTURIS:
        c = COLORS.get(label, None)
        line_ori, = ax.plot([], [], color=c, alpha=0.25, linewidth=1)
        line_ven, = ax.plot([], [], color=c, alpha=0.25, linewidth=1, linestyle="--")
        sc_ori = ax.scatter([], [], color=c, s=25, label=f"{label} orifice", zorder=3)
        sc_ven = ax.scatter([], [], color=c, s=25, marker="^", label=f"{label} venturi",
                            zorder=3, alpha=0.7)
        plot_objs[label] = dict(sc_ori=sc_ori, sc_ven=sc_ven,
                                 line_ori=line_ori, line_ven=line_ven)
    ax.set_xlabel("Mass flow rate  m  [kg/s]")
    ax.set_ylabel("CdA  [m²]")
    ax.set_title("CdA vs mass flow rate  (live)\n"
                 "Orifice: CdA = m/√(2ρΔP)    Venturi: CdA = m·√(1−β⁴)/√(2ρΔP)")
    ax.legend()
    ax.grid(True, alpha=0.3)


def update(_frame, ax):
    any_data = False
    for label in plot_objs:
        with lock:
            m_vals  = list(series[label]["m"])
            cda_ori = list(series[label]["cda_ori"])
            cda_ven = list(series[label]["cda_ven"])

        if not m_vals:
            continue
        any_data = True
        objs = plot_objs[label]

        objs["line_ori"].set_data(m_vals, cda_ori)
        objs["line_ven"].set_data(m_vals, cda_ven)

        import numpy as np
        objs["sc_ori"].set_offsets(np.c_[m_vals, cda_ori])
        objs["sc_ven"].set_offsets(np.c_[m_vals, cda_ven])

    if any_data:
        ax.relim()
        ax.autoscale_view()


def main():
    t = threading.Thread(target=reader_thread, daemon=True)
    t.start()

    fig, ax = plt.subplots(figsize=(11, 6))
    init_plot(ax)
    plt.tight_layout()

    ani = animation.FuncAnimation(fig, update, fargs=(ax,),
                                  interval=POLL_INTERVAL_MS, cache_frame_data=False)

    plt.show()


if __name__ == "__main__":
    main()
