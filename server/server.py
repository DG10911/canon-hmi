#!/usr/bin/env python3
"""
CANON — real LLM HMI-generation backend (for NVIDIA DGX A100 / any CUDA box).

Flow implemented here (the "real prompt to models" the demo talks about):
    intent (natural language) + canonical machine model
      -> LLM (local, OpenAI-compatible endpoint: vLLM or Ollama)
      -> STRICT JSON (component tree, enum-constrained to model signals)
      -> server-side VALIDATION against the canonical model (cannot invent a tag)
      -> returns {screen, trace, prompt} to the browser

The model NEVER controls the PLC. It only proposes a layout; every binding is
checked against the canonical model before it is returned. Unresolved refs are
downgraded to UNKNOWN, not rendered.

Run: see server/README.md  (vLLM or Ollama, both OpenAI-compatible).
"""
import os, json, time
from typing import Any, Dict, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

# ---- config (env-overridable) ---------------------------------------------
LLM_BASE   = os.getenv("CANON_LLM_BASE",  "http://localhost:8000/v1")  # vLLM default; Ollama = http://localhost:11434/v1
LLM_MODEL  = os.getenv("CANON_LLM_MODEL", "Qwen/Qwen2.5-Coder-32B-Instruct")
LLM_KEY    = os.getenv("CANON_LLM_KEY",   "not-needed-for-local")
PORT       = int(os.getenv("CANON_PORT",  "8088"))

# widget "type" is a closed enum -> the model literally cannot emit anything else
WIDGET_TYPES = ["gaugeP", "gaugeL", "tile", "pump", "valve", "trend",
                "cmd", "alarms", "diagnostic"]

app = FastAPI(title="CANON HMI Generator", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class GenReq(BaseModel):
    intent: str
    model: Dict[str, Any]           # the canonical model M (signals, commands, alarms)
    size: str = "M"


def json_schema(model: Dict[str, Any]) -> Dict[str, Any]:
    """A JSON schema whose 'ref' is an ENUM of the real signal/command ids.
    This is the guarantee: structured output can only reference what exists."""
    sig_ids = [s["name"] for s in model.get("signals", [])] + \
              [s["id"]   for s in model.get("signals", [])]
    cmd_ids = [c["id"] for c in model.get("commands", [])]
    return {
        "type": "object",
        "properties": {
            "widgets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": WIDGET_TYPES},
                        "ref":  {"type": "string", "enum": sig_ids + cmd_ids + [""]},
                        "priority": {"type": "integer", "minimum": 1, "maximum": 3},
                    },
                    "required": ["type"],
                    "additionalProperties": False,
                },
            },
            "rationale": {"type": "string"},
        },
        "required": ["widgets"],
        "additionalProperties": False,
    }


def build_prompt(req: GenReq) -> List[Dict[str, str]]:
    """The actual prompt sent to the model (shown verbatim in the UI)."""
    sig = "\n".join(
        f"  - {s['name']} ({s['desc']}) io={s['io']} "
        f"range={(str(s['range']['min'])+'-'+str(s['range']['max'])+' '+s['unit']) if s.get('range') else 'discrete'}"
        for s in req.model.get("signals", []))
    cmds = "\n".join(
        f"  - {c['id']} writes {c['writes']} permissives={c.get('pre')}"
        for c in req.model.get("commands", []))
    system = (
        "You are CANON, an HMI layout compiler for industrial machines. "
        "You are given a CANONICAL MACHINE MODEL (the single source of truth) and an operator/engineer INTENT. "
        "Propose an HMI as a flat list of widgets. RULES:\n"
        "1. Every widget 'ref' MUST be an exact signal name/id or command id from the model. Never invent a tag.\n"
        "2. Use gaugeP for pressure, gaugeL for level, tile for other analog signals, pump/valve for those assets, "
        "cmd for commands, alarms for the alarm banner, trend for a trend, diagnostic for an abnormal-condition panel.\n"
        "3. Follow ISA-101: show what the intent asks for, nothing decorative. priority 1=primary, 3=secondary.\n"
        "4. You propose only. The model defines, a validator checks, and the PLC controls. "
        "You never emit control logic, setpoints, or safety decisions.\n"
        "Return ONLY JSON matching the provided schema."
    )
    user = (
        f"MACHINE MODEL: unit {req.model['unit']['name']} ({req.model['unit']['type']})\n"
        f"SIGNALS:\n{sig}\nCOMMANDS:\n{cmds}\n\n"
        f"INTENT: {req.intent}\nHMI SIZE: {req.size}\n\nReturn the widget list as JSON."
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def validate(widgets: List[Dict[str, Any]], model: Dict[str, Any]):
    """Server-side guarantee: drop/flag anything not in the canonical model."""
    names = {s["name"] for s in model.get("signals", [])} | {s["id"] for s in model.get("signals", [])}
    cmds  = {c["id"] for c in model.get("commands", [])}
    ok, unknown = [], []
    for w in widgets:
        t = w.get("type")
        r = w.get("ref", "")
        needs_ref = t not in ("alarms", "diagnostic")
        if needs_ref and r not in names and r not in cmds:
            unknown.append(r or f"<{t} with no ref>")
            continue
        ok.append(w)
    return ok, unknown


@app.get("/health")
async def health():
    """Reports whether the local model endpoint is reachable."""
    info = {"backend": LLM_BASE, "model": LLM_MODEL, "llm": "down"}
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(f"{LLM_BASE}/models", headers={"Authorization": f"Bearer {LLM_KEY}"})
            if r.status_code == 200:
                info["llm"] = "up"
    except Exception as e:
        info["error"] = str(e)
    return info


@app.post("/generate")
async def generate(req: GenReq):
    t0 = time.time()
    messages = build_prompt(req)
    schema = json_schema(req.model)
    prompt_shown = messages[0]["content"] + "\n\n---\n" + messages[1]["content"]

    body = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": 0.1,
        # vLLM & Ollama both honor OpenAI structured outputs / json_schema:
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": "hmi", "schema": schema, "strict": True}},
    }
    raw, err = None, None
    try:
        async with httpx.AsyncClient(timeout=90) as c:
            r = await c.post(f"{LLM_BASE}/chat/completions",
                             headers={"Authorization": f"Bearer {LLM_KEY}"}, json=body)
            r.raise_for_status()
            raw = r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        err = str(e)

    if err:
        return {"ok": False, "error": err, "prompt": prompt_shown,
                "hint": "Start a local OpenAI-compatible server (vLLM or Ollama). See server/README.md."}

    try:
        parsed = json.loads(raw)
        widgets = parsed.get("widgets", [])
    except Exception as e:
        return {"ok": False, "error": f"model returned non-JSON: {e}", "raw": raw, "prompt": prompt_shown}

    ok, unknown = validate(widgets, req.model)
    return {
        "ok": True,
        "screen": {"widgets": ok},
        "unknown": unknown,
        "rationale": parsed.get("rationale", ""),
        "prompt": prompt_shown,
        "model": LLM_MODEL,
        "latency_ms": int((time.time() - t0) * 1000),
        "trace": [
            "Interpret intent (LLM)",
            f"Model proposed {len(widgets)} widgets",
            f"Validate against canonical model — {len(unknown)} rejected as UNKNOWN",
            f"{len(ok)} widgets bound",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
