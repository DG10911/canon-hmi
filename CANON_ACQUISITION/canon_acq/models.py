"""Corpus data models (spec sections 32-39, 57).

Implemented as stdlib dataclasses so the P0 pipeline runs with zero external
deps. Each dataclass maps 1:1 to a Postgres table in db/schema.sql and to a
Pydantic model in a production build. Field names follow the spec schemas.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


def _clean(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


class Record:
    def to_dict(self) -> dict:
        return _clean(asdict(self))


# --- 01 sources / 02 documents / 03 revisions (section 32, 58, 59) ---
@dataclass
class Source(Record):
    source_id: str
    title: str
    publisher: str
    trust_tier: int
    access_type: str = "PUBLIC"
    source_url: Optional[str] = None
    canonical_url: Optional[str] = None
    manufacturer: Optional[str] = None
    document_type: Optional[str] = None
    product_family: Optional[str] = None
    product_model: Optional[str] = None
    version: Optional[str] = None
    revision: Optional[str] = None
    publication_date: Optional[str] = None
    last_updated: Optional[str] = None
    language: Optional[str] = "en"
    region: Optional[str] = None
    license: Optional[str] = None
    retrieval_timestamp: Optional[str] = None
    content_hash: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    parser: Optional[str] = None
    parser_version: Optional[str] = None
    status: str = "DISCOVERED"


@dataclass
class Document(Record):
    document_id: str
    source_id: str
    title: str
    document_type: Optional[str] = None
    content_hash: Optional[str] = None
    mime_type: Optional[str] = None
    page_count: Optional[int] = None
    file_path: Optional[str] = None
    classification: Optional[str] = None    # section 49 classification result
    status: str = "PROCESSED"


@dataclass
class DocumentRevision(Record):
    revision_id: str
    document_id: str
    content_hash: str
    supersedes: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[str] = None


# --- 04 entities / 05 aliases (section 37, 38) ---
@dataclass
class Entity(Record):
    entity_id: str          # canonical id
    kind: str               # one of ENTITY_KINDS
    name: str
    machine_id: Optional[str] = None
    parent: Optional[str] = None
    knowledge_state: str = "KNOWN"
    truth_status: str = "PROPOSED"
    attributes: dict = field(default_factory=dict)


@dataclass
class EntityAlias(Record):
    entity_id: str
    alias: str
    resolution_status: str = "RESOLVED"
    confidence: str = "OFFICIAL"
    evidence_id: Optional[str] = None


# --- 29 facts / 31 evidence (section 33, 34) ---
@dataclass
class Fact(Record):
    fact_id: str
    subject: str
    predicate: str
    object: str
    source_id: str
    value: Optional[Any] = None
    unit: Optional[str] = None
    source_location: Optional[str] = None
    page: Optional[Any] = None
    section: Optional[str] = None
    table: Optional[str] = None
    paragraph: Optional[str] = None
    evidence_text: Optional[str] = None
    evidence_id: Optional[str] = None
    confidence: str = "OFFICIAL"
    trust_tier: int = 1
    knowledge_state: str = "KNOWN"
    extraction_method: str = "structured-ingest"
    created_at: Optional[str] = None
    revision: Optional[str] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None


@dataclass
class Evidence(Record):
    evidence_id: str
    fact_id: str
    source_id: str
    source_location: str
    evidence_text: str
    trust_tier: int
    extraction_method: str = "structured-ingest"


# --- 30 relationships (section 39) ---
@dataclass
class Relationship(Record):
    relationship_id: str
    subject: str
    predicate: str
    object: str
    source_id: Optional[str] = None
    evidence_id: Optional[str] = None
    confidence: str = "OFFICIAL"
    knowledge_state: str = "KNOWN"


# --- 32 conflicts (section 35) ---
@dataclass
class Conflict(Record):
    conflict_id: str
    subject: str
    property: str
    value_a: Any
    source_a: str
    value_b: Any
    source_b: str
    source_trust_a: int
    source_trust_b: int
    revision_a: Optional[str] = None
    revision_b: Optional[str] = None
    resolution_status: str = "UNRESOLVED"
    resolution_note: Optional[str] = None


# --- 33 unknowns (section 50, 67) ---
@dataclass
class Unknown(Record):
    unknown_id: str
    kind: str                       # reference | file | capability | reference-integrity
    subject: str
    reason: str
    review_required: bool = True
    filename: Optional[str] = None
    mime: Optional[str] = None
    hash: Optional[str] = None
    size: Optional[int] = None
    detected_structure: Optional[str] = None
    possible_type: Optional[str] = None


# --- 34 dependencies / 35 change history (section 36, 61) ---
@dataclass
class Dependency(Record):
    dependency_id: str
    from_entity: str
    edge_type: str
    to_entity: str
    revision_id: Optional[str] = None


@dataclass
class ChangeEvent(Record):
    change_id: str
    change_type: str                # NEW_REVISION | CHANGED_FACT | NEW_SOURCE ...
    entity: str
    field: Optional[str] = None
    from_value: Any = None
    to_value: Any = None
    from_revision: Optional[str] = None
    to_revision: Optional[str] = None
    action: Optional[str] = None
    review_required: bool = False


# --- 37 embeddings (section 52) ---
@dataclass
class Embedding(Record):
    embedding_id: str
    ref_kind: str                   # document_chunk | fact | entity ...
    ref_id: str
    text: str
    vector: list
    dim: int
    method: str = "placeholder-hash"
    note: str = "NOT a semantic embedding; replace with an embedding model in production (section 52/67)."
    # metadata filters (section 52)
    vendor: Optional[str] = None
    product: Optional[str] = None
    trust_tier: Optional[int] = None
    machine: Optional[str] = None
