# CANON Resource Blueprint — Web Verification Report

**Date:** 2026-09-10 · **Scope:** every resource, URL, product, library, protocol, standard, and AI model in the CANON PS2 blueprint (files 01–18), checked against the live public web. **Method:** parallel web research; each claim tagged **CONFIRMED / CHANGED / UNVERIFIABLE / DEAD**. Where a fact could not be confirmed, nothing was invented — it is marked UNVERIFIABLE, and for the *system's own* data we generated correct-by-construction synthetic datasets instead (see `../synthetic/`, `../datasets/`, `../engine/`, `../ai/`).

> **Headline:** the blueprint holds up remarkably well. Almost everything is CONFIRMED. The changes are (a) version drift in fast-moving OSS, (b) two citation fixes, and (c) one genuinely important standards correction (IEC 63280 was abandoned).

---

## A. Schneider Electric products & documents

| # | Item | Status | Finding |
|---|------|--------|---------|
| 1 | EcoStruxure OPC UA Server Expert | **CONFIRMED** (1 citation fix) | Product live; SKUs OFSUASCZZSPMZZ etc. Guide **MFR53158.03, 08/2025** confirmed. M340+M580, Modbus/TCP mapping, symbolic access (.XVM/.CSV), M580 Safety read-only — all confirmed. **Fix:** the "72-hour demo" is real but is **not** stated in MFR53158 (guide only names the "DemoMode" license state); the 72h figure comes from the SE community forum. Don't cite MFR53158 as its source. |
| 2 | M580 BMENUA0100 (PHA83350) | **CONFIRMED** (version bump) | OPC UA embedded module for M580. Guide now **v07, 2026-07-01** (blueprint said v07 2026-07 — matches). |
| 3 | M262 embedded OPC UA server, port 4840 | **CONFIRMED** | Embedded server configurable in Machine Expert; default **4840** confirmed ("Firewall Eth2 Allow TCP port 4840"). |
| 4 | M241 / M251 OPC UA server | **CONFIRMED (both)** | Both have documented OPC UA server config in Machine Expert product-help (m241prg / m251prg). Blueprint had M241/M251 as PARTIALLY_FOUND → upgrade to VERIFIED. |
| 5 | M221 / M258 OPC UA | **RESOLVED (was UNKNOWN)** | **M221 = no embedded OPC UA** (Machine Expert Basic only; needs external Server Expert). **M258 = not documented / treat as unsupported.** Embedded OPC UA server is an **M241/M251/M262** feature. |
| 6 | OpcUaHandling library (EIO0000004021) | **CONFIRMED** (version bump) | Controller-side OPC UA **client** function blocks. Now **v06, 2025-10**. |
| 7 | Operator Terminal Expert (DIA5ED2140703EN) | **CONFIRMED** | Catalog v16.2 ~2026-03. **"650+ objects" confirmed** ("over 650 built-in vector icons, images, compound objects, templates"). Compound-object create/edit **requires Professional** license — confirmed. OPC UA server = Professional; OPC UA client on Basic+Pro from v4.4. |
| 8 | EOTE_Compound_Object download | **CHANGED (good news)** | Exists: "Compound Object.zip", v01, 2025-06-13, **236.5 KB** (matches). **It is FREELY downloadable, NOT login-gated** — contains `.coux` files. Only *authoring* compound objects needs the Professional license. Blueprint's RESTRICTED/LICENSE_REQUIRED flag on the file itself is too strong. |
| 9 | HMI Product Line-up Guide (DIA5ED1161001EN) | **CONFIRMED** | Live; current English edition **v8.0, 2025-01-01**. Verify the blueprint isn't pinning an older version. |
| 10 | Machine Expert Programming Guide (EIO0000002854) | **CONFIRMED** | Live, **v09, 2026-04-01**. **Project > Export PLCopenXML** confirmed. |
| 11 | Control Expert XEF/ZEF export | **CONFIRMED** | File > Export project → **.XEF** (XML, no DTM config) or **.ZEF** (with DTM config). (.STU/.STA are the other file types.) |
| 12 | Vijeo Designer current? | **CONFIRMED** | Still orderable — **v6.3**, SKU VJDBTPRO1P; Vijeo Designer Basic v2.1.1.47 released 2025-11. For newest panels SE steers to OTE. Keep as "current lineup entry; not the CANON runtime." |
| 13 | Harmony families ST6/STM6/GTU/GTUX/iPC | **CONFIRMED** | All real (ST6 range 65770, GTU 61981, GTUX 65749, STM6 modular box variant, iPC under category 2100). |
| 14 | Altivar / Lexium-PacDrive / TeSys | **CONFIRMED** | ATV320/340 (machine), ATV630/930 (process); Lexium + PacDrive 3 motion; TeSys (Deca/K/Easy) motor control. All real families. Do **not** invent parameter maps. |

**Domain note:** `product-help.schneider-electric.com` now 301-redirects to `product-help.se.com`. Old links still resolve; prefer the new host.

## B. Open-source libraries & tools

All claimed **licenses are correct**. The only issues are **version drift** in fast-moving frontend/test tooling.

| Resource | License (verified) | Latest (2026-09) | Status |
|---|---|---|---|
| asyncua (opcua-asyncio) | **LGPL-3.0-or-later** (COPYING = LGPLv3; no custom exceptions) | 1.1.8 | CONFIRMED |
| pymodbus | BSD-3-Clause | 3.13.0 | CONFIRMED |
| node-opcua | MIT | 2.182.0 | CONFIRMED |
| open62541 | MPL-2.0 | 1.5.8 | CONFIRMED |
| pgvector | PostgreSQL License | 0.8.6 | CONFIRMED |
| Docling | MIT | 2.126.0 | CONFIRMED — repo path `docling-project/docling` is now correct (donated to **LF AI & Data**; old `DS4SD/docling` is legacy). Bundled models carry own licenses. |
| pdfplumber | MIT | 0.11.10 | CONFIRMED |
| OpenPLC Runtime v4 | **MIT** (was "VERIFY_ON_REPO") | v4 on `main`, no tagged GA | CHANGED — license resolved; v4 is pre-release/in-dev. |
| UaExpert | proprietary freeware (registration) | 2.0.2 (2026-05) | CONFIRMED — not OSS, not embeddable; the paid UA C++ Client SDK is what you'd license to embed. |
| FastAPI | MIT | 0.141.1 | CONFIRMED |
| Pydantic v2 | MIT | 2.13.5 | CONFIRMED |
| **Zod** | MIT | **4.6.1** | CHANGED — 4.x is current (blueprint said 3.x/4.x). |
| **React** | MIT | **19.3.0** | CHANGED — React **19** is stable now, not 18. |
| **Vite** | MIT | **8.3.0** | CHANGED — v8, not "Vite SPA" era assumptions. |
| **Apache ECharts** | Apache-2.0 | **6.1.0** | CHANGED — 6.x exists now, blueprint said 5.x. |
| React Flow / @xyflow/react | **MIT** (verified at repo + npm) | 12.11.6 | CONFIRMED — despite past community license chatter, still MIT. |
| Playwright | Apache-2.0 | 1.63.0 | CONFIRMED |
| **Pytest** | MIT | **9.1.1** | CHANGED — v9 (blueprint said 8.x). |
| **Vitest** | MIT | **5.0.0** | CHANGED — v5 (blueprint said "pin"). |
| jsmodbus | MIT | 4.0.10 | CONFIRMED (published from Cloud-Automation/node-modbus repo). |
| njs-modbus | **BUSL-1.1** | 5.0.0 | CONFIRMED — "avoid" verdict is correct (Business Source License). |
| BGE-M3 | MIT | — | CONFIRMED — dense 1024 + sparse + multi-vector, 8192 tok. |
| nomic-embed-text | Apache-2.0 | v1.5 / v2-moe | CONFIRMED. |

## C. Protocols & standards

| Item | Status | Key fact / correction |
|---|---|---|
| OPC UA (IEC 62541) | CONFIRMED | Client/server + subscriptions + Part 14 pub/sub; port **4840**; security = X.509 certs + SecurityPolicies + user tokens. **Full text free** via OPC Foundation (reference.opcfoundation.org / free-registration PDFs); IEC copy is paid. Part 1 updated to a 2026 edition. |
| Modbus | CONFIRMED | **Free PDFs** at modbus.org. FCs 1,2,3,4,5,6,15,16; 4 tables (Coils RW, Discrete Inputs RO, Holding RW, Input RO); port **502**. No native security **but** an optional "Modbus Security" (TLS+X.509v3) spec now exists. |
| ISA-101 (HMI) | CONFIRMED | ANSI/ISA-101.01-2015 "HMI for Process Automation Systems." Display hierarchy, style guide, situation awareness. **Paid.** |
| ISA-18.2 / IEC 62682 (alarms) | CONFIRMED | Harmonized (ISA-18.2-2016 ↔ IEC 62682:2022). Philosophy → rationalization → lifecycle. **Paid.** The **"flood = >10 alarms/10 min/operator"** figure originates in **EEMUA 191** (also paid) and was adopted by ISA-18.2/IEC 62682 — cite EEMUA 191 as origin, not ISA. |
| PackML / ISA-TR88.00.02 | **CONFIRMED — important naming fix** | The producing/running state is officially **"Execute"**, NOT "Running" (OPC 30050 companion spec). 17 states total. Built on ISA-88 (IEC 61512). Standard paid; overviews free. → CANON's state model now documents the `Running → Execute` mapping. |
| IEC 61131-3 | CONFIRMED | LD/FBD/ST/IL/SFC + POUs. **IL deprecated in Ed.3 (2013), removed in Ed.4 (2025)** which added OOP. Paid. |
| IEC 62443 (security) | CONFIRMED | Zones & conduits, SL 1–4, roles (asset owner / integrator / product supplier). Paid; free-to-members via ISA. Underpins CANON's "no browser-to-PLC" posture. |
| IEC 62714 AutomationML | CONFIRMED | CAEX + COLLADA + PLCopen XML. IEC text paid; **AutomationML e.V. schemas/whitepapers/Engine are free**. |
| IEC 63278 AAS | **CONFIRMED — blueprint claim verified TRUE** | AAS is IEC 63278-1:2023 (EN 2024). **There is NO official/standardized AAS submodel for "HMI".** Verified against the IDTA catalog and `admin-shell-io/submodel-templates` (~90 templates, none HMI/visualization/UI). MTP and worker-data submodels exist, but no HMI submodel. → CANON may say "no AAS HMI submodel exists yet" with confidence. |
| PLCopen XML | CONFIRMED | Public **XSD free** (`TC6_XML_V201.xsd`, v2.01); adopted as **IEC 61131-10:2019** (that IEC doc is paid). Machine Expert exports it. |
| **NAMUR MTP** | **CHANGED — important** | MTP is real, specified in **VDI/VDE/NAMUR 2658** (Blatt 1 concept; **Blatt 2 = HMI modeling**; Blatt 3 data objects; Blatt 4 services; Blatt 5.1 OPC UA runtime). **BUT the international standard IEC 63280 was ABANDONED — "project deleted," stage 30.98, 6 Dec 2024.** So there is **no IEC 63280**; the live basis is the German VDI/VDE/NAMUR 2658 (paid). The "~70% engineering-effort cut / ~50% faster TTM / ~80% more flexible" numbers are **proponent/marketing claims** (NAMUR-ZVEI + suppliers), not independently audited. Use "aligned to / informed by," and drop any "standardized as IEC 63280" phrasing. |
| ISA-95 / ISA-88 | CONFIRMED | ISA-95 = IEC 62264 (enterprise-control / MES, Levels 0–4); ISA-88 = IEC 61512 (batch: physical/procedural models, recipe types). Both paid; B2MML/BatchML open schemas free. |

## D. AI models & embeddings (verified as of mid-2026; IDs rotate — pin at build)

- **Structured-intent LLMs — all four majors support strict JSON-schema output:** Anthropic Claude (`claude-opus-5`/`claude-sonnet-5`/`claude-haiku-4-5`, 1M ctx on Opus/Sonnet; `messages.parse()` schema validation), OpenAI GPT-5.x (`response_format json_schema` + `strict:true`, grammar-constrained 100% match), Google Gemini 2.5 Pro/Flash (`responseSchema`, anyOf/$ref, order preserved), xAI Grok 4.x (native structured outputs). Exact GPT-5.x / Grok specs are **UNVERIFIABLE** on pricing/context — pin after the 20-prompt CANON bench. **Adapter pattern (no hard-wired vendor) is the right call.**
- **Embeddings:** `text-embedding-3-small` still current (1536, Matryoshka; OpenAI hasn't refreshed embeddings since Jan-2024) → good confirmed default. Quality option **voyage-3-large** (MongoDB-owned Voyage; lineup CHANGED from voyage-3). Cohere **embed-v4.0** (supersedes v3). Local: **BGE-M3** (MIT) / **nomic-embed-text-v2-moe** (Apache-2.0).
- **Rerankers:** keep **NONE** for the prototype (verdict stands). If needed: `cohere-rerank-4-fast` (v3.5 deprecated 2026-07) or `BAAI/bge-reranker-v2-m3` (self-hostable).
- **Local fallback:** Qwen2.5-32B still runs but is superseded by **Qwen3-32B** (Apache-2.0); `qwen2.5-coder:7b` for a laptop demo; Llama 3.3 70B fine, Llama 4 newer. vLLM/Ollama both support JSON-schema-constrained decoding (xgrammar/outlines) → schema enforcement is feasible locally.

---

## E. Summary of edits the blueprint should absorb

1. **IEC 63280 does not exist** (abandoned Dec-2024). MTP = VDI/VDE/NAMUR 2658 only. Fix the "isn't this just MTP?" rebuttal and any "standardized as IEC 63280" line.
2. **PackML running state = "Execute"**, not "Running." (State model updated accordingly.)
3. **MFR53158 does not state "72 hours"** — cite the SE community forum for that figure.
4. **EOTE_Compound_Object is publicly downloadable** (not license-gated); only *authoring* needs Professional. Relax the RESTRICTED flag.
5. **M241/M251 confirmed OPC UA**, M221 confirmed *no* embedded OPC UA, M258 undocumented. Resolve the UNKNOWNs.
6. **Alarm-flood ">10/10min" origin = EEMUA 191**, adopted by ISA-18.2/IEC 62682.
7. **Version bumps:** React 19, Zod 4, ECharts 6, Vite 8, pytest 9, Vitest 5; asyncua 1.1.8, pymodbus 3.13, node-opcua 2.182, open62541 1.5.8, pgvector 0.8.6, Docling 2.126, UaExpert 2.0.2. OpenPLC v4 = MIT (in-dev).
8. **No AAS "HMI" submodel exists** — blueprint claim VERIFIED; safe to state.
9. Everything else in the blueprint (architecture bans, stack choices, protocol/DB/simulator evaluations, the four-layer authority model) is **consistent with current reality** — no corrections needed.

## F. What we generated where the web couldn't (per the "if you can't get it, create it" instruction)
- `../datasets/canon_demo_machine.json` — full TK-401 hero canonical model.
- `../engine/` — command contracts, component registry, validation rules, PackML-mapped state models, change-impact rules, protocol registry.
- `../ai/` — ai_models.json, embedding/rerank registry, prompt templates, QLoRA training spec — all populated with the **verified** 2026 model data.
- `../synthetic/` — a deterministic generator producing **1,200 synthetic machines + 23,298 correct-by-construction NL→intent pairs + 1,200 runtime traces (~15 MB)**, with the anti-hallucination guarantee machine-checked (0 violations).
