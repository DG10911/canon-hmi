#!/usr/bin/env python3
"""
CANON super-synthetic dataset generator  (PS2)
------------------------------------------------
Deterministic, seeded, pure-stdlib. "Correct by construction": every training
pair is generated FROM a machine model that CANON's deterministic engine would
itself accept, so labels never require a human and never hallucinate.

Outputs (into ./out):
  machines.jsonl              - N synthetic machines (assets/signals/cmds/alarms/io)
  intents_train.jsonl         - NL -> validated intent JSON pairs (+ hard negatives)
  intents_eval.jsonl          - held-out eval split
  runtime_traces.jsonl        - deterministic simulator traces (regression fixtures)
  manifest.json               - counts, splits, class balance, provenance

Truth rule: tags, addresses, physics are CANON-authored (PROPOSED). Controller
families are family-level references only (VERIFIED families: M262/M580/M241/M251/M340).
No Schneider proprietary internals.
"""
import json, random, hashlib, os, argparse

VERIFIED_CONTROLLERS = ["M262", "M580", "M241", "M251", "M340"]
REGISTRY = ["TankLevel","PressureGauge","MotorStarter","ValveStatus","AlarmBanner",
            "AlarmList","Trend","NumericValue","NavHeader","PermissivePanel","QualityBadge"]

ARCHETYPES = ["transfer_line","mixer","packaging_line","pump_station","heat_exchanger"]

def h(*parts):
    return "sha256:" + hashlib.sha256("|".join(map(str,parts)).encode()).hexdigest()[:16]

def mk_signal(sid, asset, kind, dtype, unit=None, emin=0, emax=100, access="read", **kw):
    s = {"signalId": sid, "asset": asset, "kind": kind, "dataType": dtype, "access": access}
    if unit is not None:
        s.update({"engUnit": unit, "engMin": emin, "engMax": emax})
    s.update(kw); return s

def build_machine(rng, idx):
    arche = rng.choice(ARCHETYPES)
    unit = 100 + idx  # e.g. 137 -> TK-437 style numbering
    ctrl = rng.choice(VERIFIED_CONTROLLERS)
    mid = f"mch_{arche}_{unit}"
    assets, signals, commands, contracts, alarms, io = [], [], [], [], [], []
    coil = di = hr = 0
    def add_io(sid, area):
        nonlocal coil, di, hr
        if area == "coil": a = coil; coil += 1
        elif area == "discrete-input": a = di; di += 1
        else: a = hr; hr += 1
        io.append({"signalId": sid, "area": area, "address": a, "dtype": "bool" if area != "holding" else "uint16"})

    def add_pump(tag, tank_level_tag=None, valve_open_tag=None):
        assets.append({"assetId": tag, "type": "pump", "name": f"Pump {tag}"})
        run, flt, es = f"{tag}_RUNNING", f"{tag}_FAULT", f"{tag}_ESTOP_OK"
        sreq, streq = f"{tag}_START_REQ", f"{tag}_STOP_REQ"
        signals.extend([
            mk_signal(run, tag, "discrete-in", "BOOL"),
            mk_signal(flt, tag, "discrete-in", "BOOL"),
            mk_signal(es, tag, "discrete-in", "BOOL"),
            mk_signal(sreq, tag, "discrete-out", "BOOL", access="request"),
            mk_signal(streq, tag, "discrete-out", "BOOL", access="request"),
        ])
        for s,a in [(run,"discrete-input"),(flt,"discrete-input"),(es,"discrete-input"),(sreq,"coil"),(streq,"coil")]:
            add_io(s,a)
        perms = []
        if valve_open_tag: perms.append({"signal": valve_open_tag, "expected": True, "rejectCode": "PERM_VALVE_CLOSED"})
        if tank_level_tag:
            perms.append({"signal": tank_level_tag, "expected": "> 5", "rejectCode": "PERM_LEVEL_LOW"})
            perms.append({"signal": tank_level_tag, "expected": "< 95", "rejectCode": "PERM_LEVEL_HIGH"})
        perms.append({"signal": flt, "expected": False, "rejectCode": "PERM_FAULT_ACTIVE"})
        commands.extend([f"{tag}_START", f"{tag}_STOP"])
        contracts.append({"command": f"{tag}_START","target": tag,"request": sreq,"feedback": run,
                          "permissives": perms,"interlocks":[{"signal": es,"expected": True,"rejectCode":"IL_ESTOP"}],
                          "timeoutSec": 5})
        contracts.append({"command": f"{tag}_STOP","target": tag,"request": streq,"feedback": run,"permissives":[],"timeoutSec":5})
        alarms.append({"alarmId": f"ALM_{flt}","signal": flt,"condition":"== true","priority":"high","class":"device","message": f"{tag} motor fault"})
        return run

    def add_valve(tag, block_if_running=None):
        assets.append({"assetId": tag, "type": "valve", "name": f"Valve {tag}"})
        opn, cls = f"{tag}_OPEN", f"{tag}_CLOSED"
        oreq, creq = f"{tag}_OPEN_REQ", f"{tag}_CLOSE_REQ"
        signals.extend([
            mk_signal(opn, tag, "discrete-in", "BOOL"), mk_signal(cls, tag, "discrete-in", "BOOL"),
            mk_signal(oreq, tag, "discrete-out", "BOOL", access="request"),
            mk_signal(creq, tag, "discrete-out", "BOOL", access="request")])
        for s,a in [(opn,"discrete-input"),(cls,"discrete-input"),(oreq,"coil"),(creq,"coil")]:
            add_io(s,a)
        commands.extend([f"{tag}_OPEN", f"{tag}_CLOSE"])
        contracts.append({"command": f"{tag}_OPEN","target": tag,"request": oreq,"feedback": opn,"permissives":[],"timeoutSec":8})
        cperm = []
        if block_if_running: cperm.append({"signal": block_if_running,"expected": False,"rejectCode":"PERM_PUMP_RUNNING"})
        contracts.append({"command": f"{tag}_CLOSE","target": tag,"request": creq,"feedback": cls,"permissives": cperm,"timeoutSec":8})
        return opn

    def add_tank(tag):
        assets.append({"assetId": tag, "type": "tank", "name": f"Tank {tag}"})
        lt = f"LT{tag[-3:]}"
        signals.append(mk_signal(lt, tag, "analog-in", "REAL", "%", 0, 100, hh=95, h=85, l=15, ll=5))
        add_io(lt, "holding")
        alarms.append({"alarmId": f"ALM_{lt}_HH","signal": lt,"condition":">= 95","priority":"high","class":"level","message": f"{tag} level high-high"})
        alarms.append({"alarmId": f"ALM_{lt}_LL","signal": lt,"condition":"<= 5","priority":"high","class":"level","message": f"{tag} level low-low"})
        return lt

    def add_pressure(tag_asset):
        pt = f"PT{unit}"
        signals.append(mk_signal(pt, tag_asset, "analog-in", "REAL", "bar", 0, 10, hh=9.0, h=8.0))
        add_io(pt, "holding")
        alarms.append({"alarmId": f"ALM_{pt}_HH","signal": pt,"condition":">= 9.0","priority":"high","class":"pressure","message": f"{pt} pressure high-high"})
        return pt

    def add_temp(tag_asset):
        tt = f"TT{unit}"
        signals.append(mk_signal(tt, tag_asset, "analog-in", "REAL", "degC", 0, 150, hh=140, h=120))
        add_io(tt, "holding")
        return tt

    # archetype wiring
    if arche == "transfer_line":
        tk=f"TK-{unit}"; pump=f"P{unit}"; xv=f"XV{unit}"
        lt=add_tank(tk); vo=add_valve(xv, block_if_running=f"{pump}_RUNNING"); add_pressure(pump); add_pump(pump, lt, vo)
    elif arche == "mixer":
        tk=f"MX-{unit}"; ag=f"AG{unit}"; xin=f"XV{unit}A"; xout=f"XV{unit}B"
        lt=add_tank(tk); add_temp(tk); add_valve(xin); vo=add_valve(xout, block_if_running=f"{ag}_RUNNING"); add_pump(ag, lt, None)
    elif arche == "packaging_line":
        cv=f"CV{unit}"; rej=f"XV{unit}"
        add_pump(cv); add_valve(rej)
        signals.append(mk_signal(f"CNT{unit}", cv, "analog-in", "INT", "pcs", 0, 100000)); add_io(f"CNT{unit}","holding")
    elif arche == "pump_station":
        p1=f"P{unit}A"; p2=f"P{unit}B"; add_pressure(p1); add_pump(p1); add_pump(p2)
    else:  # heat_exchanger
        hx=f"HX-{unit}"; cv=f"TCV{unit}"
        add_temp(hx); add_temp(hx); add_valve(cv)
        signals.append(mk_signal(f"FT{unit}", hx, "analog-in", "REAL", "m3h", 0, 50)); add_io(f"FT{unit}","holding")

    machine = {
        "machineId": mid, "archetype": arche, "name": f"{arche.replace('_',' ').title()} {unit}",
        "controller": {"family": ctrl, "note": "family-level reference only (VERIFIED family)", "opcuaPort": 4840, "modbusPort": 502},
        "revision": {"revisionId": "rev-1", "contentHash": h(mid, arche, unit)},
        "assets": assets, "signals": signals, "commands": commands, "commandContracts": contracts,
        "alarms": alarms, "io": io, "truthStatus": "PROPOSED"
    }
    return machine

# ---------------- intent synthesis (correct by construction) ----------------
GEN_TEMPLATES = ["make an operator screen for {a}","generate an HMI for {a}","build a faceplate for {a}",
    "I need a display for {a}","create a screen showing {a}","show me {a} on an operator panel"]
CMD_TEMPLATES = {"start":["start {t}","turn on {t}","run {t}"],"stop":["stop {t}","turn off {t}","shut down {t}"],
    "open":["open {t}","open valve {t}"],"close":["close {t}","close valve {t}"]}
ALARM_TEMPLATES = ["why is {alm} active","explain the {alm} alarm","what does {alm} mean"]
CHANGE_TEMPLATES = ["change {sig} range to 0-{v} {u}","re-range {sig} to 0-{v} {u}","update {sig} span to 0-{v} {u}"]
BOGUS_TAGS = ["MADE_UP_TAG","FLOW_9999","XT_NONEXISTENT","PUMP_GHOST","TEMP_FAKE","LT_000"]

def component_for(sig):
    u = sig.get("engUnit")
    if u == "bar": return "PressureGauge"
    if u == "%": return "TankLevel"
    if u in ("degC","m3h","pcs") or sig["dataType"] in ("INT","REAL"): return "NumericValue"
    return "NumericValue"

def synth_intents(rng, m):
    ex = []
    sigs = m["signals"]; analog = [s for s in sigs if "engUnit" in s]
    pumps = [a for a in m["assets"] if a["type"] == "pump"]
    valves = [a for a in m["assets"] if a["type"] == "valve"]

    def paraphrases(templates, **kw):
        # 2 distinct paraphrases per positive case for NL diversity
        picks = rng.sample(templates, min(2, len(templates)))
        return [t.format(**kw) for t in picks]

    # generate_hmi (positive) -- one screen per asset, paraphrased
    for asset in m["assets"]:
        target = asset["assetId"]
        tsig = [s for s in analog if s["asset"] == target]
        widgets = []
        for s in tsig[:3]:
            widgets.append({"id": f"w.{s['signalId'].lower()}","component": component_for(s),
                            "binding": s["signalId"],"unit": s.get("engUnit"),"range": [s.get("engMin"), s.get("engMax")]})
        if asset["type"] == "pump":
            widgets.append({"id": f"w.{target.lower()}","component":"MotorStarter","target": target,
                            "running": f"{target}_RUNNING","fault": f"{target}_FAULT",
                            "startCommand": f"{target}_START","stopCommand": f"{target}_STOP"})
        if asset["type"] == "valve":
            widgets.append({"id": f"w.{target.lower()}","component":"ValveStatus","target": target,
                            "open": f"{target}_OPEN","closed": f"{target}_CLOSED",
                            "openCommand": f"{target}_OPEN","closeCommand": f"{target}_CLOSE"})
        if not widgets: continue
        for txt in paraphrases(GEN_TEMPLATES, a=target):
            ex.append({"machineId": m["machineId"],"intentType":"generate_hmi","input": txt,
                "intent": {"pageId": f"hmi.{target.lower()}.operator","layout":"faceplate-grid","widgets": widgets,
                           "usedSignalIds": sorted({w.get("binding") or w.get("running") for w in widgets if w.get("binding") or w.get("running")}),
                           "usedEvidenceIds": [], "unknowns": []}, "label":"accept"})

    # command_request (positive + permissive-reject) -- every pump & valve command
    for p in pumps:
        ctr = [c for c in m["commandContracts"] if c["command"]==f"{p['assetId']}_START"][0]
        for txt in paraphrases(CMD_TEMPLATES["start"], t=p["assetId"]):
            ex.append({"machineId": m["machineId"],"intentType":"command_request","input": txt,
                "intent": {"command": f"{p['assetId']}_START","target": p["assetId"],
                           "expectedPermissives": ctr["permissives"],"usedSignalIds": [f"{p['assetId']}_START_REQ"], "unknowns": []},
                "label":"accept"})
        ex.append({"machineId": m["machineId"],"intentType":"command_request",
            "input": rng.choice(CMD_TEMPLATES["stop"]).format(t=p["assetId"]),
            "intent": {"command": f"{p['assetId']}_STOP","target": p["assetId"],"usedSignalIds": [f"{p['assetId']}_STOP_REQ"],"unknowns": []},
            "label":"accept"})
        for perm in ctr["permissives"]:
            ex.append({"machineId": m["machineId"],"intentType":"command_request",
                "input": f"start {p['assetId']} even though {perm['signal']} is not satisfied",
                "intent": {"command": f"{p['assetId']}_START","target": p["assetId"],"predictedResult":"reject",
                           "rejectCode": perm["rejectCode"],"note":"PLC authoritative; CANON pre-check advisory only","unknowns": []},
                "label":"reject_expected"})
    for v in valves:
        for verb, cmd in [("open","OPEN"),("close","CLOSE")]:
            ex.append({"machineId": m["machineId"],"intentType":"command_request",
                "input": rng.choice(CMD_TEMPLATES[verb]).format(t=v["assetId"]),
                "intent": {"command": f"{v['assetId']}_{cmd}","target": v["assetId"],"usedSignalIds": [f"{v['assetId']}_{cmd}_REQ"],"unknowns": []},
                "label":"accept"})

    # explain_alarm (positive) -- every alarm
    for alm in m["alarms"]:
        ex.append({"machineId": m["machineId"],"intentType":"explain_alarm",
            "input": rng.choice(ALARM_TEMPLATES).format(alm=alm["alarmId"]),
            "intent": {"alarmId": alm["alarmId"],"signal": alm["signal"],"condition": alm["condition"],
                       "priority": alm["priority"],"usedEvidenceIds": [], "unknowns": []}, "label":"accept"})

    # change_impact (positive) -- every analog signal
    for s in analog:
        newmax = int((s.get("engMax") or 10)) + rng.choice([6,4,8,10])
        ex.append({"machineId": m["machineId"],"intentType":"change_impact",
            "input": rng.choice(CHANGE_TEMPLATES).format(sig=s["signalId"], v=newmax, u=s.get("engUnit","")),
            "intent": {"changedEntity": f"signal:{s['signalId']}","field":"engMax","from": s.get("engMax"),"to": newmax,
                       "impactEdges": ["BINDS","ALARMS","SCALES","READS","TESTS","DOCUMENTS"],
                       "requiresEngineerApproval": True, "unknowns": []}, "label":"accept"})

    # HARD NEGATIVES: invented tag / command / product -> refusal (the CANON guarantee)
    for bogus in rng.sample(BOGUS_TAGS, 2):
        ex.append({"machineId": m["machineId"],"intentType":"generate_hmi",
            "input": f"add a gauge bound to {bogus}",
            "intent": {"pageId": None,"widgets": [],"usedSignalIds": [],"unknowns": [{"ref": bogus,"status":"UNKNOWN","code":"TAG_MISSING","reason": f"{bogus} is not present in the machine model; CANON refuses to invent it."}]},
            "label":"refuse"})
    ex.append({"machineId": m["machineId"],"intentType":"command_request",
        "input": "engage the turbo boost sequence",
        "intent": {"command": None,"unknowns": [{"ref":"TURBO_BOOST","status":"UNKNOWN","code":"COMMAND_MISSING","reason":"No such command in the approved model."}]},
        "label":"refuse"})
    ex.append({"machineId": m["machineId"],"intentType":"generate_hmi",
        "input": "use the Schneider AutoScreen AI module to build this",
        "intent": {"pageId": None,"widgets": [],"unknowns": [{"ref":"AutoScreen AI module","status":"UNKNOWN","code":"EVIDENCE_MISSING","reason":"No evidence of such a Schneider product; CANON will not assert an unverified capability."}]},
        "label":"refuse"})
    return ex

def sim_trace(m, ticks=50, seed=401):
    """Deterministic runtime trace for a machine's first analog + pump if present."""
    rng = random.Random(seed + hash(m["machineId"]) % 1000)
    analog = [s for s in m["signals"] if "engUnit" in s]
    pumps = [a for a in m["assets"] if a["type"]=="pump"]
    if not analog: return None
    a = analog[0]; lvl = 60.0; running = bool(pumps)
    frames = []
    for t in range(ticks):
        if running: lvl = min(a.get("engMax",100), lvl + 0.15*0.2*100/ (a.get("engMax",100) or 100) * 5)
        else: lvl = max(0, lvl - 0.02)
        frames.append({"t": round(t*0.2,1), a["signalId"]: round(lvl,2), "running": running})
        if lvl >= (a.get("hh") or a.get("engMax",100)): running = False  # HH trips
    return {"machineId": m["machineId"],"signal": a["signalId"],"seed": seed,"dt": 0.2,"frames": frames}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--machines", type=int, default=250)
    ap.add_argument("--seed", type=int, default=401)
    ap.add_argument("--eval-frac", type=float, default=0.1)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "out"))
    args = ap.parse_args()
    rng = random.Random(args.seed)
    os.makedirs(args.out, exist_ok=True)

    machines = [build_machine(rng, i) for i in range(args.machines)]
    all_intents, traces = [], []
    for m in machines:
        all_intents.extend(synth_intents(rng, m))
        tr = sim_trace(m)
        if tr: traces.append(tr)

    rng.shuffle(all_intents)
    n_eval = int(len(all_intents) * args.eval_frac)
    eval_split, train_split = all_intents[:n_eval], all_intents[n_eval:]

    def dump(name, rows):
        p = os.path.join(args.out, name)
        with open(p, "w") as f:
            for r in rows: f.write(json.dumps(r) + "\n")
        return p, os.path.getsize(p)

    mp = dump("machines.jsonl", machines)
    tp = dump("intents_train.jsonl", train_split)
    ep = dump("intents_eval.jsonl", eval_split)
    rp = dump("runtime_traces.jsonl", traces)

    from collections import Counter
    label_bal = Counter(x["label"] for x in all_intents)
    type_bal = Counter(x["intentType"] for x in all_intents)
    arche_bal = Counter(m["archetype"] for m in machines)
    manifest = {
        "generated": "2026-09-10", "seed": args.seed, "authority": "PROPOSED / synthetic / correct-by-construction",
        "counts": {"machines": len(machines), "intents_total": len(all_intents),
                   "intents_train": len(train_split), "intents_eval": len(eval_split),
                   "signals_total": sum(len(m["signals"]) for m in machines),
                   "commands_total": sum(len(m["commands"]) for m in machines),
                   "alarms_total": sum(len(m["alarms"]) for m in machines),
                   "runtime_traces": len(traces)},
        "label_balance": dict(label_bal), "intentType_balance": dict(type_bal), "archetype_balance": dict(arche_bal),
        "files": {"machines.jsonl": mp[1], "intents_train.jsonl": tp[1], "intents_eval.jsonl": ep[1], "runtime_traces.jsonl": rp[1]},
        "guarantee": "Every 'accept' pair binds only to signals present in its machine model. Every 'refuse' pair references a tag/command absent from the model and returns UNKNOWN. No pair invents a Schneider capability.",
        "verifiedControllerFamilies": VERIFIED_CONTROLLERS
    }
    with open(os.path.join(args.out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print(json.dumps(manifest["counts"], indent=2))
    print("label_balance:", dict(label_bal))
    print("intentType_balance:", dict(type_bal))
    print("bytes:", {k: v for k, v in manifest["files"].items()})

if __name__ == "__main__":
    main()
