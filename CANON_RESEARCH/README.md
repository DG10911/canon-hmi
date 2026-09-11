# CANON_RESEARCH

Deliverable for: *"verify by web check; where you can't get it, create a huge synthetic dataset + model for our system; do all."* (2026-09-10)

## Layout
```
report/CANON_VERIFICATION_REPORT.md   ← START HERE. Every blueprint resource web-verified + corrections.
datasets/canon_demo_machine.json      ← TK-401 hero canonical model (assets/signals/io/cmds/alarms/runtime).
engine/                               ← CANON deterministic engine data
  canon_command_contracts.json        ← permissives, interlocks, reject codes, timeouts
  canon_component_registry.json       ← HMI component registry (LLM may only SELECT from this)
  canon_validation_rules.json         ← deterministic check catalog (no rule calls an LLM)
  canon_state_models.json             ← PackML-mapped device state machines (Running→Execute)
  canon_change_rules.json             ← change-impact edges + the PT401 0-10→0-16 bar hero scenario
  protocol_registry.json              ← OPC UA / Modbus verified facts + libs
ai/                                   ← AI stack, populated with VERIFIED 2026 models
  ai_models.json  embedding_and_rerank_models.json  prompt_templates.json  training_spec.json
synthetic/                            ← the "super crazy amount" of data
  gen_canon_dataset.py                ← deterministic seeded generator (pure stdlib)
  README.md                           ← counts, balance, the guarantee
  out/                                ← 1,200 machines · 23,298 NL→intent pairs · 1,200 traces (~15 MB)
```

## Bottom line
- **Verification:** the blueprint is largely accurate. Corrections: IEC 63280 abandoned (MTP = VDI/VDE/NAMUR 2658 only); PackML state = "Execute" not "Running"; MFR53158 doesn't state the 72h figure; EOTE compound-object library is public not gated; M241/M251 confirmed OPC UA / M221 confirmed none; alarm-flood ">10/10min" origin = EEMUA 191; OSS version bumps (React 19, Zod 4, ECharts 6, Vite 8, pytest 9, Vitest 5, etc.); **no official AAS HMI submodel exists** (claim verified). All licenses check out.
- **Synthetic data + model:** 23,298 correct-by-construction NL→intent pairs across 1,200 machines, anti-hallucination guarantee machine-verified (0 violations), plus a QLoRA training + eval spec targeting a local Qwen3/Qwen2.5-coder model. Regenerate bit-identically with `python3 synthetic/gen_canon_dataset.py --machines 1200 --seed 401`.

All CANON-authored data is tagged **PROPOSED**; Schneider facts are **VERIFIED** with citations in the report. No Schneider proprietary internals, no invented SKUs/APIs.
