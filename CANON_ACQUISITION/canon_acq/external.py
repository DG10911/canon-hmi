"""Merge the ingested external datasets (out_external/) into the main corpus.

Part B (`datasets/ingest_all.sh`) writes real ICS/sensor data to out_external/ as
CANDIDATE/OBSERVED rows. This folds them into the corpus so they are actually
consumed — they appear in 01_sources / 06_signals / 29_facts / 31_evidence /
33_unknowns, the manifest, and search — as REFERENCE data (tier 4/5, observed),
never authoritative machine truth (§62). Machine coverage + the TK-401 context
pack are computed BEFORE this merge, so they stay clean.
"""
from __future__ import annotations
import json
import os

# out_external dataset stem -> corpus collection
_MAP = {
    "01_sources": "sources", "06_signals": "signals", "29_facts": "facts",
    "31_evidence": "evidence", "33_unknowns": "unknowns",
}


def _load(ext_dir, stem):
    path = os.path.join(ext_dir, f"{stem}.jsonl")
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def merge_external(corpus, ext_dir: str, min_cols: int = 10, max_cols: int = 120,
                   min_samples: int = 200) -> dict:
    """Fold external datasets in — but only real ENGINEERING tag datasets. A source
    is kept only if it has `min_cols`..`max_cols` signals AND at least `min_samples`
    rows. Real ICS datasets are WIDE (SWaT 51 tags, steel 34, motor 13, SCADA 11);
    the noise is narrow (3-4 col log/shard/code files). This keeps the genuine ones."""
    if not os.path.isdir(ext_dir):
        return {"present": False}
    from collections import Counter, defaultdict
    sigs = _load(ext_dir, "06_signals")
    per_source = Counter(s.get("source") for s in sigs)
    max_samp = defaultdict(int)
    for s in sigs:
        max_samp[s.get("source")] = max(max_samp[s.get("source")], s.get("samples") or 0)
    keep = {src for src, n in per_source.items()
            if min_cols <= n <= max_cols and max_samp[src] >= min_samples}
    total_sources = len(_load(ext_dir, "01_sources"))

    def src_of(row):
        return (row.get("source") or row.get("source_id")
                or str(row.get("subject", "")).rsplit(":", 1)[0])

    added = {}
    for stem, coll in _MAP.items():
        n = 0
        for row in _load(ext_dir, stem):
            if src_of(row) not in keep:
                continue
            row.setdefault("origin", "external-reference")
            corpus.add(coll, row)
            n += 1
        added[stem] = n
    kept_sample = sorted(keep, key=lambda s: -per_source[s])[:15]
    return {"present": True, "reference_sources": len(keep),
            "reference_signals": added.get("06_signals", 0),
            "reference_facts": added.get("29_facts", 0),
            "dropped_low_quality_sources": total_sources - len(keep),
            "filter": f"{min_cols}-{max_cols} cols AND >={min_samples} rows",
            "kept": [{"source": s, "signals": per_source[s]} for s in kept_sample], "rows": added}
