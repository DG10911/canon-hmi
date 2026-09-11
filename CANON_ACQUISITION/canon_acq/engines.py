"""Corpus engines: entity resolution, coverage, HMI readiness, integrity.

These operate on an already-populated Corpus. They never invent data; they
only aggregate, cross-check and score what evidence exists (sec 35-43, 55).
"""
from __future__ import annotations
import re
from typing import Any

from .enums import (COVERAGE_DIMENSIONS, HmiReadiness, KnowledgeState,
                    ResolutionStatus)
from .ids import content_hash
from .models import EntityAlias
from .store import Corpus


# --- Entity resolution (section 37) ---------------------------------------
def _norm(tag: str) -> str:
    """PT-401 / PT_401 / Pressure_401 -> comparable key. Conservative."""
    return re.sub(r"[^a-z0-9]", "", tag.lower())


def resolve_entities(corpus: Corpus) -> int:
    """Attach candidate aliases by normalised-tag match. Never auto-merges
    distinct canonical entities (section 37: no merge without evidence)."""
    entities = corpus.data["entities"]
    by_norm: dict[str, list[dict]] = {}
    for e in entities:
        by_norm.setdefault(_norm(e["entity_id"]), []).append(e)
    added = 0
    for e in entities:
        # register the canonical id as its own resolved alias
        corpus.add("entity_aliases", EntityAlias(
            entity_id=e["entity_id"], alias=e["entity_id"],
            resolution_status=ResolutionStatus.RESOLVED.value,
        ))
        added += 1
        # if the entity's human name differs, register it as a candidate alias
        name = e.get("name", "")
        if name and _norm(name) != _norm(e["entity_id"]):
            status = (ResolutionStatus.CANDIDATE.value
                      if _norm(e["entity_id"]) in _norm(name) or _norm(name) in _norm(e["entity_id"])
                      else ResolutionStatus.AMBIGUOUS.value)
            corpus.add("entity_aliases", EntityAlias(
                entity_id=e["entity_id"], alias=name, resolution_status=status,
                confidence="INFERRED",
            ))
            added += 1
    return added


# --- Duplicate/revision engine (section 36, 51) ---------------------------
def detect_duplicates(corpus: Corpus) -> int:
    seen: dict[str, str] = {}
    dupes = 0
    for d in corpus.data["documents"]:
        h = d.get("content_hash")
        if not h:
            continue
        if h in seen and seen[h] != d["document_id"]:
            dupes += 1
        else:
            seen[h] = d["document_id"]
    return dupes


# --- Coverage (section 41) ------------------------------------------------
def _pct(have: bool | int, need: int = 1) -> float:
    if isinstance(have, bool):
        return 100.0 if have else 0.0
    return round(100.0 * min(have, need) / need, 1) if need else 0.0


def compute_coverage(corpus: Corpus) -> dict:
    d = corpus.data
    n_signals = len(d["signals"])
    signals_with_io = len({r["signalId"] for r in d["io"]})
    signals_with_evidence = len({f["subject"] for f in d["facts"]
                                 if any(s["signalId"] == f["subject"] for s in d["signals"])})
    facts_with_ev = sum(1 for f in d["facts"] if f.get("evidence_id"))
    cov = {
        "MachineIdentity": _pct(len(d["entities"]) > 0 and any(e["kind"] == "MACHINE" for e in d["entities"])),
        "Controller": _pct(any(e["kind"] == "CONTROLLER" for e in d["entities"])),
        "IO": _pct(signals_with_io, max(1, n_signals)),
        "Signal": _pct(signals_with_evidence, max(1, n_signals)),
        "Asset": _pct(len(d["assets"]) > 0),
        "Process": _pct(len(d["process_relationships"]), 6),
        "Command": _pct(len(d["commands"]), 4),
        "Permissive": _pct(len(d["permissives"]) > 0),
        "Interlock": _pct(len(d["interlocks"]) > 0),
        "Alarm": _pct(len(d["alarms"]), 6),
        "State": _pct(len(d["states"]) > 0),
        "Sequence": _pct(len(d["sequences"]) > 0),
        "HMI": _pct(len(d["hmi_components"]) > 0 and len(d["hmi_screens"]) > 0),
        "Documentation": _pct(len(d["documents"]) > 0),
        "Evidence": _pct(facts_with_ev, max(1, len(d["facts"]))),
        "Revision": _pct(len(d["document_revisions"]) > 0),
    }
    assert set(cov) == set(COVERAGE_DIMENSIONS)
    cov["_overall"] = round(sum(v for k, v in cov.items() if not k.startswith("_")) / len(COVERAGE_DIMENSIONS), 1)
    corpus.coverage = cov
    return cov


# --- HMI readiness (section 42) -------------------------------------------
def compute_readiness(corpus: Corpus) -> dict:
    d = corpus.data
    open_conflicts = [c for c in d["conflicts"]
                      if c.get("resolution_status") == "UNRESOLVED"]
    review_unknowns = [u for u in d["unknowns"] if u.get("review_required")]
    checks = {
        "identity_complete": any(e["kind"] == "MACHINE" for e in d["entities"]),
        "assets_resolved": len(d["assets"]) > 0,
        "signals_resolved": len(d["signals"]) > 0 and all(
            any(f["subject"] == s["signalId"] for f in d["facts"]) or s.get("kind", "").startswith("discrete")
            for s in d["signals"]),
        "commands_resolved": len(d["commands"]) > 0,
        "permissives_resolved": len(d["permissives"]) > 0,
        "alarms_resolved": len(d["alarms"]) > 0,
        "states_resolved": len(d["states"]) > 0,
        "process_relationships_resolved": len(d["process_relationships"]) > 0,
        "evidence_available": corpus.coverage.get("Evidence", 0) >= 90,
        "conflicts_resolved": len(open_conflicts) == 0,
        "revision_consistent": len(d["document_revisions"]) > 0,
    }
    if all(checks.values()) and not review_unknowns:
        verdict = HmiReadiness.READY
    elif all(checks.values()) and review_unknowns:
        verdict = HmiReadiness.READY_WITH_REVIEW
    elif checks["identity_complete"] and checks["signals_resolved"] and checks["commands_resolved"]:
        verdict = HmiReadiness.PARTIAL
    else:
        verdict = HmiReadiness.BLOCKED
    out = {
        "readiness": verdict.value,
        "checks": checks,
        "open_conflicts": len(open_conflicts),
        "review_required_unknowns": len(review_unknowns),
        "blocking": [k for k, v in checks.items() if not v],
    }
    corpus.readiness = out
    return out


# --- No-hallucination audit (section 55, 67) ------------------------------
def audit_no_hallucination(corpus: Corpus) -> dict[str, Any]:
    """Machine-check the core guarantees. Returns violations (should be empty)."""
    d = corpus.data
    violations: list[str] = []

    # (1) every fact must carry a real source_id present in 01_sources
    source_ids = {s["source_id"] for s in d["sources"]}
    for f in d["facts"]:
        if f["source_id"] not in source_ids:
            violations.append(f'fact {f["fact_id"]} references unknown source {f["source_id"]}')
        if not f.get("evidence_id"):
            violations.append(f'fact {f["fact_id"]} has no evidence pointer')

    # (2) every evidence row must back an existing fact
    fact_ids = {f["fact_id"] for f in d["facts"]}
    for ev in d["evidence"]:
        if ev["fact_id"] not in fact_ids:
            violations.append(f'evidence {ev["evidence_id"]} backs unknown fact {ev["fact_id"]}')

    # (3) UNKNOWN must never be presented as KNOWN
    for e in d["entities"]:
        if e.get("knowledge_state") == KnowledgeState.UNKNOWN.value and e.get("truth_status") == "VERIFIED":
            violations.append(f'entity {e["entity_id"]} is UNKNOWN yet marked VERIFIED')

    # (4) every embedding must be flagged non-semantic (no fake vectors sold as real)
    for emb in d["embeddings"]:
        if emb.get("method") != "placeholder-hash":
            violations.append(f'embedding {emb["embedding_id"]} not flagged placeholder')

    # (5) every relationship subject/object should be a known entity id or signal/command
    known = ({e["entity_id"] for e in d["entities"]}
             | {s["signalId"] for s in d["signals"]}
             | {c["command_id"] for c in d["commands"]}
             | {s["source_id"] for s in d["sources"]})   # DOCUMENTED_BY -> source_id
    for r in d["relationships"]:
        for endp in (r["subject"], r["object"]):
            if endp not in known and not endp.startswith(("PERM_", "IL_", "STATE_", "CMP_", "MODE_")):
                # tolerate protocol names / literal expected-values only if entity exists
                if endp not in {p["id"] for p in d["protocols"]} and endp not in {p["name"] for p in d["protocols"]}:
                    violations.append(f'relationship {r["relationship_id"]} endpoint {endp!r} not a known entity')

    return {
        "checked_facts": len(d["facts"]),
        "checked_evidence": len(d["evidence"]),
        "checked_relationships": len(d["relationships"]),
        "violations": violations,
        "ok": len(violations) == 0,
        "corpus_hash": _structural_hash(d),
    }


_VOLATILE = {"created_at", "retrieval_timestamp", "generated", "last_updated"}


def _structural_hash(data: dict) -> str:
    """Hash the corpus structure, ignoring volatile timestamps so an unchanged
    input yields a stable hash across runs (sec 51 duplicate/revision engine)."""
    def strip(obj):
        if isinstance(obj, dict):
            return {k: strip(v) for k, v in obj.items() if k not in _VOLATILE}
        if isinstance(obj, list):
            return [strip(x) for x in obj]
        return obj
    return content_hash(strip({k: v for k, v in data.items() if k != "context_packs"}))
