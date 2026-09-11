# CANON — Context Research Report

## ⚠ Honesty statement (read first)
This report was produced **without live web access** in this build. Per the spec's own rules
(*"do not rely on memory for current Schneider info"*, *"never turn 'not found' into 'does not
exist'"*, *"do not invent Schneider APIs/capabilities/URLs"*), **no Schneider-specific fact below
is marked VERIFIED with a citation**, because I could not open an authoritative source here.
Everything Schneider-specific is **SUPPORTED** (well-established public product knowledge) or
**VERIFY** (confirm against se.com before relying on it). To complete this properly, re-run the
research with web access and attach real URLs to each record — the schema below is ready to hold them.

Established public product knowledge already lives, truth-tagged, in **`../corpus.js`** (families,
controllers, software, HMI, drives, standards) — this report references it rather than duplicating.

## Findings (status-tagged, no fabricated citations)
| Topic | Statement | Status |
|---|---|---|
| Modicon families | M262 (machine + motion), M580 ePAC, M340 are real current/again-current Modicon families | SUPPORTED |
| M580/M262 OPC UA | M580 offers an embedded OPC UA server; M262 supports OPC UA — **exact node/namespace behaviour must be confirmed** per firmware | VERIFY |
| BMENUA0100 | Named as an M580 OPC UA module | VERIFY |
| EcoStruxure OPC UA Server Expert | Real Schneider OPC UA server product | SUPPORTED |
| Machine Expert / Control Expert | Real engineering software (Somachine/Unity Pro successors); export formats (XEF/ZEF etc.) exist — exact schema **VERIFY** | SUPPORTED / VERIFY |
| Operator Terminal Expert / Harmony | Real HMI config software + panel range; object/template counts **VERIFY** | SUPPORTED / VERIFY |
| OPC UA (IEC 62541) | Nodes, namespaces, node-ids, subscriptions, quality, timestamps — standard concepts | SUPPORTED |
| Modbus | Coils/discrete-inputs/input-&-holding-registers, function codes, addressing, endianness | SUPPORTED |
| Standards | ISA-101, ISA-18.2, IEC 61131-3, IEC 62541, ISA/IEC 62443, PackML, AutomationML, AAS — names/scope only (no paid text) | SUPPORTED |

## Critical distinction preserved
> "This controller **CAN** support OPC UA" ≠ "This machine **HAS** OPC UA enabled."
Controller capability = A4 (Schneider doc). Machine reality = A1/A2 (this machine's PLC/protocol). Never merged.

## Unknowns / to verify (with web access)
Exact OPC UA node/namespace behaviour per controller+firmware; exact export file schemas; EOTE object-library counts; per-product commercial references; any conformance claims. Until confirmed: **VERIFY / UNKNOWN**, never asserted.

## Licensing / access
No proprietary Schneider software, object libraries, paid standard text, or restricted manuals were downloaded or redistributed. Anything needing an account/licence = `ACCESS_REQUIRED`.

## Recommendation
Run batched research (Modicon OPC UA · EcoStruxure OPC UA Server Expert · Machine/Control Expert exports · Operator Terminal Expert · Modbus · OPC UA · standards) against **official se.com / OPC Foundation / Modbus Org** sources and populate `EvidenceRecord.sourceURI/document/revision/date` per fact. The dataset + evidence schema here is built to receive those citations without rework.
