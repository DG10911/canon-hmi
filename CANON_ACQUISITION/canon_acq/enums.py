"""Controlled vocabularies for the acquisition corpus (spec sections 2, 38, 55)."""
from __future__ import annotations
from enum import Enum


class TrustTier(int, Enum):
    """Section 2 — Source Priority Hierarchy. Lower = more authoritative."""
    MACHINE_REALITY = 0          # live OPC UA / Modbus / PLC & HMI project exports
    OFFICIAL_VENDOR = 1          # Schneider official product docs
    OFFICIAL_STANDARDS = 2       # OPC Foundation, Modbus Org, IEC, ISO, ISA, NAMUR...
    AUTHORIZED_TECHNICAL = 3     # distributor tech docs, app notes, training
    SECONDARY = 4                # papers, university, conference
    COMMUNITY = 5                # forums, GitHub, StackOverflow, Reddit


class KnowledgeState(str, Enum):
    """Section 55 — No-hallucination policy. The only allowed epistemic states."""
    KNOWN = "KNOWN"
    SUPPORTED = "SUPPORTED"
    INFERRED = "INFERRED"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"
    CONFLICTED = "CONFLICTED"
    STALE = "STALE"


class Confidence(str, Enum):
    """Section 33 — fact confidence. NOT a substitute for evidence (section 43)."""
    AUTHORITATIVE = "AUTHORITATIVE"   # Tier 0 machine reality
    OFFICIAL = "OFFICIAL"             # Tier 1-2 vendor/standards
    REPORTED = "REPORTED"            # Tier 3-4
    COMMUNITY = "COMMUNITY"          # Tier 5
    UNVERIFIED = "UNVERIFIED"


class SourceStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    ACQUIRED = "ACQUIRED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ConflictStatus(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    RESOLVED_AUTHORITATIVE = "RESOLVED_AUTHORITATIVE"
    RESOLVED_REVISION = "RESOLVED_REVISION"
    RESOLVED_ENGINEER = "RESOLVED_ENGINEER"
    STALE_SOURCE = "STALE_SOURCE"


class ResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    CANDIDATE = "CANDIDATE"
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"


class HmiReadiness(str, Enum):
    READY = "READY"
    READY_WITH_REVIEW = "READY_WITH_REVIEW"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"


# Section 38 — engineering ontology entity kinds.
ENTITY_KINDS = [
    "PLANT", "AREA", "CELL", "MACHINE", "UNIT", "ASSET", "EQUIPMENT",
    "CONTROLLER", "MODULE", "IO", "SIGNAL", "INSTRUMENT", "MOTOR", "DRIVE",
    "VALVE", "ACTUATOR", "PROCESS_VARIABLE", "COMMAND", "STATE", "MODE",
    "ALARM", "EVENT", "PERMISSIVE", "INTERLOCK", "SEQUENCE", "SCREEN",
    "FACEPLATE", "PROCEDURE", "DOCUMENT", "STANDARD", "PROTOCOL", "PRODUCT",
    "VENDOR",
]

# Section 39 — relationship predicates.
RELATIONSHIP_PREDICATES = [
    "CONTAINS", "CONNECTED_TO", "MEASURES", "CONTROLS", "ACTUATES", "FEEDS",
    "PUMPS", "OPENS", "CLOSES", "STARTS", "STOPS", "REQUIRES", "BLOCKED_BY",
    "PROTECTED_BY", "HAS_ALARM", "HAS_STATE", "HAS_COMMAND", "HAS_PERMISSIVE",
    "HAS_INTERLOCK", "USES_PROTOCOL", "USES_CONTROLLER", "DISPLAYED_ON",
    "DOCUMENTED_BY", "DEFINED_BY", "SUPPORTED_BY", "DEPENDS_ON", "PRECEDES",
    "FOLLOWS", "PARENT_OF", "CHILD_OF",
]

# Section 57 — the 37 required output datasets, in order.
DATASETS = [
    "01_sources", "02_documents", "03_document_revisions", "04_entities",
    "05_entity_aliases", "06_signals", "07_io", "08_assets", "09_controllers",
    "10_modules", "11_instruments", "12_motors", "13_drives", "14_valves",
    "15_commands", "16_permissives", "17_interlocks", "18_alarms", "19_states",
    "20_modes", "21_sequences", "22_process_relationships", "23_hmi_screens",
    "24_hmi_components", "25_protocols", "26_products", "27_standards",
    "28_procedures", "29_facts", "30_relationships", "31_evidence",
    "32_conflicts", "33_unknowns", "34_dependencies", "35_change_history",
    "36_context_packs", "37_embeddings",
]

# Coverage dimensions (section 41).
COVERAGE_DIMENSIONS = [
    "MachineIdentity", "Controller", "IO", "Signal", "Asset", "Process",
    "Command", "Permissive", "Interlock", "Alarm", "State", "Sequence",
    "HMI", "Documentation", "Evidence", "Revision",
]
