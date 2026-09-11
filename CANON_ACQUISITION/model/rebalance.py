#!/usr/bin/env python3
"""Rebalance train.jsonl to over-weight the weak tasks (classify + refuse).

The v1 eval showed refusal_recall ~92% and classify ~69% because the 8k-subset /
1-epoch run under-fed those tasks. This keeps ALL classify + refuse + fact + io
rows and caps the abundant intent/resolve rows, so a v1.1 train sees the hard
tasks far more often — without ballooning training time.

  python3 rebalance.py                 # -> data/train_balanced.jsonl
"""
from __future__ import annotations
import argparse
import json
import random
from collections import Counter

# per-task cap (None = keep all). Weak tasks kept whole; abundant ones trimmed.
CAPS = {
    "classify_file": None, "refuse": None, "fact_extract": None, "io_map": None,
    "entity_resolve": 3000, "intent": 5000,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/train.jsonl")
    ap.add_argument("--out", default="data/train_balanced.jsonl")
    ap.add_argument("--seed", type=int, default=401)
    a = ap.parse_args()
    rng = random.Random(a.seed)

    by_task = {}
    for line in open(a.inp, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        by_task.setdefault(r.get("task", "?"), []).append(r)

    out = []
    for task, rows in by_task.items():
        cap = CAPS.get(task)
        if cap is not None and cap < len(rows):
            rng.shuffle(rows)
            rows = rows[:cap]
        out += rows
    rng.shuffle(out)

    with open(a.out, "w", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")

    print("source mix:", dict(Counter(t for t in by_task for _ in by_task[t]) if False else
                              {t: len(v) for t, v in by_task.items()}))
    print("balanced mix:", dict(Counter(r["task"] for r in out)))
    print(f"wrote {a.out}: {len(out)} rows")
    print(f"train v1.1: python train_qlora.py --data {a.out} --out out/canon-brain-3b-v11 --epochs 2")


if __name__ == "__main__":
    main()
