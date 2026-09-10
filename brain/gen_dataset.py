#!/usr/bin/env python3
"""
CANON brain — dataset generator.

The canonical-model compiler is the TEACHER. For many synthetic machines and many
phrasings of engineering intent, we emit the *correct* widget proposal (as the
deterministic compiler would). Fine-tuning on this teaches an open model to
GENERALISE machine-specific HMI generation to machines it has never seen —
while the runtime validator still guarantees every binding.

Output: brain/data/train.jsonl + brain/data/eval.jsonl  (OpenAI chat format)
Run:    python gen_dataset.py --n 6000
"""
import json, random, argparse, os

random.seed(7)

WIDGET_TYPES = ["gaugeP","gaugeL","tile","pump","valve","trend","cmd","alarms","diagnostic"]

SYSTEM = (
 "You are CANON, an HMI layout compiler for industrial machines. Given a CANONICAL "
 "MACHINE MODEL (the single source of truth) and an operator/engineer INTENT, propose an "
 "HMI as a flat JSON list of widgets. RULES: (1) every widget 'ref' MUST be an exact signal "
 "name or command id from the model — never invent a tag; (2) gaugeP=pressure, gaugeL=level, "
 "tile=other analog signal, pump/valve for those assets, cmd=command, alarms=alarm banner, "
 "trend=a trend, diagnostic=abnormal-condition panel; (3) follow ISA-101 — show what the intent "
 "asks for, nothing decorative; priority 1=primary,3=secondary; (4) you propose only — the model "
 "defines, a validator checks, the PLC controls. Return ONLY JSON: "
 '{"widgets":[{"type","ref","priority"}],"rationale"}'
)

# ---- signal roles the compiler understands ----
def sig(name, desc, io, role, unit="", lo=0, hi=0):
    return {"name":name,"desc":desc,"io":io,"role":role,"unit":unit,"min":lo,"max":hi}

# ---- a family of machines (diverse tag sets → generalisation) ----
def tank(i):
    n=f"TK-{400+i}"
    return {"name":n,"type":"Process Tank Unit","signals":[
        sig(f"LT{400+i}","Tank level","AI","level","%",0,100),
        sig(f"PT{400+i}","Discharge pressure","AI","pressure","bar",0,random.choice([10,16,25])),
        sig(f"FT{400+i}","Discharge flow","AI","flow","m3/h",0,120),
        sig(f"TT{400+i}","Fluid temperature","AI","temp","C",0,150),
        sig(f"P{400+i}_RUN_FB","Pump run feedback","DI","run"),
        sig(f"XV{400+i}_OPEN_FB","Inlet valve open feedback","DI","valve"),
    ],"commands":[
        {"id":f"command:P{400+i}:START","writes":f"P{400+i}_START_CMD","pre":[f"XV{400+i}_OPEN_FB"]},
        {"id":f"command:P{400+i}:STOP","writes":f"P{400+i}_STOP_CMD","pre":[]},
    ]}

def drive(i):
    n=f"ATV{630+i}"
    return {"name":n,"type":"Variable Frequency Drive","signals":[
        sig(f"{n}_SPD","Output frequency","AI","freq","Hz",0,60),
        sig(f"{n}_CUR","Motor current","AI","current","A",0,150),
        sig(f"{n}_PWR","Output power","AI","power","%",0,150),
        sig(f"{n}_RUN_FB","Drive run feedback","DI","run"),
        sig(f"{n}_FLT","Drive fault","DI","fault"),
    ],"commands":[
        {"id":f"command:{n}:START","writes":f"{n}_CMD","pre":[f"{n}_FLT"]},
        {"id":f"command:{n}:STOP","writes":f"{n}_CMD","pre":[]},
    ]}

def meter(i):
    n=f"PM{8000+i}"
    return {"name":n,"type":"Power & Energy Meter","signals":[
        sig(f"{n}_I","Current average","AI","current","A",0,1000),
        sig(f"{n}_V","Voltage L-L average","AI","voltage","V",0,600),
        sig(f"{n}_P","Active power total","AI","power","kW",0,2000),
        sig(f"{n}_PF","Power factor","AI","pf","",-1,1),
        sig(f"{n}_F","Frequency","AI","freq","Hz",45,65),
    ],"commands":[]}

def mixer(i):
    n=f"MX-{200+i}"
    return {"name":n,"type":"Agitated Mixer Skid","signals":[
        sig(f"AT{200+i}_SPD","Agitator speed","AI","speed","rpm",0,300),
        sig(f"AT{200+i}_TRQ","Agitator torque","AI","torque","%",0,150),
        sig(f"TT{200+i}","Batch temperature","AI","temp","C",0,120),
        sig(f"LT{200+i}","Batch level","AI","level","%",0,100),
        sig(f"AG{200+i}_RUN_FB","Agitator run feedback","DI","run"),
    ],"commands":[
        {"id":f"command:AG{200+i}:START","writes":f"AG{200+i}_START","pre":[]},
        {"id":f"command:AG{200+i}:STOP","writes":f"AG{200+i}_STOP","pre":[]},
    ]}

def make_machine():
    f=random.choice([tank,drive,meter,mixer]); return f(random.randint(0,9))

# ---- recipes: intent-kind -> which roles/widgets to include ----
RECIPES = {
 "overview":   {"kinds":["level","pressure","flow","temp","run","valve","alarms","controls"], "phr":[
    "Create an operator HMI for {m} with the key process values, pump/valve status, alarms and start/stop.",
    "Operator overview screen for {m}.",
    "I need a runtime HMI showing the main values and controls for {m}.",
    "Give the operator a status view of {m} with alarms and controls."]},
 "control":    {"kinds":["run","controls","pressure","alarms"], "phr":[
    "Pump/drive control faceplate for {m}.",
    "Control screen for {m} — start/stop plus the main feedback.",
    "Make a compact control HMI for {m}."]},
 "diagnostic": {"kinds":["diagnostic","pressure","run","alarms"], "phr":[
    "Diagnostics screen for the current abnormal condition on {m}.",
    "Show a fault/diagnostic view for {m}.",
    "Maintenance diagnostics for {m} with active condition and alarms."]},
 "energy":     {"kinds":["power","current","voltage","freq","pf","trend"], "phr":[
    "Energy dashboard for {m}.",
    "Show power, current and energy quality for {m}.",
    "Metering overview for {m}."]},
 "trendview":  {"kinds":["trend","pressure","level"], "phr":[
    "Trend view for {m}.",
    "Add a pressure trend and the main analogs for {m}.",
    "Historian/trend screen for {m}."]},
 "compact":    {"kinds":["pressure","run","controls"], "phr":[
    "Small-panel HMI for {m}.",
    "Compact pump + pressure view for {m}.",
    "Minimal operator panel for {m}."]},
}

ROLE_WIDGET = {"level":("gaugeL",1),"pressure":("gaugeP",1),"flow":("tile",3),"temp":("tile",3),
 "current":("tile",2),"voltage":("tile",2),"power":("tile",2),"pf":("tile",3),"freq":("tile",3),
 "speed":("tile",2),"torque":("tile",3),"run":("pump",1)}

def compile_target(machine, kinds):
    """The TEACHER: deterministic correct widget list for these kinds on this machine."""
    widgets=[]; sigs=machine["signals"]; used=set()
    for k in kinds:
        if k=="alarms": widgets.append({"type":"alarms","priority":1}); continue
        if k=="diagnostic": widgets.append({"type":"diagnostic","priority":1}); continue
        if k=="trend":
            s=next((x for x in sigs if x["role"] in ("pressure","flow","power","level")),None)
            if s: widgets.append({"type":"trend","ref":s["name"],"priority":2}); continue
        if k=="valve":
            s=next((x for x in sigs if x["role"]=="valve"),None)
            if s: widgets.append({"type":"valve","ref":s["name"],"priority":1}); continue
        if k=="controls":
            for c in machine["commands"]:
                widgets.append({"type":"cmd","ref":c["id"],"priority":1})
            continue
        # analog/run roles
        for s in sigs:
            if s["role"]==k and s["name"] not in used:
                wt=ROLE_WIDGET.get(k)
                if wt: widgets.append({"type":wt[0],"ref":s["name"],"priority":wt[1]}); used.add(s["name"])
    return widgets

def model_text(m):
    sl="\n".join(f"  - {s['name']} ({s['desc']}) io={s['io']} "
                 f"range={(str(s['min'])+'-'+str(s['max'])+' '+s['unit']) if s['unit'] else 'discrete'}"
                 for s in m["signals"])
    cl="\n".join(f"  - {c['id']} permissives={c['pre']}" for c in m["commands"]) or "  (none)"
    return f"MACHINE MODEL: {m['name']} ({m['type']})\nSIGNALS:\n{sl}\nCOMMANDS:\n{cl}"

FAKE_TAGS=["PT_MAIN_999","LEVEL_X","MOTOR_TEMP_A7","PRESSURE2","TAG_UNKNOWN"]

def make_example():
    m=make_machine(); rk=random.choice(list(RECIPES)); rec=RECIPES[rk]
    # only keep kinds whose role exists (so target is achievable) — teaches "ignore what's absent"
    have={s["role"] for s in m["signals"]}|{"alarms","diagnostic","trend","controls","valve"}
    kinds=[k for k in rec["kinds"] if k in have or k in ("alarms","diagnostic","trend","controls")]
    widgets=compile_target(m,kinds)
    if not widgets: return None
    intent=random.choice(rec["phr"]).format(m=m["name"])
    # 20%: inject a fake-tag request → target must NOT include it (anti-hallucination)
    if random.random()<0.20:
        intent+=f" Also show {random.choice(FAKE_TAGS)}."
    rationale=f"{rk} view for {m['name']}: {len(widgets)} widgets bound to validated signals; unresolved requests omitted."
    out={"widgets":widgets,"rationale":rationale}
    user=f"{model_text(m)}\n\nINTENT: {intent}\n\nReturn the widget list as JSON."
    return {"messages":[{"role":"system","content":SYSTEM},
                        {"role":"user","content":user},
                        {"role":"assistant","content":json.dumps(out,separators=(',',':'))}]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--n",type=int,default=6000); a=ap.parse_args()
    ex=[]; seen=set()
    while len(ex)<a.n:
        e=make_example()
        if not e: continue
        key=e["messages"][1]["content"]+e["messages"][2]["content"]
        if key in seen: continue
        seen.add(key); ex.append(e)
    random.shuffle(ex); cut=int(len(ex)*0.92)
    os.makedirs("data",exist_ok=True)
    with open("data/train.jsonl","w") as f:
        for e in ex[:cut]: f.write(json.dumps(e)+"\n")
    with open("data/eval.jsonl","w") as f:
        for e in ex[cut:]: f.write(json.dumps(e)+"\n")
    print(f"wrote {cut} train / {len(ex)-cut} eval examples")
    print("machine types: tank / drive / meter / mixer · anti-hallucination examples included")

if __name__=="__main__": main()
