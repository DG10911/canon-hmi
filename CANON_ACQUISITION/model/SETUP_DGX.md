# Running CANON-brain on the DGX A100

The code lives in your Conductor workspace on your **laptop**, not on the DGX.
Copy it over first, then run. `data/` (the 61 MB training set) is already built and
travels with the folder, so the DGX does **not** need the rest of the repo.

## 1. On your LAPTOP (a new terminal, NOT inside the ssh session)
```bash
rsync -avz --progress \
  "/Users/devanshgoenka/conductor/workspaces/dgrfrfeerf/santo-domingo/.context/CANON_ACQUISITION" \
  dgx:~/
```
(Uses your existing `dgx` ssh alias. ~65 MB total.)

## 2. On the DGX — one-time tool setup
```bash
# build tools for the CPU/GGUF export step
git clone https://github.com/ggml-org/llama.cpp ~/llama.cpp
cmake -B ~/llama.cpp/build ~/llama.cpp && cmake --build ~/llama.cpp/build -j
```

## 2b. IMPORTANT — make a CUDA env (do NOT reuse a CPU-only torch env)
The shared `voxshield` env ships **CPU-only torch** (`torch 2.11.0+cpu`), which
cannot use the A100 and breaks `bitsandbytes` 4-bit. Create a clean CUDA env:
```bash
conda deactivate
conda create -n canon python=3.11 -y
conda activate canon
pip install torch --index-url https://download.pytorch.org/whl/cu124   # if this fails, try cu121
pip install "transformers>=4.44" "peft>=0.12" "trl>=0.9" bitsandbytes accelerate datasets sentencepiece
# sanity — must print True:
python -c "import torch; print('CUDA?', torch.cuda.is_available(), torch.version.cuda)"
```
Do NOT install torchvision here — it is not needed and a mismatched build crashes
transformers (`operator torchvision::nms does not exist`). train_qlora.py also sets
TRANSFORMERS_NO_TORCHVISION=1 as a guard.

## 3. On the DGX — train once, export the CPU model
```bash
cd ~/CANON_ACQUISITION/model
chmod +x run_on_dgx.sh
LLAMA_CPP=$HOME/llama.cpp ./run_on_dgx.sh
```
This installs deps, fine-tunes on the A100 (~20–40 min), then merges + quantizes to
`out/canon-brain-3b-Q4_K_M.gguf` (~2 GB) — the file that runs on any laptop CPU.

### Just train (skip export) if you prefer step-by-step
```bash
cd ~/CANON_ACQUISITION/model
pip install -r requirements.txt
python3 train_qlora.py --base Qwen/Qwen2.5-3B-Instruct --data data/train.jsonl --out out/canon-brain-3b
python3 export_gguf.py  --base Qwen/Qwen2.5-3B-Instruct --adapter out/canon-brain-3b --llama-cpp $HOME/llama.cpp --quant Q4_K_M
```

## 4. Copy the CPU model back to your laptop (no GPU needed to run it)
```bash
# on the laptop:
rsync -avz dgx:~/CANON_ACQUISITION/model/out/canon-brain-3b-Q4_K_M.gguf ./
ollama create canon-brain -f out/Modelfile     # or: llama-server -m canon-brain-3b-Q4_K_M.gguf --port 8000
```

## Notes
- You are in the `voxshield` conda env — that's fine; `pip install -r requirements.txt` targets it.
- `bitsandbytes` needs CUDA; it's already an A100 so fine.
- If `pip` is slow, the training deps are: torch, transformers, datasets, peft, trl, bitsandbytes, accelerate, sentencepiece.
