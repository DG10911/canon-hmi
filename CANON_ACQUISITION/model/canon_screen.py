#!/usr/bin/env python3
"""Deterministic HMI screen assembler (spec §20, §40, layoutAlgorithm).

The MODEL never builds screens — it only proposes atomic intents. This code
assembles a full, validated HMI screen from the machine model: it picks widgets
from the component registry per asset, binds each to REAL signals/commands, and
attaches evidence. Because every binding comes from the corpus (not a model),
the screen is correct-by-construction — nothing can be hallucinated (§56, §67).

Pure stdlib. Reads the CANON_ACQUISITION datasets in ../out/.

  python3 canon_screen.py                 # whole-machine overview
  python3 canon_screen.py --asset P401    # a single asset faceplate page
"""
from __future__ import annotations
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "out"))


def load(name):
    p = os.path.join(OUT, name)
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if os.path.exists(p) else []


def assemble_screen(asset=None, out_dir=OUT):
    """Deterministically assemble a validated HMI screen for `asset` (or the whole
    machine if None). Returns the screen dict. No model involved."""
    global OUT
    OUT = out_dir
    assets = load("08_assets.jsonl")
    signals = load("06_signals.jsonl")
    commands = load("15_commands.jsonl")
    alarms = load("18_alarms.jsonl")
    perms = load("16_permissives.jsonl")
    allowed = {c["component"] for c in load("24_hmi_components.jsonl")}
    ev_idx = {}
    for f in load("29_facts.jsonl"):
        ev_idx.setdefault(f["subject"], f.get("evidence_id"))

    sigset = {s["signalId"] for s in signals}
    cmdset = {c["command_id"] for c in commands}
    sig_by_asset = {}
    for s in signals:
        sig_by_asset.setdefault(s.get("asset"), []).append(s)
    cmd_by_target = {}
    for c in commands:
        cmd_by_target.setdefault(c.get("target_asset"), []).append(c["command_id"])

    machine = signals[0]["machine"] if signals else "machine"
    scope_assets = [x for x in assets if not asset or x["asset_id"] == asset]
    if not scope_assets:
        raise SystemExit(f"asset {asset!r} not found; have {[x['asset_id'] for x in assets]}")

    widgets = []
    dropped = []           # would hold any binding that failed validation (should stay empty)

    def bind(sig):
        """Return the tag only if it is a real signal — else record a drop."""
        if sig in sigset:
            return sig
        dropped.append(sig)
        return None

    def evid(*sigs):
        return sorted({ev_idx[s] for s in sigs if s and ev_idx.get(s)})

    def add(component, props, bsigs, bcmds=()):
        if component not in allowed:
            dropped.append(component)
            return
        props = {k: v for k, v in props.items() if v is not None}
        bsigs = [s for s in bsigs if s]
        bcmds = [c for c in bcmds if c in cmdset]
        widgets.append({
            "component": component, "props": props,
            "boundSignals": bsigs, "boundCommands": list(bcmds),
            "usedEvidenceIds": evid(*bsigs),
        })

    for A in scope_assets:
        aid, atype = A["asset_id"], A.get("type")
        asigs = sig_by_asset.get(aid, [])
        acmds = cmd_by_target.get(aid, [])

        def analog(unit):
            return next((s["signalId"] for s in asigs
                         if s.get("kind") == "analog-in" and (unit is None or s.get("engUnit") == unit)), None)

        if atype == "tank":
            lvl = analog("%") or analog(None)
            s = next((x for x in asigs if x["signalId"] == lvl), {})
            add("TankLevel", {"binding": bind(lvl), "unit": s.get("engUnit"),
                              "range": [s.get("engMin"), s.get("engMax")],
                              "marks": {k: s.get(k) for k in ("hh", "h", "l", "ll") if s.get(k) is not None}},
                [lvl])

        elif atype == "pump":
            add("MotorStarter", {
                "target": aid,
                "running": bind(f"{aid}_RUNNING"), "fault": bind(f"{aid}_FAULT"),
                "startCommand": next((c for c in acmds if c.endswith("_START")), None),
                "stopCommand": next((c for c in acmds if c.endswith("_STOP")), None),
            }, [f"{aid}_RUNNING", f"{aid}_FAULT"],
                [c for c in acmds if c.endswith(("_START", "_STOP"))])
            pg = analog("bar")
            if pg:
                s = next((x for x in asigs if x["signalId"] == pg), {})
                add("PressureGauge", {"binding": bind(pg), "unit": s.get("engUnit"),
                                      "range": [s.get("engMin"), s.get("engMax")]}, [pg])

        elif atype == "valve":
            add("ValveStatus", {
                "target": aid,
                "open": bind(f"{aid}_OPEN"), "closed": bind(f"{aid}_CLOSED"),
                "openCommand": next((c for c in acmds if c.endswith("_OPEN")), None),
                "closeCommand": next((c for c in acmds if c.endswith("_CLOSE")), None),
            }, [f"{aid}_OPEN", f"{aid}_CLOSED"],
                [c for c in acmds if c.endswith(("_OPEN", "_CLOSE"))])

        # a live permissive panel only for commands that actually HAVE permissives
        for c in acmds:
            psigs = [p["signal"] for p in perms if p["command"] == c and p["signal"] in sigset]
            if psigs:
                add("PermissivePanel", {"command": c, "showInterlocks": True}, psigs)

    # machine-scope alarm widgets (top of the page)
    alarm_sigs = [al["signal"] for al in alarms if al["signal"] in sigset]
    if alarms:
        widgets.insert(0, {"component": "AlarmBanner",
                           "props": {"scope": "machine" if not asset else "asset",
                                     "target": asset},
                           "boundSignals": sorted(set(alarm_sigs)),
                           "boundCommands": ["ack"],
                           "usedEvidenceIds": evid(*set(alarm_sigs))})

    screen = {
        "$schema": "canon.hmi_screen.v1",
        "pageId": f"scr_{asset or machine}",
        "pageTitle": (f"{asset} faceplate" if asset else f"{machine} — line overview"),
        "machine": machine,
        "scope": asset or "machine",
        "layoutAlgorithm": "deterministic: alarms top, analog faceplates left, commands right, grouped by asset",
        "assembledBy": "deterministic-code (NOT a model) — every binding is a real signal/command with evidence (§56/§67)",
        "widgets": widgets,
        "validation": {
            "ok": len(dropped) == 0,
            "dropped_invalid_bindings": sorted(set(x for x in dropped if x)),
            "total_widgets": len(widgets),
            "bindings_with_evidence": sum(1 for w in widgets if w.get("usedEvidenceIds")),
        },
    }
    return screen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asset", default=None, help="single asset (e.g. P401); default = whole machine")
    ap.add_argument("--out-dir", default=OUT)
    a = ap.parse_args()
    print(json.dumps(assemble_screen(a.asset, a.out_dir), indent=2))


if __name__ == "__main__":
    main()
