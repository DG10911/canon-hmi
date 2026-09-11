# AssetFlow — Engineering Intent → Verified Automation
**Team DigiSeva** · a credible prototype of an AI-assisted engineering intelligence & traceability layer around the Schneider EcoStruxure ecosystem.

Self-contained, **offline**, single-file web app. No install, no backend, no dependencies — one `index.html`.
Everything on every screen is derived from **one canonical engineering model** (single source of truth).

## ▶ Run
Double-click `index.html` (or open the hosted link). Works with Wi-Fi off.

## The three hero capabilities (all functional)
1. **Intent Compiler** (AI Copilot) — natural-language intent → structured proposal: detected equipment/requirements, **engineering decisions surfaced**, unknowns **not silently invented**, would-generate counts. *AI proposes; it never writes the model.*
2. **Engineering Continuity** (Change Impact) — change PT101 `0–10 → 0–16 bar` and the **deterministic impact engine** (graph traversal, not LLM) classifies every object **DIRECT / INDIRECT / NOT AFFECTED / UNKNOWN**, selects regression tests, flags stale docs, blocks release.
3. **Runtime Trust + PLC Authority** — the HMI faceplate + **command response ladder**: a START request with `XV101_OPEN_FB = FALSE` is **REJECTED by the PLC** (HMI cannot bypass); freezing PT101 trips the **trust gate** (STALE → consequential commands disabled). Operator Copilot explains *why*.

## What is real vs. labeled
- **Real:** canonical model, deterministic dependency graph + bidirectional traversal, impact engine, engineering-guard linter, behaviour simulator (deterministic scenarios), runtime trust/freshness gate, PLC-authoritative command ladder, generated tests + regression selection, approval state machine, revisions, audit trail, truth states (VERIFIED/INFERRED/PROPOSED/UNKNOWN), provenance, evidence, query engine.
- **Honestly labeled (not faked):** NL parsing is a **deterministic parser** with an **LLM adapter point** (no cloud LLM in the offline prototype); EOTE integration is **DOCUMENTED PROTOTYPE**; PLC is **SIMULATED**. The app never shows "CONNECTED" unless it is, never fabricates plant state, and shows **UNKNOWN** where evidence is missing.

## The Five Authorities (visible throughout)
`AI proposes → CANONICAL MODEL is truth → RULES validate → ENGINEER approves → PLC controls.`
AI may not: control actuators, bypass PLC/permissives, modify approved engineering, approve its own work, invent critical values, fabricate state, or deploy.

## Views
Overview (command center) · AI Copilot · Engineering Model (+ confidence inspector) · Engineering Graph · Engineering Guard (linter) · Change Impact · Simulation · Tests · Runtime/HMI · Governance (approval/revisions/audit/deployment gate) · Project X-Ray (upgrade radar).

## 5-minute demo path
Overview → **Copilot** (compile intent) → **Graph** (select PT101) → **Runtime** (START rejected by PLC → open valve → START authorized → *Freeze PT101* trust gate) → **Change Impact** (change PT101 → impact) → **Tests** (run regression) → **Governance** (approve → Rev 18). Deep-link a view with `index.html#runtime` etc.

## Safety
AssetFlow does not implement or replace safety-rated control. Safety logic remains in the appropriate safety PLC/device. No SIL/safety-certification claims.

## Positioning
AssetFlow does **not** replace EcoStruxure — it gives the engineering information flowing through EcoStruxure a memory, a graph, an AI copilot and a verification layer.
