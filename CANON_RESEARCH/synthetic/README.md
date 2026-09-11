# CANON Super-Synthetic Dataset

Deterministic, seeded, pure-stdlib generator for the CANON PS2 "brain". Everything is
**correct by construction**: each training pair is generated *from* a machine model that
CANON's own deterministic engine would accept, so labels need no human and cannot hallucinate.

## Regenerate
```bash
python3 gen_canon_dataset.py --machines 1200 --seed 401
```
Outputs land in `out/`. Bit-identical for a given seed.

## What's in `out/` (default 1200 machines, seed 401)

| File | Rows | Bytes | Contents |
|---|---|---|---|
| `machines.jsonl` | 1,200 | ~4.5 MB | Synthetic machines across 5 archetypes (transfer_line, mixer, packaging_line, pump_station, heat_exchanger). 12,818 signals, 4,740 commands, 2,519 alarms. Controller families are VERIFIED family-level refs only (M262/M580/M241/M251/M340). |
| `intents_train.jsonl` | 20,969 | ~7.2 MB | NL → validated intent JSON. |
| `intents_eval.jsonl` | 2,329 | ~0.8 MB | Held-out split. |
| `runtime_traces.jsonl` | 1,200 | ~2.7 MB | Deterministic simulator traces (regression fixtures). |
| `manifest.json` | — | — | Counts, class balance, provenance. |

**Total: 23,298 NL→intent pairs.**

## Class / intent balance
- Labels: `accept` ~16.2k · `refuse` ~4.8k · `reject_expected` ~2.3k
- Intent types: `command_request` ~9.4k · `generate_hmi` ~9.2k · `explain_alarm` ~2.5k · `change_impact` ~2.2k

## The guarantee (verified)
A checker confirms over all 23,298 rows:
- Every `accept`/`reject_expected` pair binds **only** to signals present in its own machine model — 0 leaks.
- Every `refuse` pair carries an `UNKNOWN` and binds to **nothing** (invented tag / invented command / unverified Schneider product).

This is the CANON thesis as data: *AI proposes, the machine model defines, the validator checks.*
The tuned model's output is still re-validated by deterministic code, which drops any unknown identifier — so a fine-tune failure degrades gracefully to a refusal, never to a fabricated tag.

## Truth status
`PROPOSED / synthetic`. Tags, addresses, and physics are CANON-authored. No Schneider proprietary internals.
