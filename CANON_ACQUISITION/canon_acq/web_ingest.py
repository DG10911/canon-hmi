"""Ingest the web-verified seed registry into the corpus.

Turns each real discovered source into: an 01_sources row, a 02_documents row,
a DOCUMENT entity, and — for standards bodies (26/27) — a 27_standards row, or
for Schneider product docs a 26_products row. Every derived fact points back to
the real URL as its evidence (sec 34, 43). No content is downloaded or
reproduced; only publicly-stated metadata (title/publisher/version) is lifted,
respecting the copyright note recorded on each source (sec 0, 26).
"""
from __future__ import annotations

from .discovery import load_seed_registry
from .ids import content_hash, fact_id, evidence_id, relationship_id
from .models import (Document, Entity, Fact, Evidence, Relationship)
from .store import Corpus

STANDARDS_PUBLISHERS = {"IEC", "ISA", "EEMUA", "OPC Foundation", "Modbus Organization",
                        "PLCopen", "AutomationML e.V.", "NAMUR", "IDTA"}


def ingest_web_sources(corpus: Corpus, seed_path: str) -> dict:
    sources = load_seed_registry(seed_path)
    counts = {"sources": 0, "standards": 0, "products": 0, "documents": 0}
    for s in sources:
        corpus.add("sources", s)
        counts["sources"] += 1
        sid = s.source_id
        loc = s.source_url
        chash = content_hash(loc)  # hash of the URL (no content downloaded)

        doc_id = f"DOC-{sid}"
        corpus.add("documents", Document(
            document_id=doc_id, source_id=sid, title=s.title,
            document_type=s.document_type, content_hash=chash,
            mime_type="text/html", file_path=s.source_url,
            classification="EXTERNAL_METADATA", status="DISCOVERED",
        ))
        counts["documents"] += 1

        ent_id = f"DOCENT-{sid}"
        corpus.add("entities", Entity(
            entity_id=ent_id, kind="DOCUMENT", name=s.title,
            knowledge_state="KNOWN", truth_status="VERIFIED",
            attributes={"url": s.source_url, "publisher": s.publisher,
                        "trust_tier": s.trust_tier, "license": s.license},
        ))

        # title fact, evidenced by the live URL
        ev_text = f'Public page at {s.source_url} — title "{s.title}", publisher {s.publisher}.'
        fid = fact_id(ent_id, "title", s.title, sid)
        eid = evidence_id(sid, loc, ev_text)
        corpus.add("facts", Fact(
            fact_id=fid, subject=ent_id, predicate="title", object=s.title,
            source_id=sid, source_location=loc, evidence_text=ev_text,
            evidence_id=eid, confidence="OFFICIAL", trust_tier=s.trust_tier,
            knowledge_state="KNOWN", extraction_method="web-metadata",
        ))
        corpus.add("evidence", Evidence(
            evidence_id=eid, fact_id=fid, source_id=sid, source_location=loc,
            evidence_text=ev_text, trust_tier=s.trust_tier,
            extraction_method="web-verified",
        ))

        # standards vs products classification
        if s.publisher in STANDARDS_PUBLISHERS and s.trust_tier == 2:
            corpus.add("standards", {
                "standard_id": sid, "title": s.title, "version": s.version,
                "publisher": s.publisher, "source_url": s.source_url,
                "access_status": s.license, "trust_tier": s.trust_tier,
            })
            counts["standards"] += 1
        elif s.manufacturer == "Schneider Electric" and s.trust_tier == 1:
            corpus.add("products", {
                "manufacturer": s.manufacturer, "family": s.product_family,
                "model": s.product_model, "document_type": s.document_type,
                "documentation": s.source_url, "revision": s.revision,
                "official_source": sid,
                # capability is UNKNOWN until parsed from the doc body (sec 22)
                "capability_status": "UNKNOWN",
                "note": "Metadata only; product capabilities not asserted until the document body is parsed (sec 22/62).",
            })
            counts["products"] += 1

        # link the document entity to its publisher as a vendor/standard body
        corpus.add("relationships", Relationship(
            relationship_id=relationship_id(ent_id, "DOCUMENTED_BY", sid),
            subject=ent_id, predicate="DOCUMENTED_BY", object=sid,
            source_id=sid, evidence_id=eid, knowledge_state="KNOWN",
        ))
    return counts
