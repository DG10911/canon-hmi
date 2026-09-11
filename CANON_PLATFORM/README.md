# CANON Platform

A projects-based web app for the full CANON flow, reusing everything from the
engine: **upload a machine project → it builds the canonical model ("brain"
context) → generate an HMI screen from a prompt → refine the screen with more
prompts.** Every binding is validated against the model — nothing can be
invented (§56/§67).

```
┌──────────────┐  upload   ┌──────────────┐  "pump page"  ┌──────────────┐  "add a trend"
│ machine JSON │ ────────▶ │ canonical    │ ───────────▶  │ HMI screen   │ ───────────▶ edited screen
│ (assets,     │ normalize │ model        │  deterministic│ (widgets +   │  validated   (no invented
│  signals,…)  │           │ (the brain)  │  assembly     │  evidence)   │  edit         tags ever)
└──────────────┘           └──────────────┘               └──────────────┘
```

## Run
```bash
cd .context/CANON_PLATFORM
./run.sh                      # installs deps, serves http://localhost:8090
```
Open **http://localhost:8090**.

## What you can do
1. **Projects dashboard** — the 3 seeded machines (TK-401 · PACK-07/M580 · MIX-02/M241) with live status, controller, asset/signal/alarm counts. **+ New Project** to upload your own.
2. **Upload a machine project** — a JSON with `assets / signals / commands (or contracts) / alarms` (the `canon.machine.v2` shape, e.g. `../CANON_RESEARCH/datasets/canon_demo_machine.json`). It's normalized into the canonical model and appears as a project. (Or "Synthesise a demo machine" for a quick one.)
3. **Open a project → Model tab** — the canonical model: assets, signals (with units/ranges), commands & permissives.
4. **HMI Studio tab → Generate** — type `operator page for the pump`, `show me the whole line`, `tank level`… It analyzes the machine context, picks the scope from **real assets only**, and assembles a validated screen (rendered widgets with evidence counts).
5. **Refine with a prompt** — `add a trend for PT401`, `remove alarms`, `show pressure value`. The edit is applied deterministically and **any tag not in the model is refused** ("no invented tags").

## Files
```
app.py            FastAPI backend (projects, upload, generate, edit) + serves the UI
platform_core.py  pure-stdlib engine: normalize machine · synth machine · assemble screen · analyze scope · apply edit
web/index.html     single-page UI (dashboard + project + HMI studio)
projects/*.json    persisted canonical models (3 seeds; your uploads land here too)
requirements.txt   fastapi · uvicorn · python-multipart
run.sh             one-command launch
```

## How it reuses the "brain"
- The **canonical model** is the brain's knowledge for a machine — the same evidence-first model the acquisition pipeline produces.
- **Screen generation + edits are deterministic and validated**, exactly like `../CANON_ACQUISITION/model/canon_screen.py` and `canon_hmi.py`, so a screen can never bind a hallucinated tag.

## Part A — wire the trained CANON-brain (v2) in
The platform is **brain-first and auto-detecting**. Serve the v2 GGUF and it connects itself:
```bash
# on the DGX (after training/export):
llama-server -m out/canon-brain-3b-v2-Q4_K_M.gguf --port 8000 &
# from the laptop running the platform, tunnel the endpoint to localhost:8000:
ssh -N -L 8000:localhost:8000 dgx
```
The platform probes `http://localhost:8000/v1` on startup (override with `CANON_LLM_BASE`).
If it's live, the sidebar shows **Brain ● CONNECTED** and NL requests are interpreted by the
model; if not, it runs the deterministic engine and shows a **Connect v2 brain** button. A
mid-session drop correctly surfaces **BRAIN OFFLINE** — never a silent fallback (§9).

## Part B — reference corpus grounding
The acquisition run merges **23 real ICS/sensor datasets → 939 OBSERVED signal series**
(SWaT, NASA C-MAPSS, steel-plate faults, SCADA pipeline, motor telemetry…). Pull them in:
```bash
bash sync_reference.sh          # copies seed/reference_signals.jsonl (+sources, meta)
```
Then the **Model tab → Reference grounding** panel cross-references each machine signal
(by measure: pressure/level/temperature/flow/speed…) against comparable real-world sensors,
showing their OBSERVED ranges. This is **CANDIDATE / OBSERVED corroboration only — never
authoritative machine truth (§62)**. Endpoints: `GET /api/reference`, `GET /api/projects/{id}/grounding`.

## Guarantee
Upload → model → generate → edit, and at every step: **the model proposes, the
canonical model defines, the validator checks.** Invented assets/tags are
refused, not rendered. Try `build a page for reactor R500` or `add value for
FT999` and watch it refuse.
