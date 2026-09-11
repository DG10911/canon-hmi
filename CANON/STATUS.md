# CANON — build status (honest)

**Live site:** https://dg10911.github.io/canon-hmi/  ·  **PS2** · Team DigiSeva

## ✅ Implemented & verified (real, working now)
- **Full product site + app** — Schneider-themed landing → 10-screen engineering app.
- **Real WebGL 3D process twin** (Three.js) — tank/pump/valve/pipes, live-bound, rotatable.
- **Real recorded dataset** — SKAB (Skoltech Anomaly Benchmark), 240 pts / 96 labelled anomalies, replayed to drive PT/flow/temp and raise real alarms.
- **Real LLM backend** (`server/server.py`) — FastAPI, OpenAI-compatible (vLLM/Ollama), JSON-schema-constrained output, **server-side validation** against the canonical model. Proven end-to-end: model proposed 6 widgets → **5 bound, 1 invented tag rejected as UNKNOWN**. `/health` + `/generate`.
- **Generate screen wired to it** — set your DGX endpoint → real generation with exact prompt, model name, latency, validation trace shown. Offline → deterministic compiler (same guarantees), so the public link never breaks.
- **Schneider equipment catalog** (`equipment.js`) — Modicon M241/M580, Altivar ATV630/ATV320, PowerLogic PM8000, TeSys island, Lexium 28, Harmony — with representative register/parameter maps + protocols.
- **PLC-authoritative control path** — START rejected on false permissive; stale/comm-loss disable commands.
- **Change-impact + governance** — R17→R18 impact traversal, regenerate, regression, approval, audit.

## 🖥️ Needs your DGX A100 (real, ready to run — I can't run a GPU model here)
1. `cd server && pip install -r requirements.txt`
2. Serve a model: `vllm serve Qwen/Qwen2.5-Coder-32B-Instruct --port 8000` (or Ollama).
3. `python server.py` → set the site's **LLM endpoint** to `http://<dgx>:8088`.
Full steps in `server/README.md`. Suggested models on one A100 80GB: Qwen2.5-Coder-32B, Llama-3.1-8B; 70B needs tensor-parallel.

## 🚧 Not yet real (roadmap — what I *can* build next)
- **Live device I/O** — replace the SKAB replay with a real OPC UA / Modbus poller (node-opcua / pymodbus in the backend) reading a Modicon M580 or Altivar over the network. Browser can't speak OPC UA directly, so this lives in `server.py`.
- **Model-driven unit swap** — clicking "Generate HMI for this device" on the Devices screen currently opens Generate; wiring a selected Schneider device to *rebuild the canonical model* (so TK-401 becomes an ATV630 drive faceplate, a PM8000 energy dashboard, etc.) is a focused next step.
- **Export adapter** — CANON layout → Vijeo Designer / EcoStruxure Operator Terminal Expert project (roadmap; today output is ISA-101-aligned HTML).
- **Ingestion** — parse a real AutomationML / OPC UA nodeset / MTP file into the canonical model (today the model + equipment maps are curated).
- **Auth/RBAC** for the approve step; persistence of revisions.

## ⚠️ Known limitations / honesty
- PLC is **SIMULATED**; CANON is **not safety-rated** and does not implement safety-rated control.
- Equipment register addresses are **typical per manuals — verify against firmware**.
- Standards are **"informed by / aligned to"**, never "certified/compliant".
- Data is a **replayed real dataset**, not a live plant feed (until the poller above is added).
- Three.js is vendored (`three.min.js`); WebGL required for the 3D twin (graceful message otherwise).

## What each file is
`index.html` app+site · `three.min.js` 3D · `data.js` SKAB data · `equipment.js` Schneider catalog · `server/` real LLM backend.
