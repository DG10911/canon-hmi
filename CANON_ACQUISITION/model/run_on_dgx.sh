#!/usr/bin/env bash
# CANON-brain — one-time training on the DGX A100, then a CPU-portable model.
# GPU is used ONLY by this script. The output .gguf runs on any laptop CPU after.
set -euo pipefail
cd "$(dirname "$0")"

BASE="${BASE:-Qwen/Qwen2.5-3B-Instruct}"     # Apache-2.0, 3B -> ~2GB Q4 GGUF
QUANT="${QUANT:-Q4_K_M}"
LLAMA_CPP="${LLAMA_CPP:-$HOME/llama.cpp}"     # export LLAMA_CPP=/path if elsewhere
PY="${PY:-python}"                            # conda env's `pip` wrapper can be broken;
command -v "$PY" >/dev/null 2>&1 || PY=python3 #   call pip via `python -m pip` instead.

echo "== 0. deps (once) =="
"$PY" -m pip install -q -r requirements.txt

echo "== 1. dataset =="
if [ -s data/train.jsonl ] && [ -s data/eval.jsonl ]; then
  echo "   data/ already present ($(wc -l < data/train.jsonl) train rows) — skipping rebuild."
  echo "   (rebuild only needs ../../CANON_RESEARCH; not required on the DGX)"
else
  "$PY" build_dataset.py          # -> data/train.jsonl, data/eval.jsonl (needs CANON_RESEARCH)
fi

echo "== 2. QLoRA fine-tune on the A100 (~20-40 min) =="
"$PY" train_qlora.py --base "$BASE" --data data/train.jsonl --out out/canon-brain-3b

echo "== 3. merge -> GGUF -> ${QUANT} (the CPU model) =="
if [ ! -x "$LLAMA_CPP/convert_hf_to_gguf.py" ] && [ ! -f "$LLAMA_CPP/convert_hf_to_gguf.py" ]; then
  echo "!! llama.cpp not found at $LLAMA_CPP — clone & build it:"
  echo "   git clone https://github.com/ggml-org/llama.cpp $LLAMA_CPP && cmake -B $LLAMA_CPP/build $LLAMA_CPP && cmake --build $LLAMA_CPP/build -j"
  exit 1
fi
"$PY" export_gguf.py --base "$BASE" --adapter out/canon-brain-3b --llama-cpp "$LLAMA_CPP" --quant "$QUANT"

echo "== 4. package for CPU (no GPU from here on) =="
if command -v ollama >/dev/null; then
  ollama create canon-brain -f out/Modelfile
  echo "Serve on CPU:  ollama run canon-brain"
  echo "Eval:          ollama serve & "$PY" eval.py --url http://localhost:11434/v1 --model canon-brain"
else
  echo "Serve on CPU:  $LLAMA_CPP/build/bin/llama-server -m out/canon-brain-3b-${QUANT}.gguf --port 8000"
  echo "Eval:          "$PY" eval.py --url http://localhost:8000/v1 --model canon-brain"
fi
echo "== done. Ship out/canon-brain-3b-${QUANT}.gguf — it needs no GPU. =="
