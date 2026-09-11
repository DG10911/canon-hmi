#!/usr/bin/env python3
"""CANON Platform — core engine (pure stdlib).

Turns an uploaded machine project into a normalized canonical model, assembles
validated HMI screens from it, and applies natural-language edits — all with the
same guarantee as the rest of CANON: nothing binds to a tag/command that isn't in
the model. The model proposes; this deterministic layer defines + validates.

Reused by app.py (FastAPI). No third-party deps.
"""
from __future__ import annotations
import json
import random
import re
from typing import Any, Optional

# ---- component registry (what a screen may contain) -----------------------
COMPONENTS = ["AlarmBanner", "TankLevel", "PressureGauge", "NumericValue",
              "MotorStarter", "ValveStatus", "PermissivePanel", "Trend"]


# ======================================================================
# 1. NORMALIZE an uploaded machine project -> canonical model
# ======================================================================
def normalize_machine(raw: dict, project_id: str) -> dict:
    """Accept a canon.machine.v2-style project (assets/signals/io/commands/
    alarms/permissives) and return a normalized model the platform uses."""
    assets = [{"asset_id": a.get("assetId") or a.get("asset_id"),
               "type": a.get("type"), "name": a.get("name")}
              for a in raw.get("assets", []) if a.get("assetId") or a.get("asset_id")]

    signals = []
    for s in raw.get("signals", []):
        signals.append({
            "signalId": s["signalId"], "asset": s.get("asset"),
            "kind": s.get("kind"), "dataType": s.get("dataType"),
            "engUnit": s.get("engUnit"), "engMin": s.get("engMin"), "engMax": s.get("engMax"),
            "hh": s.get("hh"), "h": s.get("h"), "l": s.get("l"), "ll": s.get("ll"),
            "description": s.get("description"), "access": s.get("access"),
        })

    # commands + permissives may live in raw or a separate contracts block
    commands, permissives, interlocks = [], [], []
    contracts = raw.get("commandContractsInline") or raw.get("contracts") or []
    for ct in contracts:
        commands.append({"command_id": ct["command"], "target_asset": ct.get("target"),
                         "request_signal": ct.get("request"), "feedback_signal": ct.get("feedback")})
        for p in ct.get("permissives", []):
            permissives.append({"command": ct["command"], "signal": p["signal"],
                                "expected": p.get("expected"), "rejectCode": p.get("rejectCode"),
                                "message": p.get("message")})
        for il in ct.get("interlocks", []):
            interlocks.append({"command": ct["command"], "signal": il["signal"],
                               "expected": il.get("expected"), "rejectCode": il.get("rejectCode")})
    # fallback: a plain commands list of ids
    for cid in raw.get("commands", []):
        if isinstance(cid, str) and not any(c["command_id"] == cid for c in commands):
            tgt = cid.split("_")[0]
            commands.append({"command_id": cid, "target_asset": tgt,
                             "request_signal": None, "feedback_signal": None})

    alarms = [{"alarm_id": a.get("alarmId") or a.get("alarm_id"), "signal": a.get("signal"),
               "condition": a.get("condition"), "priority": a.get("priority"),
               "message": a.get("message")} for a in raw.get("alarms", [])]

    ctl = raw.get("controller", {})
    return {
        "projectId": project_id,
        "name": raw.get("name", project_id),
        "subtitle": raw.get("description", ""),
        "controller": ctl.get("family") or ctl.get("model") or raw.get("controllerName") or "UNKNOWN",
        "site": raw.get("site"), "area": raw.get("area"),
        "assets": assets, "signals": signals, "commands": commands,
        "permissives": permissives, "interlocks": interlocks, "alarms": alarms,
        "runtimeSeed": raw.get("runtimeSeed"),      # real sim physics (TK-401), if present
        "counts": {"assets": len(assets), "signals": len(signals), "alarms": len(alarms)},
    }


# ======================================================================
# 1b. Parse an uploaded tag-list CSV -> canonical model
# ======================================================================
_KIND_MAP = {"ai": "analog-in", "analog-in": "analog-in", "analog": "analog-in", "analogin": "analog-in",
             "di": "discrete-in", "discrete-in": "discrete-in", "digital-in": "discrete-in", "discretein": "discrete-in",
             "do": "discrete-out", "discrete-out": "discrete-out", "digital-out": "discrete-out", "discreteout": "discrete-out"}


def _row_get(row, *aliases):
    for k, v in row.items():
        if k and str(k).strip().lower().replace(" ", "").replace("_", "") in aliases:
            return v.strip() if isinstance(v, str) else v
    return None


def _num(x):
    try:
        return float(x) if x not in (None, "") else None
    except (ValueError, TypeError):
        return None


def rows_to_model(rows: list, project_id: str, controller: str = "UNKNOWN") -> dict:
    """Shared engine: a list of loose row-dicts (from CSV/XLSX/XML/PDF) -> canonical
    model. Flexible headers: asset,type,signal,kind,unit,min,max,hh,h,l,ll,desc.
    Commands inferred from *_REQ signals; alarms from hh/ll limits and *_FAULT."""
    get, num = _row_get, _num
    assets: dict = {}
    signals: list = []
    for r in rows:
        sig = get(r, "signal", "signalid", "tag", "tagname", "name")
        if not sig:
            continue
        sig = sig.strip()
        asset = (get(r, "asset", "assetid", "equipment", "unit") or sig).strip()
        atype = (get(r, "type", "assettype", "equipmenttype", "class") or "asset").strip().lower()
        kind = _KIND_MAP.get((get(r, "kind", "io", "iotype", "signalkind") or "").strip().lower(), "analog-in")
        unit = get(r, "unit", "engunit", "eu")
        signals.append({
            "signalId": sig, "asset": asset, "kind": kind,
            "dataType": "REAL" if kind == "analog-in" else "BOOL",
            "engUnit": (unit or None), "engMin": num(get(r, "min", "engmin", "rangemin")),
            "engMax": num(get(r, "max", "engmax", "rangemax")),
            "hh": num(get(r, "hh")), "h": num(get(r, "h")), "l": num(get(r, "l")), "ll": num(get(r, "ll")),
            "description": get(r, "desc", "description", "comment"),
            "access": "request" if kind == "discrete-out" else "read",
        })
        assets.setdefault(asset, {"assetId": asset, "type": atype, "name": asset})

    ids = {s["signalId"] for s in signals}
    contracts, alarms = [], []
    for aid in assets:
        def has(suf):
            return f"{aid}{suf}" in ids
        if has("_START_REQ"):
            contracts.append({"command": f"{aid}_START", "target": aid, "request": f"{aid}_START_REQ",
                              "feedback": f"{aid}_RUNNING" if has("_RUNNING") else None,
                              "permissives": ([{"signal": f"{aid}_FAULT", "expected": False,
                                                "rejectCode": "PERM_FAULT_ACTIVE",
                                                "message": f"{aid} must be fault-free."}] if has("_FAULT") else [])})
        if has("_STOP_REQ"):
            contracts.append({"command": f"{aid}_STOP", "target": aid, "request": f"{aid}_STOP_REQ",
                              "feedback": f"{aid}_RUNNING" if has("_RUNNING") else None, "permissives": []})
        if has("_OPEN_REQ"):
            contracts.append({"command": f"{aid}_OPEN", "target": aid, "request": f"{aid}_OPEN_REQ",
                              "feedback": f"{aid}_OPEN" if has("_OPEN") else None, "permissives": []})
        if has("_CLOSE_REQ"):
            contracts.append({"command": f"{aid}_CLOSE", "target": aid, "request": f"{aid}_CLOSE_REQ",
                              "feedback": f"{aid}_CLOSED" if has("_CLOSED") else None, "permissives": []})
    for s in signals:
        if s.get("hh") is not None:
            alarms.append({"alarmId": f"ALM_{s['signalId']}_HH", "signal": s["signalId"],
                           "condition": f">= {s['hh']}", "priority": "high", "message": f"{s['signalId']} high-high"})
        elif s.get("ll") is not None:
            alarms.append({"alarmId": f"ALM_{s['signalId']}_LL", "signal": s["signalId"],
                           "condition": f"<= {s['ll']}", "priority": "high", "message": f"{s['signalId']} low-low"})
        if s["signalId"].endswith("_FAULT"):
            alarms.append({"alarmId": f"ALM_{s['signalId']}", "signal": s["signalId"],
                           "condition": "== true", "priority": "high", "message": f"{s['signalId']} active"})

    raw = {"name": project_id, "description": "Ingested from uploaded document",
           "controller": {"family": controller},
           "assets": list(assets.values()), "signals": signals, "contracts": contracts, "alarms": alarms}
    return normalize_machine(raw, project_id)


# ---- per-format loaders (all funnel into rows_to_model) --------------------
def normalize_csv(text: str, project_id: str, controller: str = "UNKNOWN") -> dict:
    import csv
    import io
    return rows_to_model(list(csv.DictReader(io.StringIO(text))), project_id, controller)


def normalize_xlsx(data: bytes, project_id: str, controller: str = "UNKNOWN") -> dict:
    """First worksheet: row 1 = headers, following rows = one signal each."""
    import io
    import openpyxl  # noqa: F401 — optional dep, present via requirements
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    header = [str(c).strip() if c is not None else "" for c in next(rows_iter)]
    rows = []
    for vals in rows_iter:
        if not any(v not in (None, "") for v in vals):
            continue
        rows.append({header[i]: vals[i] for i in range(min(len(header), len(vals)))})
    return rows_to_model(rows, project_id, controller)


def normalize_xml(text: str, project_id: str, controller: str = "UNKNOWN") -> dict:
    """Any XML: every element carrying a signal/tag/name (attribute or child text)
    becomes a row. Handles a simple <signal .../> schema and PLCopen <variable .../>."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(text)
    rows = []
    for el in root.iter():
        a = {k.lower(): v for k, v in el.attrib.items()}
        tag_name = a.get("signal") or a.get("tag") or a.get("name")
        if not tag_name:
            continue
        # PLCopen <variable name= type=BOOL/REAL ...> -> infer kind from type/address
        row = dict(a)
        row.setdefault("signal", tag_name)
        if "kind" not in row:
            t = (a.get("type") or a.get("datatype") or "").upper()
            addr = (a.get("address") or "").upper()
            if t in ("BOOL",) or addr.startswith(("%I", "%Q")):
                row["kind"] = "discrete-out" if addr.startswith("%Q") else "discrete-in"
            else:
                row["kind"] = "analog-in"
        # nested <asset>/<type> children
        for ch in el:
            ct = ch.tag.split("}")[-1].lower()
            if ct in ("asset", "type", "unit", "desc", "description") and ch.text:
                row.setdefault(ct, ch.text.strip())
        rows.append(row)
    return rows_to_model(rows, project_id, controller)


def normalize_canon_json(raw: dict, project_id: str) -> dict:
    """SUPER context analysis of a rich CANON canonical-model JSON:
    understands signals with only {id, semantic, type, unit, range}, assigns each to
    the right asset (by tag prefix → semantics → type heuristics), parses permissive
    conditions, and maps string alarm names to real signals. Nothing invented."""
    cm = raw.get("canonical_model", raw)
    proj = raw.get("project", {}) or {}
    name = proj.get("name") or raw.get("package_name") or project_id
    controller = proj.get("controller", "UNKNOWN")
    assets = [{"assetId": a.get("id") or a.get("assetId"), "type": a.get("type"), "name": a.get("name")}
              for a in cm.get("assets", []) if a.get("id") or a.get("assetId")]
    asset_ids = [a["assetId"] for a in assets]

    def assign_asset(sig):
        sid = sig.get("id") or sig.get("signalId"); sem = (sig.get("semantic") or sig.get("description") or "").lower()
        for aid in sorted(asset_ids, key=len, reverse=True):          # 1. tag-prefix match
            if sid.startswith(aid):
                return aid
        for a in assets:                                             # 2. asset name / type in the semantic
            if a.get("type") and a["type"] in sem:
                return a["assetId"]
            for tok in (a.get("name") or "").lower().split():
                if len(tok) > 3 and tok in sem:
                    return a["assetId"]
        kw = {"level": "tank", "temperature": "tank", "reactor": "tank", "flow": "pump",
              "pump": "pump", "discharge": "pump", "agitator": "motor", "speed": "motor"}
        for k, ty in kw.items():                                     # 3. semantic keyword → asset type
            if k in sem:
                cand = [a["assetId"] for a in assets if a.get("type") == ty]
                if cand:
                    return cand[0]
        tanks = [a["assetId"] for a in assets if a.get("type") == "tank"]  # 4. fallback: the process vessel
        return tanks[0] if tanks else (asset_ids[0] if asset_ids else None)

    signals = []
    for s in cm.get("signals", []):
        t = (s.get("type") or "").lower()
        kind = "analog-in" if t in ("analog", "real", "analog-in", "analogin") else "discrete-in"
        rng = s.get("range") or [None, None]
        signals.append({"signalId": s.get("id") or s.get("signalId"), "asset": assign_asset(s), "kind": kind,
                        "dataType": "REAL" if kind == "analog-in" else "BOOL", "engUnit": s.get("unit"),
                        "engMin": rng[0] if len(rng) > 0 else None, "engMax": rng[1] if len(rng) > 1 else None,
                        "description": s.get("semantic") or s.get("description"), "access": "read"})
    sigset = {x["signalId"] for x in signals}

    contracts = []
    for c in cm.get("commands", []):
        cid, tgt, typ = c.get("id"), c.get("asset"), (c.get("type") or "").lower()
        fb = None
        if typ == "open" and f"{tgt}_OPEN" in sigset: fb = f"{tgt}_OPEN"
        elif typ == "close" and f"{tgt}_CLOSED" in sigset: fb = f"{tgt}_CLOSED"
        elif typ == "start" and f"{tgt}_RUNNING" in sigset: fb = f"{tgt}_RUNNING"
        contracts.append({"command": cid, "target": tgt, "request": None, "feedback": fb,
                          "permissives": [], "interlocks": []})
    for p in cm.get("permissives", []):
        mt = re.match(r"\s*([A-Za-z0-9_\-]+)\s*(==|!=|<=|>=|<|>)\s*(\S+)", p.get("condition", ""))
        if mt:
            sig, op, val = mt.group(1), mt.group(2), mt.group(3).lower()
            expected = (val == "true") if val in ("true", "false") else (f"{op} {val}" if op in ("<", ">", "<=", ">=") else val)
            for ct in contracts:
                if ct["command"] == p.get("command") and sig in sigset:
                    ct["permissives"].append({"signal": sig, "expected": expected,
                                              "rejectCode": p.get("id"), "message": p.get("condition")})

    def _map_alarm_signal(aid):
        low = aid.lower()
        for s in signals:                                            # direct id containment
            if s["signalId"].lower() in low:
                return s["signalId"]
        by_unit = lambda u: next((s["signalId"] for s in signals if (s.get("engUnit") or "").lower() == u), None)
        if "level" in low: return by_unit("%")
        if "temperature" in low: return by_unit("degc")
        if "pressure" in low: return by_unit("bar")
        if "speed" in low: return by_unit("rpm")
        if "fault" in low:
            toks = set(re.split(r"[_\-]", low))
            return next((s["signalId"] for s in signals if s["signalId"].endswith("_FAULT")
                         and set(re.split(r"[_\-]", s["signalId"].lower())) & toks), None)
        return None

    alarms = []
    for a in cm.get("alarms", []):
        if isinstance(a, dict):
            alarms.append({"alarmId": a.get("id"), "signal": a.get("signal") or _map_alarm_signal(a.get("id", "")),
                           "condition": a.get("condition"), "priority": a.get("priority", "high"),
                           "message": a.get("message") or a.get("id")})
        else:
            alarms.append({"alarmId": a, "signal": _map_alarm_signal(a),
                           "condition": None, "priority": "high", "message": a.replace("_", " ")})

    raw2 = {"name": name, "description": "Canonical model (brain-test package)",
            "controller": {"family": controller}, "assets": assets, "signals": signals,
            "contracts": contracts, "alarms": alarms, "runtimeSeed": raw.get("runtimeSeed")}
    return normalize_machine(raw2, project_id)


def normalize_pdf(data: bytes, project_id: str, controller: str = "UNKNOWN") -> dict:
    """Extract tag tables from a PDF (needs pdfplumber). Each detected table row
    with a header row becomes signal rows."""
    import io
    try:
        import pdfplumber
    except ImportError as e:
        raise RuntimeError("PDF ingestion needs pdfplumber — pip install pdfplumber") from e
    rows = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            for table in (page.extract_tables() or []):
                if len(table) < 2:
                    continue
                header = [str(c).strip() if c else "" for c in table[0]]
                for tr in table[1:]:
                    rows.append({header[i]: tr[i] for i in range(min(len(header), len(tr)))})
    if not rows:
        raise RuntimeError("no tag tables found in the PDF (expected a table with a header row incl. a 'signal'/'tag' column)")
    return rows_to_model(rows, project_id, controller)


# ======================================================================
# 2. SYNTH a machine at scale (for seed projects matching the dashboard)
# ======================================================================
_ASSET_KINDS = ["pump", "valve", "tank", "motor"]


def synth_machine(name: str, subtitle: str, controller: str, n_assets: int,
                  seed: int, project_id: str) -> dict:
    """Deterministically build a plausible machine model of a given size, so a
    seed project shows realistic asset/signal/alarm counts (correct-by-construction)."""
    rng = random.Random(seed)
    assets, signals, contracts, alarms = [], [], [], []
    for i in range(n_assets):
        kind = _ASSET_KINDS[i % len(_ASSET_KINDS)]
        tag = f"{ {'pump':'P','valve':'XV','tank':'TK','motor':'M'}[kind] }{100 + i}"
        assets.append({"assetId": tag, "type": kind, "name": f"{kind.title()} {tag}"})
        if kind == "tank":
            lt = f"LT{100 + i}"
            signals.append({"signalId": lt, "asset": tag, "kind": "analog-in", "dataType": "REAL",
                            "engUnit": "%", "engMin": 0, "engMax": 100, "hh": 95, "h": 85, "l": 15, "ll": 5,
                            "description": "Level", "access": "read"})
            alarms.append({"alarmId": f"ALM_{lt}_HH", "signal": lt, "condition": ">= 95",
                           "priority": "high", "message": f"{tag} level high-high"})
        elif kind == "pump":
            pt = f"PT{100 + i}"
            signals += [
                {"signalId": pt, "asset": tag, "kind": "analog-in", "dataType": "REAL",
                 "engUnit": "bar", "engMin": 0, "engMax": 10, "hh": 9, "h": 8,
                 "description": "Discharge pressure", "access": "read"},
                {"signalId": f"{tag}_RUNNING", "asset": tag, "kind": "discrete-in", "dataType": "BOOL",
                 "description": "Running fb", "access": "read"},
                {"signalId": f"{tag}_FAULT", "asset": tag, "kind": "discrete-in", "dataType": "BOOL",
                 "description": "Fault", "access": "read"},
                {"signalId": f"{tag}_START_REQ", "asset": tag, "kind": "discrete-out", "dataType": "BOOL",
                 "description": "Start", "access": "request"},
                {"signalId": f"{tag}_STOP_REQ", "asset": tag, "kind": "discrete-out", "dataType": "BOOL",
                 "description": "Stop", "access": "request"},
            ]
            contracts += [
                {"command": f"{tag}_START", "target": tag, "request": f"{tag}_START_REQ",
                 "feedback": f"{tag}_RUNNING",
                 "permissives": [{"signal": f"{tag}_FAULT", "expected": False,
                                  "rejectCode": "PERM_FAULT_ACTIVE", "message": f"{tag} must be fault-free."}]},
                {"command": f"{tag}_STOP", "target": tag, "request": f"{tag}_STOP_REQ",
                 "feedback": f"{tag}_RUNNING", "permissives": []},
            ]
            alarms.append({"alarmId": f"ALM_{tag}_FAULT", "signal": f"{tag}_FAULT", "condition": "== true",
                           "priority": "high", "message": f"{tag} motor fault"})
        elif kind == "valve":
            signals += [
                {"signalId": f"{tag}_OPEN", "asset": tag, "kind": "discrete-in", "dataType": "BOOL",
                 "description": "Open limit", "access": "read"},
                {"signalId": f"{tag}_CLOSED", "asset": tag, "kind": "discrete-in", "dataType": "BOOL",
                 "description": "Closed limit", "access": "read"},
                {"signalId": f"{tag}_OPEN_REQ", "asset": tag, "kind": "discrete-out", "dataType": "BOOL",
                 "description": "Open", "access": "request"},
                {"signalId": f"{tag}_CLOSE_REQ", "asset": tag, "kind": "discrete-out", "dataType": "BOOL",
                 "description": "Close", "access": "request"},
            ]
            contracts += [
                {"command": f"{tag}_OPEN", "target": tag, "request": f"{tag}_OPEN_REQ",
                 "feedback": f"{tag}_OPEN", "permissives": []},
                {"command": f"{tag}_CLOSE", "target": tag, "request": f"{tag}_CLOSE_REQ",
                 "feedback": f"{tag}_CLOSED", "permissives": []},
            ]
        else:  # motor
            signals += [
                {"signalId": f"{tag}_SPEED", "asset": tag, "kind": "analog-in", "dataType": "REAL",
                 "engUnit": "rpm", "engMin": 0, "engMax": 1500, "h": 1400,
                 "description": "Speed", "access": "read"},
                {"signalId": f"{tag}_RUNNING", "asset": tag, "kind": "discrete-in", "dataType": "BOOL",
                 "description": "Running", "access": "read"},
            ]
    raw = {"name": name, "description": subtitle,
           "controller": {"family": controller}, "assets": assets, "signals": signals,
           "contracts": contracts, "alarms": alarms}
    return normalize_machine(raw, project_id)


# ======================================================================
# 3. Screen assembly (deterministic) + scope analysis
# ======================================================================
def describe_context(model: dict) -> dict:
    """Human-readable 'what this document means' — derived from the canonical model,
    so it's a real reading of the uploaded content (not a template)."""
    from collections import Counter
    atypes = Counter(a.get("type", "asset") for a in model["assets"])
    # measured variables grouped by engineering unit
    meas = Counter()
    for s in model["signals"]:
        if s.get("kind") == "analog-in" and s.get("engUnit"):
            meas[s["engUnit"]] += 1
    unit_name = {"%": "level", "bar": "pressure", "psi": "pressure", "degC": "temperature",
                 "m3/h": "flow", "L/min": "flow", "rpm": "speed", "A": "current", "kW": "power",
                 "NTU": "turbidity", "pH": "pH", "Pa": "differential pressure", "uS/cm": "conductivity",
                 "mbar": "pressure", "kg": "weight"}
    instruments = [f"{n}× {unit_name.get(u, u)} ({u})" for u, n in meas.most_common()]
    # control
    starts = [c for c in model["commands"] if c["command_id"].endswith("_START")]
    valves = [c for c in model["commands"] if c["command_id"].endswith(("_OPEN", "_CLOSE"))]
    alarm_pri = Counter(a.get("priority", "?") for a in model["alarms"])

    asset_phrase = ", ".join(f"{n} {t}{'s' if n > 1 else ''}" for t, n in atypes.most_common())
    narrative = (
        f"{model['name']} is a {atypes.most_common(1)[0][0] if atypes else 'process'}-centric unit on a "
        f"{model.get('controller', 'controller')}. It contains {len(model['assets'])} assets ({asset_phrase}), "
        f"instrumented with {len(model['signals'])} tags measuring "
        f"{', '.join(instruments) if instruments else 'discrete states'}. "
        f"Operators can run {len(model['commands'])} commands "
        f"({len(starts)} motor start/stop, {len(valves)} valve open/close), gated by "
        f"{len(model['permissives'])} permissives. {len(model['alarms'])} alarms are defined"
        + (f" ({', '.join(f'{n} {p}' for p, n in alarm_pri.most_common())})." if alarm_pri else ".")
    )
    # what an operator needs to see/do + which screens are worth building (ISA-101)
    operator_needs = []
    if any(u == "%" for u in meas):
        operator_needs.append("monitor levels vs HH/LL alarm limits")
    if any(u in ("bar", "psi") for u in meas):
        operator_needs.append("watch process pressure trends")
    if any(u == "degC" for u in meas):
        operator_needs.append("track temperatures")
    if starts:
        operator_needs.append(f"start/stop {len(starts)} motor(s) through the permissive gate")
    if valves:
        operator_needs.append(f"open/close {len(valves)} valve(s)")
    if model["alarms"]:
        operator_needs.append(f"acknowledge {len(model['alarms'])} alarms")
    recommended = [{"screen": "Line overview", "why": "one page showing every asset, alarms on top"}]
    for t, n in atypes.most_common():
        recommended.append({"screen": f"{t.title()} faceplate", "why": f"{n} {t}(s) — detailed control + trends"})
    if model["alarms"]:
        recommended.append({"screen": "Alarm summary", "why": f"{len(model['alarms'])} alarms across the unit"})

    return {
        "identity": model["name"], "controller": model.get("controller"),
        "narrative": narrative,
        "asset_breakdown": dict(atypes),
        "instrumentation": instruments,
        "control": {"commands": len(model["commands"]), "starts": len(starts),
                    "valves": len(valves), "permissives": len(model["permissives"]),
                    "interlocks": len(model["interlocks"])},
        "alarms": dict(alarm_pri),
        "operator_needs": operator_needs,
        "recommended_screens": recommended,
        "counts": model["counts"],
        "assets": [{"id": a["asset_id"], "type": a.get("type"),
                    "signals": sum(1 for s in model["signals"] if s.get("asset") == a["asset_id"]),
                    "commands": sum(1 for c in model["commands"] if c.get("target_asset") == a["asset_id"])}
                   for a in model["assets"]],
    }


_COMP_HUMAN = {"StatusHeader": "KPI status header", "AlarmBanner": "alarm banner", "TankLevel": "level gauge", "PressureGauge": "pressure gauge",
               "NumericValue": "numeric reading", "MotorStarter": "motor start/stop control",
               "ValveStatus": "valve open/close control", "PermissivePanel": "permissive gate", "Trend": "live trend"}


def explain_screen(screen: dict, model: dict) -> str:
    """Plain-language description of a generated screen (shown under the HMI)."""
    from collections import Counter
    comp = Counter(w["component"] for w in screen["widgets"])
    parts = [f"{n}× {_COMP_HUMAN.get(c, c)}{'s' if n > 1 and not _COMP_HUMAN.get(c, c).endswith('s') else ''}"
             for c, n in comp.most_common()]
    sigs = sorted({s for w in screen["widgets"] for s in w.get("boundSignals", [])})
    ev = sum(len(w.get("usedEvidenceIds", [])) for w in screen["widgets"])
    cmds = sorted({c for w in screen["widgets"] for c in w.get("boundCommands", []) if c != "ack"})
    scope = screen.get("scope")
    where = f"the {scope} faceplate" if scope and scope != "machine" else "a line overview"
    txt = (f"This is {where}. It has {len(screen['widgets'])} widgets — {', '.join(parts)} — "
           f"bound to {len(sigs)} real signals with {ev} evidence links. ")
    if cmds:
        txt += f"Operators can command {', '.join(cmds)}, each gated by its permissive contract. "
    txt += "Every binding was validated against the canonical model — nothing is invented."
    return txt


def edit_help(model: dict, screen: Optional[dict] = None) -> dict:
    """Copilot guidance: what you can add/remove on THIS machine, with examples."""
    on = {s for w in (screen or {}).get("widgets", []) for s in w.get("boundSignals", [])}
    analog = [s["signalId"] for s in model["signals"] if s.get("kind") == "analog-in"]
    addable = [s for s in analog if s not in on][:8]
    present = sorted({w["component"] for w in (screen or {}).get("widgets", [])})
    examples = []
    if analog:
        examples.append(f"add trend for {analog[0]}")   # a trend can always be added
    if addable:
        examples.append(f"add value for {addable[0]}")
    if "AlarmBanner" in present:
        examples.append("remove alarms")
    if "PressureGauge" in present:
        examples.append("remove pressure")
    return {"can_add_signals": addable, "removable": [_COMP_HUMAN.get(c, c) for c in present], "examples": examples}


def analyze_scope(request: str, model: dict) -> tuple[Optional[str], str, list]:
    req = request.lower()
    reqn = re.sub(r"[^a-z0-9]", "", req)
    ids = {a["asset_id"]: a for a in model["assets"]}
    by_id = [aid for aid in ids if re.sub(r"[^a-z0-9]", "", aid.lower()) in reqn]
    type_words = {"pump": "pump", "motor": "motor", "tank": "tank", "level": "tank", "valve": "valve"}
    hit_types = {type_words[w] for w in type_words if re.search(rf"\b{w}\b", req)}
    by_type = [aid for aid, a in ids.items() if a.get("type") in hit_types]
    matched = list(dict.fromkeys(by_id + by_type))
    overview = any(re.search(rf"\b{w}\b", req)
                   for w in ["line", "overview", "all", "whole", "everything", "plant", "summary"])
    if overview or len(matched) != 1:
        return None, ("overview keyword" if overview else f"{len(matched)} assets matched"), matched
    return matched[0], ("named" if matched[0] in by_id else "by type"), matched


def assemble_screen(model: dict, scope: Optional[str] = None) -> dict:
    sigset = {s["signalId"] for s in model["signals"]}
    cmdset = {c["command_id"] for c in model["commands"]}
    sig_by_asset: dict = {}
    for s in model["signals"]:
        sig_by_asset.setdefault(s.get("asset"), []).append(s)
    cmd_by_target: dict = {}
    for c in model["commands"]:
        cmd_by_target.setdefault(c.get("target_asset"), []).append(c["command_id"])
    ev = {s["signalId"]: f"ev::{model['projectId']}::{s['signalId']}" for s in model["signals"]}
    scope_assets = [a for a in model["assets"] if not scope or a["asset_id"] == scope]

    widgets, dropped = [], []
    _sec = {"s": "System"}

    def add(component, props, bsigs, bcmds=()):
        bs = [s for s in bsigs if s in sigset]
        dropped.extend([s for s in bsigs if s and s not in sigset])
        widgets.append({"component": component, "props": {k: v for k, v in props.items() if v is not None},
                        "boundSignals": bs, "boundCommands": [c for c in bcmds if c in cmdset],
                        "usedEvidenceIds": [ev[s] for s in bs if s in ev], "section": _sec["s"]})

    # ISA-101 KPI status header (top strip)
    n_alarm = len({a["signal"] for a in model["alarms"] if a["signal"] in sigset})
    widgets.append({"component": "StatusHeader", "section": "System",
                    "props": {"machine": model["name"], "controller": model.get("controller"),
                              "assets": len(scope_assets), "alarmSources": n_alarm,
                              "commands": sum(len(cmd_by_target.get(a["asset_id"], [])) for a in scope_assets)},
                    "boundSignals": [], "boundCommands": [], "usedEvidenceIds": []})

    alarm_sigs = sorted({a["signal"] for a in model["alarms"] if a["signal"] in sigset})
    if model["alarms"]:
        widgets.append({"component": "AlarmBanner", "section": "System",
                        "props": {"scope": "machine" if not scope else "asset", "target": scope},
                        "boundSignals": alarm_sigs, "boundCommands": ["ack"],
                        "usedEvidenceIds": [ev[s] for s in alarm_sigs if s in ev]})

    def analog_widget(s, atype):
        """Pick the right analog widget by engineering unit (surfaces EVERY reading)."""
        sid, unit = s["signalId"], (s.get("engUnit") or "").lower()
        rng = [s.get("engMin"), s.get("engMax")]
        marks = {k: s.get(k) for k in ("hh", "h", "l", "ll") if s.get(k) is not None}
        if unit == "%":
            add("TankLevel", {"binding": sid, "unit": s.get("engUnit"), "range": rng, "marks": marks}, [sid])
        elif unit in ("bar", "psi", "kpa", "mbar", "pa"):
            add("PressureGauge", {"binding": sid, "unit": s.get("engUnit"), "range": rng, "marks": marks}, [sid])
        else:  # flow, temp, speed, turbidity, weight, current, …
            add("NumericValue", {"binding": sid, "unit": s.get("engUnit"), "range": rng, "marks": marks}, [sid])

    for a in scope_assets:
        aid, atype = a["asset_id"], a.get("type")
        _sec["s"] = f"{aid} · {atype}"
        asigs = sig_by_asset.get(aid, [])
        acmds = cmd_by_target.get(aid, [])
        analogs = [s for s in asigs if s.get("kind") == "analog-in"]

        # 1. control / status
        if atype in ("pump", "motor") and ((f"{aid}_RUNNING" in sigset) or any(c.endswith(("_START", "_STOP")) for c in acmds)):
            running = f"{aid}_RUNNING" if f"{aid}_RUNNING" in sigset else None
            fault = f"{aid}_FAULT" if f"{aid}_FAULT" in sigset else None
            add("MotorStarter", {"target": aid, "running": running, "fault": fault,
                                 "startCommand": next((c for c in acmds if c.endswith("_START")), None),
                                 "stopCommand": next((c for c in acmds if c.endswith("_STOP")), None)},
                [x for x in (running, fault) if x], [c for c in acmds if c.endswith(("_START", "_STOP"))])
        elif atype == "valve":
            op = f"{aid}_OPEN" if f"{aid}_OPEN" in sigset else None
            cl = f"{aid}_CLOSED" if f"{aid}_CLOSED" in sigset else None
            add("ValveStatus", {"target": aid, "open": op, "closed": cl,
                                "openCommand": next((c for c in acmds if c.endswith("_OPEN")), None),
                                "closeCommand": next((c for c in acmds if c.endswith("_CLOSE")), None)},
                [x for x in (op, cl) if x], [c for c in acmds if c.endswith(("_OPEN", "_CLOSE"))])

        # 2. EVERY analog reading gets a widget (level, pressure, flow, temp, speed, turbidity…)
        for s in analogs:
            analog_widget(s, atype)

        # 3. on a single-asset faceplate, add a live trend of its analogs
        if scope and analogs:
            series = [s["signalId"] for s in analogs[:4]]
            add("Trend", {"series": series, "windowSec": 300}, series)

        # 4. permissive panels
        for c in acmds:
            psigs = [p["signal"] for p in model["permissives"] if p["command"] == c and p["signal"] in sigset]
            if psigs:
                add("PermissivePanel", {"command": c, "showInterlocks": True}, psigs)

    return {
        "$schema": "canon.hmi_screen.v2", "projectId": model["projectId"],
        "pageTitle": (f"{scope} faceplate" if scope else f"{model['name']} — overview"),
        "scope": scope or "machine",
        "layout": "alarms top · analog left · commands right · grouped by asset",
        "assembledBy": "deterministic — every binding is a real signal/command with evidence",
        "widgets": widgets,
        "validation": {"ok": len(dropped) == 0, "dropped": sorted(set(dropped)),
                       "widgets": len(widgets), "with_evidence": sum(1 for w in widgets if w["usedEvidenceIds"])},
    }


# ======================================================================
# 4. Prompt-driven EDIT (deterministic ops, validated)
# ======================================================================
_COMPONENT_WORDS = {"alarm": "AlarmBanner", "pressure": "PressureGauge", "trend": "Trend",
                    "motor": "MotorStarter", "starter": "MotorStarter",
                    "valve": "ValveStatus", "level": "TankLevel", "tank": "TankLevel",
                    "permissive": "PermissivePanel", "interlock": "PermissivePanel",
                    "value": "NumericValue", "numeric": "NumericValue", "reading": "NumericValue",
                    "gauge": "PressureGauge"}


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def apply_edit(screen: dict, model: dict, prompt: str) -> dict:
    """Natural-language edit of a screen. Deterministic + validated: an edit can
    add/remove any widget type but can NEVER bind a tag not in the model."""
    req = prompt.lower()
    sigset = {s["signalId"] for s in model["signals"]}
    sig_by = {s["signalId"]: s for s in model["signals"]}
    widgets = [dict(w) for w in screen["widgets"]]
    applied, rejected = [], []
    ev = lambda sid: f"ev::{model['projectId']}::{sid}"

    def find_signals():
        reqn = _norm(prompt)
        return [s for s in model["signals"] if _norm(s["signalId"]) in reqn]

    def mk(comp, sid):
        s = sig_by[sid]; u = (s.get("engUnit") or "").lower()
        if comp == "gauge/auto":
            comp = "PressureGauge" if u in ("bar", "psi", "kpa", "mbar") else ("TankLevel" if u == "%" else "NumericValue")
        props = ({"series": [sid], "windowSec": 300} if comp == "Trend"
                 else {"binding": sid, "unit": s.get("engUnit"), "range": [s.get("engMin"), s.get("engMax")]})
        return {"component": comp, "props": props, "boundSignals": [sid],
                "boundCommands": [], "usedEvidenceIds": [ev(sid)]}

    is_remove = bool(re.search(r"\b(remove|hide|delete|drop|without)\b", req))
    is_add = bool(re.search(r"\b(add|show|include|display|put|with)\b", req)) and not is_remove

    # REMOVE any component named in the prompt
    if is_remove:
        for word, comp in _COMPONENT_WORDS.items():
            if re.search(rf"\b{word}", req):
                before = len(widgets)
                widgets = [w for w in widgets if w["component"] != comp]
                if len(widgets) < before:
                    applied.append(f"removed {comp}")

    # ADD a widget for each real signal named (widget kind by keyword, else auto)
    if is_add:
        sigs = find_signals()
        want = ("Trend" if "trend" in req else "gauge/auto" if ("gauge" in req or "pressure" in req)
                else "NumericValue" if ("value" in req or "reading" in req or "numeric" in req) else "gauge/auto")
        if sigs:
            for s in sigs:
                widgets.append(mk(want, s["signalId"]))
                applied.append(f"added {want.replace('gauge/auto','widget')} for {s['signalId']}")
        else:
            rejected.append("nothing added — no signal from this machine was named in the request")

    # GUARD: any tag-looking token not in the model is refused (never invented)
    for tok in re.findall(r"\b[A-Za-z]{1,4}[-_]?\d{2,4}[A-Za-z_]*\b", prompt):
        if tok not in sigset and tok.upper() not in sigset:
            rejected.append(f"'{tok}' is not in the machine model — refused (no invented tags)")

    why = None
    if not applied:
        if any("not in the machine model" in r for r in rejected):
            why = ("You named a tag that isn't in this machine's model, so I refused it — "
                   "I only ever bind to real signals (that's the no-hallucination guarantee).")
        else:
            why = ("I couldn't find a signal or component from this machine in your request. "
                   "Name a real tag (see the suggestions), or say remove <alarms/pressure/trend>.")

    new = dict(screen)
    new["widgets"] = widgets
    new["validation"] = {"ok": True, "dropped": [], "widgets": len(widgets),
                         "with_evidence": sum(1 for w in widgets if w.get("usedEvidenceIds"))}
    return {"screen": new, "applied": applied, "rejected": sorted(set(rejected)),
            "why": why, "help": edit_help(model, new)}
