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
TABLE2_PT_CODES      = [0, 2]

# Valve indices (0–16) to show in each table.
TABLE1_VALVE_INDICES = [0]
TABLE2_VALVE_INDICES = []

# Group readings within this many seconds into one row of Table 2.
GROUP_INTERVAL_S = 1.0

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
    pt_set = set(pt_codes)

    groups: dict[int, dict[int, float]] = defaultdict(dict)
    group_rep_ts: dict[int, float] = {}

    for ts, code, val in pt_readings:
        if code not in pt_set:
            continue
        gk = group_key(ts, interval)
        groups[gk][code] = val
        if gk not in group_rep_ts or ts < group_rep_ts[gk]:
            group_rep_ts[gk] = ts

    valve_cols = [f"valve_{i}" for i in valve_indices]
    header = ["time_s"] + [pt_name(c) for c in pt_codes] + valve_cols

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
