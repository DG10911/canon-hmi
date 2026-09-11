#!/usr/bin/env python3
"""Blend open function-calling datasets into CANON-brain training (v2 model).

Run on the DGX (needs internet / HF access). Downloads the OPEN instruction/
function-calling datasets, normalises each to CANON's chat format
({"messages":[...]}), caps the count, and blends them with the synthetic CANON
corpus so CANON-specific data stays dominant (default 75% CANON / 25% external).

  python mix_external.py --out data/train_v2.jsonl --external-frac 0.25
  python train_qlora.py --data data/train_v2.jsonl --out out/canon-brain-3b-v2 --max-samples 12000

Gated datasets (Salesforce xLAM / APIGen — cc-by-nc / login) are SKIPPED unless
you pass --include-gated and have accepted their terms. We never bypass access.
"""
from __future__ import annotations
import argparse
import json
import os
import random

# open, non-gated function-calling / tool-use datasets (HF ids)
OPEN_SOURCES = [
    "glaiveai/glaive-function-calling-v2",
    "NousResearch/hermes-function-calling-v1",
]
GATED_SOURCES = [
    "Salesforce/xlam-function-calling-60k",   # cc-by-4.0 but login/agreement
    "Salesforce/APIGen-MT-5k",                # cc-by-nc-4.0 (non-commercial)
]

ROLE_MAP = {"human": "user", "user": "user", "gpt": "assistant",
            "assistant": "assistant", "system": "system", "tool": "tool",
            "function": "tool", "function_call": "assistant", "observation": "tool"}


def to_messages(row: dict):
    """Best-effort normalise a HF row to a [{'role','content'}, ...] list."""
    # 1. already-chat formats
    if isinstance(row.get("messages"), list):
        out = [{"role": ROLE_MAP.get(m.get("role", "user"), "user"),
                "content": str(m.get("content", ""))} for m in row["messages"] if m.get("content")]
        return out or None
    if isinstance(row.get("conversations"), list):
        out = [{"role": ROLE_MAP.get(m.get("from", "user"), "user"),
                "content": str(m.get("value", ""))} for m in row["conversations"] if m.get("value")]
        return out or None
    # 2. glaive: {"system": "...", "chat": "USER: ... ASSISTANT: ..."}
    if "chat" in row and isinstance(row["chat"], str):
        msgs = []
        if row.get("system"):
            msgs.append({"role": "system", "content": str(row["system"])})
        text = row["chat"]
        # split on USER:/ASSISTANT: markers, keep order
        import re
        parts = re.split(r"(USER:|ASSISTANT:|FUNCTION RESPONSE:)", text)
        role = "user"
        buf = ""
        for p in parts:
            if p == "USER:":
                if buf.strip():
                    msgs.append({"role": role, "content": buf.strip()})
                role, buf = "user", ""
            elif p == "ASSISTANT:":
                if buf.strip():
                    msgs.append({"role": role, "content": buf.strip()})
                role, buf = "assistant", ""
            elif p == "FUNCTION RESPONSE:":
                if buf.strip():
                    msgs.append({"role": role, "content": buf.strip()})
                role, buf = "tool", ""
            else:
                buf += p
        if buf.strip():
            msgs.append({"role": role, "content": buf.strip()})
        return msgs or None
    # 3. xlam: {"query","tools","answers"}
    if "query" in row and "answers" in row:
        tools = row.get("tools", "")
        user = f"{row['query']}\n\nAvailable tools:\n{tools}"
        ans = row["answers"]
        ans = ans if isinstance(ans, str) else json.dumps(ans)
        return [{"role": "user", "content": user},
                {"role": "assistant", "content": ans}]
    # 4. prompt/completion
    if row.get("prompt") and row.get("completion"):
        return [{"role": "user", "content": str(row["prompt"])},
                {"role": "assistant", "content": str(row["completion"])}]
    return None


def load_external(sources, cap_each, seed):
    from datasets import load_dataset
    rng = random.Random(seed)
    rows = []
    for sid in sources:
        try:
            ds = load_dataset(sid, split="train")
        except Exception as e:
            print(f"  SKIP {sid}: {e}")
            continue
        n = 0
        idxs = list(range(len(ds)))
        rng.shuffle(idxs)
        for i in idxs:
            if n >= cap_each:
                break
            msgs = to_messages(ds[i])
            if msgs and len(msgs) >= 2:
                rows.append({"messages": msgs, "task": "external-toolcall", "label": "accept",
                             "source": sid})
                n += 1
        print(f"  {sid}: {n} rows")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--canon", default="data/train.jsonl", help="synthetic CANON corpus")
    ap.add_argument("--out", default="data/train_v2.jsonl")
    ap.add_argument("--external-frac", type=float, default=0.25,
                    help="fraction of the blend that is external (rest is CANON)")
    ap.add_argument("--cap-each", type=int, default=6000, help="max rows per external dataset")
    ap.add_argument("--include-gated", action="store_true",
                    help="also pull gated datasets (only if you accepted their HF terms)")
    ap.add_argument("--seed", type=int, default=401)
    a = ap.parse_args()

    canon = [json.loads(l) for l in open(a.canon, encoding="utf-8") if l.strip()]
    print(f"CANON synthetic rows: {len(canon)}")

    srcs = list(OPEN_SOURCES) + (GATED_SOURCES if a.include_gated else [])
    print(f"downloading external ({'incl. gated' if a.include_gated else 'open only'}) ...")
    external = load_external(srcs, a.cap_each, a.seed)
    print(f"external rows: {len(external)}")
    if not external:
        print("no external rows obtained (offline or gated) — writing CANON only.")

    # size external to the requested fraction of the final blend
    rng = random.Random(a.seed)
    if external and 0 < a.external_frac < 1:
        target_ext = int(len(canon) * a.external_frac / (1 - a.external_frac))
        rng.shuffle(external)
        external = external[:target_ext]
    blend = canon + external
    rng.shuffle(blend)

    with open(a.out, "w", encoding="utf-8") as fh:
        for r in blend:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
    frac = (len(external) / len(blend)) if blend else 0
    print(f"wrote {a.out}: {len(blend)} rows ({len(external)} external = {frac:.0%})")
    print(f"train:  python train_qlora.py --data {a.out} --out out/canon-brain-3b-v2 --max-samples 12000")


if __name__ == "__main__":
    main()
