# CANON-brain — your own model, trained once on the DGX, runs on CPU forever

A **compact CANON specialist** (3B), fine-tuned once on your DGX A100, then
exported to a **4-bit GGUF (~2 GB) that runs on any laptop CPU — no GPU ever
again**. It is not a general "super-intelligent" model (no single A100 can make
one of those); it is a disciplined domain model whose every output is still
re-checked by CANON's deterministic validator.

```
DGX A100  ── build_dataset ──► train_qlora ──► export_gguf (merge+quantize)
 (one time)                                          │
                                Ollama / llama.cpp on any CPU  ◄── no GPU
```

## One command on the DGX
```bash
cd .context/CANON_ACQUISITION/model
LLAMA_CPP=$HOME/llama.cpp ./run_on_dgx.sh
# -> out/canon-brain-3b-Q4_K_M.gguf   (ship this; needs no GPU)
```

## What it learns (correct-by-construction — the CANON engine is the teacher)
Dataset already generated in `data/` (48,222 train / 2,586 eval, split by machine so eval machines are unseen):

| task | rows | what it teaches |
|------|-----:|-----------------|
| `intent` | 23,298 | NL command → validated intent JSON (bind only to real signals) |
| `classify_file` | 7,328 | uploaded file → CANON file class (§49/50) |
| `entity_resolve` | 7,020 | tag alias (PT-401 / pt401) → canonical id (§37) |
| `refuse` | 6,624 | prompt about a tag NOT in the machine → `UNKNOWN`, never a binding (§55/67) |
| `io_map` | 1,976 | signal → Modbus area/address/dtype/scale (§25) |
| `fact_extract` | 1,976 | evidence sentence → fact JSON with `usedEvidenceIds` (§33/34) |

Every assistant label lists `usedSignalIds`, `usedEvidenceIds`, `unknowns` — the response contract from `../../CANON_RESEARCH/ai/ai_models.json`.

## Files
```
build_dataset.py   pure stdlib; regenerate data/ from the two CANON corpora
train_qlora.py     QLoRA on the A100; --base Qwen/Qwen2.5-3B-Instruct (Apache-2.0)
export_gguf.py     merge adapter → GGUF → 4-bit quantize → Ollama Modelfile
eval.py            pure stdlib; scores any OpenAI-compatible endpoint (the CPU model)
run_on_dgx.sh      the 4 steps above, one command
requirements.txt   GPU-only training deps (build/eval need none)
data/              train.jsonl (58 MB), eval.jsonl (3 MB)  ← already built
```

## Prove it works (on the CPU model, unseen machines)
```bash
llama-server -m out/canon-brain-3b-Q4_K_M.gguf --port 8000 &
python3 eval.py --url http://localhost:8000/v1 --model canon-brain
```
Reports `json_valid_rate` (≥99%), `zero_invented_tag_rate` (→100%), `refusal_recall`
(≥98%), `classify_accuracy` (≥95%). Run the same against the **stock base model**
first — the story is "our brain invents far fewer tags than the stock model," and
the deterministic validator guarantees the rest regardless.

## Honest expectations
- **Not AGI.** A 3B specialist is *narrow*: great at CANON's JSON tasks, not general reasoning. That's the right tool — the validator, not the model, is the guarantee.
- **CPU inference is slower** than GPU (a few tokens/sec on a laptop for 3B Q4) but needs zero GPU. For faster serving, keep the fp16 merged model on the DGX with vLLM; ship the GGUF for offline/edge.
- **Data is synthetic but correct-by-construction** — say so; the compiler labels it, so it scales for free and can't mislabel.
- Bigger/smarter proposals → use a 7B base (change `--base`); it still exports to GGUF, just ~4 GB and slower on CPU.
