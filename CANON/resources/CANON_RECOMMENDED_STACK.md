# CANON — Resource Blueprint & Recommended Stack (v2.0)

> Honesty: real, well-known tools (VERIFIED). Schneider specifics flagged VERIFY. Licenses
> accurate to best knowledge — confirm per version (esp. **PyMuPDF AGPL**, **asyncua LGPL**,
> **Qwen license per size**). No live web crawl performed. CANON components = PROPOSED/BUILT.

## Executive architecture
```
        MACHINE DATA (B)        KNOWLEDGE (A)          AI (D)
        OPC UA / Modbus         Schneider corpus       local LLM (Qwen)
        PLC export / sim        standards / docs       embeddings (BGE)
              │                       │                    │
              └───────────────┬───────┴────────────────────┘
                              ▼
                     CANON MACHINE MODEL (C)  ← single source of truth
                              ▼
                DETERMINISTIC ENGINE (validate · compile · contract)
                       │                         │
                       ▼                         ▼
                   HMI ENGINE                CONTROL (permissive-gated)
                       │                         │
                       ▼                         ▼
                   RUNTIME HMI  ◄── feedback ── PLC
                              ▼
                    CHANGE IMPACT → REGENERATION → BASELINE
```
**Rule:** AI proposes → model defines → validator checks → engineer approves → **PLC controls**.
AI never invents a tag, never writes the PLC, never overrides validation.

## Final recommended stack (one choice per slot)
| Slot | Recommended | Backup | Why |
|---|---|---|---|
| Frontend / HMI | React + TS + SVG/Canvas, **Three.js** twin, uPlot trends | vanilla (current) | schema-driven component registry maps JSON→validated widget |
| HMI generation | **JSON UI schema + component registry** | DSL | AI emits *structured spec*, not code |
| Backend | **FastAPI (Python)** | Node/Express | pairs with pymodbus/asyncua + local LLM (server.py already FastAPI) |
| Realtime | **WebSocket** | SSE | live PLC state/alarms/validation |
| Relational DB | **PostgreSQL** | SQLite (demo) | one DB for relational + vector + graph |
| Vector | **pgvector** | Qdrant | simplest; no extra service; corpus is small |
| Graph | **in-memory adjacency** (BUILT) | Apache AGE | Neo4j is overkill for prototype |
| Validation | **JSON Schema + Zod + Pydantic** (BUILT) | — | enum-constrained schema = the guarantee |
| OPC UA | **node-opcua** / **asyncua** | open62541 | ingest M580 embedded server; subscriptions |
| Modbus | **pymodbus** | modbus-serial | real Schneider device I/O + built-in sim |
| PLC sim | **CANON deterministic sim** (BUILT, demo-safe) | **OpenPLC** (realistic) | reproducible; OpenPLC adds real soft-PLC credibility |
| LLM | **Qwen2.5-Coder 7B/32B local** (via vLLM/Ollama) | hosted (optional) | private, strong JSON; is the brain's base |
| Embeddings | **BGE-M3** (local) | OpenAI/Voyage | private retrieval; no API |
| Reranker | **NONE for prototype** | bge-reranker-v2-m3 | avoid needless complexity |
| Docs | **PyMuPDF + pdfplumber** | Docling | provenance-preserving extraction (mind AGPL) |
| OCR | **skip** (P3) | Tesseract/PaddleOCR | only if scanned PDFs |
| Testing | **Vitest + Pytest + Playwright** | — | invalid-tag/range/permissive/regeneration |
| Observability | **audit trail (BUILT)** + OTel later | Sentry | demo covered; OTel for production |
| Security | **JWT + RBAC + command contract**; PLC write only via backend | — | never browser→raw PLC |
| Deploy | **Docker** (frontend static + backend + model) | — | one-command, offline-capable |

## What's already BUILT in the prototype (map to blueprint)
Deterministic validator & command contracts · permissive-gated control · change-impact→regenerate→baseline · in-memory engineering graph · SKAB real-data sim · Three.js twin · Schneider register catalog + truth-tagged corpus · local-LLM adapter (`server/`) · QLoRA fine-tune pipeline (`brain/`) · audit trail. **The core CANON loop is real today.**

## Priorities
- **P0 (demo-critical, all BUILT):** canonical model · deterministic validation · JSON-schema guarantee · dynamic HMI · PLC-authoritative control · permissives · live feedback · change impact · SKAB data.
- **P1:** FastAPI backend on a server · WebSocket realtime · pymodbus **or** node-opcua to one real/soft device · local LLM served · PostgreSQL persistence.
- **P2:** OpenPLC soft-PLC · pgvector RAG over corpus · uPlot trends · Docker · Vitest/Playwright · QLoRA brain.
- **P3:** hosted LLM · reranker · Docling · OCR · OpenTelemetry/Grafana · CODESYS.

## Demo-critical vs nice-to-have
| Resource | Required for demo? | Real or mock? | Priority |
|---|---|---|---|
| Canonical model + validator | **Yes** | real | P0 |
| Dynamic HMI + 3D twin | **Yes** | real | P0 |
| PLC-authoritative start/stop + permissive | **Yes** | deterministic sim (real logic) | P0 |
| Change impact → baseline | **Yes** | real | P0 |
| SKAB live data | **Yes** | real recorded data | P0 |
| Local LLM generation | Nice | real (optional) | P1 |
| Real Modbus/OPC UA device | Nice | OpenPLC/sim | P2 |
| RAG over Schneider corpus | Nice | real | P2 |

## Minimum viable prototype (the 17-step flow) — status
Import context → build model → intent → structured proposal → retrieve context → **validate** → generate HMI → START P401 → permissive eval → pump runs → feedback → close valve → **START rejected** → change PT401 range → impact → regenerate → regression. **All 17 steps run today** (retrieval/LLM optional; sim is deterministic).

## Security architecture
`Browser → CANON API → AuthZ → Command Contract → Validation → PLC interface`. **Never** `Browser → raw PLC write`. Every command is authorized, permissive-checked, and audit-logged; approve role ≠ propose role.

## Red-team (attack → mitigation)
| Attack | Mitigation (status) |
|---|---|
| LLM hallucinates a tag | enum-constrained JSON schema + server-side validation → UNKNOWN (**BUILT**, proven) |
| LLM invents a Schneider product | corpus truth-tags; generic info never becomes a binding (**BUILT**) |
| HMI bypasses validation | render only from validated spec; no free-form code (**BUILT**) |
| Browser writes PLC directly | writes only via backend command contract + permissive (**design**; enforce in backend P1) |
| Stale doc overrides current | lifecycle/truth status per record; revisions immutable (**BUILT** for model) |
| Command without permissive | contract gate rejects (**BUILT**, the START-reject demo) |
| Change leaves HMI stale | change-impact blocks release until regenerate+regression (**BUILT**) |
| Evidence lost | evidence/source fields + audit trail (**BUILT** for model/audit; corpus URLs = VERIFY) |
| Can't tell VERIFIED vs PROPOSED | truth badges throughout corpus/model (**BUILT**) |

## Unknowns / gaps (honest)
Exact Schneider commercial refs, register maps, and object counts → **VERIFY on se.com** (schema ready to hold sources). Live OPC UA/Modbus to a physical device, WebSocket runtime, Postgres persistence, and backend-enforced auth are **P1/P2 TODO** (prototype currently runs in-page + optional backend).

## The one question that matters
> "Can CANON understand a machine, generate a useful HMI, prove its bindings are valid, request actions without bypassing PLC authority, receive feedback, and survive engineering changes?" — **Yes, today**, on the deterministic core. Everything else scales it.
