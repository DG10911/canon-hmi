#!/usr/bin/env python3
"""Prompt -> context analysis -> generated HMI screen (the full loop, testable offline).

Given a natural-language request, CANON:
  1. ANALYZES the machine context to decide the screen SCOPE (which asset(s), or
     the whole line) — deterministically, by matching asset ids/types that ACTUALLY
     exist in the machine model. It cannot pick an asset that isn't real.
  2. GENERATES the screen via the deterministic assembler (canon_screen), so every
     widget binds to a real signal/command with evidence (§56/§67).

No model/GPU needed for scope+assembly — grounding comes from the corpus. (Atomic
command prompts like "close XV401" go through canon_infer.py + the LLM instead.)

  python3 canon_hmi.py --request "build the operator page for the pump"
  python3 canon_hmi.py --request "show me the whole line"
  python3 canon_hmi.py --request "I need to monitor tank level"
"""
from __future__ import annotations
import argparse
import json
import os
import re

from canon_screen import assemble_screen, load

OVERVIEW_WORDS = {"line", "overview", "everything", "all", "whole", "plant",
                  "summary", "system", "machine", "dashboard"}
TYPE_WORDS = {"pump": "pump", "motor": "pump", "tank": "tank", "level": "tank",
              "vessel": "tank", "valve": "valve"}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def analyze(request, assets):
    """Deterministic context analysis -> (scope_asset|None, explanation)."""
    req = request.lower()
    reqn = norm(request)
    ids = {a["asset_id"]: a for a in assets}

    # 1. explicit asset id mentioned (PT-401 / p401 / TK401 all normalise)
    by_id = [aid for aid in ids if norm(aid) in reqn]
    # 2. asset type mentioned (pump/tank/valve...)
    hit_types = {TYPE_WORDS[w] for w in TYPE_WORDS if re.search(rf"\b{w}\b", req)}
    by_type = [aid for aid, a in ids.items() if a.get("type") in hit_types]

    matched = list(dict.fromkeys(by_id + by_type))  # de-dup, keep order
    overview = any(re.search(rf"\b{w}\b", req) for w in OVERVIEW_WORDS)

    if overview or len(matched) != 1:
        scope = None
        why = ("overview keyword" if overview else
               f"{len(matched)} assets matched ({matched})" if matched else
               "no specific asset named")
        return scope, f"scope = WHOLE MACHINE ({why})", matched
    scope = matched[0]
    reason = "named explicitly" if scope in by_id else f"type '{ids[scope]['type']}' referenced"
    return scope, f"scope = {scope} ({reason})", matched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--out-dir", default=os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "out")))
    ap.add_argument("--full", action="store_true", help="print the full screen JSON")
    a = ap.parse_args()

    assets = load("08_assets.jsonl")
    scope, explanation, matched = analyze(a.request, assets)

    print("=== CONTEXT ANALYSIS ===")
    print(f"request      : {a.request}")
    print(f"assets known : {[x['asset_id'] + '(' + str(x.get('type')) + ')' for x in assets]}")
    print(f"matched      : {matched or 'none'}")
    print(f"decision     : {explanation}")

    screen = assemble_screen(scope, a.out_dir)
    print("\n=== GENERATED SCREEN ===")
    print(f"page   : {screen['pageTitle']}")
    print(f"layout : {screen['layoutAlgorithm']}")
    for w in screen["widgets"]:
        b = w.get("boundSignals", [])
        c = w.get("boundCommands", [])
        ev = len(w.get("usedEvidenceIds", []))
        print(f"  - {w['component']:<15} signals={b or '-'} commands={c or '-'} evidence={ev}")
    v = screen["validation"]
    print(f"validation: ok={v['ok']} dropped={v['dropped_invalid_bindings'] or 'none'} "
          f"widgets={v['total_widgets']} with_evidence={v['bindings_with_evidence']}")
    if a.full:
        print("\n=== FULL SCREEN JSON ===")
        print(json.dumps(screen, indent=2))


if __name__ == "__main__":
    main()
