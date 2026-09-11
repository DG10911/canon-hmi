#!/usr/bin/env python3
"""Build the CANON-brain training set (pure stdlib — no GPU, no installs).

Combines two task families, all correct-by-construction (the deterministic
CANON engine is the teacher, so labels never hallucinate):

  A. INTENT   — NL command -> validated intent JSON (reuses the 23,298-pair
                synthetic corpus in ../../CANON_RESEARCH/synthetic/out/).
  B. ACQUISITION — the new evidence-first tasks, generated per machine:
       fact_extract      evidence sentence -> {subject,predicate,object,unit,evidence,knowledge_state}
       io_map            signal -> {area,address,dtype,scale}
       entity_resolve    alias   -> canonical id (or AMBIGUOUS)
       classify_file     filename -> file_class
       refuse            prompt about a tag NOT in the machine -> UNKNOWN (never a binding)

Every row is a chat triple {system, user, assistant}. Machine context is injected
compactly so a 3B model can hold it. Split is BY MACHINE so eval machines are unseen.

    python3 build_dataset.py                 # -> data/train.jsonl, data/eval.jsonl
    python3 build_dataset.py --max-per-task 8000
"""
from __future__ import annotations
import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CTX = os.path.normpath(os.path.join(HERE, "..", ".."))          # .context/
SYNTH = os.path.join(CTX, "CANON_RESEARCH", "synthetic", "out")
ACQ_OUT = os.path.normpath(os.path.join(HERE, "..", "out"))

sys.path.insert(0, os.path.join(HERE, ".."))
from canon_acq.classify import classify_file  # reuse the real classifier  # noqa: E402

SEED = 401
SYSTEM = (
    "You are CANON-brain, an engineering-context model. You NEVER invent tags, "
    "commands, alarms, products, or facts. You bind only to identifiers present "
    "in the provided MACHINE model or EVIDENCE. If an identifier is not present, "
    "you return it under \"unknowns\" and refuse to bind. You always emit a single "
    "valid JSON object and nothing else. Every answer lists usedSignalIds, "
    "usedEvidenceIds and unknowns."
)


def load_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def machine_context(m: dict) -> str:
    """Compact, deterministic machine card the model must ground against."""
    sigs = []
    for s in m.get("signals", []):
        rng = ""
        if s.get("engMin") is not None and s.get("engMax") is not None:
            rng = f" {s['engMin']}-{s['engMax']}{s.get('engUnit','')}"
        sigs.append(f"{s['signalId']}({s.get('kind','')}{rng})")
    cmds = list(m.get("commands", []))
    alarms = [a["alarmId"] for a in m.get("alarms", [])]
    return (
        f"MACHINE {m['machineId']} :: signals=[{', '.join(sigs)}] "
        f"commands=[{', '.join(cmds)}] alarms=[{', '.join(alarms)}]"
    )


def triple(system_ctx, user, assistant_obj, task, label):
    return {
        "task": task, "label": label,
        "messages": [
            {"role": "system", "content": SYSTEM + "\n\n" + system_ctx},
            {"role": "user", "content": user},
            {"role": "assistant", "content": json.dumps(assistant_obj, separators=(",", ":"))},
        ],
    }


# ---------------- task generators (correct-by-construction) ----------------
def gen_intent(rows, machines_by_id, out):
    for r in rows:
        m = machines_by_id.get(r["machineId"])
        if not m:
            continue
        ctx = machine_context(m)
        intent = dict(r["intent"])
        intent.setdefault("usedEvidenceIds", [])
        intent.setdefault("unknowns", intent.get("unknowns", []))
        out.append(triple(ctx, r["input"], intent, "intent", r.get("label", "accept")))


def gen_acquisition(m, rng, out, caps):
    ctx = machine_context(m)
    mid = m["machineId"]
    sigs = m.get("signals", [])
    io_by = {i["signalId"]: i for i in m.get("io", [])}

    # fact_extract — engineering range, grounded in an evidence sentence
    for s in sigs:
        if s.get("engMin") is None or s.get("engMax") is None:
            continue
        if caps["fact"] <= 0:
            break
        ev = (f"{s['signalId']} PLC scaling configures engineering range "
              f"{s['engMin']}-{s['engMax']} {s.get('engUnit','')}".strip())
        ans = {
            "subject": s["signalId"], "predicate": "engineering_range",
            "object": f"{s['engMin']}-{s['engMax']} {s.get('engUnit','')}".strip(),
            "value": [s["engMin"], s["engMax"]], "unit": s.get("engUnit"),
            "knowledge_state": "KNOWN",
            "usedSignalIds": [s["signalId"]], "usedEvidenceIds": [f"ev::{mid}::{s['signalId']}"],
            "unknowns": [],
        }
        out.append(triple(ctx, f"Extract the engineering fact from this evidence:\n\"{ev}\"",
                          ans, "fact_extract", "accept"))
        caps["fact"] -= 1

        # io_map fact
        io = io_by.get(s["signalId"])
        if io and caps["io"] > 0:
            ans2 = {"subject": s["signalId"], "predicate": "modbus_address",
                    "object": f"{io['area']}:{io['address']}",
                    "area": io["area"], "address": io["address"], "dtype": io.get("dtype"),
                    "scale": io.get("scale"), "usedSignalIds": [s["signalId"]],
                    "usedEvidenceIds": [f"ev::{mid}::io::{s['signalId']}"], "unknowns": []}
            out.append(triple(ctx, f"What is the I/O mapping for {s['signalId']}?",
                              ans2, "io_map", "accept"))
            caps["io"] -= 1

    # entity_resolve — alias variants map back to the canonical id
    for s in sigs:
        if caps["resolve"] <= 0:
            break
        base = s["signalId"]
        alias = rng.choice([base.replace("40", "-40"), base.lower(),
                             base.replace("_", "-"), base])
        ans = {"canonical_entity": base, "alias": alias,
               "resolution_status": "RESOLVED" if alias.replace("-", "").replace("_", "").lower() == base.replace("_", "").lower() else "CANDIDATE",
               "usedSignalIds": [base], "usedEvidenceIds": [], "unknowns": []}
        out.append(triple(ctx, f"Resolve tag \"{alias}\" to a canonical machine entity.",
                          ans, "entity_resolve", "accept"))
        caps["resolve"] -= 1

    # classify_file — deterministic classifier is the teacher
    for fn in ["machine_project.xef", "hmi_export.xml", "PT_scaling.csv",
               "P&ID_rev3.pdf", "nodeset.xml", "register_map.csv", "unknown.bin"]:
        if caps["classify"] <= 0:
            break
        c = classify_file(fn)
        ans = {"filename": fn, "file_class": c["file_class"], "domain": c["domain"],
               "review_required": c["review_required"], "unknowns": [fn] if c["review_required"] else []}
        out.append(triple(ctx, f"Classify the uploaded file \"{fn}\".", ans, "classify_file", "accept"))
        caps["classify"] -= 1

    # refuse — a tag that is NOT in this machine must go to unknowns, never bind
    present = {s["signalId"] for s in sigs}
    for _ in range(6):
        if caps["refuse"] <= 0:
            break
        fake = rng.choice(["PT999", "LT000", "XV777", "FT404", "MTR_GHOST", "AI_1234"])
        if fake in present:
            continue
        ans = {"status": "UNKNOWN", "reason": f"{fake} is not in the machine model",
               "usedSignalIds": [], "usedEvidenceIds": [], "unknowns": [fake]}
        out.append(triple(ctx, f"Show the live value and start command for {fake}.",
                          ans, "refuse", "refuse"))
        caps["refuse"] -= 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-per-task", type=int, default=8000,
                    help="cap per acquisition task family (total, across machines)")
    ap.add_argument("--eval-frac", type=float, default=0.08)
    ap.add_argument("--out", default=os.path.join(HERE, "data"))
    a = ap.parse_args()
    rng = random.Random(SEED)

    machines = load_jsonl(os.path.join(SYNTH, "machines.jsonl"))
    by_id = {m["machineId"]: m for m in machines}

    # hold out whole machines for eval (no leakage)
    ids = sorted(by_id)
    rng.shuffle(ids)
    n_eval = int(len(ids) * a.eval_frac)
    eval_ids = set(ids[:n_eval])

    train, evl = [], []

    # A. INTENT (reuse synthetic corpus; split by machine)
    for split_file in ["intents_train.jsonl", "intents_eval.jsonl"]:
        path = os.path.join(SYNTH, split_file)
        if not os.path.exists(path):
            continue
        rows = load_jsonl(path)
        tmp = []
        gen_intent(rows, by_id, tmp)
        for r in tmp:
            (evl if _mid(r) in eval_ids else train).append(r)

    # B. ACQUISITION (generated per machine, correct-by-construction)
    caps = {k: a.max_per_task for k in ["fact", "io", "resolve", "classify", "refuse"]}
    for mid in ids:
        tmp = []
        gen_acquisition(by_id[mid], rng, tmp, caps)
        for r in tmp:
            (evl if mid in eval_ids else train).append(r)

    rng.shuffle(train)
    os.makedirs(a.out, exist_ok=True)
    _write(os.path.join(a.out, "train.jsonl"), train)
    _write(os.path.join(a.out, "eval.jsonl"), evl)

    print(f"machines: {len(machines)} ({len(eval_ids)} held out for eval)")
    print(f"train rows: {len(train)}   eval rows: {len(evl)}")
    print("task mix (train):", _mix(train))
    print("task mix (eval): ", _mix(evl))
    print("wrote", os.path.join(a.out, "train.jsonl"), "and eval.jsonl")


def _mid(row):
    # machine id is embedded in the system context "MACHINE <id> ::"
    c = row["messages"][0]["content"]
    i = c.find("MACHINE ")
    return c[i + 8:c.find(" ::", i)] if i >= 0 else "?"


def _mix(rows):
    from collections import Counter
    return dict(Counter(r["task"] for r in rows))


def _write(path, rows):
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
