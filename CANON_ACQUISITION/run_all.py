#!/usr/bin/env python3
"""End-to-end P0 acquisition run (spec section 60 discovery loop, 64/65 outputs).

    DISCOVER -> CLASSIFY -> ACQUIRE -> PARSE -> EXTRACT -> LINK -> VERIFY
    -> DEDUPLICATE -> INDEX -> UPDATE CANON

Pure stdlib. From this directory:  python3 run_all.py
Outputs land in out/ : the 37 datasets (JSONL), corpus_manifest.json,
source_registry.json, context_pack.tk401.json, coverage_report.json,
hmi_readiness.json, no_hallucination_audit.json.
"""
from __future__ import annotations
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from canon_acq.store import Corpus
from canon_acq.discovery import query_families, total_queries
from canon_acq.web_ingest import ingest_web_sources
from canon_acq.ingest_tk401 import ingest as ingest_tk401, MACHINE_ID
from canon_acq import engines
from canon_acq.context_pack import build_context_pack


def main() -> int:
    ap = argparse.ArgumentParser(description="CANON acquisition P0 end-to-end run")
    ap.add_argument("--context-base", default=os.path.dirname(HERE),
                    help="dir containing CANON_RESEARCH/ (default: parent .context)")
    ap.add_argument("--seed", default=os.path.join(HERE, "sources", "source_registry.seed.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    args = ap.parse_args()

    corpus = Corpus()
    notes = []

    # 1. DISCOVER (query-family generation is deterministic + offline) --------
    fams = query_families(machine_hint="Modicon M580")
    notes.append(f"discovery: generated {total_queries(fams)} queries across {len(fams)} families")

    # 2-7. ACQUIRE + CLASSIFY web-verified sources --------------------------
    web = ingest_web_sources(corpus, args.seed)
    notes.append(f"web sources ingested: {web}")

    # 8. INGEST machine reality (Tier 0) — dominates generic vendor knowledge -
    ingest_tk401(corpus, args.context_base)
    notes.append("TK-401 machine reality ingested (Tier 0)")

    # 9. LINK / RESOLVE -----------------------------------------------------
    engines.resolve_entities(corpus)
    dupes = engines.detect_duplicates(corpus)

    # 10. VERIFY coverage + readiness --------------------------------------
    coverage = engines.compute_coverage(corpus)
    readiness = engines.compute_readiness(corpus)

    # 11. CONTEXT PACK ------------------------------------------------------
    pack = build_context_pack(corpus, MACHINE_ID)

    # 11b. MERGE external reference datasets (out_external/) — real ICS/sensor data
    #      folded in AFTER machine coverage/context so those stay clean (§62).
    from canon_acq.external import merge_external
    ext = merge_external(corpus, os.path.join(HERE, "out_external"))
    notes.append(f"external reference datasets merged: {ext}")

    # 12. AUDIT (no-hallucination guarantee) --------------------------------
    audit = engines.audit_no_hallucination(corpus)

    # 13. WRITE -------------------------------------------------------------
    os.makedirs(args.out, exist_ok=True)
    written = corpus.write(args.out)
    corpus.write_manifest(args.out, {
        "duplicates": dupes,
        "reference_datasets": ext,
        "licenses": sorted({s.get("license") for s in corpus.data["sources"] if s.get("license")}),
        "notes": notes,
        "errors": [] if audit["ok"] else ["no-hallucination audit found violations"],
    })
    corpus.write_source_registry(args.out)
    _dump(os.path.join(args.out, "context_pack.tk401.json"), pack)
    _dump(os.path.join(args.out, "coverage_report.json"), coverage)
    _dump(os.path.join(args.out, "hmi_readiness.json"), readiness)
    _dump(os.path.join(args.out, "no_hallucination_audit.json"), audit)

    # 14. REPORT ------------------------------------------------------------
    print("=" * 64)
    print("CANON_ACQUISITION — P0 run complete")
    print("=" * 64)
    print(f"datasets written : {len(written)} (out/*.jsonl)")
    print(f"sources          : {corpus.count('sources')} "
          f"({corpus.count('documents')} documents)")
    print(f"entities         : {corpus.count('entities')}")
    print(f"facts / evidence : {corpus.count('facts')} / {corpus.count('evidence')}")
    print(f"relationships    : {corpus.count('relationships')}")
    print(f"conflicts        : {corpus.count('conflicts')}  "
          f"unknowns: {corpus.count('unknowns')}  duplicates: {dupes}")
    print(f"coverage overall : {coverage['_overall']}%")
    print(f"HMI readiness    : {readiness['readiness']}  "
          f"(blocking: {readiness['blocking'] or 'none'})")
    print(f"no-hallucination : {'PASS (0 violations)' if audit['ok'] else 'FAIL: ' + str(audit['violations'])}")
    print("-" * 64)
    for dim, val in coverage.items():
        if not dim.startswith("_"):
            print(f"  {dim:<16} {val:>5}%")
    print("=" * 64)
    return 0 if audit["ok"] else 1


def _dump(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)


if __name__ == "__main__":
    raise SystemExit(main())
