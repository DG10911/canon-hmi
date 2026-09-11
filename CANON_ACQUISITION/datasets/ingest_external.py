#!/usr/bin/env python3
"""Ingest a downloaded tabular ICS/sensor dataset into CANON_ACQUISITION.

Turns a CSV (CMAPSS, bearing vibration, pump_sensor, Modbus-derived features,
SWaT/WADI exports, etc.) into CANON records — but every value is marked
OBSERVED / CANDIDATE / REPORTED, never AUTHORITATIVE. Real machine config
(§62) always dominates observed telemetry; this ingestor respects that so it
can never masquerade dataset columns as verified machine truth (§67).

Pure stdlib (csv). Run on the DGX AFTER pull_datasets.sh downloads a dataset:

  python3 ingest_external.py --csv downloads/KG-CMAPSS/train_FD001.txt \
      --source-id KG-CMAPSS-001 --name "NASA C-MAPSS FD001" --sep " "

Outputs append to CANON_ACQUISITION/out_external/*.jsonl (kept separate from the
verified TK-401 corpus in out/). Merge later only with explicit provenance.
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ACQ = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, ACQ)
from canon_acq.ids import content_hash, fact_id, evidence_id  # noqa: E402

REGISTRY = os.path.join(HERE, "dataset_registry.json")


def registry_lookup(source_id):
    if not os.path.exists(REGISTRY):
        return {}
    reg = json.load(open(REGISTRY))
    for d in reg.get("datasets", []):
        if d.get("dataset_id") == source_id:
            return d
    return {}


def is_number(x):
    try:
        float(x)
        return True
    except (TypeError, ValueError):
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--source-id", required=True, help="dataset_id from dataset_registry.json")
    ap.add_argument("--name", default=None)
    ap.add_argument("--sep", default=",")
    ap.add_argument("--max-rows", type=int, default=100000, help="cap rows scanned for stats")
    ap.add_argument("--outdir", default=os.path.join(ACQ, "out_external"))
    a = ap.parse_args()

    meta = registry_lookup(a.source_id)
    name = a.name or meta.get("name") or os.path.basename(a.csv)
    tier = int(meta.get("trust_tier", 4)) if str(meta.get("trust_tier", "")).isdigit() else 4
    license_ = meta.get("license", "UNKNOWN")
    url = meta.get("url", f"file://{a.csv}")

    # read header + column stats
    with open(a.csv, newline="", encoding="utf-8", errors="replace") as fh:
        sniff_sep = None if a.sep == "auto" else a.sep
        reader = csv.reader(fh, delimiter=(sniff_sep or ","))
        rows = []
        header = None
        for i, r in enumerate(reader):
            r = [c for c in r if c != ""]
            if not r:
                continue
            if header is None:
                # if the first row is non-numeric treat as header, else synth names
                header = r if not all(is_number(c) for c in r) else [f"col{j}" for j in range(len(r))]
                if all(is_number(c) for c in r):
                    rows.append(r)  # first row was data
                continue
            rows.append(r)
            if len(rows) >= a.max_rows:
                break

    ncol = max((len(r) for r in rows), default=0)
    if len(header) < ncol:
        header += [f"col{j}" for j in range(len(header), ncol)]

    # per-column observed stats
    stats = {}
    for j in range(ncol):
        vals = [float(r[j]) for r in rows if j < len(r) and is_number(r[j])]
        if len(vals) >= max(3, 0.5 * len(rows)):
            stats[header[j]] = {"min": min(vals), "max": max(vals), "n": len(vals)}

    os.makedirs(a.outdir, exist_ok=True)

    def dump(fname, obj):
        with open(os.path.join(a.outdir, fname), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, separators=(",", ":")) + "\n")

    chash = content_hash(name + "|" + "|".join(header))
    dump("01_sources.jsonl", {
        "source_id": a.source_id, "title": name, "publisher": meta.get("source", "external"),
        "trust_tier": tier, "access_type": meta.get("access", "public"), "source_url": url,
        "document_type": "DATASET", "license": license_, "content_hash": chash,
        "mime_type": "text/csv", "status": "ACQUIRED",
        "note": "External dataset — OBSERVED telemetry, not authoritative machine config.",
    })

    n_sig = n_fact = n_unk = 0
    for col, st in stats.items():
        sig = f"{a.source_id}:{col}"
        dump("06_signals.jsonl", {
            "signalId": sig, "column": col, "kind": "observed-series", "dataType": "REAL",
            "observedMin": round(st["min"], 6), "observedMax": round(st["max"], 6),
            "samples": st["n"], "source": a.source_id, "machine": a.source_id,
            "knowledge_state": "CANDIDATE", "truthStatus": "REPORTED",
        })
        n_sig += 1
        loc = f"{os.path.basename(a.csv)}#col:{col}"
        ev_text = (f"Column '{col}' in dataset {name}: {st['n']} samples, "
                   f"observed range [{st['min']:.4g}, {st['max']:.4g}].")
        fid = fact_id(sig, "observed_range", f"{st['min']}-{st['max']}", a.source_id)
        eid = evidence_id(a.source_id, loc, ev_text)
        dump("29_facts.jsonl", {
            "fact_id": fid, "subject": sig, "predicate": "observed_range",
            "object": f"[{st['min']:.4g}, {st['max']:.4g}]",
            "value": [st["min"], st["max"]], "source_id": a.source_id, "source_location": loc,
            "evidence_text": ev_text, "evidence_id": eid,
            "confidence": "REPORTED", "trust_tier": tier, "knowledge_state": "CANDIDATE",
            "extraction_method": "tabular-ingest",
            "note": "OBSERVED from data, NOT an authoritative engineering range (§62).",
        })
        dump("31_evidence.jsonl", {
            "evidence_id": eid, "fact_id": fid, "source_id": a.source_id,
            "source_location": loc, "evidence_text": ev_text, "trust_tier": tier,
            "extraction_method": "tabular-ingest",
        })
        n_fact += 1

    # non-numeric / ambiguous columns -> unknowns for review (never dropped, §50)
    for j in range(ncol):
        if header[j] not in stats:
            dump("33_unknowns.jsonl", {
                "unknown_id": f"UNK_{a.source_id}_{header[j]}", "kind": "dataset-column",
                "subject": f"{a.source_id}:{header[j]}", "reason": "non-numeric or sparse column; needs mapping",
                "review_required": True, "possible_type": "label|category|timestamp",
            })
            n_unk += 1

    print(f"{a.source_id}: {n_sig} candidate signals, {n_fact} observed facts, "
          f"{n_unk} unknown columns -> {a.outdir}/")
    print("NOTE: all marked CANDIDATE/REPORTED/OBSERVED — not authoritative machine config.")


if __name__ == "__main__":
    main()
