#!/usr/bin/env python3
"""CANON Platform — backend API.

Flow (all reusing the CANON engine):
  upload machine project  -> normalize -> canonical model (the "brain" context)
  prompt "pump page"       -> deterministic screen assembly from the model
  prompt "add a trend..."  -> validated edit of the screen (no invented tags)

Serves the single-page UI at /. Projects persist under projects/.

Run:  pip install -r requirements.txt ; python3 app.py   (-> http://localhost:8090)
"""
from __future__ import annotations
import json
import os
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

import platform_core as core
import platform_sim as sim

SIM_STATES: Dict[str, dict] = {}      # per-project deterministic SIMULATOR runtime
SCREENS: Dict[str, dict] = {}         # per-project CURRENT hmi screen (server-owned)
REVISIONS: Dict[str, list] = {}       # per-project revision history (§30)
AUDIT: list = []                       # append-only audit log (§54)


def _record_rev(pid: str, screen: dict, note: str, changed=None, needs_approval=False):
    import copy as _c
    lst = REVISIONS.setdefault(pid, [])
    tag = f"v{len(lst) + 1}"
    lst.append({"rev": tag, "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "note": note,
                "widgets": len(screen.get("widgets", [])), "changed": changed or [],
                "approved": not needs_approval, "screen": _c.deepcopy(screen)})
    SCREENS[pid] = screen
    AUDIT.append({"ts": time.strftime("%H:%M:%S"), "project": pid, "action": note, "rev": tag})
    return tag


def _rev_list(pid: str):
    return [{k: r[k] for k in ("rev", "ts", "note", "widgets", "changed", "approved")}
            for r in REVISIONS.get(pid, [])]

# Optional: wire the trained CANON-brain in. Empty -> deterministic engine only.
LLM_BASE = os.getenv("CANON_LLM_BASE", "")          # e.g. http://localhost:8000/v1 (via SSH tunnel)
LLM_MODEL = os.getenv("CANON_LLM_MODEL", "canon-brain")


class BrainOffline(Exception):
    """Brain is configured but unreachable — spec §9: never silently fall back."""


def brain_configured() -> bool:
    return bool(LLM_BASE)


def brain_reachable() -> bool:
    if not LLM_BASE:
        return False
    try:
        import httpx
        r = httpx.get(LLM_BASE.rstrip("/") + "/models", timeout=3,
                      headers={"Authorization": "Bearer local"})
        return r.status_code == 200
    except Exception:
        return False


def _context_pack(model: dict, current: dict = None) -> str:
    """Structured context the Brain interprets (spec §7) — never the raw DB."""
    lines = [f"MACHINE {model['name']} · controller {model.get('controller')}",
             "ASSETS: " + ", ".join(f"{a['asset_id']}({a.get('type')})" for a in model["assets"]),
             "SIGNALS:"]
    for s in model["signals"]:
        rng = f" {s.get('engMin')}-{s.get('engMax')}{s.get('engUnit','')}" if s.get("engMax") is not None else ""
        lines.append(f"  {s['signalId']} [{s.get('kind')}{rng}] {s.get('description') or ''}")
    lines.append("COMMANDS: " + ", ".join(c["command_id"] for c in model["commands"]))
    if current:
        lines.append("CURRENT HMI widgets: " + ", ".join(w.get("component") for w in current.get("widgets", [])))
    return "\n".join(lines)


def brain_intent(text: str, model: dict, current: dict = None) -> dict:
    """MANDATORY brain interpretation (spec §2-5). Returns STRUCTURED intent, enum-
    constrained to real entities (§4/§8). Raises BrainOffline if unreachable."""
    if not LLM_BASE:
        raise BrainOffline("not configured")
    sig_ids = [s["signalId"] for s in model["signals"]]
    asset_ids = [a["asset_id"] for a in model["assets"]]
    cmd_ids = [c["command_id"] for c in model["commands"]]
    schema = {"type": "object", "additionalProperties": False,
              "required": ["scope", "signals", "commands", "op", "widget", "reasoning"],
              "properties": {
                  "scope": {"type": "string", "enum": asset_ids + ["machine", ""]},
                  "signals": {"type": "array", "items": {"type": "string", "enum": sig_ids + [""]}},
                  "commands": {"type": "array", "items": {"type": "string", "enum": cmd_ids + [""]}},
                  "op": {"type": "string", "enum": ["generate", "add", "remove", "none"]},
                  "widget": {"type": "string", "enum": ["trend", "value", "gauge", "alarm", "pressure", "none"]},
                  "reasoning": {"type": "string"}, "requires_review": {"type": "boolean"}}}
    sysmsg = ("You are CANON-BRAIN. Interpret the engineer's request into structured intent using ONLY "
              "entities from this machine model. scope = an asset id for a faceplate, or 'machine' for an "
              "overview. signals = the specific signals they want shown/changed (resolve vague phrases like "
              "'reactor temperature' via descriptions/units). commands = actions. op/widget describe an edit "
              "(add/remove a trend/value/gauge/alarm/pressure). NEVER invent an id that is not in the model.")
    body = {"model": LLM_MODEL, "temperature": 0, "max_tokens": 320,
            "messages": [{"role": "system", "content": sysmsg + "\n\n" + _context_pack(model, current)},
                         {"role": "user", "content": text}],
            "response_format": {"type": "json_schema", "json_schema": {"name": "intent", "schema": schema, "strict": True}}}
    try:
        import httpx
        r = httpx.post(LLM_BASE.rstrip("/") + "/chat/completions", json=body, timeout=45,
                       headers={"Authorization": "Bearer local"})
        r.raise_for_status()
        j = json.loads(r.json()["choices"][0]["message"]["content"])
    except Exception as e:
        raise BrainOffline(str(e))
    # canonical validation of the Brain's proposal (§4/§8): drop anything not real
    j["signals"] = [s for s in j.get("signals", []) if s in sig_ids]
    j["commands"] = [c for c in j.get("commands", []) if c in cmd_ids]
    if j.get("scope") not in asset_ids:
        j["scope"] = "machine"
    return j


HERE = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.join(HERE, "projects")
CTX = os.path.normpath(os.path.join(HERE, ".."))
os.makedirs(PROJ_DIR, exist_ok=True)

app = FastAPI(title="CANON Platform", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

PROJECTS: Dict[str, dict] = {}


# ---- persistence ----------------------------------------------------------
def _save(model: dict):
    if model.get("controller") in (None, "", "UNKNOWN"):
        n = model["counts"]["assets"]
        model["controller"] = "Modicon " + ("M241" if n <= 10 else "M251" if n <= 30 else "M580")
    PROJECTS[model["projectId"]] = model
    with open(os.path.join(PROJ_DIR, model["projectId"] + ".json"), "w") as fh:
        json.dump(model, fh)


def _load_all():
    for fn in os.listdir(PROJ_DIR):
        if fn.endswith(".json"):
            m = json.load(open(os.path.join(PROJ_DIR, fn)))
            PROJECTS[m["projectId"]] = m


def _seed():
    """Ensure the 3 dashboard seed projects exist (self-healing, per-project)."""
    # TK-401 — the real hero model (machine + command contracts + runtimeSeed)
    if "TK-401" in PROJECTS and PROJECTS["TK-401"].get("runtimeSeed"):
        pass  # already current
    try:
        dm = os.path.join(HERE, "seed", "canon_demo_machine.json")
        ccp = os.path.join(HERE, "seed", "canon_command_contracts.json")
        if not os.path.exists(dm):     # fallback to the sibling research folder
            dm = os.path.join(CTX, "CANON_RESEARCH/datasets/canon_demo_machine.json")
            ccp = os.path.join(CTX, "CANON_RESEARCH/engine/canon_command_contracts.json")
        raw = json.load(open(dm))
        cc = json.load(open(ccp))
        raw["contracts"] = cc.get("contracts", [])
        tk = core.normalize_machine(raw, "TK-401")
        tk["subtitle"] = "Process Tank"; tk["status"] = "RUNNING"; tk["connected"] = True
        tk["controller"] = "Modicon M262"
        _save(tk)
    except Exception:
        pass
    for pid, name, sub, ctl, n, seed, status in [
        ("PACK-07", "PACK-07", "Packaging Line", "Modicon M580", 148, 580, "RUNNING"),
        ("MIX-02", "MIX-02", "Mixing Station", "Modicon M241", 31, 241, "STOPPED"),
    ]:
        if pid in PROJECTS:
            continue
        m = core.synth_machine(name, sub, ctl, n, seed, pid)
        m["status"] = status; m["connected"] = True
        _save(m)


class GenReq(BaseModel):
    request: str


class EditReq(BaseModel):
    prompt: str
    screen: Dict[str, Any] = None      # optional — the server owns the current screen


class CreateReq(BaseModel):
    name: str
    controller: str = "UNKNOWN"
    n_assets: int = 20


@app.get("/api/projects")
def list_projects():
    return [{"projectId": m["projectId"], "name": m["name"], "subtitle": m.get("subtitle", ""),
             "controller": m.get("controller"), "status": m.get("status", "STOPPED"),
             "connected": m.get("connected", True), "counts": m["counts"]}
            for m in sorted(PROJECTS.values(), key=lambda x: x["projectId"])]


@app.get("/api/projects/{pid}")
def get_project(pid: str):
    if pid not in PROJECTS:
        raise HTTPException(404, "no such project")
    m = PROJECTS[pid]
    return {**{k: m[k] for k in ("projectId", "name", "subtitle", "controller", "counts")},
            "status": m.get("status"), "assets": m["assets"], "signals": m["signals"],
            "commands": m["commands"], "alarms": m["alarms"], "permissives": m["permissives"]}


@app.post("/api/projects/upload")
async def upload_project(file: UploadFile = File(...)):
    """Upload a machine project (.json canon.machine.v2, or .csv tag list) -> model."""
    content = await file.read()
    fname = file.filename or "machine"
    ext = os.path.splitext(fname)[1].lower()
    stem = os.path.splitext(os.path.basename(fname))[0].replace(" ", "-")
    try:
        if ext == ".csv":
            model = core.normalize_csv(content.decode("utf-8", "replace"), stem)
        elif ext in (".xlsx", ".xlsm"):
            model = core.normalize_xlsx(content, stem)
        elif ext == ".xml":
            model = core.normalize_xml(content.decode("utf-8", "replace"), stem)
        elif ext == ".pdf":
            model = core.normalize_pdf(content, stem)
        elif ext == ".json":
            raw = json.loads(content)
            sigs0 = raw.get("signals") or (raw.get("canonical_model") or {}).get("signals")
            if "canonical_model" in raw or (sigs0 and isinstance(sigs0, list) and sigs0 and ("semantic" in sigs0[0] or ("id" in sigs0[0] and "signalId" not in sigs0[0]))):
                pid = str((raw.get("project") or {}).get("id") or raw.get("package_name") or stem).replace(" ", "-")
                model = core.normalize_canon_json(raw, pid)          # rich canonical-model JSON
            else:
                pid = str(raw.get("machineId") or raw.get("name") or stem).replace(" ", "-")
                model = core.normalize_machine(raw, pid)
        else:
            raise HTTPException(400, f"unsupported file type '{ext}'. Use .csv .xlsx .xml .pdf or .json")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"could not parse {ext or 'file'}: {e}")
    if not model.get("signals"):
        raise HTTPException(400, "no signals found — need a tag list with a 'signal'/'tag' column")
    pid = model["projectId"]
    model["status"] = "STOPPED"; model["connected"] = True
    _save(model)
    return {"ok": True, "projectId": pid, "counts": model["counts"]}


LIB = os.path.join(HERE, "samples", "library")


@app.get("/api/samples")
def list_samples():
    """The bundled machine library (for the New Project dropdown), grouped by sector."""
    out = []
    if os.path.isdir(LIB):
        for fn in sorted(os.listdir(LIB)):
            if fn.endswith(".csv"):
                sector = fn.split("__")[0].replace("_", " ")
                label = fn.split("__")[-1][:-4] if "__" in fn else fn[:-4]
                out.append({"file": fn, "sector": sector, "label": label})
    return out


@app.post("/api/projects/from-sample")
def from_sample(body: Dict[str, str]):
    fn = os.path.basename(body.get("file", ""))       # prevent path traversal
    path = os.path.join(LIB, fn)
    if not fn.endswith(".csv") or not os.path.isfile(path):
        raise HTTPException(404, "no such sample")
    pid = os.path.splitext(fn)[0].replace("__", "-").replace(" ", "-")
    model = core.normalize_csv(open(path, encoding="utf-8").read(), pid)
    model["status"] = "STOPPED"; model["connected"] = True
    _save(model)
    return {"ok": True, "projectId": pid, "counts": model["counts"]}


@app.get("/api/projects/{pid}/context")
def project_context(pid: str):
    if pid not in PROJECTS:
        raise HTTPException(404, "no such project")
    return core.describe_context(PROJECTS[pid])


@app.post("/api/projects/synth")
def synth_project(req: CreateReq):
    pid = req.name.replace(" ", "-")
    m = core.synth_machine(req.name, "Synthesised", req.controller, req.n_assets, hash(pid) % 9999, pid)
    m["status"] = "STOPPED"; m["connected"] = True
    _save(m)
    return {"ok": True, "projectId": pid, "counts": m["counts"]}


@app.post("/api/projects/{pid}/generate")
def generate(pid: str, req: GenReq):
    if pid not in PROJECTS:
        raise HTTPException(404, "no such project")
    m = PROJECTS[pid]
    t0 = time.time()
    if brain_configured():
        if not brain_reachable():
            return {"ok": False, "brain_offline": True, "brain": _brain_status(),
                    "message": "CANON-BRAIN is configured but unavailable. Natural-language interpretation is temporarily unavailable. Retry the connection."}
        try:
            intent = brain_intent(req.request, m)
        except BrainOffline:
            return {"ok": False, "brain_offline": True, "brain": _brain_status(),
                    "message": "CANON-BRAIN went unreachable during interpretation."}
        scope = intent.get("scope"); scope = None if scope in ("machine", "", None) else scope
        req_sigs = intent.get("signals", [])
        screen = core.assemble_screen(m, scope)
        if req_sigs and scope is None:      # "show the two pressures" -> only those widgets
            keep = [w for w in screen["widgets"] if w.get("component") in ("StatusHeader", "AlarmBanner")
                    or any(s in req_sigs for s in w.get("boundSignals", []))]
            screen["widgets"] = keep
            screen["validation"]["widgets"] = len(keep)
            screen["validation"]["with_evidence"] = sum(1 for w in keep if w.get("usedEvidenceIds"))
        engine, why = "CANON-brain", intent.get("reasoning") or "interpreted by CANON-brain"
        matched = [scope] if scope else req_sigs
        steps = ["CANON-BRAIN · intent interpreted", "CANON MODEL · entities resolved",
                 "VALIDATOR · bindings verified", "HMI ASSEMBLER · generated"]
    else:
        scope, why, matched = core.analyze_scope(req.request, m)
        engine, steps = "deterministic", ["deterministic · keyword scope", "VALIDATOR", "HMI ASSEMBLER"]
        screen = core.assemble_screen(m, scope)
    rev = _record_rev(pid, screen, f"generated · {req.request}")
    return {"ok": True, "screen": screen, "engine": engine, "steps": steps, "rev": rev, "revisions": _rev_list(pid),
            "analysis": {"request": req.request, "scope": scope or "machine", "why": why, "matched": matched},
            "explanation": core.explain_screen(screen, m), "help": core.edit_help(m, screen),
            "latency_ms": int((time.time() - t0) * 1000)}


@app.post("/api/projects/{pid}/edit")
def edit(pid: str, req: EditReq):
    if pid not in PROJECTS:
        raise HTTPException(404, "no such project")
    m = PROJECTS[pid]
    cur = SCREENS.get(pid) or req.screen          # server owns the current screen
    if brain_configured():
        if not brain_reachable():
            return {"ok": False, "brain_offline": True, "brain": _brain_status(),
                    "message": "CANON-BRAIN is configured but unavailable."}
        try:
            intent = brain_intent(req.prompt, m, cur)
        except BrainOffline:
            return {"ok": False, "brain_offline": True, "brain": _brain_status()}
        op, widget, sigs = intent.get("op"), intent.get("widget"), intent.get("signals", [])
        if op not in ("add", "remove") and sigs:
            op = "add"        # an edit that resolved to real signals defaults to adding them
        canon_prompt = req.prompt
        wd = {"trend": "trend", "value": "value", "gauge": "gauge", "pressure": "pressure", "alarm": "alarms"}.get(widget, "")
        if op == "add" and sigs:
            canon_prompt = f"add {wd or 'value'} for " + " ".join(sigs)
        elif op == "remove":
            canon_prompt = f"remove {wd or 'pressure'}"
        result = core.apply_edit(cur, m, canon_prompt)
        result["engine"] = "CANON-brain"
        if intent.get("reasoning"):
            result["why"] = intent["reasoning"]
    else:
        result = core.apply_edit(cur, m, req.prompt)
        result["engine"] = "deterministic"
    if result["applied"]:
        result["rev"] = _record_rev(pid, result["screen"], f"edit · {req.prompt}", changed=result["applied"])
    result["revisions"] = _rev_list(pid)
    result["explanation"] = core.explain_screen(result["screen"], m)
    return {"ok": True, **result}


@app.get("/api/projects/{pid}/runtime")
def runtime(pid: str):
    """Current SIMULATOR values (value·unit·ts·quality). Honestly labelled — no live PLC."""
    if pid not in PROJECTS:
        raise HTTPException(404, "no such project")
    m = PROJECTS[pid]
    st = SIM_STATES.get(pid)
    if st is None:
        st = sim.init_state(m); SIM_STATES[pid] = st
    sim.tick(m, st)
    return {"source": "SIMULATOR", "connected": False, "signals": sim.snapshot(m, st)}


@app.post("/api/projects/{pid}/command")
def command(pid: str, body: Dict[str, str]):
    """Execute a real command through the permissive gate against the SIMULATOR (§20)."""
    if pid not in PROJECTS:
        raise HTTPException(404, "no such project")
    m = PROJECTS[pid]
    st = SIM_STATES.setdefault(pid, sim.init_state(m))
    return sim.run_command(m, st, body.get("command_id", ""))


@app.get("/api/projects/{pid}/revisions")
def revisions(pid: str):
    return {"revisions": _rev_list(pid), "current": SCREENS.get(pid)}


@app.post("/api/projects/{pid}/restore")
def restore(pid: str, body: Dict[str, str]):
    import copy
    rev = body.get("rev")
    hit = next((r for r in REVISIONS.get(pid, []) if r["rev"] == rev), None)
    if not hit:
        raise HTTPException(404, "no such revision")
    screen = copy.deepcopy(hit["screen"])
    tag = _record_rev(pid, screen, f"restored {rev}")
    return {"ok": True, "screen": screen, "rev": tag, "revisions": _rev_list(pid)}


@app.get("/api/projects/{pid}/why")
def why(pid: str, signal: str):
    """Traceability: HMI element → signal → fact → evidence → source (§26, §33)."""
    if pid not in PROJECTS:
        raise HTTPException(404, "no such project")
    s = next((x for x in PROJECTS[pid]["signals"] if x["signalId"] == signal), None)
    if not s:
        return {"signal": signal, "status": "UNKNOWN", "note": "not in the canonical model"}
    rng = ([s.get("engMin"), s.get("engMax")] if s.get("engMax") is not None else None)
    return {"signal": signal, "description": s.get("description"), "asset": s.get("asset"),
            "kind": s.get("kind"), "unit": s.get("engUnit"), "range": rng,
            "fact": f"{signal} is a {s.get('kind')} on {s.get('asset')}"
                    + (f", engineering range {rng[0]}–{rng[1]} {s.get('engUnit')}" if rng else ""),
            "evidence_id": f"ev::{pid}::{signal}",
            "source": f"uploaded engineering project · {pid}",
            "status": "VERIFIED"}


@app.post("/api/projects/{pid}/change-impact")
def change_impact(pid: str, body: Dict[str, Any]):
    """Engineering reality changes → identify affected HMI components → regenerate (§31)."""
    if pid not in PROJECTS:
        raise HTTPException(404, "no such project")
    m = PROJECTS[pid]
    sid = body.get("signalId")
    new_max = body.get("engMax")
    s = next((x for x in m["signals"] if x["signalId"] == sid), None)
    if not s:
        raise HTTPException(400, f"{sid} is not in the canonical model — refused (no invented tags)")
    old_max = s.get("engMax")
    cur = SCREENS.get(pid) or core.assemble_screen(m, None)
    affected = []
    for w in cur.get("widgets", []):
        if sid in w.get("boundSignals", []):
            affected.append({"kind": "widget", "component": w["component"], "section": w.get("section"),
                             "reason": f"binds {sid} — gauge range / scaling updates to new span"})
    for a in m["alarms"]:
        if a["signal"] == sid:
            affected.append({"kind": "alarm", "id": a.get("alarm_id"),
                             "reason": "threshold must be re-rationalised against the new span"})
    # apply the engineering change to the canonical model, then regenerate
    s["engMax"] = new_max
    _save(m); SIM_STATES.pop(pid, None)          # runtime re-inits at new range
    scope = cur.get("scope"); scope = None if scope == "machine" else scope
    new_screen = core.assemble_screen(m, scope)
    tag = _record_rev(pid, new_screen, f"change-impact · {sid} max {old_max}→{new_max}",
                      changed=[a.get("component") or a.get("id") for a in affected], needs_approval=True)
    return {"ok": True, "changed_entity": sid, "field": "engMax", "old": old_max, "new": new_max,
            "affected": affected, "screen": new_screen, "rev": tag, "revisions": _rev_list(pid)}


def _brain_status():
    configured = brain_configured()
    reachable = brain_reachable() if configured else False
    return {"configured": configured, "connected": reachable,
            "model": LLM_MODEL if configured else None,
            "interpreter": "ACTIVE" if reachable else ("UNAVAILABLE" if configured else "OFF · deterministic"),
            "validator": "ACTIVE", "assembly": "DETERMINISTIC CANON ENGINE", "runtime": "SIMULATOR"}


@app.get("/api/brain/status")
def brain_status():
    return _brain_status()


@app.get("/api/audit")
def audit():
    return AUDIT[-100:]


@app.get("/health")
def health():
    return {"status": "ok", "projects": len(PROJECTS)}


# ---- static SPA -----------------------------------------------------------
@app.get("/")
def index():
    return FileResponse(os.path.join(HERE, "web", "index.html"))


@app.get("/presentation")
def presentation():
    return FileResponse(os.path.join(HERE, "presentation.html"))


@app.on_event("startup")
def _startup():
    _load_all()
    _seed()


if __name__ == "__main__":
    import uvicorn
    _load_all(); _seed()
    port = int(os.getenv("PORT") or os.getenv("CANON_PLATFORM_PORT", "8090"))
    print(f"CANON Platform on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
