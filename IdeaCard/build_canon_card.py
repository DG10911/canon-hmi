#!/usr/bin/env python3
"""CANON — final SRM Ideation Card (PS2). 4:3, template green identity, industrial look."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.backends.backend_pdf import PdfPages

GREEN="#2FA84F"; GREEN_D="#1c8a3e"; GREEN_L="#eaf7ee"
INK="#1e2a32"; INK2="#3f5059"; MUT="#7a8a92"; LINE="#cfe0d6"
PANEL="#f3f6f7"; PANEL_B="#c6d0d6"; PANELINK="#2b363e"
AMBER="#e79a1a"; RED="#d64533"; BLUE="#2b6fb0"; WHITE="#ffffff"
W,H=1000.0,750.0
def Y(py): return H-py

fig=plt.figure(figsize=(10,7.5),dpi=220)
ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,W); ax.set_ylim(0,H); ax.axis("off")
ax.add_patch(Rectangle((0,0),W,H,fc=WHITE,ec="none",zorder=0))

def rrect(x,py,w,h,fc,ec,lw=1.4,rs=7,z=2):
    ax.add_patch(FancyBboxPatch((x,Y(py)-h),w,h,boxstyle=f"round,pad=2,rounding_size={rs}",fc=fc,ec=ec,lw=lw,zorder=z))
def box(x,py,w,h,label,icon="",body_z=2,head_h=26,ec=GREEN,head=GREEN):
    rrect(x,py,w,h,WHITE,ec,1.6,7,body_z)                     # outer
    ax.add_patch(FancyBboxPatch((x+3,Y(py)-head_h-3),w-6,head_h,boxstyle="round,pad=2,rounding_size=5",fc=head,ec="none",zorder=body_z+1))
    ax.text(x+13,Y(py)-3-head_h/2,label,color=WHITE,fontsize=9,fontweight="bold",va="center",zorder=body_z+2)
    return (x+14, py+head_h+8)  # body text start (x, py)
def arrow(x1,py1,x2,py2,color=GREEN,lw=1.8):
    ax.add_patch(FancyArrowPatch((x1,Y(py1)),(x2,Y(py2)),arrowstyle="-|>",mutation_scale=11,color=color,lw=lw,zorder=6,shrinkA=1,shrinkB=1))
def chip(x,py,w,h,t,fc,tc,fs=8.2,ec="none",bold=True):
    ax.add_patch(FancyBboxPatch((x,Y(py)-h),w,h,boxstyle=f"round,pad=1.5,rounding_size={h/2}",fc=fc,ec=ec,lw=1,zorder=7))
    ax.text(x+w/2,Y(py)-h/2,t,color=tc,fontsize=fs,fontweight="bold" if bold else "normal",ha="center",va="center",zorder=8)
def blk(x,py,w,h,t,sub="",fc=WHITE,ec=GREEN,tc=INK,fs=8.6,z=5):
    rrect(x,py,w,h,fc,ec,1.5,6,z)
    if sub:
        ax.text(x+w/2,Y(py)-h*0.36,t,color=tc,fontsize=fs,fontweight="bold",ha="center",va="center",zorder=z+1)
        ax.text(x+w/2,Y(py)-h*0.70,sub,color=MUT,fontsize=7,ha="center",va="center",zorder=z+1)
    else:
        ax.text(x+w/2,Y(py)-h/2,t,color=tc,fontsize=fs,fontweight="bold",ha="center",va="center",zorder=z+1,linespacing=1.2)

# ===== TOP ROW =====
# PROBLEM STATEMENT
bx,by=box(12,12,470,116,"PROBLEM STATEMENT","▣")
ax.text(bx-2,Y(by),"HMI engineering depends on manually creating, binding &\nmaintaining screens as PLC tags, I/O, alarms & process\nneeds evolve — raising engineering effort, commissioning\ntime & lifecycle cost.  PS2: dynamically generate machine-\nspecific HMI at runtime and enable machine control via HMI.",
        color=INK2,fontsize=8.1,va="top",linespacing=1.42)
# TITLE
bx,by=box(494,12,268,116,"TITLE","▤")
ax.text(494+134,Y(by+4),"CANON",color=INK,fontsize=27,fontweight="bold",ha="center",va="top")
ax.text(494+134,Y(by+38),"Machine Context → Dynamic HMI",color=GREEN_D,fontsize=8.4,ha="center",va="top",fontweight="bold")
ax.text(494+134,Y(by+50),"→ Verified Control",color=GREEN_D,fontsize=8.4,ha="center",va="top",fontweight="bold")
# TEAM
bx,by=box(774,12,214,116,"TEAM & MEMBERS")
ax.text(bx-2,Y(by+2),"DigiSeva",color=INK,fontsize=13,fontweight="bold",va="top")
ax.text(bx-2,Y(by+26),"Devansh Goenka\nPanshul Arora\nTanmay Singh",color=INK2,fontsize=8.6,va="top",linespacing=1.5)

# ===== HERO: PROPOSED SOLUTION =====
HX,HPY,HW,HH=12,138,976,404
box(HX,HPY,HW,HH,"PROPOSED SOLUTION","💡",head_h=28)
# 6-step pipeline
steps=[("MACHINE\nCONTEXT",GREEN),("CANONICAL\nMODEL",GREEN),("AI\nINTENT",GREEN),("DETERMINISTIC\nVALIDATION",GREEN),("DYNAMIC\nHMI",GREEN),("PLC-AUTH.\nCONTROL",GREEN_D)]
cw=142; gap=13; x0=26; py_pipe=182
for i,(t,c) in enumerate(steps):
    x=x0+i*(cw+gap)
    ax.add_patch(FancyBboxPatch((x,Y(py_pipe)-34),cw,34,boxstyle="round,pad=2,rounding_size=6",fc=(GREEN_L if i<5 else "#d9f0e0"),ec=c,lw=1.5,zorder=5))
    ax.text(x+cw/2,Y(py_pipe)-17,t,color=GREEN_D,fontsize=7.6,fontweight="bold",ha="center",va="center",zorder=6,linespacing=1.1)
    if i<5: arrow(x+cw+1,py_pipe-17,x+cw+gap-1,py_pipe-17,GREEN,1.6)
ax.text(26,Y(175),"THE MACHINE MODEL IS THE SOURCE OF TRUTH",color="#20643a",fontsize=6.8,fontweight="bold",va="center",zorder=6)

# --- three panels ---
PANEL_TOP=232; PANEL_H=210
# LEFT: machine context -> canonical model
lx,lw_=26,300
rrect(lx,PANEL_TOP,lw_,PANEL_H,"#fbfdfc",LINE,1.2,8,3)
ax.text(lx+12,Y(PANEL_TOP)-12,"MACHINE ENGINEERING CONTEXT",color=INK,fontsize=8,fontweight="bold",va="top")
items=["PLC / controller tags","I/O configuration","Asset hierarchy","Alarm definitions","Communication config","Machine documentation"]
for i,it in enumerate(items):
    ax.text(lx+16,Y(PANEL_TOP)-28-i*13.5,"•  "+it,color=INK2,fontsize=7.7,va="top")
arrow(lx+lw_/2,PANEL_TOP+118,lx+lw_/2,PANEL_TOP+132,GREEN,1.8)
blk(lx+40,PANEL_TOP+134,lw_-80,32,"CANONICAL MACHINE MODEL","stable IDs · typed signals · provenance",fc=GREEN_L,ec=GREEN,tc=GREEN_D,fs=8)
arrow(lx+lw_/2,PANEL_TOP+168,lx+lw_/2,PANEL_TOP+180,GREEN,1.8)
ax.text(lx+lw_/2,Y(PANEL_TOP+182),"AI INTENT  →  DETERMINISTIC VALIDATION",color=INK2,fontsize=7.4,fontweight="bold",ha="center",va="top")
ax.text(lx+lw_/2,Y(PANEL_TOP+195),"“Create HMI for TK-401: level, pressure, pump, valve”",color=MUT,fontsize=6.6,style="italic",ha="center",va="top")

# CENTER: HMI mockup
cx,cw2=344,300
rrect(cx,PANEL_TOP,cw2,PANEL_H,PANEL,PANEL_B,1.3,8,3)
# faceplate header
ax.add_patch(FancyBboxPatch((cx+10,Y(PANEL_TOP)-26),cw2-20,20,boxstyle="round,pad=1,rounding_size=4",fc="#e4e9ec",ec=PANEL_B,lw=1,zorder=5))
ax.text(cx+20,Y(PANEL_TOP)-16,"TK-401 · PROCESS TANK",color=PANELINK,fontsize=8,fontweight="bold",va="center",zorder=6)
chip(cx+cw2-58,PANEL_TOP+6,44,15,"● LIVE",GREEN,WHITE,7)
# value tiles
def tile(tx,tpy,tw,lab,val,unit,col=PANELINK):
    ax.add_patch(FancyBboxPatch((tx,Y(tpy)-40),tw,40,boxstyle="round,pad=1,rounding_size=4",fc=WHITE,ec=PANEL_B,lw=1,zorder=5))
    ax.text(tx+8,Y(tpy)-12,lab,color=MUT,fontsize=6.4,fontweight="bold",va="center",zorder=6)
    ax.text(tx+8,Y(tpy)-28,val,color=col,fontsize=13,fontweight="bold",va="center",zorder=6)
    ax.text(tx+8+len(val)*10+6,Y(tpy)-28,unit,color=MUT,fontsize=7,va="center",zorder=6)
tile(cx+14,PANEL_TOP+34,132,"LEVEL","72"," %")
tile(cx+154,PANEL_TOP+34,132,"PRESSURE","6.8"," bar")
tile(cx+14,PANEL_TOP+80,132,"PUMP","RUNNING","",GREEN_D)
tile(cx+154,PANEL_TOP+80,132,"INLET VALVE","OPEN","",GREEN_D)
# alarms + commands
ax.text(cx+22,Y(PANEL_TOP+134),"ACTIVE ALARMS   0",color=GREEN_D,fontsize=8,fontweight="bold",va="center")
chip(cx+16,PANEL_TOP+150,86,24,"START",GREEN,WHITE,9)
chip(cx+108,PANEL_TOP+150,86,24,"STOP","#e6ebee",PANELINK,9)
chip(cx+206,PANEL_TOP+150,40,24,"PLC","#dfe6ea",BLUE,7.5)
chip(cx+248,PANEL_TOP+150,44,24,"VERIFIED","#dff0e4",GREEN_D,7)
ax.text(cx+cw2/2,Y(PANEL_TOP+190),"PT401 → PLC.PT401.DischargePressure → LIVE · VERIFIED",
        color=MUT,fontsize=6.6,ha="center",va="top")

# RIGHT: control + change continuity
rx,rw=662,300
rrect(rx,PANEL_TOP,rw,PANEL_H,"#fbfdfc",LINE,1.2,8,3)
ax.text(rx+12,Y(PANEL_TOP)-12,"VERIFIED CONTROL",color=INK,fontsize=8,fontweight="bold",va="top")
cpath=["START (request)","Command Contract","Permissive check","PLC authorizes","Machine → Feedback","HMI: RUNNING ✓"]
for i,s in enumerate(cpath):
    yy=PANEL_TOP+26+i*15
    ax.text(rx+18,Y(PANEL_TOP+26+i*15),("↓ " if i else "")+s,color=INK2,fontsize=7.5,va="top")
ax.text(rx+12,Y(PANEL_TOP+126),"CHANGE-AWARE CONTINUITY",color=INK,fontsize=8,fontweight="bold",va="top")
chip(rx+16,PANEL_TOP+140,120,18,"PT101  0–10 → 0–16 bar",AMBER,"#241a06",7)
ax.text(rx+18,Y(PANEL_TOP+162),"impact ✓ PLC scaling ✓ HMI range\n✓ alarm ✓ trend ✓ test  →  regenerate → validate",
        color=INK2,fontsize=7,va="top",linespacing=1.4)

# --- trust strip ---
ts=[("AI","proposes"),("MODEL","truth"),("VALIDATOR","checks"),("ENGINEER","approves"),("PLC","controls")]
tw=180; tg=8; tx0=26; tpy=468
for i,(a,b) in enumerate(ts):
    x=tx0+i*(tw+tg)
    ax.add_patch(FancyBboxPatch((x,Y(tpy)-26),tw,26,boxstyle="round,pad=1,rounding_size=6",fc="#f4f8f5",ec=GREEN,lw=1.2,zorder=5))
    ax.text(x+12,Y(tpy)-13,a,color=GREEN_D,fontsize=8.2,fontweight="bold",va="center",zorder=6)
    ax.text(x+tw-12,Y(tpy)-13,b,color=INK2,fontsize=7.6,va="center",ha="right",zorder=6)
    if i<4: arrow(x+tw+1,tpy-13,x+tw+tg-1,tpy-13,GREEN,1.5)
# --- tagline ---
ax.add_patch(FancyBboxPatch((26,Y(528)),936,28,boxstyle="round,pad=2,rounding_size=8",fc=GREEN,ec="none",zorder=5))
ax.text(494,Y(514),"WE DON'T GENERATE A SCREEN FROM A PROMPT — WE GENERATE A VALIDATED INTERFACE FROM THE MACHINE, AND KEEP IT IN SYNC AS IT CHANGES.",
        color=WHITE,fontsize=7.0,fontweight="bold",ha="center",va="center",zorder=6)

# ===== BOTTOM ROW =====
# WHY THIS SOLUTION
bx,by=box(12,552,718,186,"WHY THIS SOLUTION","🏅",head_h=26)
whys=[("Machine-specific by design","generated from the machine's real assets, signals, alarms & commands"),
      ("Dynamic at runtime","contextual views without relying on manually authored machine-specific screens"),
      ("Control, not just visualization","commands follow defined contracts + PLC-authoritative execution"),
      ("Verified bindings","every HMI signal resolves against the canonical machine model"),
      ("Change-aware","engineering changes identify affected HMI, alarms, trends & tests"),
      ("Engineering continuity","one model drives generation, validation, diagnostics & regeneration")]
for i,(t,s) in enumerate(whys):
    col=0 if i<3 else 1
    row=i%3
    xx=24+col*352; yy=by+row*30
    ax.text(xx,Y(yy),"✓",color=GREEN,fontsize=9,fontweight="bold",va="top")
    ax.text(xx+16,Y(yy),t,color=INK,fontsize=8,fontweight="bold",va="top")
    ax.text(xx+16,Y(yy+11),s,color=MUT,fontsize=6.7,va="top")
ax.text(24,Y(by+96),"“AI proposes.  The machine model defines.  The validator checks.  The PLC controls.”",
        color=GREEN_D,fontsize=8,fontweight="bold",style="italic",va="top")
ax.text(24,Y(by+112),"Not just HMI generation — validated, machine-context-driven generation with control authority & change continuity.",
        color=INK2,fontsize=7,va="top")

# TECHNOLOGY & TOOLS
bx,by=box(742,552,246,186,"TECHNOLOGY & TOOLS","🛠",head_h=26)
tools=["AI / LLM · structured (typed) output","Canonical engineering model","NL intent compiler","OPC UA · Modbus TCP","PLC simulator (PLC-authoritative)","React / TypeScript HMI runtime","Deterministic validation","Engineering knowledge graph","Change-impact + regression","ISA-101 / ISA-18.2-informed","MTP / OPC-UA-inspired context","EcoStruxure / EOTE workflow-aligned"]
for i,t in enumerate(tools):
    ax.text(bx-2,Y(by+i*12.6),"▸ "+t,color=INK2,fontsize=7.0,va="top")

pdf=PdfPages("/Users/devanshgoenka/conductor/workspaces/dgrfrfeerf/santo-domingo/.context/IdeaCard/CANON_IdeaCard.pdf")
pdf.savefig(fig); pdf.close(); plt.close(fig)
print("card written")
