"""Source discovery — query-family generation (sec 31) + discovery loop (sec 60).

The query generator is deterministic and offline: it produces the query
families a live discovery worker would issue to a search API. Actual web
acquisition is handled out-of-band (see sources/source_registry.seed.json,
produced by a real web-verified discovery pass) so that this module never
fabricates URLs (sec 67).
"""
from __future__ import annotations
import json
import os
from typing import Iterable

from .enums import SourceStatus
from .models import Source

# Section 3 — Schneider corpus scope.
SCHNEIDER_CONTROLLERS = ["M580", "M340", "M221", "M241", "M251", "M262", "M258", "Premium", "Quantum"]
SCHNEIDER_SOFTWARE = [
    "Control Expert", "Machine Expert", "Automation Expert",
    "Operator Terminal Expert", "Machine SCADA Expert", "OPC UA Server Expert",
]
SCHNEIDER_HARDWARE = ["Harmony HMI", "Altivar", "TeSys", "Modicon I/O"]

# Section 4 — document types to discover.
DOC_TYPES = [
    "programming guide", "hardware manual", "reference manual",
    "installation manual", "communication guide", "OPC UA", "Modbus",
    "datasheet", "user guide", "release notes", "migration guide",
    "cybersecurity guide",
]

# Section 26 — standards to discover (abstracts only; paid standards not reproduced).
STANDARDS = [
    "IEC 61131-3", "IEC 62541 OPC UA", "ISA-101 HMI", "ISA-18.2 alarm management",
    "IEC 62682", "ISA-95", "ISA-88", "IEC 62443", "PackML OPC 30050",
    "AutomationML", "Asset Administration Shell", "NAMUR NE", "EEMUA 191",
]


def query_families(machine_hint: str | None = None) -> list[dict]:
    """Generate the query families a discovery worker would run (section 31)."""
    families: list[dict] = []

    def add(domain, product, queries):
        families.append({"domain": domain, "product": product, "queries": queries})

    for c in SCHNEIDER_CONTROLLERS:
        add("schneider.controller", c, [
            f"Schneider Electric {c} {dt}" for dt in DOC_TYPES
        ])
    for s in SCHNEIDER_SOFTWARE:
        add("schneider.software", s, [
            f"Schneider Electric {s} user guide",
            f"Schneider Electric {s} XML export",
            f"Schneider Electric {s} variables",
        ])
    for h in SCHNEIDER_HARDWARE:
        add("schneider.hardware", h, [
            f"Schneider Electric {h} programming guide",
            f"Schneider Electric {h} communication",
            f"Schneider Electric {h} datasheet",
        ])
    for st in STANDARDS:
        add("standards", st, [f"{st} specification", f"{st} overview public"])

    # Protocol families (sections 23-25).
    add("protocol", "OPC UA", [
        "OPC UA specification reference opcfoundation.org",
        "OPC UA NodeSet companion specification",
        "OPC 30050 PackML companion specification",
    ])
    add("protocol", "Modbus", [
        "Modbus application protocol specification modbus.org",
        "Modbus messaging TCP implementation guide",
    ])

    if machine_hint:
        add("machine-specific", machine_hint, [
            f"{machine_hint} programming guide",
            f"{machine_hint} OPC UA namespace",
            f"{machine_hint} Modbus register map",
        ])
    return families


def total_queries(families: Iterable[dict]) -> int:
    return sum(len(f["queries"]) for f in families)


def load_seed_registry(path: str) -> list[Source]:
    """Load the web-verified seed registry into Source records (no fabrication).

    Only entries carrying a real ``source_url`` are ingested; the loader never
    invents a URL. Returns [] if the seed file is absent (discovery not yet run).
    """
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    out: list[Source] = []
    for row in payload.get("sources", []):
        if not row.get("source_url"):
            continue
        status = row.get("status", "DISCOVERED")
        if status == "VERIFIED":
            status = SourceStatus.VERIFIED.value
        elif status not in {s.value for s in SourceStatus}:
            status = SourceStatus.ACQUIRED.value
        out.append(Source(
            source_id=row["source_id"],
            title=row.get("title", row["source_id"]),
            publisher=row.get("publisher", "UNKNOWN"),
            trust_tier=int(row.get("trust_tier", 2)),
            access_type=row.get("access_type", "PUBLIC"),
            source_url=row.get("source_url"),
            canonical_url=row.get("canonical_url"),
            manufacturer=row.get("manufacturer"),
            document_type=row.get("document_type"),
            product_family=row.get("product_family"),
            product_model=row.get("product_model"),
            version=row.get("version"),
            revision=row.get("revision"),
            publication_date=row.get("publication_date"),
            language=row.get("language", "en"),
            region=row.get("region"),
            license=row.get("license"),
            retrieval_timestamp=row.get("retrieval_timestamp"),
            status=status,
        ))
    return out
