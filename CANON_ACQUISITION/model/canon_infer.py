#!/usr/bin/env python3
"""CANON end-to-end bridge: NL request + machine context -> VALIDATED HMI intent.

This is the runtime loop (spec §64, §71):

  Context Pack (machine card + allowed components)
      -> system prompt (+ user NL request)
      -> CANON-brain (local llama-server / Ollama, CPU)
      -> parse JSON
      -> DETERMINISTIC VALIDATOR  (drops any invented tag/command/component)
      -> validated intent + evidence pointers

The model only PROPOSES. The validator is the guarantee: every usedSignalId must
exist in the machine model, every command must be real, every component must be
in the registry — anything else is moved to "unknowns" and never bound.

Pure stdlib (urllib). Examples:
  # inspect the exact prompt the model sees:
  python3 canon_infer.py --request "close valve XV401" --show-prompt

  # real call against your CPU model:
  llama-server -m out/canon-brain-3b-Q4_K_M.gguf --port 8000 &
  python3 canon_infer.py --request "start pump P401" \
      --url http://localhost:8000/v1 --model canon-brain
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "out"))

SYSTEM = (
    "You are CANON-brain, an engineering-context model. You NEVER invent tags, "
    "commands, alarms, products, or facts. You bind only to identifiers present "
    "in the MACHINE model below. If an identifier is not present, return it under "
    "\"unknowns\" and refuse to bind. Emit a single valid JSON object and nothing "
    "else. Always include usedSignalIds, usedEvidenceIds and unknowns."
)


def load_context(path):
    p = json.load(open(path, encoding="utf-8"))
    sigs = [s["signalId"] for s in p.get("signal_dictionary", [])]
    cmds = [c["command_id"] for c in p.get("command_model", [])]
    alarms = [a["alarm_id"] for a in p.get("alarm_model", [])]
    assets = [a.get("asset_id") for a in p.get("asset_model", []) if a.get("asset_id")]
    machine = p.get("machine_id", "machine")
    return machine, sigs, cmds, alarms, assets


def load_components(path):
    return [json.loads(l)["component"] for l in open(path, encoding="utf-8") if l.strip()]


def load_evidence_index(path):
    """subject -> first evidence_id, so we can attach provenance to a binding."""
    idx = {}
    if os.path.exists(path):
        for l in open(path, encoding="utf-8"):
            f = json.loads(l)
            idx.setdefault(f["subject"], f.get("evidence_id"))
    return idx


def _jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()] if os.path.exists(path) else []


def enrich_with_contract(validated, ev_idx, out_dir):
    """Replace the model's GUESSED permissives with the AUTHORITATIVE command
    contract from the corpus (real request/feedback signals + permissives +
    interlocks + evidence). The model proposes the command; the machine model
    defines the contract (§12, §62, §71)."""
    cmd = validated.get("command")
    if not cmd:
        return validated
    commands = {c["command_id"]: c for c in _jsonl(os.path.join(out_dir, "15_commands.jsonl"))}
    if cmd not in commands:
        return validated
    crow = commands[cmd]
    perms = [p for p in _jsonl(os.path.join(out_dir, "16_permissives.jsonl")) if p.get("command") == cmd]
    ils = [i for i in _jsonl(os.path.join(out_dir, "17_interlocks.jsonl")) if i.get("command") == cmd]

    contract_sigs = [crow.get("request_signal"), crow.get("feedback_signal")]
    contract_sigs += [p["signal"] for p in perms] + [i.get("signal") for i in ils]
    contract_sigs = sorted({s for s in contract_sigs if s})

    validated.pop("expectedPermissives", None)   # drop the model's improvised block
    validated["contract"] = {
        "source": "CANON corpus (authoritative) — replaces any model-proposed permissives",
        "request": crow.get("request_signal"), "feedback": crow.get("feedback_signal"),
        "permissives": [{"signal": p["signal"], "expected": p.get("expected"),
                         "rejectCode": p.get("rejectCode"), "message": p.get("message")} for p in perms],
        "interlocks": [{"signal": i.get("signal"), "expected": i.get("expected"),
                        "rejectCode": i.get("rejectCode")} for i in ils],
    }
    used = set(validated.get("usedSignalIds", []) or []) | set(contract_sigs)
    validated["usedSignalIds"] = sorted(used)
    validated["usedEvidenceIds"] = sorted({ev_idx[s] for s in used if ev_idx.get(s)})
    return validated


def machine_card(machine, sigs, cmds, alarms, comps):
    return (f"MACHINE {machine}\n"
            f"signals: {', '.join(sigs)}\n"
            f"commands: {', '.join(cmds)}\n"
            f"alarms: {', '.join(alarms)}\n"
            f"allowed HMI components (choose only from these): {', '.join(comps)}")


def build_messages(card, request):
    return [{"role": "system", "content": SYSTEM + "\n\n" + card},
            {"role": "user", "content": request}]


def call_model(url, model, messages, timeout=180, force_json=True):
    payload = {"model": model, "messages": messages, "temperature": 0, "max_tokens": 512}
    if force_json:
        # constrained decoding: llama.cpp / vLLM force a syntactically valid JSON
        # object, so the model can never emit malformed JSON (best-practice, §55).
        payload["response_format"] = {"type": "json_object"}
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url.rstrip("/") + "/chat/completions", data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer x"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def extract_json(text):
    text = text.strip()
    if "{" in text and "}" in text:
        try:
            return json.loads(text[text.find("{"):text.rfind("}") + 1])
        except Exception:
            return None
    return None


def _collect_tagvals(obj, keys):
    """Recursively gather string values stored under the given keys (e.g. the
    tag actually bound inside a widget: {"binding": "PT401"})."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in keys and isinstance(v, str):
                out.append(v)
            else:
                out += _collect_tagvals(v, keys)
    elif isinstance(obj, list):
        for x in obj:
            out += _collect_tagvals(x, keys)
    return out


def validate(pred, sigs, cmds, comps, evidence_idx, assets=()):
    """Deterministic gate — the guarantee. Returns (validated, report)."""
    sigset, cmdset, compset, assetset = set(sigs), set(cmds), set(comps), set(assets)
    known = sigset | cmdset | compset | assetset
    used = list(pred.get("usedSignalIds", []) or [])
    unknowns = list(pred.get("unknowns", []) or [])
    dropped = []

    kept_used = []
    for tag in used:
        (kept_used if tag in sigset else dropped).append(tag)
    for tag in dropped:
        unknowns.append(tag)

    # nested bindings: a signal tag hidden in widgets[].binding / .signal must be real
    for tag in _collect_tagvals(pred, {"binding", "signal"}):
        if tag not in sigset and tag not in kept_used:
            unknowns.append(tag)
            dropped.append(tag)

    # command check
    cmd = pred.get("command")
    cmd_ok = cmd is None or cmd in cmdset
    if cmd is not None and not cmd_ok:
        unknowns.append(cmd)
        pred["command"] = None
        dropped.append(cmd)

    # target check (asset or signal)
    tgt = pred.get("target")
    tgt_ok = tgt is None or tgt in assetset or tgt in sigset
    if tgt is not None and not tgt_ok:
        unknowns.append(tgt)
        pred["target"] = None
        dropped.append(tgt)

    # a permissive/interlock CONTRACT is meaningless without a valid command+target;
    # strip any (they're where hallucinated codes/conditions hide).
    if not (cmd_ok and cmd) or not tgt_ok:
        for k in ("permissives", "expectedPermissives", "interlocks"):
            if pred.get(k):
                pred[k] = []

    # component check
    comp = pred.get("component")
    if comp is not None and comp not in compset:
        unknowns.append(comp)
        pred["component"] = None
        dropped.append(comp)

    # RECONCILE: a genuinely-known identifier is never "unknown" (fixes the model
    # putting a real tag like PT401 in both usedSignalIds and unknowns).
    unknowns = [u for u in unknowns if u not in known]

    # attach evidence for every surviving binding (traceability, §71)
    used_evidence = [evidence_idx[t] for t in kept_used if evidence_idx.get(t)]

    validated = dict(pred)
    validated["usedSignalIds"] = sorted(set(kept_used))
    validated["usedEvidenceIds"] = sorted(set(used_evidence))
    validated["unknowns"] = sorted(set(unknowns))
    real_dropped = sorted(set(u for u in dropped if u not in known))
    report = {
        "ok": len(real_dropped) == 0,
        "dropped_invented": real_dropped,
        "bindings_with_evidence": len(used_evidence),
        "verdict": "CLEAN" if not real_dropped else "SANITIZED (invented bindings removed)",
    }
    return validated, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True, help="operator NL request")
    ap.add_argument("--context", default=os.path.join(OUT, "context_pack.tk401.json"))
    ap.add_argument("--components", default=os.path.join(OUT, "24_hmi_components.jsonl"))
    ap.add_argument("--facts", default=os.path.join(OUT, "29_facts.jsonl"))
    ap.add_argument("--url", default="http://localhost:8000/v1")
    ap.add_argument("--model", default="canon-brain")
    ap.add_argument("--show-prompt", action="store_true", help="print the prompt and exit (no model call)")
    a = ap.parse_args()

    machine, sigs, cmds, alarms, assets = load_context(a.context)
    comps = load_components(a.components)
    ev_idx = load_evidence_index(a.facts)
    card = machine_card(machine, sigs, cmds, alarms, comps)
    messages = build_messages(card, a.request)

    if a.show_prompt:
        print("=== SYSTEM ===\n" + messages[0]["content"])
        print("\n=== USER ===\n" + messages[1]["content"])
        return

    raw = call_model(a.url, a.model, messages)
    pred = extract_json(raw)
    if pred is None:
        print("model did not return JSON:\n", raw, file=sys.stderr)
        sys.exit(1)

    validated, report = validate(pred, sigs, cmds, comps, ev_idx, assets)
    validated = enrich_with_contract(validated, ev_idx, OUT)
    print("=== MODEL PROPOSED ===")
    print(json.dumps(pred, indent=2))
    print("\n=== VALIDATOR ===")
    print(json.dumps(report, indent=2))
    print("\n=== VALIDATED (safe to render) ===")
    print(json.dumps(validated, indent=2))


if __name__ == "__main__":
    main()
