# CANON — Context Intelligence Engine · Architecture & Current-State Report

The engine that turns heterogeneous engineering inputs into a **versioned, evidence-backed,
machine-specific canonical understanding** — so AI-generated HMIs are grounded in reality.

```
SOURCES → INGESTION → EXTRACTION → NORMALIZATION → ENTITY RESOLUTION
→ SEMANTIC CORRELATION → EVIDENCE GRAPH → CONFLICT DETECTION
→ CANON MACHINE MODEL → CONTEXT PACK → AI PROPOSAL → DETERMINISTIC VALIDATION
```
Authority chain (fixed): **AI proposes → CANON model defines → validator checks → engineer approves → PLC controls → HMI feedback → change impact → regeneration.**

## Four layers (kept separate — see `schemas/source_authority.json`)
- **A** Official engineering evidence (Schneider docs, standards) · **B** This machine's reality (OPC UA/Modbus/PLC export/simulator) · **C** CANON machine model · **D** AI proposals (structured JSON only, never authoritative).

## Current-state report (honest)
| Capability | Status in this prototype |
|---|---|
| Canonical machine model (assets/signals/commands/permissives/alarms/relationships) | **DONE** — live in the app (`PROJDATA`) + formalised here as `datasets/tk401/tk401.canon.json` |
| Evidence + provenance model | **SCHEMA + FIXTURES** (`schemas/evidence.schema.json`, evidence records in the golden dataset); UI evidence drawer live |
| Status model (discovered/verified/unresolved/conflict/…) | **DONE** (`schemas/status_model.json`); surfaced in Context UI |
| Unresolved reference (PT401.Status) | **DONE** — live golden case + review drawer ("CANON did not invent a binding") |
| Conflict engine | **SCHEMA + GOLDEN FIXTURE** (`CF-PT401-RANGE`); surfaced as the R17→R18 change story in-app |
| Staleness / change impact | **DONE (deterministic)** in the app Change-Impact screen; `tk401.change.json` fixture |
| Relationship engine | **SCHEMA + DATA** (`schemas/relationship.schema.json`, MEASURES/ACTUATES/REQUIRES on TK-401) |
| Dependency graph | **DONE (in-memory)** in-app + adjacency described in fixture |
| Context Pack (AI input contract) | **SCHEMA** (`schemas/context_pack.schema.json`) — the only thing the AI receives |
| Intent / revision schemas | **SCHEMA** (`schemas/intent.schema.json`, `revision.schema.json`) |
| Deterministic readiness (no fake AI %) | **DONE** — "23/24 verified · 1 review · 0 invented bindings" strip live |
| AI adapter + guardrails (reject unknown tag) | **DONE** — `server/server.py` validates enum-constrained JSON, rejects `MADE_UP_TAG` (proven) |
| Retrieval / pgvector / embeddings | **NOT BUILT** — needs a real backend (P1) |
| OPC UA / Modbus adapters, WebSocket runtime | **NOT BUILT** — `asyncua`/`pymodbus` in backend (roadmap); app uses SKAB replay + deterministic sim |
| PostgreSQL 16 + tables | **NOT BUILT** — schemas here are the data contracts to seed it |
| Web-cited Schneider research | **NOT PERFORMED** — no web access in this build; see research report |

## What should NOT be rebuilt
The Context/Model UI, the unresolved+evidence+readiness+conflict surfacing, the validator/LLM adapter (`server.py`), the fine-tune pipeline (`brain/`), and the truth-tagged Schneider corpus (`corpus.js`) already exist. This artifact set **formalises the data model** behind them (schemas + golden datasets) so a real FastAPI/Postgres backend can be seeded without changing the UX.

## Honesty rules honored
- No invented Schneider APIs/SKUs/OPC-UA nodes/PLC addresses presented as real — all machine data is `fixture:true`, `sourceType:"simulator"`.
- Uncertainty (`PT401.Status` UNRESOLVED) and conflict (`CF-PT401-RANGE`) are explicit, never silently resolved.
- Every fact carries provenance + status + authority; AI (A8) is never authoritative alone.

## Files
`schemas/` — 8 canonical schemas · `datasets/tk401/` — golden model + change fixture · `CANON_CONTEXT_DATASET_CATALOG.json` · `CANON_CONTEXT_RESEARCH_REPORT.md`.
