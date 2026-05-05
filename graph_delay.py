"""
Interactively pick one of two trimmed CSVs and plot:
    x = mass flow rate (kg/s)
    y = CdA (m^2)
with two lines: one for the venturi, one for the orifice.

Once the orifice mass flow returns to its idle value (~14.848), the rest of the
file is treated as garbage and dropped from the plot.

Run:
    python plot_cda.py
"""

import csv
import sys
import matplotlib.pyplot as plt

# ── CONFIG ─────────────────────────────────────────────────────────────────────
FILES = {
    "1": "cda_test1_trimmed.csv",
    "2": "cda_test2_trimmed.csv",
}

IDLE_VALUE = 14.848    # orifice mass flow value when the sensor is idle
TOL = 1e-3             # tolerance for the "is at idle" check

# Outlier filtering on CdA (per series). Set to None to disable.
# 1.5 = standard Tukey rule. Smaller = stricter (drops more), larger = looser.
OUTLIER_IQR_K = 1.5
# ───────────────────────────────────────────────────────────────────────────────


def pick_file():
    print("Which CSV do you want to plot?")
    for k, name in FILES.items():
        print(f"  {k}) {name}")
    choice = input("Enter 1 or 2: ").strip()
    if choice not in FILES:
        print(f"Invalid choice {choice!r}.")
        sys.exit(1)
    return FILES[choice]


def find_col(header, needle):
    """Return the index of the first header containing `needle` (case-sensitive)."""
    for i, name in enumerate(header):
        if needle in name:
            return i
    raise KeyError(f"No column matching {needle!r} in header: {header}")


def load(path):
    with open(path, newline="") as f:
        r = csv.reader(f)
        header = next(r)
        rows = [row for row in r if row]   # skip blank lines
    return header, rows


def to_float(s):
    """Parse a CSV cell to float, or None if blank/invalid."""
    if s == "" or s is None:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def filter_outliers(xs, ys, k):
    """Drop (x, y) pairs whose x is outside Q1 - k*IQR .. Q3 + k*IQR.
    Returns (xs_kept, ys_kept, n_dropped)."""
    if k is None or len(xs) < 4:
        return xs, ys, 0
    sorted_xs = sorted(xs)
    n = len(sorted_xs)
    q1 = sorted_xs[n // 4]
    q3 = sorted_xs[(3 * n) // 4]
    iqr = q3 - q1
    lo, hi = q1 - k * iqr, q3 + k * iqr
    kept_x, kept_y = [], []
    for x, y in zip(xs, ys):
        if lo <= x <= hi:
            kept_x.append(x)
            kept_y.append(y)
    return kept_x, kept_y, len(xs) - len(kept_y)


def main():
    path = pick_file()
    header, rows = load(path)

    # Auto-detect which propellant by scanning the header
    propellant = "LOX" if any("LOX" in h for h in header) else "IPA"

    iv = find_col(header, f"{propellant} Venturi Mass Flow")
    io = find_col(header, f"{propellant} Orifice Mass Flow")
    cv = find_col(header, f"{propellant} CdA venturi")
    co = find_col(header, f"{propellant} CdA orifice")

    # Build two parallel series, stopping at the first row where the orifice
    # mass flow is back at its idle value (~14.848).
    v_x, v_y = [], []   # venturi: mass flow vs CdA
    o_x, o_y = [], []   # orifice: mass flow vs CdA

    cutoff_idx = None
    for i, row in enumerate(rows):
        m_orifice = to_float(row[io])
        if m_orifice is not None and abs(m_orifice - IDLE_VALUE) < TOL:
            cutoff_idx = i
            break

        m_venturi = to_float(row[iv])
        cda_v = to_float(row[cv])
        cda_o = to_float(row[co])

        if m_venturi is not None and cda_v is not None:
            v_x.append(m_venturi)
            v_y.append(cda_v)
        if m_orifice is not None and cda_o is not None:
            o_x.append(m_orifice)
            o_y.append(cda_o)

    total = len(rows)
    used = cutoff_idx if cutoff_idx is not None else total
    print(f"Loaded {total} rows from {path}")
    print(f"Using {used} rows  (cutoff at row {cutoff_idx})"
          if cutoff_idx is not None else
          f"Using all {total} rows  (orifice never returned to idle)")
    print(f"Venturi points: {len(v_x)}   Orifice points: {len(o_x)}")

    # Drop CdA outliers (per series) before plotting.
    v_x, v_y, v_dropped = filter_outliers(v_x, v_y, OUTLIER_IQR_K)
    o_x, o_y, o_dropped = filter_outliers(o_x, o_y, OUTLIER_IQR_K)
    if OUTLIER_IQR_K is not None:
        print(f"Outlier filter (k={OUTLIER_IQR_K}): "
              f"venturi dropped {v_dropped}, orifice dropped {o_dropped}")

    # ---- plot ----
    fig, ax = plt.subplots(figsize=(10, 6))
    if v_x:
        ax.plot(v_x, v_y, label=f"{propellant} venturi",
                marker="o", markersize=3, linewidth=1)
    if o_x:
        ax.plot(o_x, o_y, label=f"{propellant} orifice",
                marker="s", markersize=3, linewidth=1)

    ax.set_xlabel("Mass flow rate (kg/s)")
    ax.set_ylabel("CdA (m²)")
    ax.set_title(f"{propellant}: CdA vs mass flow rate\n({path})")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()