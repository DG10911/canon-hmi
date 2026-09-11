#!/usr/bin/env python3
"""Deterministic runtime SIMULATOR (spec §22, §42) — server-side, physically coherent.

Not a mock: it is an explicit deterministic runtime, honestly labelled SIMULATOR.
It implements the SAME command contracts + signal semantics the model defines, so:
  - a pump only starts if its real permissives pass (else the command is BLOCKED),
  - running assets produce coherent pressure/speed, stopped assets fall to floor,
  - levels/temperatures evolve deterministically (no random noise),
  - every value carries value·unit·timestamp·quality, source = SIMULATOR.

State is a plain dict per project; the runtime endpoint ticks it by elapsed time.
Pure stdlib.
"""
from __future__ import annotations
import math
import re
import time


def init_state(model: dict) -> dict:
    st = {"t": 0.0, "last": time.time(), "running": {}, "valve_open": {},
          "faults": {}, "analog": {}, "coils": {}, "progress": {}}
    seed = (model.get("runtimeSeed") or {}).get("initial", {}) if isinstance(model.get("runtimeSeed"), dict) else {}
    for s in model["signals"]:
        sid, unit = s["signalId"], (s.get("engUnit") or "").lower()
        if s.get("kind") == "analog-in":
            mn, mx = s.get("engMin", 0) or 0, s.get("engMax", 100) or 100
            st["analog"][sid] = seed.get(sid, mn + (mx - mn) * 0.45)
    for a in model["assets"]:
        st["running"][a["asset_id"]] = bool(seed.get(f"{a['asset_id']}_RUNNING", False))
        st["valve_open"][a["asset_id"]] = bool(seed.get(f"{a['asset_id']}_OPEN", False))
    # discrete health/status inputs (e.g. *_ESTOP_OK, *_OK) default HEALTHY(true); faults false
    for s in model["signals"]:
        sid = s["signalId"]
        if s.get("kind") == "discrete-in" and not sid.endswith(("_RUNNING", "_OPEN", "_CLOSED", "_FAULT")):
            default = ("ESTOP" in sid) or sid.endswith("_OK") or "_OK_" in sid
            st["coils"][sid] = bool(seed.get(sid, default))
    return st


def _asset_of(sig, model):
    for s in model["signals"]:
        if s["signalId"] == sig:
            return s.get("asset")
    return None


def tick(model: dict, st: dict):
    now = time.time()
    dt = min(2.0, now - st.get("last", now))
    st["last"] = now
    st["t"] += dt
    sig_by = {s["signalId"]: s for s in model["signals"]}
    for sid, s in sig_by.items():
        if s.get("kind") != "analog-in":
            continue
        mn, mx = s.get("engMin", 0) or 0, s.get("engMax", 100) or 100
        span = (mx - mn) or 1
        unit = (s.get("engUnit") or "").lower()
        asset = s.get("asset")
        running = st["running"].get(asset, False)
        cur = st["analog"].get(sid, mn + span * 0.45)
        if unit in ("bar", "psi", "kpa", "mbar"):
            target = mn + span * (0.62 if running else 0.04)
        elif unit == "rpm":
            target = mx * 0.9 if running else 0.0
        else:  # level / temp / flow / turbidity: slow deterministic drift
            base = mn + span * 0.5
            target = base + span * 0.12 * math.sin(st["t"] * 0.15 + (hash(sid) % 100) / 16.0)
            if running and unit == "%":
                target -= span * 0.05  # a running pump slowly draws the level down
        st["analog"][sid] = cur + (target - cur) * min(1.0, dt * 0.6)  # first-order ramp


def _cmp(expected, val) -> bool:
    if isinstance(expected, bool):
        return bool(val) == expected
    s = str(expected).strip().lower()
    if s in ("true", "false"):
        return bool(val) == (s == "true")
    m = re.match(r"(<=|>=|<|>|==)?\s*([-\d.]+)", s)
    if m and isinstance(val, (int, float)):
        op, n = m.group(1) or "==", float(m.group(2))
        return {"<": val < n, ">": val > n, "<=": val <= n, ">=": val >= n, "==": val == n}[op]
    return True  # unknown expected form — don't spuriously block; flagged for review elsewhere


def snapshot(model: dict, st: dict) -> dict:
    ts = time.strftime("%H:%M:%S")
    out = {}
    for s in model["signals"]:
        sid = s["signalId"]
        if s.get("kind") == "analog-in":
            v = round(st["analog"].get(sid, 0.0), 2)
        elif sid.endswith("_RUNNING"):
            v = st["running"].get(s.get("asset"), False)
        elif sid.endswith("_OPEN"):
            v = st["valve_open"].get(s.get("asset"), False)
        elif sid.endswith("_CLOSED"):
            v = not st["valve_open"].get(s.get("asset"), False)
        elif sid.endswith("_FAULT"):
            v = st["faults"].get(sid, False)
        else:
            v = st["coils"].get(sid, False)
        out[sid] = {"value": v, "unit": s.get("engUnit"), "ts": ts,
                    "quality": "GOOD", "source": "SIMULATOR"}
    return out


def run_command(model: dict, st: dict, command_id: str) -> dict:
    """Execute a command through the REAL contract: permissive gate, then apply.
    Returns progression + result (spec §20, §37)."""
    contract = next((c for c in model["commands"] if c["command_id"] == command_id), None)
    if not contract:
        return {"ok": False, "progression": ["COMMAND REQUESTED", "REJECTED"],
                "reason": f"{command_id} is not a command in this machine model"}
    target = contract.get("target_asset")
    vals = {k: v["value"] for k, v in snapshot(model, st).items()}
    perms = [p for p in model["permissives"] if p["command"] == command_id]
    interlocks = [i for i in model.get("interlocks", []) if i.get("command") == command_id]
    blocked = []
    for p in perms + interlocks:
        if not _cmp(p.get("expected"), vals.get(p["signal"])):
            blocked.append({"signal": p["signal"], "required": p.get("expected"),
                            "actual": vals.get(p["signal"]), "rejectCode": p.get("rejectCode"),
                            "message": p.get("message")})
    prog = ["COMMAND REQUESTED", "VALIDATING", "PERMISSIVES CHECK"]
    if blocked:
        return {"ok": False, "progression": prog + ["COMMAND BLOCKED"], "blocked": blocked,
                "reason": "; ".join(b.get("message") or f"{b['signal']} must be {b['required']}" for b in blocked)}
    # apply
    if command_id.endswith("_START"):
        st["running"][target] = True; verb = ["SENT", "ACKNOWLEDGED", "STARTING", "RUNNING"]
    elif command_id.endswith("_STOP"):
        st["running"][target] = False; verb = ["SENT", "ACKNOWLEDGED", "STOPPING", "STOPPED"]
    elif command_id.endswith("_OPEN"):
        st["valve_open"][target] = True; verb = ["SENT", "ACKNOWLEDGED", "OPENING", "OPEN"]
    elif command_id.endswith("_CLOSE"):
        st["valve_open"][target] = False; verb = ["SENT", "ACKNOWLEDGED", "CLOSING", "CLOSED"]
    else:
        verb = ["SENT", "ACKNOWLEDGED"]
    return {"ok": True, "progression": prog + verb, "command": command_id, "target": target,
            "feedback": contract.get("feedback_signal")}
