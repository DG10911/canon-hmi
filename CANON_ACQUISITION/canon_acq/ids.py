"""Deterministic identifiers and content hashing (spec sections 32, 44, 51).

Deterministic so that re-running the pipeline on unchanged inputs yields
bit-identical corpus ids (needed by the duplicate/revision engines).
"""
from __future__ import annotations
import hashlib
import json
from typing import Any


def content_hash(data: Any) -> str:
    """Stable sha256 over any JSON-serialisable payload."""
    if isinstance(data, (bytes, bytearray)):
        raw = bytes(data)
    elif isinstance(data, str):
        raw = data.encode("utf-8")
    else:
        raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _short(s: str, n: int = 12) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:n]


def fact_id(subject: str, predicate: str, obj: str, source_id: str) -> str:
    return "fact_" + _short(f"{subject}|{predicate}|{obj}|{source_id}")


def evidence_id(source_id: str, location: str, snippet: str) -> str:
    return "ev_" + _short(f"{source_id}|{location}|{snippet}")


def relationship_id(subj: str, pred: str, obj: str) -> str:
    return "rel_" + _short(f"{subj}|{pred}|{obj}")


def conflict_id(subject: str, prop: str, a: str, b: str) -> str:
    key = "|".join(sorted([a, b]))  # order-independent
    return "cflt_" + _short(f"{subject}|{prop}|{key}")


def dependency_id(frm: str, edge: str, to: str) -> str:
    return "dep_" + _short(f"{frm}|{edge}|{to}")
