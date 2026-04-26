"""
Parse mosquitto_sub output of PT readings and valve states into two CSVs.

Table 1: time | <PT_NAME> | valve_A | valve_B
Table 2: time | <PT_NAME_1> | <PT_NAME_2> | ...

Edit the CONFIG section below, then run:
    python parse_log.py
"""

import bisect
import csv
import json
import math
from collections import defaultdict


# ── CONFIGURATION ─────────────────────────────────────────────────────────────

INPUT_FILE   = "out.txt"
TABLE1_OUT   = "delay.csv"
TABLE2_OUT   = "cda.csv"

# Maps pt_code integer to column name used in CSV headers.
PT_NAMES = {
    0:  "NITROGEN_TANK_PT",
    1:  "IPA_TANK_PT",
    2:  "LOX_TANK_PT",
    3:  "LOX_LINE_PT",
    4:  "IPA_LINE_PT",
    5:  "LOX_VENTURI_1_PT",
    6:  "LOX_VENTURI_2_PT",
    7:  "IPA_VENTURI_1_PT",
    8:  "IPA_VENTURI_2_PT",
    9:  "CHAMBER_PT",
    10: "IGNITER_PT",
    11: "PFM_PT",
    12: "POM_PT",
}

# PT codes to include in each table.
TABLE1_PT_CODES      = [0]
TABLE2_PT_CODES      = [5, 6, 7, 8]

# Valve indices (0–16) to show in each table.
TABLE1_VALVE_INDICES = [0]
TABLE2_VALVE_INDICES = []

# Group readings within this many seconds into one row of Table 2.
GROUP_INTERVAL_S = 1.0

# Venturi mass flow rate columns added to Table 2.
# q_m = C/sqrt(1-β⁴) * ε * (π/4) * d² * sqrt(2*(P2-P1)*ρ)   [C=ε=1]
# Pressures from the CSV are in PSI and are converted to Pa automatically.
# Set a PT code to None to skip that venturi entirely.

LOX_P1_CODE = 5        # LOX_VENTURI_1_PT  (upstream)
LOX_P2_CODE = 6        # LOX_VENTURI_2_PT  (throat / downstream)
LOX_RHO     = 1147.0   # kg/m³
LOX_D_IN    = 0.61     # pipe diameter, inches
LOX_d_IN    = 0.2493   # throat diameter, inches

IPA_P1_CODE = 7        # IPA_VENTURI_1_PT
IPA_P2_CODE = 8        # IPA_VENTURI_2_PT
IPA_RHO     = 786.0    # kg/m³
IPA_D_IN    = 0.61
IPA_d_IN    = 0.19

# ── END CONFIGURATION ─────────────────────────────────────────────────────────


def pt_name(code: int) -> str:
    return PT_NAMES.get(code, f"pt_{code}")


def parse_file(path: str):
    pt_readings: list[tuple[float, int, float]] = []  # (ts, pt_code, value)
    valve_events: list[tuple[float, dict]]       = []  # (ts, {int: bool})

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            msg = json.loads(line)

            ts = msg.get("ts_s")
            if ts is None:
                continue

            if "pt_code" in msg:
                pt_readings.append((ts, int(msg["pt_code"]), float(msg["value"])))
            elif "states" in msg:
                states = {int(k): bool(v) for k, v in msg["states"].items()}
                valve_events.append((ts, states))

    pt_readings.sort(key=lambda x: x[0])
    valve_events.sort(key=lambda x: x[0])
    return pt_readings, valve_events


#list of timestamp and valve state at that timestamp
def make_valve_lookup(valve_events: list) -> tuple[list, list]:
    ts_list = [e[0] for e in valve_events]
    st_list = [e[1] for e in valve_events]
    return ts_list, st_list



#At this PT reading time, what was the latest known valve state? 
def valve_at(ts: float, ts_list: list, st_list: list) -> dict:
    """Most recent valve state at or before ts, or {} if none yet."""
    if not ts_list:
        return {}
    idx = bisect.bisect_right(ts_list, ts) - 1
    return st_list[idx] if idx >= 0 else {}


def fmt_valve(states: dict, idx: int) -> str:
    if idx not in states:
        return ""
    return "open" if states[idx] else "closed"


def group_key(ts: float, interval: float) -> int:
    return math.floor(ts / interval)


PSI_TO_PA = 6894.76
IN_TO_M   = 0.0254

def venturi_mfr(p1_psi, p2_psi, rho, D_in, d_in) -> str:
    """
    Venturi mass flow rate (kg/s), or '' if differential is non-positive.
    q_m = (π/4 * d²) / sqrt(1 - β⁴) * sqrt(2 * (P2-P1) * ρ)
    """
    dp_pa = (p2_psi - p1_psi) * PSI_TO_PA   # formula uses P2 - P1
    if dp_pa <= 0:
        return ""
    beta  = d_in / D_in
    d_m   = d_in * IN_TO_M
    A     = math.pi / 4 * d_m ** 2
    q_m   = (A / math.sqrt(1 - beta ** 4)) * math.sqrt(2 * dp_pa * rho)
    return f"{q_m:.6f}"


# Table 1

def write_table1(pt_readings, ts_list, st_list, pt_codes, valve_indices, output_path):
    pt_set = set(pt_codes)
    valve_cols = [f"valve_{i}" for i in valve_indices]
    pt_cols = [f"pt {pt_name(c)} value" for c in pt_codes]
    header = ["time_s"] + pt_cols + valve_cols

    rows = 0
    with open(output_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for ts, code, val in pt_readings:
            if code not in pt_set:
                continue
            states = valve_at(ts, ts_list, st_list)
            # Put the value under its named column, leave others blank
            pt_vals = [val if c == code else "" for c in pt_codes]
            row = [f"{ts:.6f}"] + pt_vals + [fmt_valve(states, i) for i in valve_indices]
            w.writerow(row)
            rows += 1

    print(f"Table 1 → {output_path}  ({rows} rows)")


# Table 2

def write_table2(pt_readings, ts_list, st_list, interval, pt_codes, valve_indices, output_path):
    # Collect all PT codes needed (display columns + venturi pairs)
    venturi_cfgs = [
        ("lox_mass_flow_rate_kg_s", LOX_P1_CODE, LOX_P2_CODE, LOX_RHO, LOX_D_IN, LOX_d_IN),
        ("ipa_mass_flow_rate_kg_s", IPA_P1_CODE, IPA_P2_CODE, IPA_RHO, IPA_D_IN, IPA_d_IN),
    ]
    extra_codes = {c for _, p1, p2, *_ in venturi_cfgs
                   for c in (p1, p2) if p1 is not None and p2 is not None}
    all_codes = set(pt_codes) | extra_codes

    groups: dict[int, dict[int, float]] = defaultdict(dict)
    group_rep_ts: dict[int, float] = {}
    last_seen: dict[int, float] = {}  # most recent value per PT code across all groups

    for ts, code, val in pt_readings:
        if code not in all_codes:
            continue
        last_seen[code] = val
        gk = group_key(ts, interval)
        # Carry forward any codes not yet seen in this group
        for c in all_codes:
            if c not in groups[gk] and c in last_seen:
                groups[gk][c] = last_seen[c]
        groups[gk][code] = val
        if gk not in group_rep_ts or ts < group_rep_ts[gk]:
            group_rep_ts[gk] = ts

    valve_cols = [f"valve_{i}" for i in valve_indices]
    mfr_cols   = [label for label, p1, p2, *_ in venturi_cfgs if p1 is not None and p2 is not None]
    header     = ["time_s"] + [pt_name(c) for c in pt_codes] + valve_cols + mfr_cols

    all_gks = sorted(group_rep_ts.keys())
    rows = 0
    with open(output_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for gk in all_gks:
            rep_ts = group_rep_ts[gk]
            states = valve_at(rep_ts, ts_list, st_list)
            row = ([f"{rep_ts:.6f}"]
                   + [groups[gk].get(c, "") for c in pt_codes]
                   + [fmt_valve(states, i) for i in valve_indices])
            for _, p1, p2, rho, D, d in venturi_cfgs:
                if p1 is None or p2 is None:
                    continue
                v1 = groups[gk].get(p1, "")
                v2 = groups[gk].get(p2, "")
                row.append(venturi_mfr(v1, v2, rho, D, d) if v1 != "" and v2 != "" else "")
            w.writerow(row)
            rows += 1

    print(f"Table 2 → {output_path}  ({rows} rows)")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    pt_readings, valve_events = parse_file(INPUT_FILE)
    print(f"Parsed: {len(pt_readings)} PT readings, {len(valve_events)} valve state messages")

    ts_list, st_list = make_valve_lookup(valve_events)

    write_table1(pt_readings, ts_list, st_list,
                 TABLE1_PT_CODES, TABLE1_VALVE_INDICES, TABLE1_OUT)

    write_table2(pt_readings, ts_list, st_list, GROUP_INTERVAL_S,
                 TABLE2_PT_CODES, TABLE2_VALVE_INDICES, TABLE2_OUT)


if __name__ == "__main__":
    main()
