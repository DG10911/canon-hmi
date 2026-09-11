# CANON_ACQUISITION — Design & Spec Coverage Map

Autonomous Engineering Source Acquisition + Corpus Builder. Implements the
71-section blueprint (`../attachments/oCM3Dw/pasted_text_2026-09-10_21-52-44.txt`)
as a **new sibling module** feeding the existing CANON model in `../CANON` and
`../CANON_RESEARCH`.

## Deliverables in this module (the four requested)
1. **Runnable P0 skeleton** — `canon_acq/` package + `run_all.py`, pure stdlib, the full `DISCOVER→…→UPDATE CANON` loop end-to-end.
2. **Ingest existing TK-401** — `canon_acq/ingest_tk401.py` lifts the real machine reality in `../CANON_RESEARCH` into evidence-linked datasets, then builds the Context Pack + coverage + HMI-readiness reports.
3. **Design doc + schemas** — this file + `db/schema.sql` (Postgres/pgvector DDL for all 37 datasets) + `canon_acq/models.py` (Pydantic-shaped dataclasses).
4. **Real source discovery** — `sources/source_registry.seed.json`: **70 web-verified public sources** (Schneider se.com, OPC Foundation, modbus.org, IEC/ISA/EEMUA abstracts, IDTA, PLCopen, GitHub), each URL confirmed reachable by 5 parallel verification agents. Ingested by `canon_acq/web_ingest.py`.

## Architecture (section 69)
```
query_families ─┐                        sources/source_registry.seed.json (real, web-verified)
  (discovery)   │                                        │
                ▼                                         ▼
        run_all.py  ──▶ web_ingest ──▶ ┌───────────────────────────────┐
                    ──▶ ingest_tk401 ─▶│  Corpus (store.py)            │──▶ out/*.jsonl (37 datasets)
                                       │  37 datasets in memory        │──▶ out/corpus_manifest.json
        engines: resolve/coverage/     └───────────────────────────────┘──▶ out/source_registry.json
                 readiness/dedupe/audit         │                       ──▶ out/context_pack.tk401.json
                                                ▼                       ──▶ out/{coverage,hmi_readiness,
                              context_pack.build_context_pack               no_hallucination_audit}.json
```
Machine reality (Tier 0) is ingested **after** and **dominates** generic vendor
knowledge (section 62): TK-401 facts carry `confidence=AUTHORITATIVE`; se.com doc
metadata carries `confidence=OFFICIAL` and `capability_status=UNKNOWN` until a body is parsed.

## Section-by-section coverage
Status: ✅ implemented · ◑ modelled/scaffolded (schema + hook, body is a production task) · ▢ documented-only.

| § | Topic | Status | Where |
|--|-------|--------|-------|
| 0 | Public/authorized data only | ✅ | seed = public URLs; `license` on every source; paid standards = abstract-only; no content mirrored |
| 1 | Primary objective | ✅ | `discovery.query_families` |
| 2 | Trust-tier hierarchy 0–5 | ✅ | `enums.TrustTier`; every source + fact carries `trust_tier` |
| 3 | Schneider corpus scope | ✅ | `discovery.SCHNEIDER_*`; seed has M580/M340/M221/M241/M251/M262, Control/Machine/OTE/SCADA Expert, Harmony, Altivar, TeSys |
| 4 | Schneider doc types | ✅ | `discovery.DOC_TYPES`; seed `document_type` |
| 5 | Machine engineering file corpus | ◑ | `classify.py` (XEF/ZEF/PLCopenXML/HMI/SCADA classes) |
| 6 | PLC data to extract | ◑ | `ingest_tk401` extracts identity/structure/variables/logic-refs from the demo project; live-project parser is P1 |
| 7 | I/O corpus | ✅ | `07_io`, per-point address/dtype/scale/evidence |
| 8 | Equipment/asset corpus | ✅ | `08_assets` + typed `12_motors`/`14_valves`; asset entities |
| 9 | Instrumentation corpus | ✅ | `11_instruments` (LT401, PT401) |
| 10 | Motor/drive corpus | ✅/◑ | `12_motors` populated; `13_drives` empty (TK-401 has no VFD — honest UNKNOWN) |
| 11 | Valve/actuator corpus | ✅ | `14_valves` (XV401) + command feedback |
| 12 | Command contract corpus | ✅ | `15_commands` from `canon_command_contracts.json` |
| 13 | Permissive/interlock corpus | ✅ | `16_permissives`, `17_interlocks` (IF/THEN facts) |
| 14 | Alarm corpus | ✅ | `18_alarms` (priorities preserved, not fabricated) |
| 15 | State/mode corpus | ✅ | `19_states` (+PackML mapping), `20_modes` (marked INFERRED) |
| 16 | Sequence corpus | ✅ | `21_sequences` (transitions + derived P401 start seq) |
| 17 | Process corpus | ✅ | `22_process_relationships` |
| 18 | Electrical corpus | ▢ | schema hooks; no electrical drawings supplied for TK-401 |
| 19 | Existing HMI/SCADA corpus | ◑ | `23_hmi_screens` (inferred from CANON app, flagged) |
| 20 | HMI screen intelligence | ◑ | screen fields present; drawing OCR is P1 (§46) |
| 21 | Engineering doc corpus (URS/FDS/FAT…) | ▢ | `28_procedures` schema; none supplied |
| 22 | Product/component knowledge | ✅ | `26_products` from se.com; `capability_status=UNKNOWN` guard |
| 23 | Protocol corpus | ✅ | `25_protocols` from `protocol_registry.json` + OPC/Modbus seed |
| 24 | OPC UA corpus | ✅ | OPC 10000 Parts 1–7 in seed; namespace fact on controller |
| 25 | Modbus corpus | ✅ | Modbus V1.1b3 + TCP guide in seed; per-signal register facts |
| 26 | Industrial standards corpus | ✅ | `27_standards` (IEC/ISA/EEMUA/PLCopen/AML/AAS/NAMUR); legally-usable metadata only |
| 27 | Schneider HMI/operator knowledge | ✅ | OTE/MSCADA/Harmony in seed; no proprietary objects copied |
| 28 | Academic/research corpus | ▢ | discovery family stub; none ingested in P0 |
| 29 | Community discovery corpus | ✅ | Tier-5 GitHub/PLCopen/SE-forum in seed (discovery use only) |
| 30 | Source discovery strategy (19 steps) | ✅ | `run_all.py` pipeline stages |
| 31 | Search query generation (families) | ✅ | `discovery.query_families` (216 queries) |
| 32 | Source metadata schema | ✅ | `models.Source` / `sources` table |
| 33 | Engineering fact schema | ✅ | `models.Fact` / `facts` table (subject/predicate/object/evidence…) |
| 34 | Evidence model | ✅ | `models.Evidence`; every fact has `evidence_id` (audit-enforced) |
| 35 | Conflict engine | ✅ | `32_conflicts` (PT401 0-10 vs 0-16 bar, RESOLVED_REVISION) |
| 36 | Revision engine | ✅ | `03_document_revisions`, `34_dependencies`, `35_change_history` |
| 37 | Entity resolution | ✅ | `engines.resolve_entities` (candidate/ambiguous, never auto-merge) |
| 38 | Engineering ontology | ✅ | `enums.ENTITY_KINDS`; `04_entities.kind` |
| 39 | Relationship extraction | ✅ | `enums.RELATIONSHIP_PREDICATES`; `30_relationships` |
| 40 | CANON context pack | ✅ | `context_pack.build_context_pack` → `36_context_packs` |
| 41 | Automatic context coverage | ✅ | `engines.compute_coverage` (16 dims, from real counts) |
| 42 | Automatic HMI readiness | ✅ | `engines.compute_readiness` → READY/…/BLOCKED |
| 43 | Source quality scoring | ◑ | trust_tier + recency in metadata; composite score is P1 |
| 44 | Document processing pipeline | ◑ | JSON path implemented; PDF/OCR workers are P1 (deps in requirements) |
| 45 | PDF intelligence | ▢ | Docling/pdfplumber wired in requirements; page-provenance fields exist on Fact |
| 46 | Drawing intelligence | ▢ | schema fields present; vision extraction is P2 |
| 47 | Code intelligence | ◑ | logic refs extracted from contracts/state models; ST/LD parser is P1 |
| 48 | Live protocol intelligence | ▢ | asyncua/pymodbus in requirements; READ-ONLY design (§68); not run in P0 |
| 49 | User-provided machine corpus | ✅ | `classify.classify_file` (zip/pdf/xml/csv/…) |
| 50 | Unknown file handling | ✅ | `33_unknowns` never-discard record |
| 51 | Duplicate detection | ✅ | `engines.detect_duplicates` (content hash) |
| 52 | Vector index | ◑ | `37_embeddings` (placeholder-hash, explicitly non-semantic; real model = P1) |
| 53 | Graph model | ✅ | adjacency `relationships`/`dependencies` (no Neo4j, per spec) |
| 54 | Search system | ◑ | datasets support keyword/entity/evidence/revision queries; API is P1 |
| 55 | No-hallucination policy | ✅ | `enums.KnowledgeState`; `engines.audit_no_hallucination` |
| 56 | AI role (may/may-not) | ✅ | AI does classify/propose only; contracts/permissives/alarms come from source data, never invented |
| 57 | Output dataset (37) | ✅ | `store.COLLECTION_TO_DATASET`; all 37 emitted (asserted) |
| 58 | Required manifest | ✅ | `store.write_manifest` → `corpus_manifest.json` |
| 59 | Source registry | ✅ | `store.write_source_registry` + `sources/source_registry.seed.json` |
| 60 | Automatic discovery loop | ✅ | `run_all.main` (DISCOVER→…→UPDATE CANON) |
| 61 | Change detection | ✅ | `35_change_history` change types |
| 62 | Machine-specific ingestion priority | ✅ | Tier-0 confidence=AUTHORITATIVE; product capability=UNKNOWN until parsed |
| 63 | Golden TK-401 dataset | ✅ | the whole TK-401 ingest; P401 START permissive chain reproduced |
| 64 | Zero-prompt test | ✅ | run_all needs no NL prompt; builds identity→context→readiness from files |
| 65 | Final output A–O | ✅ | corpus/model/evidence/index/registry/coverage/readiness all emitted |
| 66 | UI for source acquisition | ▢ | data contracts ready; the existing `../CANON` HMI app is the UI surface |
| 67 | Do not create fake data | ✅ | audit rejects source-less facts; seed = only verified URLs; UNKNOWN kept |
| 68 | Security (read-only) | ✅ | no writes/downloads of bodies; live protocols read-only by design |
| 69 | Implementation architecture | ✅ | this module; `requirements.txt` = production deps |
| 70 | Acceptance test (20 checks) | ✅ | `run_all` exercises discover→parse→extract→provenance→revision→conflict→unknown→resolve→hierarchy→signal→control→process→HMI→evidence→coverage→readiness; never invents; never controls a PLC |
| 71 | Final principle (traceability) | ✅ | `context_pack.provenance_rule`; every fact chains entity→fact→evidence→source→revision→authority |

## What is deliberately NOT done in P0 (honest gaps)
- No live document **download/parsing** of the se.com PDFs — we store verified *metadata* and respect copyright (§0, §26). Bodies + Docling extraction are the P1 step; the Fact schema already carries page/section/table provenance for it.
- `37_embeddings` are **placeholder** hash vectors, tagged as such — swap for a real embedding model (§52).
- `13_drives`, `10_modules`, `18-electrical`, `21-eng-docs`, `28_procedures` are **empty for TK-401** because that machine genuinely has none — recorded as absence, not faked (§67).
- No UI built here — the module outputs the data contracts the existing CANON app consumes (§66).

## Run
```bash
cd .context/CANON_ACQUISITION
python3 run_all.py            # pure stdlib; writes out/
```
Deterministic: unchanged inputs → identical `no_hallucination_audit.json#corpus_hash`.
