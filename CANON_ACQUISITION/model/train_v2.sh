#!/usr/bin/env bash
# CANON-brain v2 — one command on the DGX. Blends open function-calling data,
# fine-tunes, exports the CPU GGUF. Robust: if HF is unreachable it falls back to
# the rebalanced CANON data so training still runs.
#
#   source ~/canon-venv/bin/activate     # (or the script tries to)
#   ./train_v2.sh
# knobs:  MAXS=20000  EPOCHS=2  CUDA_VISIBLE_DEVICES=0  LLAMA_CPP=$HOME/llama.cpp
set -euo pipefail
cd "$(dirname "$0")"
source ~/canon-venv/bin/activate 2>/dev/null || true
BASE="Qwen/Qwen2.5-3B-Instruct"
LLAMA_CPP="${LLAMA_CPP:-$HOME/llama.cpp}"

echo "== 1/3 · build v2 dataset (CANON + open function-calling: glaive/Hermes) =="
if python3 mix_external.py --out data/train_v2.jsonl --external-frac 0.25; then
  echo "   blended dataset ready"
else
  echo "   mix_external failed (offline/HF blocked) → falling back to rebalanced CANON data"
  python3 rebalance.py && cp data/train_balanced.jsonl data/train_v2.jsonl
fi

echo "== 2/3 · QLoRA fine-tune v2 on the A100 =="
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" python3 train_qlora.py \
  --data data/train_v2.jsonl --out out/canon-brain-3b-v2 \
  --epochs "${EPOCHS:-2}" --max-samples "${MAXS:-20000}"

echo "== 3/3 · export CPU GGUF =="
python3 export_gguf.py --base "$BASE" --adapter out/canon-brain-3b-v2 --llama-cpp "$LLAMA_CPP" --quant Q4_K_M

echo
echo "DONE → out/canon-brain-3b-v2-Q4_K_M.gguf"
echo "Serve v2 on :8000 (platform picks it up automatically):"
echo "  pkill -f llama-server; $LLAMA_CPP/build/bin/llama-server -m out/canon-brain-3b-v2-Q4_K_M.gguf --port 8000 > /tmp/llama.log 2>&1 &"
