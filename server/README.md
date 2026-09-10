# CANON LLM backend — real HMI generation on your DGX A100

This is the **real "prompt → model → validated HMI"** path. The static site
(GitHub Pages) calls this server; if it's not running, the site falls back to
the deterministic compiler so the public link never breaks.

```
browser (site)  ──POST /generate──►  server.py  ──►  local LLM (vLLM/Ollama)
                                          │                 │  JSON (schema-constrained)
                                          ◄─── validated ◄──┘
```

The model **only proposes** a widget list. `server.py` validates every `ref`
against the canonical model — anything not in the model becomes `UNKNOWN` and
is not rendered. The model never touches control logic or the PLC.

## 1. Serve a model (pick ONE) — on the DGX A100

**Option A — vLLM (recommended for A100 80 GB, fastest):**
```bash
pip install vllm
# 32B coder fits one A100 80GB; use TP for 70B across GPUs
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-Coder-32B-Instruct \
  --guided-decoding-backend outlines \
  --port 8000
# 70B across 4 GPUs:  --model meta-llama/Llama-3.3-70B-Instruct --tensor-parallel-size 4
```

**Option B — Ollama (simplest):**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull qwen2.5-coder:32b
export CANON_LLM_BASE=http://localhost:11434/v1
export CANON_LLM_MODEL=qwen2.5-coder:32b
```

Model suggestions on one A100 80 GB: `Qwen2.5-Coder-32B-Instruct` (great at JSON),
`Llama-3.1-8B-Instruct` (fast). For `Llama-3.3-70B` use 2–4× A100 with tensor parallel.

## 2. Run the CANON backend
```bash
cd server
pip install -r requirements.txt
# point it at whichever server you started (defaults to vLLM on :8000):
export CANON_LLM_BASE=http://localhost:8000/v1
export CANON_LLM_MODEL=Qwen/Qwen2.5-Coder-32B-Instruct
python server.py            # listens on :8088
curl localhost:8088/health  # -> {"llm":"up", ...}
```

## 3. Connect the site
Open the site → **Generate HMI** → set **LLM endpoint** to `http://<dgx-ip>:8088`
(or run the site locally). When `/health` is `up`, generation is **real** —
you'll see the actual prompt, the model name, latency, and the validation trace.
Toll gate stays honest: rejected tags show as UNKNOWN.

### Endpoints
- `GET  /health`   → `{backend, model, llm: up|down}`
- `POST /generate` → `{ok, screen:{widgets}, unknown[], rationale, prompt, latency_ms, trace[]}`

### Security note
Bind to your LAN / VPN only, or put behind a reverse proxy. CORS is open for demo
convenience — lock it down for anything beyond a lab.
