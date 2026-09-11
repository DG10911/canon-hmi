#!/usr/bin/env python3
"""Merge LoRA -> convert to GGUF -> 4-bit quantize -> package for CPU inference.

This is the "never need a GPU again" step. Run it on the DGX right after training
(the merge needs some RAM/VRAM once); the OUTPUT .gguf then runs on any laptop CPU
via Ollama or llama.cpp — no GPU, no Python, ~2 GB for a 3B model at Q4_K_M.

  python export_gguf.py --base Qwen/Qwen2.5-3B-Instruct \
      --adapter out/canon-brain-3b --llama-cpp /path/to/llama.cpp \
      --quant Q4_K_M

Produces:
  out/canon-brain-3b-merged/            (fp16 HF model)
  out/canon-brain-3b-f16.gguf           (unquantized GGUF)
  out/canon-brain-3b-Q4_K_M.gguf        (the CPU model you ship)
  out/Modelfile                         (ollama create -f out/Modelfile canon-brain)
"""
import argparse
import os
import subprocess
import sys


def sh(cmd):
    print("+", " ".join(cmd))
    subprocess.check_call(cmd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="Qwen/Qwen2.5-3B-Instruct")
    ap.add_argument("--adapter", default="out/canon-brain-3b")
    ap.add_argument("--llama-cpp", required=True,
                    help="path to a cloned+built llama.cpp (has convert_hf_to_gguf.py and llama-quantize)")
    ap.add_argument("--quant", default="Q4_K_M",
                    help="Q4_K_M (best CPU tradeoff) | Q5_K_M (higher quality) | Q8_0")
    ap.add_argument("--outdir", default="out")
    a = ap.parse_args()

    # fail clearly if training hasn't produced the adapter yet (else peft tries
    # to fetch the path as a HuggingFace repo id and 404s confusingly).
    if not os.path.isfile(os.path.join(a.adapter, "adapter_config.json")):
        print(f"ERROR: no adapter at '{a.adapter}' (adapter_config.json missing).\n"
              f"       Run train_qlora.py first — it saves the LoRA adapter there.",
              file=sys.stderr)
        sys.exit(2)

    merged = os.path.join(a.outdir, "canon-brain-3b-merged")
    f16 = os.path.join(a.outdir, "canon-brain-3b-f16.gguf")
    quant = os.path.join(a.outdir, f"canon-brain-3b-{a.quant}.gguf")

    # 1. merge adapter into the base weights
    print(">> merging LoRA adapter into base weights ...")
    from peft import AutoPeftModelForCausalLM
    from transformers import AutoTokenizer
    m = AutoPeftModelForCausalLM.from_pretrained(a.adapter, torch_dtype="auto")
    m = m.merge_and_unload()
    m.save_pretrained(merged, safe_serialization=True)
    AutoTokenizer.from_pretrained(a.base).save_pretrained(merged)

    # 2. HF -> GGUF (f16)
    conv = os.path.join(a.llama_cpp, "convert_hf_to_gguf.py")
    sh([sys.executable, conv, merged, "--outfile", f16, "--outtype", "f16"])

    # 3. quantize to a CPU-friendly 4-bit build
    qbin = os.path.join(a.llama_cpp, "llama-quantize")
    if not os.path.exists(qbin):
        qbin = os.path.join(a.llama_cpp, "build", "bin", "llama-quantize")
    sh([qbin, f16, quant, a.quant])

    # 4. Ollama Modelfile (deterministic decoding for JSON discipline)
    modelfile = os.path.join(a.outdir, "Modelfile")
    with open(modelfile, "w") as fh:
        fh.write(_MODELFILE.format(gguf=os.path.abspath(quant)))
    size_mb = os.path.getsize(quant) / 1e6
    print(f"\nDONE. CPU model: {quant}  (~{size_mb:.0f} MB)")
    print("Package for CPU:  ollama create canon-brain -f", modelfile)
    print("Run with NO GPU:  ollama run canon-brain   (or llama-server -m {} --port 8000)".format(quant))


_MODELFILE = '''FROM {gguf}

# Deterministic, JSON-only decoding — CANON-brain must not free-associate.
PARAMETER temperature 0
PARAMETER top_p 1
PARAMETER repeat_penalty 1.05
PARAMETER num_ctx 4096

SYSTEM """You are CANON-brain. You NEVER invent tags, commands, alarms, products or facts. \
You bind only to identifiers present in the provided MACHINE model or EVIDENCE. Unknown \
identifiers go under "unknowns" and are never bound. You emit a single valid JSON object \
and nothing else, always listing usedSignalIds, usedEvidenceIds and unknowns. A downstream \
deterministic validator re-checks every binding and drops anything you got wrong."""
'''


if __name__ == "__main__":
    main()
