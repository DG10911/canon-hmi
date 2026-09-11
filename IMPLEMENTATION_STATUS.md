# CANON — IMPLEMENTATION_STATUS

Honest audit against MASTER BUILD v11.0 (no-mock rule). Repo areas:
`CANON_ACQUISITION/` (corpus+model), `CANON/` (LLM-HMI prototype), `CANON_PLATFORM/` (projects app).

Legend: ✅ WORKING · ◑ PARTIAL · ⛔ MISSING · 🔗 REQUIRES INTEGRATION · ⚠️ VIOLATION-TO-FIX

| # | Capability | Status | Where / note |
|--|-----------|--------|--------------|
| 2 | Repository audit | ✅ | this file |
| 3 | Canonical model (assets/signals/cmds/permissives/alarms/…) | ✅ | `CANON_ACQUISITION` 37 datasets + `CANON_PLATFORM/platform_core.normalize_*` |
| 4 | Every HMI element maps to canonical data | ✅ | assembler binds only real signals; validator drops the rest |
| 5–8 | Real ingestion (CSV/XLSX/XML/PDF/JSON) w/ provenance | ◑ | platform ingests CSV/XLSX/XML/JSON→model; **PDF needs pdfplumber**; ZIP/PLC-XEF/P&ID/image parsing = ⛔ |
| 7 | Per-file parse status (queued/parsed/failed/entities/facts) | ⛔ | platform returns counts only, no per-file pipeline UI |
| 9 | Context analysis (what/where/connected/measures/controls…) | ◑ | `describe_context` gives identity/instrumentation/control/operator-needs; deep relationship reasoning = ◑ |
| 10 | Entity resolution (PT401/PT-401/…) | ◑ | `CANON_ACQUISITION/engines.resolve_entities` (candidate/ambiguous); not wired into platform |
| 11 | Relationship graph (MEASURES/REQUIRES/CONTROLS) | ◑ | `30_relationships` in corpus; platform infers per-asset only, no full graph screen |
| 12 | Control-logic (permissives/interlocks/states/sequences) | ✅ | command contracts + permissives real in model |
| 13 | Real trained CANON Brain | ✅ | `canon-brain-3b` GGUF trained (100% zero-invented-tag) |
| 13/14 | Brain → structured → validator → registry | ◑ | wired in `CANON/server.py` (json_schema enum) and `CANON_PLATFORM` (`_llm_pick`, optional); validator always runs |
| 15 | Automatic HMI generation from model | ✅ | `assemble_screen` (deterministic) |
| 16 | Realistic industrial HMI (faceplates/overview/sections) | ◑ | KPI header + asset sections + faceplates present; process-graphic (P&ID) = ⛔ |
| 17–19 | Real controls / pump+valve faceplates | ◑ | buttons exist; **were flipping client booleans (⚠️) — being replaced by server command pipeline** |
| 20 | Real command pipeline (HMI→API→validator→permissives→sim) | 🔗 | **building now** (`/api/projects/{id}/command`) |
| 21 | Real-time HMI w/ value+unit+ts+quality | ⚠️→◑ | **VIOLATION: client random-walk labeled "LIVE".** Replacing with server simulator + `SIMULATOR` label + quality/ts |
| 22 | Deterministic physically-coherent simulator | 🔗 | **building now** from `runtimeSeed` physics (inflow/leak/pumpCurve) |
| 23 | Alarms (state/ack/active) | ◑ | alarm model real; ack/active from sim (server) = building; shelve/history = ⛔ |
| 24 | Trends from real history | ◑ | will use server-sim history (real), not random |
| 25–26 | Recommendations + "why?" traceability | ◑ | `recommended_screens`/`operator_needs` done; per-component "why→evidence→source" click-through = ◑ |
| 27–29 | NL HMI editing → validated change | ✅ | `apply_edit` + copilot; brain-assisted resolve |
| 30 | HMI revisions (v1/v2, compare/restore) | ⛔ | edits mutate current screen; no revision store yet |
| 31 | Change impact (PT401 0-10→0-16) | ◑ | `CANON_ACQUISITION/35_change_history` has the hero scenario; not wired into platform regen |
| 32 | Conflicts visible | ◑ | corpus `32_conflicts`; platform doesn't surface |
| 33 | Context→HMI clickable traceability | ⛔ | not in platform yet |
| 34–35 | Screen set / process overview from relationships | ◑ | overview+faceplates yes; relationship-driven P&ID graphic = ⛔ |
| 39 | Context counts from DB (not hard-coded) | ✅ | all counts computed from model |
| 40 | HMI readiness (BLOCKED/READY/…) | ◑ | `CANON_ACQUISITION` computes it; platform doesn't show |
| 41/46 | Honest runtime status (never fake LIVE) | ⚠️→◑ | **fixing: label SIMULATOR/NOT CONNECTED truthfully** |
| 42 | Simulator provides OPC UA/Modbus | ⛔ | no protocol server; deterministic sim only (labeled SIMULATOR) |
| 43–44 | TK-401 real data E2E test | ◑ | TK-401 seeded from real `canon_demo_machine.json`; full 38-step E2E = ◑ |
| 51 | Model/Brain eval (zero-invented etc.) | ✅ | `CANON_ACQUISITION/model/eval.py` |
| 52 | Test automation (unit/integration/Playwright) | ⛔ | only ad-hoc TestClient checks |
| 54 | RBAC / audit / approval | ⛔ | not implemented |

## The one thing that must be fixed immediately (VIOLATION)
§21/§41/§46: the platform's HMI showed **"● LIVE" with client-side random values**. That fabricates runtime. Fix in progress:
1. **Server-side deterministic simulator** (`CANON_PLATFORM/platform_sim.py`) driven by the machine's own physics (`runtimeSeed` for TK-401; coherent pump/valve/level/pressure model generically).
2. **Real command pipeline** `/api/projects/{id}/command` → checks the real permissive contract → applies to sim or **BLOCKS with reason**; returns state progression.
3. HMI consumes server runtime (value·unit·timestamp·quality) and is honestly labeled **RUNTIME: SIMULATOR** — never "LIVE".

## UPDATE (2026-09-11) — 3 items now WORKING
- §30 **HMI revisions** ✅ — server-owned screen + revision store; generate/edit/change-impact each create a rev; **restore** any rev; `approved`/`review required` flags. Endpoints `/revisions`, `/restore`.
- §31 **Change impact** ✅ — `/change-impact {signalId, engMax}` finds affected widgets+alarms, applies the range to the canonical model, **regenerates the screen at the new range** (PT401 0-10→0-16→0-20 verified: gauge range actually updates), records a review-required revision.
- §33 **Context→HMI traceability** ✅ — `/why?signal=` returns signal→fact→evidence→source→status; click any gauge/value in the HMI to see it. FT999 → UNKNOWN.
- §54 audit log ◑ — append-only `AUDIT` + `/api/audit` (revisions/commands). RBAC/approval-gate UI still ⛔.

## UPDATE (2026-09-11 b) — BRAIN-FIRST integration (mandatory when configured)
Per the "MANDATORY BRAIN-FIRST" spec: the Brain is now the PRIMARY interpreter for all
user-facing NL flows when `CANON_LLM_BASE` is set, with NO silent deterministic fallback.
- **Structured intent** — `brain_intent()` returns enum-constrained JSON (scope/signals/commands/op/widget/reasoning); invalid ids dropped by canonical validation (§4/§8). Brain gets a real **Context Pack** (§7).
- **Generate + edit are brain-first** — engine tag shows `CANON-brain` with the `CANON-BRAIN → CANON MODEL → VALIDATOR → HMI ASSEMBLER` step chain; deterministic used ONLY when no Brain configured.
- **BRAIN OFFLINE** — configured-but-unreachable returns `brain_offline` + a Retry UI; never claims Brain use falsely (§9).
- **Brain status panel** — sidebar shows Brain CONNECTED/OFFLINE · model · interpreter · validator · runtime (§11), polled every 8s.
- **Deterministic stays the authority** — validation/assembly/bindings/revisions/runtime all deterministic; Brain never writes truth or the PLC (§10/§15).
- **Tests** — `brain_tests.py` (stubs only the network so real validation runs): **8/8 pass** (fuzzy temp→TT-501, level→LT-501, two-pressures→PT-501/502, agitator→AGT-501, FT-999 rejected, engine=CANON-brain, fuzzy edit→trend, brain-offline no-fallback).

HONEST CAVEAT: I can't reach your DGX brain from here, so the flow was proven with a stub that emits ideal structured intent. The **real** canon-brain (trained on atomic-intent JSON, not this exact schema) will emit valid structured JSON via constrained decoding, but its *accuracy* at resolving fuzzy phrases→correct signals is unproven until you run it via the tunnel — and the v2 retrain would improve it. The safety guarantee holds regardless (validator drops anything invalid).

## Honest bottom line
A large share of v11 is real (model, brain, deterministic generation, validated editing, multi-format ingest). The gaps are: **live protocol runtime, HMI revisions, change-impact wiring, process-graphic, per-file parse UI, RBAC, test automation.** None are faked as "done." Next build target = the runtime-honesty fix, then revisions + change-impact.
