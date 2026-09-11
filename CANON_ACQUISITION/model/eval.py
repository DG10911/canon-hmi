#!/usr/bin/env python3
"""Evaluate CANON-brain — the metrics that matter (anti-hallucination first).

Runs against ANY OpenAI-compatible /v1/chat/completions endpoint, so it scores
the FINAL CPU model exactly as it will be served:

  # llama.cpp server (CPU, no GPU):
  llama-server -m out/canon-brain-3b-Q4_K_M.gguf --port 8000 &
  python3 eval.py --url http://localhost:8000/v1 --model canon-brain --data data/eval.jsonl

  # or Ollama:
  ollama serve & ; ollama create canon-brain -f out/Modelfile
  python3 eval.py --url http://localhost:11434/v1 --model canon-brain

Pure stdlib (urllib). Metrics (held-out, unseen machines):
  json_valid_rate          parses as one JSON object            target >= 0.99
  zero_invented_tag_rate   every usedSignalId is in the machine  target  1.00
  refusal_recall           refuse-tasks answered with unknowns   target >= 0.98
  classify_accuracy        file_class == teacher label           target >= 0.95
  exact_field_match        key fields equal the teacher label    (informational)
"""
from __future__ import annotations
import argparse
import json
import re
import urllib.request

SIG_RE = re.compile(r"MACHINE \S+ :: signals=\[([^\]]*)\]")


def machine_signals(system_content: str) -> set[str]:
    m = SIG_RE.search(system_content)
    if not m:
        return set()
    return {tok.split("(")[0].strip() for tok in m.group(1).split(",") if tok.strip()}


def call(url, model, messages, timeout=120):
    body = json.dumps({"model": model, "messages": messages, "temperature": 0,
                       "max_tokens": 512,
                       "response_format": {"type": "json_object"}}).encode()  # force valid JSON
    req = urllib.request.Request(url.rstrip("/") + "/chat/completions", data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer x"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def parse_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]
    try:
        return json.loads(text[text.find("{"): text.rfind("}") + 1])
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000/v1")
    ap.add_argument("--model", default="canon-brain")
    ap.add_argument("--data", default="data/eval.jsonl")
    ap.add_argument("--limit", type=int, default=600)
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(a.data)][: a.limit]
    n = 0
    json_ok = invented_ok = refusal_ok = refusal_n = classify_ok = classify_n = exact_ok = 0

    for r in rows:
        n += 1
        sys_c, usr = r["messages"][0]["content"], r["messages"][1]["content"]
        gold = json.loads(r["messages"][2]["content"])
        out = call(a.url, a.model, [{"role": "system", "content": sys_c},
                                    {"role": "user", "content": usr}])
        pred = parse_json(out)
        if pred is None:
            continue
        json_ok += 1

        # zero invented tags: usedSignalIds must be a subset of this machine's signals
        sigs = machine_signals(sys_c)
        used = set(pred.get("usedSignalIds", []) or [])
        if used <= sigs:
            invented_ok += 1

        if r["task"] == "refuse":
            refusal_n += 1
            if pred.get("unknowns") and not used:
                refusal_ok += 1
        if r["task"] == "classify_file":
            classify_n += 1
            if pred.get("file_class") == gold.get("file_class"):
                classify_ok += 1
        # informational exact match on the headline field
        if pred.get("object") == gold.get("object") or pred.get("command") == gold.get("command"):
            exact_ok += 1

    def pct(x, d):
        return f"{(100.0 * x / d):.1f}%" if d else "n/a"

    print(f"model={a.model}  n={n}")
    print(f"  json_valid_rate        {pct(json_ok, n)}   (target >= 99%)")
    print(f"  zero_invented_tag_rate {pct(invented_ok, json_ok)}   (target 100%)")
    print(f"  refusal_recall         {pct(refusal_ok, refusal_n)}   (target >= 98%)")
    print(f"  classify_accuracy      {pct(classify_ok, classify_n)}   (target >= 95%)")
    print(f"  exact_field_match      {pct(exact_ok, n)}   (informational)")
    print("Note: the deterministic validator drops any invented tag regardless — this")
    print("measures how OFTEN the model is already right before that safety net.")


if __name__ == "__main__":
    main()
