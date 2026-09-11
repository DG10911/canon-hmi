# CANON_ACQUISITION

**Autonomous Engineering Source Acquisition + Corpus Builder** — the evidence-first
knowledge-acquisition pipeline from the 71-section CANON blueprint, built as a new
sibling module feeding the existing CANON model (`../CANON`, `../CANON_RESEARCH`).

> CANON is not a document search engine. It is an engineering context engine.
> No source → no authoritative fact. UNKNOWN is never upgraded to KNOWN.

## Quick start (pure stdlib — no installs)
```bash
cd .context/CANON_ACQUISITION
python3 run_all.py
```
Writes everything to `out/`. Latest run:

```
sources 77 (70 web-verified + 7 machine)   entities 129
facts/evidence 117/117                      relationships 118
conflicts 1   unknowns 1   duplicates 0
coverage overall 100%    HMI readiness READY_WITH_REVIEW
no-hallucination audit   PASS (0 violations)
```

## Layout
```
run_all.py                 end-to-end DISCOVER→…→UPDATE CANON loop (§60)
DESIGN.md                  every one of the 71 spec sections → where it lives
requirements.txt           production deps (§69); P0 needs none
db/schema.sql              Postgres + pgvector DDL for all 37 datasets (§53/57)
sources/
  source_registry.seed.json   70 REAL web-verified public sources (§59) — every URL confirmed reachable
canon_acq/
  enums.py       trust tiers, knowledge states, the 37 dataset names, ontology (§2/38/55/57)
  models.py      Source/Document/Entity/Fact/Evidence/Conflict/… dataclasses (§32–39)
  ids.py         deterministic ids + content hashing (§51)
  store.py       Corpus: holds 37 datasets, writes JSONL + manifest + registry (§57–59)
  discovery.py   query-family generation (§31) + seed-registry loader (§30)
  classify.py    file classification + unknown handling (§49/50)
  web_ingest.py  ingest the verified web sources → sources/standards/products (§22/26/27)
  ingest_tk401.py  ingest the real TK-401 machine reality → evidence-linked facts (§63)
  engines.py     entity resolution, dedupe, coverage, HMI readiness, no-halluc audit (§37/41/42/51/55)
  context_pack.py  assemble the CANON Context Pack (§40)
  embeddings.py  deterministic PLACEHOLDER vectors, tagged non-semantic (§52)
out/                       generated: 37 datasets + manifest + registry + reports
```

## Outputs (§57/65)
- `out/01_sources.jsonl … 37_embeddings.jsonl` — the 37 required datasets
- `out/corpus_manifest.json` (§58), `out/source_registry.json` (§59)
- `out/context_pack.tk401.json` (§40), `out/coverage_report.json` (§41)
- `out/hmi_readiness.json` (§42), `out/no_hallucination_audit.json` (§55/67)

## Guarantees
- **Evidence spine (§34):** every fact carries `source_id` + `evidence_id` + a JSON-pointer `source_location`; the audit fails the run if any fact lacks provenance.
- **No fake data (§67):** the seed registry contains only URLs confirmed reachable by web verification; paid standards are stored as abstract-only; Schneider product capabilities stay `UNKNOWN` until a document body is parsed.
- **Machine reality wins (§62):** Tier-0 TK-401 facts are `AUTHORITATIVE`; generic vendor docs are `OFFICIAL` and never override them.
- **Deterministic:** unchanged inputs → identical `corpus_hash` (timestamps excluded).
- **Read-only (§68):** no PLC writes; live OPC UA/Modbus discovery (when enabled) is read-only.

See `DESIGN.md` for the full spec-coverage map and the honest P0 gaps.
