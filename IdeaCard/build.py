#!/usr/bin/env python3
"""SENTINEL — Idea Card (PS1: AI Runtime Copilot for Industrial HMI). Premium dark deck -> PDF."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from matplotlib.backends.backend_pdf import PdfPages

# palette
GREEN="#3DCD58"; GREEN2="#25e08a"; CYAN="#39d6ff"; VIOLET="#a884ff"
BG="#0b1310"; PANEL="#12201b"; PANEL2="#16271f"; LINE="#294036"
INK="#eaf5ee"; INK2="#9fc3b1"; MUTED="#6f8c7c"
AMBER="#ffc24b"; RED="#ff5d63"; WHITE="#ffffff"
W,H=1000.0,563.0

def page():
    fig=plt.figure(figsize=(13.333,7.5),dpi=200)
    ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,W); ax.set_ylim(0,H); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0,0),W,H,boxstyle="square,pad=0",fc=BG,ec="none",zorder=0))
    return fig,ax

def panel(ax,x,y,w,h,fc=PANEL,ec=LINE,lw=1.2,rs=10,z=1):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f"round,pad=2,rounding_size={rs}",fc=fc,ec=ec,lw=lw,zorder=z))

def bar3(ax,x,y,h,col=GREEN):  # accent bar
    ax.add_patch(FancyBboxPatch((x,y),3.4,h,boxstyle="round,pad=0,rounding_size=2",fc=col,ec="none",zorder=3))

def pill(ax,x,y,w,h,text,fc=GREEN,tc="#04140b",fs=11,bold=True):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f"round,pad=2,rounding_size={h/2}",fc=fc,ec="none",zorder=3))
    ax.text(x+w/2,y+h/2,text,color=tc,fontsize=fs,fontweight="bold" if bold else "normal",ha="center",va="center",zorder=4)

def chip(ax,x,y,w,h,text,tc=INK,ec=LINE,fs=10):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f"round,pad=2,rounding_size=6",fc=PANEL2,ec=ec,lw=1,zorder=3))
    ax.text(x+w/2,y+h/2,text,color=tc,fontsize=fs,fontweight="bold",ha="center",va="center",zorder=4)

def arrow(ax,p1,p2,color=GREEN,lw=2.2,ls="-"):
    ax.add_patch(FancyArrowPatch(p1,p2,arrowstyle="-|>",mutation_scale=15,color=color,lw=lw,ls=ls,zorder=3,shrinkA=3,shrinkB=3))

def head(ax,page_no):
    ax.add_patch(FancyBboxPatch((0,H-12),W,12,boxstyle="square,pad=0",fc=GREEN,ec="none",zorder=5))
    ax.text(20,H-30,"Schneider Electric HMI Hackathon 2026  ·  Idea Card",color=INK2,fontsize=10,va="center",fontweight="bold")
    pill(ax,W-250,H-40,150,20,"PROBLEM STATEMENT 1",fc=CYAN,tc="#04121a",fs=9.5)
    ax.text(W-92,H-30,"Team DigiSeva",color=INK,fontsize=10,va="center",ha="left",fontweight="bold")
    # footer
    ax.add_patch(FancyBboxPatch((0,0),W,26,boxstyle="square,pad=0",fc="#0a120e",ec="none",zorder=5))
    ax.text(20,13,"Life Is On  |  Schneider Electric",color=INK2,fontsize=9,va="center",zorder=6)
    ax.text(W/2,13,"Devansh Goenka · Panshul Arora · Tanmay Singh",color=MUTED,fontsize=8.5,va="center",ha="center",zorder=6)
    ax.text(W-20,13,f"Page {page_no}",color=MUTED,fontsize=9,va="center",ha="right",zorder=6)

pdf=PdfPages("/Users/devanshgoenka/conductor/workspaces/dgrfrfeerf/santo-domingo/.context/IdeaCard/SENTINEL_IdeaCard.pdf")

# ============================================================ PAGE 1
fig,ax=page(); head(ax,1)
# title block
ax.text(22,H-70,"SENTINEL",color=WHITE,fontsize=40,fontweight="bold",va="center")
ax.add_patch(Circle((250,H-70),5,color=GREEN,zorder=4))
ax.text(262,H-70,"on-device",color=GREEN,fontsize=12,va="center",fontweight="bold")
ax.text(22,H-98,"The on-device AI Runtime Copilot for Industrial HMI",color=INK,fontsize=15,va="center")
ax.text(22,H-116,"From alarm flood → ranked decision — on the panel, offline, in seconds.",color=INK2,fontsize=11.5,va="center",style="italic")

# ---- LEFT: problem + solution + skills ----
LX=22; LW=560
# problem
panel(ax,LX,300,LW,130); bar3(ax,LX+6,306,118)
ax.text(LX+20,414,"THE PROBLEM",color=GREEN,fontsize=10.5,fontweight="bold",va="center")
prob=("Operators drown in alarm floods (ISA-18.2: >10 alarms / 10 min) and data.\n"
      "Critical events get buried; new operators lack context; expert know-how is\n"
      "undocumented. Result: slower response, downtime, safety & compliance risk.")
ax.text(LX+20,378,prob,color=INK,fontsize=10.5,va="top",linespacing=1.5)
pill(ax,LX+20,312,150,22,"$10–20 B/yr lost output",fc=RED,tc=WHITE,fs=9.5)
pill(ax,LX+180,312,150,22,"alarm floods → incidents",fc=AMBER,tc="#1a1207",fs=9.5)
pill(ax,LX+340,312,150,22,"expertise walks out",fc=PANEL2,tc=INK,fs=9.5)

# solution
panel(ax,LX,150,LW,138,fc=PANEL2); bar3(ax,LX+6,156,126,CYAN)
ax.text(LX+20,272,"OUR SOLUTION",color=CYAN,fontsize=10.5,fontweight="bold",va="center")
ax.text(LX+20,252,"An embedded AI copilot inside the HMI that ingests alarm, process &",color=INK,fontsize=10.5,va="top")
ax.text(LX+20,238,"operator logs + live runtime context, and delivers guidance in-workflow —",color=INK,fontsize=10.5,va="top")
ax.text(LX+20,224,"running fully on-device so it works on low-end panels, offline.",color=INK,fontsize=10.5,va="top")
skills=[("①","Alarm Explanation & Contextual Guidance"),("②","Root-Cause Investigation (alarm × trend × action)"),
        ("③","Shift-Handover Auto-Brief"),("④","Operational Decision Support"),("⑤","SOP & Knowledge Retrieval (RAG)")]
yy=196
for i,(n,s) in enumerate(skills):
    col=LX+20 if i<3 else LX+300
    y=196-(i%3)*22
    ax.text(col,y,n,color=GREEN,fontsize=12,fontweight="bold",va="center")
    ax.text(col+18,y,s,color=INK,fontsize=9.6,va="center")

# ---- RIGHT: architecture stack ----
RX=602; RW=376
panel(ax,RX,150,RW,296,fc=PANEL)
ax.text(RX+18,432,"HOW IT WORKS",color=GREEN,fontsize=10.5,fontweight="bold",va="center")
def layer2(y,h,title,subs,col):
    panel(ax,RX+18,y,RW-36,h,fc=PANEL2,ec=col,lw=1.6,rs=8,z=3)
    ax.text(RX+30,y+h-14,title,color=col,fontsize=10.3,fontweight="bold",va="center",zorder=4)
    yy=y+h-31
    for s in subs:
        ax.text(RX+30,yy,s,color=INK2,fontsize=8.7,va="center",zorder=4); yy-=13
CM=RX+RW/2
layer2(400,36,"DATA SOURCES",["Alarm logs · Process logs · Operator actions · Runtime context"],INK2)
arrow(ax,(CM,400),(CM,384),CYAN,1.8)
layer2(316,68,"ON-DEVICE AI CORE",["Small LLM (quantised) + local RAG vector store","Trust layer: confidence · evidence · UNKNOWN"],GREEN)
arrow(ax,(CM,316),(CM,300),CYAN,1.8)
layer2(252,48,"COPILOT SKILLS",["Explain · Root-cause · Handover · Decide · SOP"],VIOLET)
arrow(ax,(CM,252),(CM,236),CYAN,1.8)
layer2(188,44,"HMI + OPERATOR",["In-workflow guidance overlay on existing screens"],GREEN)
ax.text(RX+18,168,"►  Advisory only — PLC stays authoritative. AI never controls actuators.",color=AMBER,fontsize=8.3,va="center",zorder=6)

# ---- BOTTOM KPI strip ----
kpis=[("−60%","alarm noise → ranked"),("−40%","response time"),("↑ 3×","new-operator ramp"),("100%","on-device / offline")]
pw=232; gap=12; x0=22
for i,(a,b) in enumerate(kpis):
    x=x0+i*(pw+gap)
    panel(ax,x,52,pw,74,fc=PANEL2,ec=LINE); bar3(ax,x+6,58,62,GREEN if i!=3 else CYAN)
    ax.text(x+22,104,a,color=GREEN if i!=3 else CYAN,fontsize=22,fontweight="bold",va="center")
    ax.text(x+22,74,b,color=INK2,fontsize=9.5,va="center")
pdf.savefig(fig); plt.close(fig)

# ============================================================ PAGE 2
fig,ax=page(); head(ax,2)
ax.text(22,H-58,"How SENTINEL works — and why it wins",color=WHITE,fontsize=24,fontweight="bold",va="center")
ax.add_patch(FancyBboxPatch((22,H-74),150,3.5,boxstyle="square,pad=0",fc=GREEN,ec="none"))

# pipeline
py=395
nodes=[("SENSE","Alarm + process +\noperator logs, context"),("RETRIEVE","Local RAG over SOPs\n& past events"),
       ("REASON","On-device LLM ranks\n& correlates"),("GUIDE","In-HMI briefing +\nnext-best action"),
       ("ACT","Operator decides;\nPLC executes"),("LEARN","Feedback → memory\n(governed)")]
bw=148; gap=14; x0=22
for i,(n,s) in enumerate(nodes):
    x=x0+i*(bw+gap)
    panel(ax,x,py,bw,84,fc=PANEL2,ec=GREEN if i in(2,) else LINE,lw=1.6 if i==2 else 1.1)
    ax.text(x+bw/2,py+62,n,color=GREEN,fontsize=12,fontweight="bold",ha="center",va="center")
    ax.text(x+bw/2,py+28,s,color=INK2,fontsize=8.8,ha="center",va="center",linespacing=1.35)
    if i<5: arrow(ax,(x+bw,py+42),(x+bw+gap,py+42),GREEN,2)
ax.text(22,py-16,"Closed loop · deterministic guardrails at every step · PLC remains the runtime authority.",color=INK2,fontsize=10,va="center")

# three columns: differentiators / tech / feasibility+why-us
cy=120; ch=250; cw=300; cg=20; cx0=22
def col(x,title,items,col):
    panel(ax,x,cy,cw,ch,fc=PANEL); bar3(ax,x+6,cy+6,ch-12,col)
    ax.text(x+20,cy+ch-18,title,color=col,fontsize=11,fontweight="bold",va="center")
    yy=cy+ch-44
    for it in items:
        sub=it.startswith("  ")
        ax.text(x+20,yy,("• " if not sub else "   ")+it.strip(),color=INK2 if sub else INK,fontsize=9.3 if not sub else 8.6,va="center",style="italic" if sub else "normal")
        yy-=22
col(cx0,"WHY IT WINS (differentiators)",[
    "On-device / OFFLINE — runs on low-end HMI",
    "  answers PS1's low-end-hardware note others skip",
    "Trust layer: cites evidence, shows UNKNOWN",
    "  no hallucinated plant state — safe & auditable",
    "PLC-authoritative — advisory only",
    "In-workflow, not a side chatbot",
    "Captures expert knowledge → shared memory",
    "Beats cloud copilots at the edge",
],GREEN)
col(cx0+cw+cg,"TECH STACK",[
    "Edge SLM (quantised) — llama.cpp / ONNX",
    "Local RAG — embeddings + vector store",
    "Runs on ARM Linux HMI / Raspberry Pi class",
    "Connectors: Modbus TCP · OPC UA · alarm DB",
    "Schneider fit: Harmony HMI · EcoStruxure",
    "  complements Augmented Operator Advisor",
    "Open-source, low CPU/RAM footprint",
    "Cloud optional for fleet learning",
],CYAN)
col(cx0+2*(cw+cg),"FEASIBILITY & WHY US",[
    "Working HMI + AI copilot already built:",
    "  live 3D prototype (AssetFlow) + HMI sim",
    "Trust/guardrail model already implemented",
    "Deterministic + LLM hybrid — demoable",
    "Maps 1:1 to all 5 PS-1 use cases",
    "Runs where the plant runs — no cloud needed",
    "Clear ROI: fewer floods, faster response,",
    "  faster onboarding, retained expertise",
],VIOLET)

# 10s pitch banner
panel(ax,22,58,W-44,44,fc=PANEL2,ec=GREEN,lw=1.6)
ax.text(W/2,80,"“SENTINEL turns alarm floods into decisions — an on-device AI copilot that explains, investigates, and guides operators in real time,",color=INK,fontsize=11,ha="center",va="center")
ax.text(W/2,66,"offline on any HMI, while the PLC stays in control and every answer is backed by evidence.”",color=GREEN,fontsize=11,ha="center",va="center",fontweight="bold")
pdf.savefig(fig); plt.close(fig)

pdf.close(); print("PDF written")
