# CANON — Schneider Electric Industrial Engineering Corpus · Report

**Purpose:** give CANON *the right engineering context, with provenance and truth status* —
not a claim to "the whole Schneider database." Built per the acquisition spec v1.0.

## A. Executive summary
CANON ships a **structured, truth-tagged corpus** of Schneider Electric product families,
controllers, software, HMI ranges, drives, motion, motor control, I/O, metering, networking,
and the relevant **standards** — plus CANON's own semantic→HMI mapping rules and a
current-vs-roadmap capability matrix. It's browsable in-app under **Engineering → Schneider Corpus**
(`corpus.js`) and available as source data here.

## B. Honesty / source policy (critical)
- **VERIFIED** = well-established public product knowledge (family names, categories, the
  software that programs them, supported communication protocols, the standards' scope).
- **VERIFY** = plausible but must be confirmed on an official source (exact commercial
  references, register addresses, object counts such as EOTE "650+ objects", exact URLs).
- **PROPOSED** = CANON demo assets and mapping rules — never presented as Schneider facts.
- **ROADMAP** = future CANON ingestion capability.
- **No live web crawl was performed in this build.** No fabricated URLs, part numbers or
  register maps. Register addresses in `equipment.js` are marked "typical — verify vs firmware."

## C. Coverage (what's in the corpus)
| Domain | Items | Truth |
|---|---|---|
| Product families | Modicon, Harmony, Altivar, Lexium, PacDrive, TeSys, Modicon I/O, PowerLogic, Zelio, Preventa | VERIFIED |
| Controllers | M221, M241, M251, M262, M340, M580, M580 Safety, legacy (Momentum/Quantum/Premium) | VERIFIED |
| Software | Machine Expert (+Basic/Safety/Motion), Control Expert, Automation Expert, EOTE, Vijeo Designer, Machine SCADA Expert, Process Expert, OPC UA Server Expert, SoMove | VERIFIED |
| HMI ranges | Harmony GTU/GTUX, ST6/STM6, STO/STU, P6, Magelis (legacy), XVU signal tower | VERIFIED |
| Drives | Altivar ATV320/340/630/650/930/950/212/6000 | VERIFIED |
| Motion | Lexium 28/32/62/ILA-ILE, BMH/BSH motors, PacDrive LMC | VERIFIED |
| Motor control | TeSys D/F/B, island, T, U/Giga, Altistart | VERIFIED |
| Metering | PowerLogic PM8000/PM5000/ION9000/Acti9 | VERIFIED |
| Standards | ISA-101, ISA-18.2/IEC 62682, IEC 61131-3, IEC 61499, OPC UA, PackML/OMAC, MTP, AutomationML, AAS, EEMUA 191 | VERIFIED |
| Register maps (device catalog) | Modicon, Altivar, PowerLogic, TeSys, Lexium, Harmony XVU | VERIFY |
| Semantic→HMI mapping | pressure/level/flow/pump/valve/state/alarm | PROPOSED (CANON rules) |
| Machine hierarchy | PLANT→…→HMI VIEW | generic normalisation target |

## D. Current vs roadmap (CANON ingestion)
- **CURRENT:** canonical model, intent→validated HMI, PLC-authoritative control, change impact,
  SKAB replay, Schneider register-map catalog, local-model fine-tune (brain).
- **ROADMAP:** OPC UA nodeset ingestion (M580 embedded server), AutomationML/MTP/AAS import,
  export to EcoStruxure Operator Terminal Expert, live Modbus/OPC UA polling to a physical device.

## E. Unknowns / to verify on se.com
Exact commercial references per product; EOTE built-in object/template count; exact Modbus
register maps per drive/meter firmware; per-standard Schneider conformance claims (we say
"informed by / aligned to", never "compliant/certified").

## F. Files
- `../corpus.js` — the in-app structured corpus (`window.SE_CORPUS`).
- `../equipment.js` — device catalog with representative register maps (VERIFY).
- This report.

## G. How CANON uses it (retrieval, honestly)
Corpus provides **generic engineering context** (what families/objects/standards exist).
It **never** becomes a machine binding automatically — machine-specific bindings come only
from the actual **canonical model**, and every generated widget is validated against that model.
Generic product info informs; the machine model binds.
