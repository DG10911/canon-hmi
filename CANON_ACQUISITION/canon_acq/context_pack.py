"""CANON Context Pack builder (spec section 40, 64).

Assembles the per-machine context model from the populated corpus: the object
CANON reasoning + HMI synthesis consume. Every binding stays traceable to a
fact -> evidence -> source (sec 71).
"""
from __future__ import annotations
from datetime import datetime, timezone

from .store import Corpus

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_context_pack(corpus: Corpus, machine_id: str) -> dict:
    d = corpus.data

    def for_machine(rows):
        return [r for r in rows if r.get("machine") == machine_id
                or r.get("machine_id") == machine_id]

    machine_ent = next((e for e in d["entities"]
                        if e["kind"] == "MACHINE" and e["entity_id"] == machine_id), None)
    controllers = [e for e in d["entities"] if e["kind"] == "CONTROLLER"]

    pack = {
        "$schema": "canon.context_pack.v1",
        "generated": NOW,
        "machine_id": machine_id,
        "provenance_rule": "Every binding is traceable HMI->requirement->entity->signal->fact->evidence->source->revision->authority (sec 71).",
        "machine_identity": machine_ent["attributes"] if machine_ent else {},
        "plant_hierarchy": {
            "machine": machine_id,
            "assets": [a["entity_id"] for a in d["entities"] if a["kind"] in ("ASSET", "MOTOR", "VALVE") and a.get("machine_id") == machine_id],
        },
        "controller_topology": [{"id": c["entity_id"], "attrs": c["attributes"]} for c in controllers],
        "io_topology": for_machine(d["io"]),
        "signal_dictionary": for_machine(d["signals"]),
        "asset_model": for_machine(d["assets"]),
        "instrumentation_model": for_machine(d["instruments"]),
        "command_model": for_machine(d["commands"]),
        "permissive_model": for_machine(d["permissives"]),
        "interlock_model": for_machine(d["interlocks"]),
        "alarm_model": for_machine(d["alarms"]),
        "state_model": for_machine(d["states"]),
        "mode_model": for_machine(d["modes"]),
        "sequence_model": for_machine(d["sequences"]),
        "process_model": for_machine(d["process_relationships"]),
        "hmi_model": {
            "components_available": [c["component"] for c in d["hmi_components"]],
            "screens": for_machine(d["hmi_screens"]),
        },
        "protocol_model": [p for p in d["protocols"]],
        "standards_model": [s["standard_id"] for s in d["standards"]],
        "document_model": [{"source_id": s["source_id"], "title": s["title"], "trust_tier": s["trust_tier"]}
                           for s in d["sources"]],
        "evidence_model": {"facts": len(d["facts"]), "evidence": len(d["evidence"])},
        "revision_model": for_machine(d["change_history"]) or d["change_history"],
        "conflict_model": d["conflicts"],
        "uncertainty_model": {
            "unknowns": d["unknowns"],
            "inferred_relationships": [r for r in d["relationships"] if r.get("knowledge_state") == "INFERRED"],
        },
        "coverage": corpus.coverage,
        "hmi_readiness": corpus.readiness,
    }
    corpus.add("context_packs", pack)
    return pack
