"""CANON Platform — Part B: reference corpus grounding.

The acquisition pipeline (CANON_ACQUISITION) merged 23 real ICS / sensor datasets
(SWaT, NASA C-MAPSS turbofan, steel-plate faults, SCADA pipeline, motor telemetry,
Monash time-series…) into 939 OBSERVED signal series. This module folds that corpus
into the live platform as *reference grounding*:

  - it shows what real-world datasets back the platform, and
  - for a machine's signals it surfaces OBSERVED ranges from comparable real sensors.

Per spec §62 this is CANDIDATE / OBSERVED evidence ONLY — it is advisory, never written
into the canonical model and never treated as authoritative machine truth. Everything is
labelled OBSERVED · CANDIDATE · reference.

Data files live in seed/ (pulled from the acquisition corpus):
  reference_signals.jsonl · reference_sources.jsonl · reference_meta.json
"""
from __future__ import annotations
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = os.path.join(HERE, "seed")

# physical measure  ->  keyword tokens found in reference column names
KIND_TOKENS = {
    "pressure":    ("pressure", "psia", "dpit", "pit", "kpa", "bar"),
    "level":       ("level", "lit", "tank"),
    "flow":        ("flow", "fit", "gpm", "m3h"),
    "temperature": ("temp", "◦r", "[k]", "coolant", "winding", "stator", "tooth", "yoke", "thermo"),
    "speed":       ("speed", "rpm", "fan speed", "core speed", "motor_speed"),
    "current":     ("i_d", "i_q", "current", "amp", "amperage"),
    "torque":      ("torque", "nm"),
    "vibration":   ("vib", "accel"),
    "power":       ("power", "energy", "kw", "watt", "consumption"),
}


def measure_of(sig: dict):
    """Infer the physical quantity of a signal from its tag prefix, unit and description
    (the `kind` field is only the I/O class, e.g. analog-in). Returns None for signals
    with no analogue in the corpus (discretes, states, analyzers)."""
    sid = str(sig.get("signalId", "")).upper()
    unit = str(sig.get("engUnit") or "").lower()
    desc = str(sig.get("description") or "").lower()
    m = re.match(r"[A-Z]+", sid)
    pre = m.group(0) if m else ""
    if unit in ("bar", "kpa", "psi", "psia", "mbar", "pa") or pre in ("PT", "PIT", "DPT", "DPIT", "PI") or "pressure" in desc:
        return "pressure"
    if unit in ("°c", "c", "°f", "f", "k", "degc", "degf") or pre in ("TT", "TE", "TIT", "TI") or "temperature" in desc or "temp" in desc:
        return "temperature"
    if unit in ("rpm", "hz") or pre in ("ST", "SIT", "SE", "SI") or "speed" in desc:
        return "speed"
    if unit in ("m3/h", "m³/h", "gpm", "l/min", "lpm", "kg/h") or pre in ("FT", "FIT", "FI") or "flow" in desc:
        return "flow"
    if pre in ("LT", "LIT", "LI", "LSH", "LSL") or "level" in desc:
        return "level"
    if unit in ("a", "amp", "ma") or pre in ("IT", "II") or "current" in desc:
        return "current"
    if unit in ("kw", "w", "kwh", "mw") or "power" in desc or "energy" in desc:
        return "power"
    return None

_CACHE: dict | None = None


def _read_jsonl(path):
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def _clean_title(t: str) -> str:
    return re.sub(r"\.csv$", "", (t or "").strip(), flags=re.I) or t


def _load():
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    sigs = _read_jsonl(os.path.join(SEED, "reference_signals.jsonl"))
    srcs = _read_jsonl(os.path.join(SEED, "reference_sources.jsonl"))
    meta = {}
    mp = os.path.join(SEED, "reference_meta.json")
    if os.path.exists(mp):
        meta = json.load(open(mp, encoding="utf-8"))
    titles = {s.get("source_id"): _clean_title(s.get("title")) for s in srcs}
    for s in sigs:                       # pre-lowercase column for matching
        s["_col_l"] = str(s.get("column", "")).lower()
    _CACHE = {"signals": sigs, "sources": srcs, "titles": titles, "meta": meta}
    return _CACHE


def loaded() -> bool:
    return bool(_load()["signals"])


def stats() -> dict:
    d = _load()
    if not d["signals"]:
        return {"loaded": False,
                "howto": "Reference corpus not present. Pull it with: bash sync_reference.sh "
                         "(copies 939 OBSERVED signals from the acquisition corpus into seed/)."}
    from collections import Counter
    per = Counter(s.get("source") for s in d["signals"])
    top = [{"source": src, "title": d["titles"].get(src, src), "signals": n}
           for src, n in per.most_common()]
    return {"loaded": True, "datasets": len(per), "signals": len(d["signals"]),
            "policy": "OBSERVED · CANDIDATE · reference only (never authoritative, §62)",
            "sources": top,
            "highlights": [t for t in ("SWaT water-treatment", "NASA C-MAPSS turbofan",
                           "steel-plate faults", "SCADA pipeline", "motor telemetry") ],
            "dropped_low_quality": d["meta"].get("dropped_low_quality_sources"),
            "filter": d["meta"].get("filter")}


def _matches(kind: str):
    toks = KIND_TOKENS.get((kind or "").lower())
    if not toks:
        return []
    d = _load()
    out = []
    for s in d["signals"]:
        cl = s["_col_l"]
        if any(t in cl for t in toks):
            out.append(s)
    return out


def ground(model: dict, max_per: int = 4) -> dict:
    """For each machine signal whose kind has real-world analogues in the corpus,
    surface OBSERVED ranges from comparable sensors. Advisory only."""
    d = _load()
    if not d["signals"]:
        return {"loaded": False, **stats()}
    titles = d["titles"]
    grounded = []
    for sig in model.get("signals", []):
        measure = measure_of(sig)
        if not measure:
            continue
        hits = _matches(measure)
        if not hits:
            continue
        hits = sorted(hits, key=lambda s: -(s.get("samples") or 0))[:max_per]
        obs = [{"source": h.get("source"), "title": titles.get(h.get("source"), h.get("source")),
                "column": h.get("column"), "observedMin": h.get("observedMin"),
                "observedMax": h.get("observedMax"), "samples": h.get("samples")}
               for h in hits]
        eng = ([sig.get("engMin"), sig.get("engMax")] if sig.get("engMax") is not None else None)
        grounded.append({"signalId": sig["signalId"], "measure": measure, "unit": sig.get("engUnit"),
                         "engRange": eng, "observations": obs,
                         "note": f"OBSERVED ranges from real-world {measure} sensors — "
                                 "corroboration only, not an authoritative range (§62)"})
    return {"loaded": True, "policy": "OBSERVED · CANDIDATE · reference",
            "grounded": grounded, "grounded_signals": len(grounded),
            "total_signals": len(model.get("signals", [])),
            "corpus": {"datasets": stats()["datasets"], "signals": stats()["signals"]}}
