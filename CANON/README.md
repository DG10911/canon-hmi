# CANON — Machine Context → Dynamic HMI → Verified Control
**Team DigiSeva · Schneider HMI Hackathon 2026 · PS2** (dynamic HMI generation at runtime + machine control).

Self-contained, offline, single-file web app (`index.html`). One **canonical machine model** (TK-401 process unit) drives every screen.

## The loop it demonstrates (all real, deterministic)
1. **Machine Context** → fused into a **canonical model** (typed signals, commands, alarms, provenance, truth states).
2. **Generate HMI** — natural-language intent → **PROPOSE → COMPILE → VALIDATE**: a deterministic parser (LLM-adapter-ready) proposes a layout; the compiler validates every binding against the model and **cannot invent a tag** (unresolved → UNKNOWN). Size toggle: small/medium/large from one model.
3. **Runtime / HMI** — operator drives the generated screen; **PLC-authoritative** command path: START is **REJECTED** when `XV401_OPEN_FB=FALSE`; open the valve → authorized + verified. Data-quality (LIVE/STALE/UNKNOWN/SIMULATED); stale → controls disabled.
4. **Engineering Graph** — traceability that drives impact.
5. **Change Impact** — change PT401 `0–10 → 0–16 bar` → DIRECT/INDIRECT/NOT-AFFECTED/UNKNOWN → regenerate HMI → regression → approve → new baseline (R18).
6. **Validation** + **Governance** — generated tests, approval state machine, revisions, audit.

Hover any HMI widget to see its binding chain (signal → PLC var → range → quality → revision → truth state).

## Honesty
NL parsing is a **deterministic parser with an LLM adapter point** (no cloud LLM offline). PLC = **SIMULATED**. No certification/novelty claims. AI proposes · model defines · validator checks · engineer approves · **PLC controls**.
