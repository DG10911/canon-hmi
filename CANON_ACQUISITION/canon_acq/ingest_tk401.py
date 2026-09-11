"""Ingest the existing TK-401 corpus into the acquisition datasets.

Reads the machine reality already in ../CANON_RESEARCH (the demo machine +
deterministic engine data) and the ../CANON HMI component registry, and lifts
every value into evidence-linked Facts, ontology Entities, Relationships,
Conflicts, Change events and Dependencies.

Provenance rule (sec 34, 45, 47): every fact records its source_id and a
source_location JSON-pointer into the origin file. No value is created without
a source. truthStatus in the source files is preserved verbatim (they are
CANON-authored PROPOSED data, not Schneider facts).
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone

from .enums import Confidence, KnowledgeState, TrustTier, ConflictStatus
from .ids import (content_hash, fact_id, evidence_id, relationship_id,
                  conflict_id, dependency_id)
from .models import (Source, Document, DocumentRevision, Entity, EntityAlias,
                     Fact, Evidence, Relationship, Conflict, Unknown,
                     Dependency, ChangeEvent, Embedding)
from .embeddings import embed
from .store import Corpus

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# The CANON-authored corpus files that constitute TK-401 machine reality.
MACHINE_ID = "mch_tk401_line"
FILES = {
    "machine":  ("SRC-TK401-MACHINE",      "CANON_RESEARCH/datasets/canon_demo_machine.json",      0),
    "cmds":     ("SRC-TK401-CMDCONTRACTS",  "CANON_RESEARCH/engine/canon_command_contracts.json",   0),
    "states":   ("SRC-TK401-STATEMODELS",   "CANON_RESEARCH/engine/canon_state_models.json",        0),
    "change":   ("SRC-TK401-CHANGERULES",   "CANON_RESEARCH/engine/canon_change_rules.json",        0),
    "compreg":  ("SRC-TK401-COMPREG",       "CANON_RESEARCH/engine/canon_component_registry.json",  1),
    "valrules": ("SRC-TK401-VALRULES",      "CANON_RESEARCH/engine/canon_validation_rules.json",    1),
    "protocol": ("SRC-TK401-PROTOCOLS",     "CANON_RESEARCH/engine/protocol_registry.json",         2),
}


class Tk401Ingestor:
    def __init__(self, corpus: Corpus, base_dir: str):
        self.c = corpus
        self.base = base_dir
        self.raw: dict[str, dict] = {}
        self.src_meta: dict[str, tuple[str, str, int]] = {}

    # ---- helpers -------------------------------------------------------
    def _load(self):
        for key, (sid, rel, tier) in FILES.items():
            path = os.path.join(self.base, rel)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            data = json.loads(text)
            self.raw[key] = data
            self.src_meta[key] = (sid, rel, tier)
            chash = content_hash(text)
            self.c.add("sources", Source(
                source_id=sid,
                title=data.get("$schema", os.path.basename(rel)),
                publisher="CANON (self-authored)",
                manufacturer=None,
                trust_tier=tier,
                access_type="INTERNAL",
                source_url=f"file://{rel}",
                canonical_url=f"file://{rel}",
                document_type="MACHINE_PROJECT" if tier == 0 else "ENGINE_DATA",
                product_family="TK-401 Transfer Line",
                product_model=MACHINE_ID,
                revision=data.get("revision", {}).get("revisionId") if isinstance(data.get("revision"), dict) else "n/a",
                publication_date=data.get("generated"),
                license="CANON-authored — PROPOSED; freely usable within CANON",
                retrieval_timestamp=NOW,
                content_hash=chash,
                mime_type="application/json",
                file_size=len(text.encode("utf-8")),
                parser="json.stdlib",
                parser_version="1.0",
                status="VERIFIED",
            ))
            doc_id = f"DOC-{sid}"
            self.c.add("documents", Document(
                document_id=doc_id, source_id=sid,
                title=os.path.basename(rel), document_type="JSON",
                content_hash=chash, mime_type="application/json",
                file_path=rel, classification="STRUCTURED", status="PROCESSED",
            ))
            rev = data.get("revision")
            if isinstance(rev, dict):
                self.c.add("document_revisions", DocumentRevision(
                    revision_id=rev.get("revisionId", "rev-?"),
                    document_id=doc_id,
                    content_hash=rev.get("contentHash", chash),
                    note=rev.get("note"), created_at=rev.get("createdAt"),
                ))

    def _fact(self, subject, predicate, obj, src_key, location, evidence_text,
              value=None, unit=None, tier=None, confidence=None, state=KnowledgeState.KNOWN,
              revision=None):
        sid, rel, default_tier = self.src_meta[src_key]
        tier = default_tier if tier is None else tier
        conf = confidence or (Confidence.AUTHORITATIVE if tier == 0 else
                              Confidence.OFFICIAL if tier <= 2 else Confidence.REPORTED)
        loc = f"{rel}#{location}"
        fid = fact_id(subject, predicate, str(obj), sid)
        eid = evidence_id(sid, loc, evidence_text)
        self.c.add("facts", Fact(
            fact_id=fid, subject=subject, predicate=predicate, object=str(obj),
            value=value, unit=unit, source_id=sid, source_location=loc,
            evidence_text=evidence_text, evidence_id=eid,
            confidence=conf.value, trust_tier=tier, knowledge_state=state.value,
            created_at=NOW, revision=revision,
        ))
        self.c.add("evidence", Evidence(
            evidence_id=eid, fact_id=fid, source_id=sid, source_location=loc,
            evidence_text=evidence_text, trust_tier=tier,
        ))
        return fid

    def _entity(self, entity_id, kind, name, attributes=None, parent=None, truth="PROPOSED"):
        self.c.add("entities", Entity(
            entity_id=entity_id, kind=kind, name=name, machine_id=MACHINE_ID,
            parent=parent, knowledge_state=KnowledgeState.KNOWN.value,
            truth_status=truth, attributes=attributes or {},
        ))

    def _rel(self, subj, pred, obj, src_key=None, evidence_id_=None, state=KnowledgeState.KNOWN):
        self.c.add("relationships", Relationship(
            relationship_id=relationship_id(subj, pred, obj),
            subject=subj, predicate=pred, object=obj,
            source_id=self.src_meta[src_key][0] if src_key else None,
            evidence_id=evidence_id_, knowledge_state=state.value,
        ))

    def _dep(self, frm, edge, to, rev=None):
        self.c.add("dependencies", Dependency(
            dependency_id=dependency_id(frm, edge, to),
            from_entity=frm, edge_type=edge, to_entity=to, revision_id=rev,
        ))

    # ---- section ingestors --------------------------------------------
    def run(self):
        self._load()
        m = self.raw["machine"]
        self._machine_identity(m)
        self._controller(m)
        self._assets(m)
        self._signals_io(m)
        self._commands()
        self._interlocks(m)
        self._alarms(m)
        self._states()
        self._sequences()
        self._process_relationships()
        self._protocols()
        self._hmi_components()
        self._change_and_conflict()
        self._reference_integrity(m)
        self._embeddings()

    def _machine_identity(self, m):
        self._entity(MACHINE_ID, "MACHINE", m["name"], attributes={
            "site": m.get("site"), "area": m.get("area"),
            "description": m.get("description"),
        })
        self._fact(MACHINE_ID, "name", m["name"], "machine", "/name", f'machine name = {m["name"]}',
                   state=KnowledgeState.KNOWN)
        self._fact(MACHINE_ID, "site", m.get("site"), "machine", "/site", f'site = {m.get("site")}')
        self._fact(MACHINE_ID, "area", m.get("area"), "machine", "/area", f'area = {m.get("area")}')

    def _controller(self, m):
        ctl = m["controller"]
        cid = ctl["controllerId"]
        self._entity(cid, "CONTROLLER", "TK-401 Controller", attributes={
            "family": ctl.get("family"), "protocols": ctl.get("protocols"),
            "scanTimeMs": ctl.get("scanTimeMs"), "truthStatus": ctl.get("truthStatus"),
        }, parent=MACHINE_ID)
        self.c.add("controllers", {"controllerId": cid, "family": ctl.get("family"),
                                   "protocols": ctl.get("protocols"),
                                   "opcuaNamespace": ctl.get("opcuaNamespace"),
                                   "opcuaPort": ctl.get("opcuaPort"), "modbusPort": ctl.get("modbusPort"),
                                   "scanTimeMs": ctl.get("scanTimeMs"), "machine": MACHINE_ID,
                                   "truthStatus": ctl.get("truthStatus"),
                                   "source": "SRC-TK401-MACHINE"})
        self._rel(MACHINE_ID, "USES_CONTROLLER", cid, "machine")
        self._fact(cid, "family", ctl.get("family"), "machine", "/controller/family",
                   f'controller family (reference-level) = {ctl.get("family")}')
        self._fact(cid, "opcua_namespace", ctl.get("opcuaNamespace"), "machine",
                   "/controller/opcuaNamespace", f'OPC UA namespace = {ctl.get("opcuaNamespace")}')
        for p in ctl.get("protocols", []):
            pid = self._protocol_id(p)   # map descriptive string -> registry id
            self._rel(cid, "USES_PROTOCOL", pid, "machine")
            self._fact(cid, "uses_protocol", pid, "machine", "/controller/protocols",
                       f'controller declares protocol "{p}" (registry id {pid})')

    @staticmethod
    def _protocol_id(descriptor: str) -> str:
        d = descriptor.lower()
        if "opc" in d:
            return "opcua"
        if "modbus" in d:
            return "modbus_tcp"
        return descriptor

    def _assets(self, m):
        for a in m["assets"]:
            aid = a["assetId"]
            kind = {"tank": "ASSET", "pump": "MOTOR", "valve": "VALVE"}.get(a["type"], "ASSET")
            self._entity(aid, kind, a["name"], attributes=a, parent=MACHINE_ID,
                         truth=a.get("truthStatus", "PROPOSED"))
            self._rel(MACHINE_ID, "CONTAINS", aid, "machine")
            self._fact(aid, "type", a["type"], "machine", f"/assets[{aid}]/type",
                       f'{aid} is a {a["type"]}')
            # domain-specific datasets
            if a["type"] == "tank":
                self.c.add("assets", {"asset_id": aid, "type": "tank", "name": a["name"],
                                      "capacityLiters": a.get("capacityLiters"),
                                      "geometry": a.get("geometry"), "machine": MACHINE_ID,
                                      "truth_status": a.get("truthStatus")})
            elif a["type"] == "pump":
                self.c.add("motors", {"asset_id": aid, "name": a["name"],
                                      "driveType": a.get("driveType"),
                                      "ratedFlowM3h": a.get("ratedFlowM3h"),
                                      "machine": MACHINE_ID, "truth_status": a.get("truthStatus")})
                self.c.add("assets", {"asset_id": aid, "type": "pump", "name": a["name"], "machine": MACHINE_ID})
            elif a["type"] == "valve":
                self.c.add("valves", {"asset_id": aid, "name": a["name"],
                                      "valveType": a.get("valveType"), "machine": MACHINE_ID,
                                      "truth_status": a.get("truthStatus")})
                self.c.add("assets", {"asset_id": aid, "type": "valve", "name": a["name"], "machine": MACHINE_ID})

    def _signals_io(self, m):
        io_by_signal = {row["signalId"]: row for row in m.get("io", [])}
        for s in m["signals"]:
            sig = s["signalId"]
            self._entity(sig, "SIGNAL", s.get("description", sig), attributes=s,
                         parent=s.get("asset"), truth=s.get("truthStatus", "PROPOSED"))
            self.c.add("signals", {**s, "machine": MACHINE_ID})
            if s.get("asset"):
                self._rel(s["asset"], "HAS_STATE" if s["kind"].startswith("discrete") else "MEASURES", sig, "machine")
            # engineering-range fact (this is the hero fact from spec section 33)
            if "engMin" in s and s.get("engMax") is not None:
                self._fact(sig, "engineering_range",
                           f'{s["engMin"]}-{s["engMax"]} {s.get("engUnit","")}'.strip(),
                           "machine", f"/signals[{sig}]/engMax",
                           f'{sig} PLC scaling configures engineering range '
                           f'{s["engMin"]}-{s["engMax"]} {s.get("engUnit","")}',
                           value=[s["engMin"], s["engMax"]], unit=s.get("engUnit"),
                           revision=m.get("revision", {}).get("revisionId"))
            # instrument dataset for transmitters
            if s.get("kind") == "analog-in":
                self.c.add("instruments", {"tag": sig, "asset": s.get("asset"),
                                           "unit": s.get("engUnit"), "range": [s.get("engMin"), s.get("engMax")],
                                           "hh": s.get("hh"), "h": s.get("h"), "l": s.get("l"), "ll": s.get("ll"),
                                           "description": s.get("description"), "source": "SRC-TK401-MACHINE",
                                           "machine": MACHINE_ID})
            # io point
            io = io_by_signal.get(sig)
            if io:
                self.c.add("io", {**io, "signalId": sig, "machine": MACHINE_ID, "source": "SRC-TK401-MACHINE"})
                self._fact(sig, "modbus_address", f'{io["area"]}:{io["address"]}', "machine",
                           f"/io[{sig}]/address",
                           f'{sig} mapped to Modbus {io["area"]} @ {io["address"]} '
                           f'(dtype {io.get("dtype")}, scale {io.get("scale")})',
                           value=io.get("address"))

    def _commands(self):
        contracts = self.raw["cmds"]["contracts"]
        for ct in contracts:
            cmd = ct["command"]
            self._entity(cmd, "COMMAND", cmd, attributes=ct, parent=ct["target"])
            self.c.add("commands", {"command_id": cmd, "target_asset": ct["target"],
                                    "request_signal": ct.get("request"),
                                    "feedback_signal": ct.get("feedback"),
                                    "authority": ct.get("role"), "timeoutSec": ct.get("timeoutSec"),
                                    "source": "SRC-TK401-CMDCONTRACTS", "truth_status": ct.get("truthStatus"),
                                    "machine": MACHINE_ID})
            self._rel(ct["target"], "HAS_COMMAND", cmd, "cmds")
            self._fact(cmd, "target_asset", ct["target"], "cmds",
                       f"/contracts[{cmd}]/target", f'{cmd} targets {ct["target"]}')
            self._fact(cmd, "request_signal", ct.get("request"), "cmds",
                       f"/contracts[{cmd}]/request",
                       f'{cmd} request coil = {ct.get("request")}; feedback = {ct.get("feedback")}')
            # permissives
            for i, p in enumerate(ct.get("permissives", [])):
                pid = f"PERM_{cmd}_{i}"
                self.c.add("permissives", {"permissive_id": pid, "command": cmd,
                                           "signal": p["signal"], "expected": p["expected"],
                                           "rejectCode": p.get("rejectCode"), "message": p.get("message"),
                                           "source": "SRC-TK401-CMDCONTRACTS", "machine": MACHINE_ID})
                self._rel(cmd, "HAS_PERMISSIVE", pid, "cmds")
                self._rel(cmd, "REQUIRES", p["signal"], "cmds")
                self._fact(cmd, "permissive", f'{p["signal"]} {p["expected"]}', "cmds",
                           f"/contracts[{cmd}]/permissives[{i}]",
                           f'{cmd} requires {p["signal"]} expected {p["expected"]} '
                           f'(reject {p.get("rejectCode")})')
            # interlocks (from contract)
            for i, il in enumerate(ct.get("interlocks", [])):
                iid = f"IL_{cmd}_{i}"
                self.c.add("interlocks", {"interlock_id": iid, "command": cmd,
                                          "signal": il["signal"], "expected": il["expected"],
                                          "rejectCode": il.get("rejectCode"), "message": il.get("message"),
                                          "type": "command-gate", "source": "SRC-TK401-CMDCONTRACTS",
                                          "machine": MACHINE_ID})
                self._rel(cmd, "HAS_INTERLOCK", iid, "cmds")
                self._rel(cmd, "BLOCKED_BY", il["signal"], "cmds")

    def _interlocks(self, m):
        for il in m.get("interlocks", []):
            iid = il["interlockId"]
            self.c.add("interlocks", {"interlock_id": iid, "signal": il["signal"],
                                      "appliesTo": il.get("appliesTo"), "type": il.get("type"),
                                      "onFail": il.get("onFail"), "source": "SRC-TK401-MACHINE",
                                      "machine": MACHINE_ID, "truth_status": il.get("truthStatus")})
            self._entity(iid, "INTERLOCK", f'{il["appliesTo"]} {il["type"]} interlock',
                         attributes=il, parent=il.get("appliesTo"))
            self._rel(il["appliesTo"], "PROTECTED_BY", iid, "machine")
            self._fact(iid, "on_fail", il.get("onFail"), "machine",
                       f"/interlocks[{iid}]/onFail",
                       f'{iid}: on {il["signal"]} fail -> {il.get("onFail")}')

    def _alarms(self, m):
        for al in m.get("alarms", []):
            aid = al["alarmId"]
            self.c.add("alarms", {"alarm_id": aid, "signal": al["signal"],
                                  "condition": al["condition"], "priority": al["priority"],
                                  "class": al.get("class"), "message": al.get("message"),
                                  "source": "SRC-TK401-MACHINE", "machine": MACHINE_ID,
                                  "truth_status": al.get("truthStatus")})
            self._entity(aid, "ALARM", al.get("message", aid), attributes=al, parent=al.get("signal"))
            self._rel(al["signal"], "HAS_ALARM", aid, "machine")
            self._fact(aid, "trigger", al["condition"], "machine",
                       f"/alarms[{aid}]/condition",
                       f'{aid} triggers when {al["signal"]} {al["condition"]} '
                       f'(priority {al["priority"]})', value=al["condition"])

    def _states(self):
        models = self.raw["states"]["deviceModels"]
        pk = self.raw["states"].get("packmlReference", {})
        for dev, model in models.items():
            for st in model["states"]:
                sid = f"STATE_{dev}_{st}"
                packml = model.get("packmlMapping", {}).get(st)
                self.c.add("states", {"state_id": sid, "device": dev, "state": st,
                                      "packmlMapping": packml, "source": "SRC-TK401-STATEMODELS",
                                      "machine": MACHINE_ID})
                self._entity(sid, "STATE", f'{dev}:{st}', attributes={"packml": packml})
                if packml and packml != st:
                    self._fact(sid, "packml_mapping", packml, "states",
                               f"/deviceModels/{dev}/packmlMapping/{st}",
                               f'{dev} CANON state "{st}" maps to PackML "{packml}" '
                               f'(official producing state name is "Execute", OPC 30050)')
            for i, tr in enumerate(model.get("transitions", [])):
                self.c.add("sequences", {"sequence_id": f"TRANS_{dev}_{i}", "kind": "transition",
                                         "device": dev, "from": tr["from"], "event": tr["event"],
                                         "to": tr["to"], "emit": tr.get("emit"),
                                         "source": "SRC-TK401-STATEMODELS", "machine": MACHINE_ID})
        # modes derived from the analog/discrete auto/manual/local/remote vocabulary present in spec 15
        for mode in ["AUTO", "MANUAL", "LOCAL", "REMOTE"]:
            self.c.add("modes", {"mode_id": f"MODE_{mode}", "mode": mode,
                                 "knowledge_state": KnowledgeState.INFERRED.value,
                                 "note": "Standard operator mode vocabulary; not asserted present in TK-401 project unless bound to a signal.",
                                 "machine": MACHINE_ID})

    def _sequences(self):
        # Derive the P401 start sequence from its command contract (evidence-backed).
        start = next(c for c in self.raw["cmds"]["contracts"] if c["command"] == "P401_START")
        steps = [f'{p["signal"]} {p["expected"]}' for p in start.get("permissives", [])]
        steps += [f'{il["signal"]} {il["expected"]}' for il in start.get("interlocks", [])]
        self.c.add("sequences", {"sequence_id": "SEQ_P401_START", "kind": "command-sequence",
                                 "device": "P401",
                                 "steps": steps + [f'set {start["request"]}', f'await {start["feedback"]}'],
                                 "timeoutSec": start.get("timeoutSec"),
                                 "source": "SRC-TK401-CMDCONTRACTS", "machine": MACHINE_ID,
                                 "knowledge_state": KnowledgeState.KNOWN.value})

    def _process_relationships(self):
        # Explicit process topology (evidence: machine description + IO direction).
        edges = [("TK-401", "FEEDS", "P401"), ("P401", "PUMPS", "XV401"),
                 ("LT401", "MEASURES", "TK-401"), ("PT401", "MEASURES", "P401"),
                 ("P401_START", "STARTS", "P401"), ("XV401_OPEN", "OPENS", "XV401")]
        for subj, pred, obj in edges:
            self.c.add("process_relationships", {"subject": subj, "predicate": pred,
                                                 "object": obj, "source": "SRC-TK401-MACHINE",
                                                 "machine": MACHINE_ID})
            self._rel(subj, pred, obj, "machine")

    def _protocols(self):
        for p in self.raw["protocol"]["protocols"]:
            self.c.add("protocols", {**p, "source": "SRC-TK401-PROTOCOLS"})
            self._entity(p["id"], "PROTOCOL", p["name"], attributes=p)
            if p.get("status") == "VERIFIED":
                self._fact(p["id"], "standard", p.get("standard"), "protocol",
                           f"/protocols[{p['id']}]/standard",
                           f'{p["name"]} standard = {p.get("standard")}; access: {p.get("access","")}',
                           tier=int(TrustTier.OFFICIAL_STANDARDS), confidence=Confidence.OFFICIAL)

    def _hmi_components(self):
        for comp in self.raw["compreg"]["components"]:
            self.c.add("hmi_components", {"component": comp["component"], "category": comp["category"],
                                         "version": comp["version"], "states": comp.get("states"),
                                         "commands": comp.get("commands"),
                                         "extractableFromSchneider": comp.get("extractableFromSchneider"),
                                         "source": "SRC-TK401-COMPREG"})
            self._entity(f'CMP_{comp["component"]}', "FACEPLATE", comp["component"],
                         attributes={"category": comp["category"], "version": comp["version"]})
        # A single primary asset screen exists in the CANON app (index.html); record it.
        self.c.add("hmi_screens", {"screen_id": "SCR_TK401_OVERVIEW", "purpose": "TK-401 line overview + P401 control",
                                   "asset_scope": [MACHINE_ID], "operator_role": "operator",
                                   "visible_assets": ["TK-401", "P401", "XV401"],
                                   "commands": ["P401_START", "P401_STOP", "XV401_OPEN", "XV401_CLOSE"],
                                   "source": "SRC-TK401-COMPREG",
                                   "knowledge_state": KnowledgeState.INFERRED.value,
                                   "note": "Derived from the CANON demo HMI; structure inferred, not exported from a Schneider HMI project."})

    def _change_and_conflict(self):
        hero = self.raw["change"]["heroChangeScenario"]
        # change events + dependency edges
        for imp in hero["impact"]:
            self.c.add("change_history", ChangeEvent(
                change_id=f'CHG_{hero["changedEntity"]}_{imp["entity"]}'.replace(":", "_").replace("#", "_"),
                change_type="CHANGED_FACT", entity=hero["changedEntity"],
                field=hero.get("field"), from_value=hero.get("from"), to_value=hero.get("to"),
                from_revision=hero["resultRevision"]["from"], to_revision=hero["resultRevision"]["to"],
                action=imp.get("action"),
                review_required=imp.get("truthStatus") == "review-required",
            ))
            self._dep(hero["changedEntity"], imp["edge"], imp["entity"],
                      rev=hero["resultRevision"]["from"])
        # THE conflict: baseline PT401 range (0-10, rev-17) vs proposed change (0-16, rev-18)
        self.c.add("conflicts", Conflict(
            conflict_id=conflict_id("PT401", "engineering_range", "0-10 bar", "0-16 bar"),
            subject="PT401", property="engineering_range",
            value_a="0-10 bar", source_a="SRC-TK401-MACHINE",
            value_b="0-16 bar", source_b="SRC-TK401-CHANGERULES",
            source_trust_a=0, source_trust_b=0,
            revision_a="rev-17", revision_b="rev-18",
            resolution_status=ConflictStatus.RESOLVED_REVISION.value,
            resolution_note="Not a contradiction: rev-18 supersedes rev-17 via an approved change "
                            "(PT401 engMax 10->16). Alarm ALM_PT401_HH HH=9.0 re-rationalization is "
                            "review-required before the new revision is authoritative.",
        ))

    def _reference_integrity(self, m):
        ri = m.get("referenceIntegrity", {})
        if ri.get("reviewRequired", 0):
            self.c.add("unknowns", Unknown(
                unknown_id="UNK_PT401_ALARM_RERATIONALIZE",
                kind="reference-integrity", subject="ALM_PT401_HH",
                reason=ri.get("note", "reference requires engineer review"),
                review_required=True,
            ))

    def _embeddings(self):
        # Placeholder vectors over facts + entities (explicitly non-semantic).
        for f in self.c.data["facts"]:
            text = f'{f["subject"]} {f["predicate"]} {f["object"]}'
            self.c.add("embeddings", Embedding(
                embedding_id=f'EMB_{f["fact_id"]}', ref_kind="fact", ref_id=f["fact_id"],
                text=text, vector=embed(text), dim=len(embed(text)),
                trust_tier=f.get("trust_tier"), machine=MACHINE_ID,
            ))


def ingest(corpus: Corpus, base_dir: str):
    Tk401Ingestor(corpus, base_dir).run()
