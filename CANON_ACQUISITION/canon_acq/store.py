"""Corpus store — holds the 37 datasets and writes them + the manifest.

JSONL/JSON files under out/ mirror the Postgres tables in db/schema.sql. This
is the P0 persistence layer (spec section 53 permits Postgres adjacency tables;
JSONL keeps the demo runnable with no DB).
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from typing import Any

from .enums import DATASETS
from .models import Record


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# maps python collection name -> dataset file stem
COLLECTION_TO_DATASET = {
    "sources": "01_sources",
    "documents": "02_documents",
    "document_revisions": "03_document_revisions",
    "entities": "04_entities",
    "entity_aliases": "05_entity_aliases",
    "signals": "06_signals",
    "io": "07_io",
    "assets": "08_assets",
    "controllers": "09_controllers",
    "modules": "10_modules",
    "instruments": "11_instruments",
    "motors": "12_motors",
    "drives": "13_drives",
    "valves": "14_valves",
    "commands": "15_commands",
    "permissives": "16_permissives",
    "interlocks": "17_interlocks",
    "alarms": "18_alarms",
    "states": "19_states",
    "modes": "20_modes",
    "sequences": "21_sequences",
    "process_relationships": "22_process_relationships",
    "hmi_screens": "23_hmi_screens",
    "hmi_components": "24_hmi_components",
    "protocols": "25_protocols",
    "products": "26_products",
    "standards": "27_standards",
    "procedures": "28_procedures",
    "facts": "29_facts",
    "relationships": "30_relationships",
    "evidence": "31_evidence",
    "conflicts": "32_conflicts",
    "unknowns": "33_unknowns",
    "dependencies": "34_dependencies",
    "change_history": "35_change_history",
    "context_packs": "36_context_packs",
    "embeddings": "37_embeddings",
}


class Corpus:
    """In-memory hold-all for every dataset; append rows, then write()."""

    def __init__(self) -> None:
        self.data: dict[str, list[dict]] = {name: [] for name in COLLECTION_TO_DATASET}
        self.coverage: dict[str, Any] = {}
        self.readiness: dict[str, Any] = {}

    def add(self, collection: str, row: Any) -> None:
        if collection not in self.data:
            raise KeyError(f"unknown collection {collection!r}")
        self.data[collection].append(row.to_dict() if isinstance(row, Record) else row)

    def extend(self, collection: str, rows) -> None:
        for r in rows:
            self.add(collection, r)

    def count(self, collection: str) -> int:
        return len(self.data[collection])

    # ---- persistence ----
    def write(self, out_dir: str) -> dict:
        os.makedirs(out_dir, exist_ok=True)
        written = {}
        for coll, stem in COLLECTION_TO_DATASET.items():
            rows = self.data[coll]
            path = os.path.join(out_dir, f"{stem}.jsonl")
            with open(path, "w", encoding="utf-8") as fh:
                for row in rows:
                    fh.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            written[stem] = len(rows)
        assert set(written) == set(DATASETS), "all 37 datasets must be emitted"
        return written

    def write_manifest(self, out_dir: str, extra: dict) -> str:
        """corpus_manifest.json (spec section 58)."""
        manifest = {
            "corpus": "CANON_ACQUISITION",
            "collection_timestamp": _now(),
            "sources_discovered": self.count("sources"),
            "sources_acquired": sum(
                1 for s in self.data["sources"] if s.get("status") in ("ACQUIRED", "VERIFIED")
            ),
            "sources_failed": sum(1 for s in self.data["sources"] if s.get("status") == "FAILED"),
            "documents_processed": self.count("documents"),
            "documents_skipped": 0,
            "duplicates": extra.get("duplicates", 0),
            "revisions": self.count("document_revisions"),
            "entities": self.count("entities"),
            "facts": self.count("facts"),
            "relationships": self.count("relationships"),
            "conflicts": self.count("conflicts"),
            "unknowns": self.count("unknowns"),
            "reference_datasets": extra.get("reference_datasets", {"present": False}),
            "coverage": self.coverage,
            "hmi_readiness": self.readiness,
            "dataset_row_counts": {stem: len(self.data[c]) for c, stem in COLLECTION_TO_DATASET.items()},
            "licenses": extra.get("licenses", []),
            "errors": extra.get("errors", []),
            "notes": extra.get("notes", []),
        }
        path = os.path.join(out_dir, "corpus_manifest.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2, sort_keys=True)
        return path

    def write_source_registry(self, out_dir: str) -> str:
        """source_registry.json (spec section 59)."""
        path = os.path.join(out_dir, "source_registry.json")
        payload = {
            "generated": _now(),
            "total": self.count("sources"),
            "by_trust_tier": self._tier_counts(),
            "sources": self.data["sources"],
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
        return path

    def _tier_counts(self) -> dict:
        out: dict[str, int] = {}
        for s in self.data["sources"]:
            k = str(s.get("trust_tier"))
            out[k] = out.get(k, 0) + 1
        return dict(sorted(out.items()))
