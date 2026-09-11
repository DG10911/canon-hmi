# CANON Brain — train your own HMI-generation model on your GPU

Build a **domain-specific model** for CANON instead of calling a generic chatbot.
The idea: **CANON's deterministic compiler is the teacher.** We generate a dataset
of `(machine model + intent) → correct widget JSON` across many machine types, then
fine-tune an open model to *generalise* — while the runtime validator still
guarantees every binding.

```
compiler (teacher)  ──►  synthetic dataset  ──►  QLoRA fine-tune (your DGX A100)
                                                        │
                              serve (vLLM/Ollama)  ◄─────┘   → plug into server/server.py
```

## Pipeline (4 steps)

**1 · Generate the dataset** (self-bootstrapped from the compiler)
```bash
cd brain
python gen_dataset.py --n 6000
# → data/train.jsonl, data/eval.jsonl
# tank / drive / meter / mixer machines · ~20% include a fake-tag trap the teacher never fills
```

**2 · Fine-tune on your GPU** (QLoRA; 7B fits one A100 80GB, 32B fits too)
```bash
pip install -r requirements.txt
python train_qlora.py --base Qwen/Qwen2.5-Coder-7B-Instruct --data data/train.jsonl --out out/canon-brain
# ~20–40 min for 7B/3 epochs on one A100
```

**3 · Evaluate on held-out machines** (the metrics that matter)
```bash
python eval.py --base Qwen/Qwen2.5-Coder-7B-Instruct --adapter out/canon-brain --data data/eval.jsonl
# JSON-valid % · Binding-valid % · Hallucination % (→~0) · Widget-F1 vs teacher
```
Compare the base model vs the fine-tuned adapter — the story is *"our brain hallucinates
far fewer tags and matches the compiler more closely than the stock model."*

**4 · Serve it & connect CANON**
```bash
# merge adapter → single model, then serve with vLLM (OpenAI-compatible):
python -c "from peft import AutoPeftModelForCausalLM as M; m=M.from_pretrained('out/canon-brain'); m.merge_and_unload().save_pretrained('out/canon-brain-merged')"
vllm serve out/canon-brain-merged --served-model-name canon-brain --port 8000
# or Ollama: create a Modelfile FROM the merged dir, then `ollama create canon-brain`
cd ../server && CANON_LLM_MODEL=canon-brain python server.py
# In the app → AI Engine → endpoint http://<host>:8088 → Connect
```

## Why this is a strong final-round story
- **Your own model + your own dataset** — not a wrapper around a public API.
- **Self-bootstrapped data** — the compiler labels the data, so it scales for free and is correct-by-construction.
- **Generalises** — trained on tank/drive/meter/mixer, it proposes HMIs for machines it never saw.
- **Still guaranteed** — the model only *proposes*; `server.py`'s validator rejects any invented tag before render. The model getting better just means fewer rejections.
- **Runs on your infrastructure** — data never leaves your network.

## Honesty notes
- The dataset is **synthetic but correct-by-construction** (compiler-labelled) — say so; it's a strength, not a weakness.
- Fine-tuning improves *proposal quality*; it never bypasses validation or the PLC.
- 7B is plenty to demonstrate the pipeline; 32B/70B (DGX, tensor-parallel) is for higher-fidelity proposals.
