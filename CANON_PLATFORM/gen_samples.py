#!/usr/bin/env python3
"""Generate 100 diverse machine CSVs across industrial sectors (deterministic).

Each file is a valid tag list the platform ingests: commands infer from *_REQ,
alarms from hh/ll. Output: samples/library/<sector>__<TAG>.csv
Run: python3 gen_samples.py
"""
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "samples", "library")

# sector -> (tag prefix, asset recipe [(type, count)], analog units per type)
SECTORS = {
    "water_treatment":    ("WTP", [("tank", 2), ("pump", 3), ("valve", 3)], {"tank": [("%", "LT", "level")], "pump": [("bar", "PT", "pressure"), ("m3/h", "FT", "flow")]}),
    "wastewater":         ("WWT", [("tank", 3), ("pump", 4), ("motor", 2), ("valve", 2)], {"tank": [("%", "LT", "level"), ("NTU", "AIT", "turbidity")], "pump": [("bar", "PT", "pressure")], "motor": [("rpm", "ST", "speed")]}),
    "desalination":       ("DSL", [("tank", 2), ("pump", 4), ("valve", 4)], {"tank": [("%", "LT", "level"), ("uS/cm", "CIT", "conductivity")], "pump": [("bar", "PT", "pressure"), ("m3/h", "FT", "flow")]}),
    "oil_gas_sep":        ("OGS", [("tank", 3), ("pump", 3), ("valve", 5)], {"tank": [("%", "LT", "level"), ("bar", "PT", "pressure")], "pump": [("bar", "PT", "pressure")]}),
    "chemical_batch":     ("RX", [("tank", 2), ("motor", 2), ("pump", 2), ("valve", 4)], {"tank": [("%", "LT", "level"), ("degC", "TT", "temp"), ("bar", "PT", "pressure")], "motor": [("rpm", "ST", "agitator")], "pump": [("bar", "PT", "pressure")]}),
    "pharma_cip":         ("CIP", [("tank", 3), ("pump", 2), ("valve", 5)], {"tank": [("%", "LT", "level"), ("degC", "TT", "temp"), ("pH", "AIT", "pH")], "pump": [("bar", "PT", "pressure")]}),
    "food_pasteurizer":   ("PAS", [("tank", 2), ("pump", 3), ("valve", 3), ("motor", 1)], {"tank": [("%", "LT", "level"), ("degC", "TT", "temp")], "pump": [("bar", "PT", "pressure"), ("L/min", "FT", "flow")]}),
    "brewery":            ("BRW", [("tank", 4), ("pump", 3), ("valve", 4)], {"tank": [("%", "LT", "level"), ("degC", "TT", "temp"), ("bar", "PT", "pressure")], "pump": [("m3/h", "FT", "flow")]}),
    "dairy":              ("DRY", [("tank", 3), ("pump", 3), ("valve", 4), ("motor", 1)], {"tank": [("%", "LT", "level"), ("degC", "TT", "temp")], "pump": [("bar", "PT", "pressure")]}),
    "hvac_ahu":           ("AHU", [("motor", 2), ("valve", 2), ("tank", 1)], {"motor": [("rpm", "ST", "fan"), ("Pa", "DPT", "dp")], "tank": [("degC", "TT", "temp")]}),
    "chiller_plant":      ("CHW", [("motor", 2), ("pump", 3), ("valve", 2)], {"motor": [("rpm", "ST", "compressor"), ("bar", "PT", "refrig"), ("degC", "TT", "temp")], "pump": [("m3/h", "FT", "flow")]}),
    "boiler_house":       ("BLR", [("tank", 2), ("pump", 2), ("valve", 3), ("motor", 1)], {"tank": [("%", "LT", "drum-level"), ("bar", "PT", "steam-pressure"), ("degC", "TT", "temp")], "pump": [("bar", "PT", "pressure")], "motor": [("rpm", "ST", "fd-fan")]}),
    "compressor_station": ("CMP", [("motor", 3), ("tank", 2), ("valve", 3)], {"motor": [("rpm", "ST", "speed"), ("bar", "PT", "discharge"), ("A", "IT", "current")], "tank": [("bar", "PT", "receiver")]}),
    "power_genset":       ("GEN", [("motor", 2), ("tank", 2), ("valve", 2)], {"motor": [("rpm", "ST", "speed"), ("kW", "JT", "power"), ("degC", "TT", "temp")], "tank": [("%", "LT", "fuel"), ("bar", "PT", "oil")]}),
    "packaging_line":     ("PKG", [("motor", 4), ("valve", 2), ("tank", 1)], {"motor": [("rpm", "ST", "speed")], "tank": [("%", "LT", "level")]}),
    "bottling_line":      ("BOT", [("motor", 3), ("pump", 2), ("valve", 3), ("tank", 1)], {"motor": [("rpm", "ST", "speed")], "pump": [("bar", "PT", "pressure")], "tank": [("%", "LT", "level")]}),
    "conveyor_sortation": ("SORT", [("motor", 5), ("valve", 3)], {"motor": [("rpm", "ST", "speed"), ("A", "IT", "current")]}),
    "mining_slurry":      ("MIN", [("pump", 4), ("tank", 3), ("valve", 3)], {"pump": [("bar", "PT", "pressure"), ("m3/h", "FT", "flow")], "tank": [("%", "LT", "level"), ("%", "DIT", "density")]}),
    "cement_plant":       ("CEM", [("motor", 4), ("valve", 3), ("tank", 2)], {"motor": [("rpm", "ST", "speed"), ("degC", "TT", "temp")], "tank": [("%", "LT", "silo-level")]}),
    "paper_machine":      ("PPR", [("motor", 5), ("valve", 3), ("tank", 2)], {"motor": [("rpm", "ST", "speed"), ("kW", "JT", "power")], "tank": [("%", "LT", "level")]}),
    "steel_reheat":       ("STL", [("motor", 2), ("valve", 4), ("tank", 1)], {"motor": [("rpm", "ST", "roller")], "valve": [("%", "ZT", "position")], "tank": [("degC", "TT", "furnace-temp")]}),
    "automotive_paint":   ("PNT", [("motor", 3), ("pump", 2), ("valve", 4)], {"motor": [("rpm", "ST", "speed")], "pump": [("bar", "PT", "pressure"), ("mL/min", "FT", "flow")]}),
    "cold_storage":       ("COLD", [("motor", 3), ("valve", 2), ("tank", 2)], {"motor": [("rpm", "ST", "compressor"), ("degC", "TT", "temp")], "tank": [("bar", "PT", "refrig")]}),
    "biogas_digester":    ("BGD", [("tank", 3), ("pump", 2), ("valve", 3), ("motor", 1)], {"tank": [("%", "LT", "level"), ("degC", "TT", "temp"), ("mbar", "PT", "gas-pressure")], "pump": [("m3/h", "FT", "flow")]}),
    "pumping_station":    ("PS", [("pump", 5), ("tank", 2), ("valve", 3)], {"pump": [("bar", "PT", "pressure"), ("m3/h", "FT", "flow")], "tank": [("%", "LT", "wet-well")]}),
}

HDR = "asset,type,signal,kind,unit,min,max,hh,h,l,ll,desc"
RANGES = {"%": (0, 100, 90, 80, 20, 10), "bar": (0, 16, 14, 12, None, 2), "degC": (0, 200, 150, 130, None, None),
          "m3/h": (0, 300, None, None, None, 10), "L/min": (0, 120, None, None, None, None), "rpm": (0, 3000, 2900, 2800, None, None),
          "NTU": (0, 50, 20, 10, None, None), "Pa": (0, 1000, 900, 800, None, None), "A": (0, 400, 380, 350, None, None),
          "kW": (0, 2000, 1900, 1800, None, None), "pH": (0, 14, 11, 10, 4, 3), "uS/cm": (0, 2000, 1800, None, None, None),
          "mbar": (0, 100, 90, 80, None, None), "mL/min": (0, 500, None, None, None, None), "kg": (0, 100, 90, 80, None, None)}


def rows_for_asset(atype, tag, prefix_map, rng):
    rows = []
    for (unit, sp, label) in prefix_map.get(atype, []):
        num = tag.split("-")[-1]
        sid = f"{sp}-{num}"
        lo, hi, hh, h, l, ll = RANGES.get(unit, (0, 100, None, None, None, None))
        rows.append([tag, atype, sid, "analog-in", unit, lo, hi, hh, h, l, ll, label])
    if atype in ("pump", "motor"):
        rows += [[tag, atype, f"{tag}_RUNNING", "discrete-in", "", "", "", "", "", "", "", "running"],
                 [tag, atype, f"{tag}_FAULT", "discrete-in", "", "", "", "", "", "", "", "fault"],
                 [tag, atype, f"{tag}_START_REQ", "discrete-out", "", "", "", "", "", "", "", "start"],
                 [tag, atype, f"{tag}_STOP_REQ", "discrete-out", "", "", "", "", "", "", "", "stop"]]
    elif atype == "valve":
        rows += [[tag, atype, f"{tag}_OPEN", "discrete-in", "", "", "", "", "", "", "", "open limit"],
                 [tag, atype, f"{tag}_CLOSED", "discrete-in", "", "", "", "", "", "", "", "closed limit"],
                 [tag, atype, f"{tag}_OPEN_REQ", "discrete-out", "", "", "", "", "", "", "", "open"],
                 [tag, atype, f"{tag}_CLOSE_REQ", "discrete-out", "", "", "", "", "", "", "", "close"]]
    return rows


def build(sector, prefix, recipe, analogs, idx, rng):
    tag_pref = {"tank": "TK", "pump": "P", "valve": "XV", "motor": "M"}
    counters = {k: 0 for k in tag_pref}
    rows = []
    base = idx * 100
    for (atype, count) in recipe:
        n = max(1, count + rng.randint(-1, 2))
        for _ in range(n):
            counters[atype] += 1
            tag = f"{tag_pref[atype]}-{base + counters[atype]}"
            rows += rows_for_asset(atype, tag, analogs, rng)
    lines = [HDR] + [",".join("" if c is None else str(c) for c in r) for r in rows]
    return "\n".join(lines) + "\n"


def main():
    os.makedirs(OUT, exist_ok=True)
    made = 0
    sectors = list(SECTORS.items())
    per = 4  # 25 sectors x 4 = 100
    for si, (sector, (prefix, recipe, analogs)) in enumerate(sectors):
        for v in range(per):
            rng = random.Random(1000 + si * 10 + v)
            idx = v + 1
            tagid = f"{prefix}-{v+1:02d}"
            csv = build(sector, prefix, recipe, analogs, idx, rng)
            with open(os.path.join(OUT, f"{sector}__{tagid}.csv"), "w") as fh:
                fh.write(csv)
            made += 1
    print(f"generated {made} machine CSVs in {OUT}")


if __name__ == "__main__":
    main()
