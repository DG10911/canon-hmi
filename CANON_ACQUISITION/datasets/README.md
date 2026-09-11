# CANON external dataset registry

**53 real, web-verified public datasets** for training/augmenting CANON, discovered
across Hugging Face, Kaggle, and GitHub/official sources by 3 parallel verification
agents. Every URL was confirmed reachable; gated ICS datasets are marked `request`/
`gated` with their real registration page — **never** claimed directly downloadable.

## Contents
```
hf_datasets.json        16  Hugging Face datasets
kaggle_datasets.json    20  Kaggle datasets
github_datasets.json    17  GitHub repos + official dataset pages
dataset_registry.json   merged, deduped registry (53) + summaries
pull_datasets.sh        fetch the public ones; gated ones listed as comments w/ request URL
consolidate.py          rebuild the registry + pull script (pure stdlib)
```

## By source / access / category
- **source:** hf 16 · kaggle 20 · github 17
- **access:** public 30 · public-login-required 20 (Kaggle) · gated 2 (Salesforce xLAM/APIGen) · request 1 (iTrust SWaT/WADI/EPIC)
- **category:** predictive-maintenance 11 · ics-security 8 · protocol-traffic 8 · timeseries-sensor 7 · instruction-tuning 5 · plc-code 4 · awesome-list 3 · technical-qa 3 · hmi-scada 2 · manufacturing 2

## Highlights per CANON need
- **PLC code (IEC 61131 ST):** Agents4PLC_dataset_v2 (HF), OpenPLC_v3 / Beremiz / OpenPLC_Editor (GitHub) — real ST/LD to teach code intelligence (§47).
- **Protocol traffic (Modbus/OPC UA/DNP3):** Edge-IIoTset (HF), ICS_PCAPS / Netresec 4SICS / Modbus injection sets (Kaggle+GitHub) — for §23–25 protocol grounding.
- **Predictive maintenance / sensor time-series:** NASA C-MAPSS turbofan, CWRU/IMS bearings, pump_sensor, PMSM motor temp, AI4I 2020 — realistic signal/alarm behavior.
- **ICS security benchmarks:** SWaT/WADI/EPIC (iTrust — **request only**), HAI, Morris gas-pipeline/water-tank, ipal_datasets — anomaly + attack context.
- **Function-calling / JSON tool-use (to sharpen the 3B model):** glaive, Hermes, xLAM-60k, APIGen-MT — directly relevant to CANON-brain's "emit valid JSON, bind only to real tags" task.

## Use it
```bash
cd datasets
./pull_datasets.sh ./downloads      # needs: huggingface-cli, kaggle (with ~/.kaggle/kaggle.json)
# gated/request datasets: open the URL in dataset_registry.json and apply for access
```

## Actually using the 53 (two layers)
The datasets feed CANON in two distinct ways — run these on the DGX after `pull_datasets.sh`:

**A) Model layer — blend function-calling data into a v2 model** (`../model/mix_external.py`)
```bash
cd ../model
python mix_external.py --out data/train_v2.jsonl --external-frac 0.25   # open glaive/Hermes only
python train_qlora.py --data data/train_v2.jsonl --out out/canon-brain-3b-v2 --max-samples 12000
```
Downloads the OPEN function-calling sets, normalises them to CANON's chat format, and
blends ~25% external / 75% CANON so the CANON task stays dominant. Gated sets
(xLAM/APIGen) are skipped unless `--include-gated` and you accepted their terms.

**B) Corpus layer — ingest raw ICS/sensor CSVs as OBSERVED data** (`ingest_external.py`)
```bash
./pull_datasets.sh ./downloads
python3 ingest_external.py --csv downloads/<dataset>/<file>.csv \
    --source-id <ID-from-registry> --name "<name>" --sep ,
# -> ../out_external/*.jsonl  (candidate signals + observed facts + evidence + unknowns)
```
Every column becomes a CANDIDATE signal with an OBSERVED range, tagged REPORTED and
`§62`-noted as **not authoritative** — real machine config always dominates observed
telemetry, so dataset columns can never masquerade as verified machine truth (§67).
Non-numeric columns become review-unknowns (never dropped, §50). Output stays in a
separate `out_external/` tree, merged into the main corpus only with explicit provenance.

## License discipline (§0, §26)
Licenses are recorded per entry (many Kaggle cards are JS-rendered so license = UNKNOWN
until a logged-in `kaggle datasets metadata` pull). **Check each license before training
on or redistributing** — some are non-commercial (APIGen-MT cc-by-nc-4.0) or AGPL (NAB).
For CANON these are *augmentation/reference* corpora; the model's grounding guarantee
still comes from the deterministic validator, not from any external dataset.

## Honesty notes from discovery
- SWaT/WADI/HAI/CIC-Modbus are **not** on Hugging Face — excluded from HF rather than invent repo ids; represented via their real iTrust/GitHub/UNB homes.
- A handful of search hits returned 404 on fetch and were **dropped, not invented** (logged in each agent's run).
- One HF entry (Agents4PLC_dataset_v2) is `REACHABLE_UNVERIFIED` — real per search but the repo returned 401 on fetch; flagged, not asserted.
