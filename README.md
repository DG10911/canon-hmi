# CANON — Engineering Intelligence → Verified Operator Experience

**PS2 · Schneider Electric Smart HMI Innovation Marathon · Team DigiSeva**

CANON turns real industrial engineering inputs into a **validated, live operator HMI**.
An AI **interprets**, a deterministic **canonical model defines truth**, a **validator guarantees
safety**, and a **simulator runtime** demonstrates reality — **nothing is ever invented**.

> ENGINEERING DATA → CORRECT CONTEXT → CORRECT MODEL → CORRECT HMI &nbsp;—&nbsp; *not* PROMPT → PRETTY SCREEN.

---

## Repository layout

| Path | What it is |
|------|------------|
| **`CANON_PLATFORM/`** | The runnable prototype — FastAPI backend + vanilla-JS SPA + deterministic simulator. **Start here.** |
| `CANON_PLATFORM/presentation.html` | The pitch deck (PS2, inputs, context, outputs, live-embed, features). |
| `CANON_ACQUISITION/` | P0 acquisition pipeline — 70 verified sources, 37-dataset corpus, external ICS merge, model training/export. |
| `CANON_RESEARCH/` | Resource verification + synthetic NL→intent dataset generation. |
| `IMPLEMENTATION_STATUS.md` | Honest WORKING / PARTIAL / MISSING audit against the spec. |

---

## Run the prototype locally

```bash
cd CANON_PLATFORM
pip install -r requirements.txt
./run.sh                 # or: python -m uvicorn app:app --port 8090
```

Then open:

- **Platform:** http://localhost:8090
- **Pitch deck (with live embed):** http://localhost:8090/presentation

Demo path: open **TK-401** → **HMI Studio** → generate a screen → click **START** on the pump
(permissive-gated) → change a signal range in **Change-impact** → **restore** a revision.

### Optional: the CANON-Brain model
The platform is **brain-first** — if a llama.cpp/Ollama endpoint is serving the fine-tuned
Qwen2.5-3B GGUF on `:8000`, natural-language generation/edit is interpreted by the model and
validated deterministically. With no brain, it shows an honest **BRAIN OFFLINE** state (never a
silent fake). See `CANON_ACQUISITION/model/`.

---

## Deploy a live URL

GitHub hosts the code; the **static deck** works on GitHub Pages, but the **live server** needs a
runner. One-click options (all read this repo):

- **Docker:** `docker build -t canon CANON_PLATFORM && docker run -p 8090:8090 canon`
- **Render / Railway / Fly:** point the service at `CANON_PLATFORM/` (see `render.yaml`).
- **Hugging Face Spaces:** Docker Space using `CANON_PLATFORM/Dockerfile`.

See `CANON_PLATFORM/DEPLOY.md` for details.

---

## Guarantees (what makes it real, not a demo)

- **No hallucination** — the validator drops any invented tag / command / target / permissive.
- **Evidence-first** — every HMI element traces element → signal → fact → evidence → source.
- **Honest runtime** — values come from a deterministic **SIMULATOR** (labelled), never fake "LIVE".
- **The model interprets; it never controls the PLC** — the canonical model is the authority.

*Reference ICS datasets (SWaT, CMAPSS, …) are folded in as CANDIDATE/OBSERVED, never authoritative.
v2 model accuracy figures in the deck are projected targets, measured after training completes.*
