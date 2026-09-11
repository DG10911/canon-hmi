#!/usr/bin/env python3
"""Brain-first integration tests (spec §17). Proves the flow WITHOUT the real DGX
model by stubbing ONLY the network call — the real brain_intent canonical validation
still runs, so invalid-tag rejection is genuinely tested.

Run: python3 brain_tests.py
"""
import json as J
import platform_core as core
import app as A

TEST_MODEL = None


def fake_post(url, json=None, timeout=None, headers=None):
    """Simulate CANON-BRAIN: read the request, emit STRUCTURED intent from the model."""
    user = json["messages"][1]["content"].lower()
    m = TEST_MODEL
    sigs = m["signals"]
    unit = lambda u: [s["signalId"] for s in sigs if (s.get("engUnit") or "").lower() == u]
    desc = lambda k: [s["signalId"] for s in sigs if k in (s.get("description") or "").lower()]
    scope, signals, op, widget = "machine", [], "generate", "none"
    if "temperature" in user or "hot" in user:
        signals = unit("degc") or desc("temp")
    elif "level" in user:
        signals = unit("%")
    elif "pressure" in user and "remove" not in user:
        signals = unit("bar")
    elif "agitator" in user:
        a = [x["asset_id"] for x in m["assets"] if x["type"] == "motor"]
        scope = a[0] if a else "machine"
    elif "pump" in user:
        a = [x["asset_id"] for x in m["assets"] if x["type"] == "pump"]
        scope = a[0] if a else "machine"
    elif "ft-999" in user or "ft999" in user:
        signals = ["FT-999"]                       # INVALID on purpose
    if ("add" in user and "trend" in user) or "monitor" in user or "easier" in user or "prominent" in user:
        op, widget, signals = "add", "trend", (unit("degc") or desc("temp") or signals)
    if "remove" in user:
        op, widget = "remove", ("pressure" if "pressure" in user else "alarm" if "alarm" in user else "none")
    payload = {"scope": scope, "signals": signals[:4], "commands": [], "op": op, "widget": widget,
               "reasoning": "CANON-BRAIN interpreted: " + user[:48], "requires_review": False}

    class R:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return {"choices": [{"message": {"content": J.dumps(payload)}}]}
    return R()


def main():
    global TEST_MODEL
    import httpx
    from fastapi.testclient import TestClient
    A._load_all(); A._seed()
    A.LLM_BASE = "http://stub/v1"; A.LLM_MODEL = "canon-brain"     # pretend a brain is configured
    A.brain_reachable = lambda: True                              # and reachable
    httpx.post = fake_post                                        # stub ONLY the network
    c = TestClient(A.app)

    # load the batch reactor as the test machine
    m = core.normalize_csv(open("samples/batch_reactor_RX-05.csv").read(), "RXTEST")
    m["status"] = "STOPPED"; A._save(m)
    TEST_MODEL = A.PROJECTS["RXTEST"]
    pid = "RXTEST"
    passed = []

    def gen(prompt):
        return c.post(f"/api/projects/{pid}/generate", json={"request": prompt}).json()

    r = gen("keep an eye on the reactor temperature")
    ok = r["engine"] == "CANON-brain" and any("TT-" in s for w in r["screen"]["widgets"] for s in w.get("boundSignals", []))
    passed.append(("T1 fuzzy temperature -> TT-501 via CANON-brain", ok))

    r = gen("show me the level of the reactor")
    ok = any("LT-" in s for w in r["screen"]["widgets"] for s in w.get("boundSignals", []))
    passed.append(("T2 level -> LT-501", ok))

    r = gen("show me the two pressures")
    pts = {s for w in r["screen"]["widgets"] for s in w.get("boundSignals", []) if s.startswith("PT-")}
    passed.append(("T3 two pressures -> PT-501+PT-502", len(pts) >= 2))

    r = gen("give me an operator page for the agitator")
    passed.append(("T4 agitator -> AGT-501 scope", r["analysis"]["scope"] == "AGT-501"))

    r = gen("show FT-999")
    invalid = any("FT-999" in w.get("boundSignals", []) for w in r["screen"]["widgets"])
    passed.append(("T5 FT-999 rejected (never a widget)", not invalid))

    r = gen("show me the whole reactor")
    passed.append(("T6 engine tag = CANON-brain (no silent deterministic)", r["engine"] == "CANON-brain"))

    # edit through brain
    e = c.post(f"/api/projects/{pid}/edit", json={"prompt": "make the reactor temperature easier to monitor"}).json()
    passed.append(("T7 fuzzy edit -> brain adds a TT trend", e.get("engine") == "CANON-brain" and bool(e.get("applied"))))

    # BRAIN OFFLINE -> no silent fallback
    A.brain_reachable = lambda: False
    off = gen("show me the whole line")
    passed.append(("T8 brain offline -> brain_offline, NO deterministic fallback", off.get("brain_offline") is True))
    A.brain_reachable = lambda: True

    print("\n=== BRAIN-FIRST INTEGRATION TESTS ===")
    for name, ok in passed:
        print(("  PASS " if ok else "  FAIL ") + name)
    n = sum(1 for _, ok in passed if ok)
    print(f"\n{n}/{len(passed)} passed")
    A.PROJECTS.pop("RXTEST", None)
    import os
    os.remove("projects/RXTEST.json")
    return 0 if n == len(passed) else 1


if __name__ == "__main__":
    raise SystemExit(main())
