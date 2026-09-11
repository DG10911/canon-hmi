# CANON / PS2 — MASTER RESEARCH DOSSIER
**PS2 = Dynamic HMI generation at runtime + machine control via HMI.** Team DigiSeva · Schneider HMI Hackathon 2026.
Research by a 6-agent, 4-model swarm (Opus/Sonnet/Haiku/Fable). Labels: VERIFIED / STRONG / INFERENCE.

---

## 0. THE ONE-PARAGRAPH VERDICT
Exhaustive search (all major vendors + startups + patents + academia, 2024–2026) confirms **no product or paper ships the FULL LOOP**: a *canonical fused machine model* → **runtime, on-demand, validated** HMI generation with **PLC-authoritative guardrails** → **LLM-reasoned change-impact continuity**. Every piece has prior art individually; the integrated loop is **genuine whitespace (verified by absence)**. CANON must therefore NOT pitch "AI generates an HMI" (patented since 2007) — it must pitch **"a generation-plus-guarantee system": validated bindings + PLC authority + change-continuity, at runtime.**

---

## 1. COMPETITIVE LANDSCAPE (VERIFIED, multi-agent)
**Headline (VERIFIED by absence across Siemens, Rockwell, Schneider, AVEVA, Ignition, COPA-DATA, GE, Emerson, Honeywell, ABB, startups):** *No vendor ships runtime, generative HMI creation with machine-control authority.* All generative HMI = **build/design-time, human-gated.** Runtime "dynamic" = pre-engineered faceplates/scripts/bindings.

### Closest competitors (must differentiate from these by name)
- **Siemens Eigen Engineering Agent** — GA **20 Apr 2026**, TIA Portal. Agentic, **self-validating**, generates PLC code + **WinCC Unified HMI** (mostly JS behavior / VB migration, not clearly full NL screen-layout). **BUILD-TIME**, engineer-reviewed, no runtime, no PLC control authority. *The strongest "we already do that" threat.* [VERIFIED]
- **Tatsoft FrameworX AI Designer** — shipping **Mar 2026**; **MCP-based** (Claude/Cursor/Copilot drive the config API: tags, alarms, **screens**, historian); claims 40–50% timeline cut. **BUILD-TIME** config generation (+ runtime AI *chat* over live data, on-prem). Architecturally the most direct analog. [VERIFIED]
- **Honeywell "vibe engineering" / Experion Cognition** — preview, 2026; NL → HMI displays + P&IDs + tests, **build-time**, DCS-scale, human-gated sandbox. [STRONG]
- **Siemens SiVArc** — genuine model-driven HMI screen/tag generation **from the PLC program via rules** (NOT AI), build-time. The incumbent deterministic baseline. [VERIFIED]
- **Runtime NL machine control** — research only: *arXiv 2510.11300* "Beyond touch-based HMI" (LLM + OPC UA tool-calling controls machines via NL); **MCP-for-PLC** emerging plumbing (no safety validation, no HMI gen). [STRONG]

### Model/template-driven HMI (mature, NON-AI — do not claim as novel)
Siemens WinCC Unified faceplates(UDT) · Rockwell Optix "Types" · AVEVA ArchestrA templates · **Ignition UDT + indirect binding** (runtime *retargeting*, not generation) · **COPA-DATA zenon Smart Objects** (deterministic template instantiation) · GE Proficy model-based HMI · ABB 800xA aspect objects. **NAMUR MTP** auto-generates a module's HMI from its package (standardized, ~70% effort cut) — the closest *standardized* precedent, but static/build-time/process-only.

### Reality-check (great pitch ammo)
**ARC Advisory "LLM-Wrapper Illusion"** (570 decision-makers, 100+ vendors, 40+ copilots): **>65% fail under real operational stress**; most are chat sidecars lacking "cyber-physical grounding." ARC prescribes **"generative UI + hardcoded execution bounds + living knowledge graph"** → *that is exactly CANON's design.* [VERIFIED]

### CANON whitespace (defensible): runtime + validated bindings + PLC authority + change-continuity, ingesting MTP/AAS/OPC-UA/UDT.
**MUST NOT claim:** "novel/first AI-generated HMI"; "nobody generates HMI with AI." **SAY:** differentiation = machine-context-driven generation with validated bindings, controlled interaction, change-aware regeneration — a *guarantee* layer, not a generator.

---

## 2. STANDARDS / MACHINE-CONTEXT MODELS (VERIFIED) — credibility backbone
- **ISA-101** (HMI): 4-level hierarchy (L1 overview→L4 diagnostics), restrained color (gray normal, color only for abnormal). → **hard, checkable render rule** in the generator (demoable).
- **ISA-18.2 / IEC 62682 / EEMUA 191** (alarms): each alarm = {tag, setpoint, priority, class, cause, consequence, required action} in a Master Alarm DB. **Flood = >10/10 min** → live computed state.
- **ISA-95 / IEC 62264 + ISA-88**: equipment hierarchy Enterprise→Site→Area→Cell→Unit→Equipment Module→Control Module → canonical-model skeleton + HMI nav.
- **OPC UA + companion specs** (DI, Machinery, PackML, AML): browsable object graph (NodeSet2.xml). → ingest/expose canonical model as OPC UA info model = **"read the type graph → generate the screen"** (best live-demo credibility).
- **AutomationML / IEC 62714** (CAEX+COLLADA+PLCopenXML): engineering exchange incl. HMI. → **offline ingestion** format.
- **AAS / IEC 63278** (IDTA): asset digital-twin shell of submodels. **PRECISION: NO official AAS "HMI"/visualization submodel** → use AAS as asset-metadata envelope ONLY.
- **NAMUR MTP (VDI/VDE/NAMUR 2658 / IEC 63280)** — deepest hit: **Part 2 = HMI**, **Part 3 = DataAssembly** (typed value+status+unit+limits), **Part 6/7 = alarms**. Frame CANON as **"MTP-inspired."** **Schneider itself publicly presents on MTP** → lands with judges. **MTP 2.0 released 2026.**
- **PackML/OMAC**: standard machine-state model (17 states) → standard state widget.
**Name-drop top 4:** MTP · OPC UA(+companion) · ISA-18.2/IEC 62682 · ISA-101. **Claim rule:** "aligned to / informed by," NEVER "compliant / certified / conformant."

---

## 3. PRIOR-ART / PATENTS (VERIFIED) — the honesty firewall
"AI/model-driven HMI generation" has **15+ years of patents**:
| Patent | Assignee | Date | Covers |
|---|---|---|---|
| US8,533,619B2 | Rockwell | 2007/2013 | context/state-driven dynamic HMI generation (ML-inferred intent) |
| US9,235,454B2 | Siemens | 2012/2016 | server generates HMI **on-demand from an engineering database + live state**, role/event-based |
| US11,175,931 / US11,861,379 | AVEVA | 2016/21-24 | runtime auto-compose GUI by traversing a navigation/metadata model ("data-driven HMI") |
| **US20250005224A1** | **Rockwell** | filed 2023, pub Jan 2025 (**pending**) | **LLM generates HMI faceplates "with connections to the respective logic" + response validation** — the closest to CANON |
| US10,281,894 / US8,798,775 | (bind graphics to controller data; **detect new/deleted PLC tags → add/flag HMI element**) | — | deterministic change-reconciliation prior art |
MTP = non-patent prior art for "auto-gen HMI from canonical module model."
**Honest novelty:** the **compound** {generation FROM canonical single-source model + *validated/typed* bindings + *PLC-as-authority* consistency + *change-continuity* with audit/operator-state retention}. **No single prior-art hit combines all four** — esp. PLC-authority invariant & continuity appear **unclaimed**. **Do FTO counsel** vs US20250005224A1 & US9,235,454 before any IP claim.
**NEVER say:** "first to use AI to generate HMI"; "no one generates HMI from NL"; "context/role-based dynamic HMI gen is novel." (all false.)

---

## 4. ROI / MARKET / USE CASES (VERIFIED)
- PS's "50–70% HMI lifecycle = screens" has **no primary source** (cite as "per the problem statement"). Back with: **MTP "up to 70% engineering-effort reduction"** (best sourced); **70% of HMI designers hand-script screens** (Pro-face/Schneider); unified platforms **~50%** cut; commissioning cuts **Siemens 70% / Rockwell 60% / Schneider ~50% (500 hrs)**, ARC 15–30%.
- **SCADA market $12.9B(2025)→$13.9B(2026), ~8.5% CAGR.** Digital twin **$39.5B→$53.6B**; 43% use ≥1 twin, 59% plan by 2028. 76% mfrs implementing AI by 2026. Boehm cost-of-change $1→$10→$100. Automation ROI 10:1–30:1, payback 12–18 mo.
- **Use cases (quantified, guarded):** brownfield migration (200–400 hrs screen re-authoring; ~50% saved) · multi-machine variant scale-out (70–80% cut) · commissioning (target 40–50%) · machine-change adaptability (40–50% change-cycle cut) · size-independent HMI (~80% responsive-layout cut) · operator onboarding (train −20–30%, errors −40–60% per ISA-101).
- **Do NOT claim numerically:** "50-70% lifecycle is screens" as fact; "AI cuts commissioning 70%" (that's Siemens motion VC); universal $ rework; "90% twin adoption"; universal "genAI cuts eng X%."

---

## 5. DATASETS & DATA SOURCES (VERIFIED free) — buildable now
**OPC UA servers (expose machine model as info model):** node-opcua sample server ⭐ (Node.js, 5-min) · open62541 ⭐ (C, Pi) · Prosys Simulation Server (free) · Unified Automation demo + UaExpert client · digitalpetri Milo (online `opc.tcp://milo.digitalpetri.com:62541/milo`).
**PLC/Modbus sims (control + permissive reject):** pymodbus ⭐ · ModbusPal ⭐ · OpenPLC ⭐ (IEC 61131-3 runtime, Pi) · CODESYS sim · Factory I/O (3D, trial).
**Canonical-model inputs:** AutomationML samples (github.com/AutomationML/AMLEngine2.1, PyAutomationML) · AAS/AASX (IDTA specs, Bosch semantic stack) · MTP sample (VDI/VDE/NAMUR 2658) · ISA-5.1 tag naming (PT/TT/XV…).
**Live data for trends/alarms:** **Tennessee Eastman** ⭐ (52 vars, 21 faults, Kaggle/IEEE) · **Wind-Turbine SCADA** (Zenodo 10958775) · **Industrial Alarm Monitoring 2018–2024** ⭐ (Kaggle, 6 yrs) · ICS Alarm Text (Kaggle) · beverage bottling line (Zenodo 18146866).
**HMI components/ref:** hmilibrary.com (900+ ISA-101 SVG) · ISA-101 docs · Node-RED PLC-sim flows · Ignition/Kepware demos (benchmark).
**Recommended 30-min stack:** node-opcua sample server + pymodbus (Tennessee-Eastman CSV playback) + minimal AML/JSON machine model (pump+3 sensors+2 valves) + Kaggle alarm CSV → CANON reads OPC UA → generates ISA-101 screen.

---

## 6. TECHNICAL STACK (VERIFIED build blueprint)
**The safety wedge (key idea): PROPOSE → COMPILE → VALIDATE.** The LLM only emits a **layout proposal** in a JSON schema whose `tag`/`widget`/`screen` fields are **`enum`s generated per-machine from the canonical model** → the model **physically cannot emit a tag that isn't in the model** (token-level grammar). A **deterministic TS compiler** then re-validates (AJV) against the model, applies ISA-101 rules, resolves bindings, and emits a flat component tree. LLM = proposer; **compiler = authority.** Keep a **no-LLM deterministic default-layout generator** as fallback so the demo never dies (also the "reproducible, same-model→same-HMI" credibility story).
- **LLM:** Claude structured outputs `output_config.format=json_schema` (GA) via `@anthropic-ai/sdk` `messages.parse` + `zodOutputFormat`, model `claude-opus-5`. Limits that shape design: **no recursion** → **flat element map** (parent-id + grid slot), **enums only** → per-machine tag/widget enums, **no numeric constraints** → ranges enforced by compiler/AJV. (Optional Vercel AI SDK `generateObject` for model-swap; offline: llguidance/xgrammar grammar-constrained decoding.)
- **Canonical model (JSON, Zod-typed):** borrow **OPC UA for Machinery (OPC 40001)** Identification/MachineryItemState + **PackML/ISA-TR88** 17-state machine vocabulary. Tag{path,dataType,unit,engRange,access,role,semantic,source} · Command{writesTag,preconditions,confirm,timeout,expectedFeedback} · AlarmDef{tag,condition,priority 1-4,message}. Load the model *into* the node-opcua server's address space so **"canonical model" and "OPC UA server" are literally the same thing** (strong demo point).
- **UI spec + renderer:** `@json-render/core`+`@json-render/react` (flat spec matches the non-recursive LLM schema; streaming render) with a **custom HMI catalog** (ValueTile/Gauge/Trend/StateBadge/AlarmBanner/AlarmList/CommandButton/SetpointInput/PumpSymbol/NavBar), SVG mimics, uPlot trends.
- **Size-independence:** proposals carry widget **priority + min-size, not pixels**; compiler solves small(7"/4-col)/medium(10-12"/8-col)/large(12-col) with CSS Grid + **container queries**; below breakpoints drop priority-3 to "More", keep state+alarm banner+E-stop always visible → **"same model, three HMIs on one screen"** demo.
- **Sim:** port existing `index.html` physics to fixed-timestep seeded TS; drive PLC logic as a **PackML statechart in XState v5**; expose via **node-opcua server + jsmodbus server** over one in-memory tag table (flip protocol live). Modbus TCP = Schneider-native (M241/ATV630/PM5300).
- **PLC-authoritative command contract:** HMI never mutates state; sends `Command{...}` → bridge checks role/preconditions/interlocks/state/range → writes command tag → PLC/sim decides → HMI shows **pending → verified/REJECTED(reason)** from feedback tag. Audit every command.
- **Data quality:** OPC UA `DataValue.StatusCode`+timestamps (Good/Uncertain/Bad/stale); Modbus derives quality (timeout→bad, no update >N·poll→stale). Bad/stale = greyed value + last-good ts; **command widgets disabled when feedback not Good**; 10-30 s startup grace.
- **Change-impact:** build a `graphology` directed graph (tag/command/alarm/interlock/state/widget/screen/test); on `diff(modelV1,V2)` BFS in-edges → classify regenerate / re-validate / re-test / unaffected; regenerate only impacted screens (cache others by hash); visualize impacted subgraph with **sigma.js**; auto-generate **Vitest** cases from command contracts → "validated HMI" = schema-valid + model-consistent + ISA-101-linted + tests pass.
- **Packaging:** pnpm workspace (model/compiler/bridge/sim/hmi); Vite `vite-plugin-singlefile` for the HMI + one node bridge/sim; **in-process "demo mode"** so `index.html` still runs offline like Round 1.
- **Team split:** P1 model+compiler+impact-graph+tests · P2 LLM proposer+schema-gen+repair-loop+fallback · P3 sim+node-opcua/jsmodbus+bridge+React catalog.
- **Top risks/mitigations:** (1) LLM quality/latency → deterministic fallback + pre-cache proposals by model-hash + streaming + warm grammar cache + ISA-101 linter w/ 1 repair round; (2) schema-subset mismatch (no recursion/numerics) → flat map + enums + AJV, test schema-gen day 1; (3) protocol plumbing eats time → `SecurityPolicy.None` (say so) + one tag table + normalized `{value,quality,ts}` frame day 1 + in-process demo mode.
- **Edge/PS4 future:** compiled tree is renderer-agnostic → **WPE WebKit/Cog** kiosk (unchanged web HMI) or **LVGL 9** (has `lv_web_emscripten` browser build) → makes the "size- & renderer-independent" claim credible. **FUXA** (MIT, OPC-UA/Modbus/S7) is the "what exists, non-generative" reference to cite.

---

## 7. SHARPENED POSITIONING & DEMO
**One-liner:** *"We don't generate a screen from a prompt — we generate a validated interface from the machine, and keep it in sync as the machine changes."*
**Differentiator sentence (safe):** *"Automatic and even LLM-assisted HMI generation already exist; CANON's contribution is the validation-and-continuity layer — provably-correct bindings against a canonical model, PLC-authoritative consistency, and continuity across regenerations."*
**5-wow demo:** (1) machine context in (OPC UA/AML) → canonical model+graph; (2) NL intent → **validated ISA-101 screen materializes**, widgets tag-bound (hover shows binding+VERIFIED); (3) START → **PLC permissive FALSE → REJECTED** (open valve → authorized); (4) *"diagnostics for current abnormal condition"* → new contextual screen; (5) **PT101 0-10→0-16 → impact map → regenerate → regression → approve → new baseline** (the moment nobody else can show).
**Judge red-team answers:** "isn't this MTP/Eigen?" → those are **build-time, static, human-gated**; CANON is **runtime + validated + PLC-authoritative + continuity, and can ingest MTP/AAS**. "how avoid hallucinated tags?" → deterministic compiler validates against canonical model; unverified = UNKNOWN, never rendered as control.
**Claims firewall:** aligned-to not certified · advisory AI, PLC controls · SIMULATED clearly labeled · UNKNOWN not fabricated · no "first/novel AI HMI" · no unsourced numbers.
