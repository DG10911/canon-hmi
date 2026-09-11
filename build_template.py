#!/usr/bin/env python3
"""Fill the official Schneider Hackathon template with EcoDrive Intelligence content.
Renders body-only diagrams (no title/footer -- template supplies those) and injects them."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
import copy

BASE = "/Users/devanshgoenka/conductor/workspaces/dgrfrfeerf/santo-domingo/.context"
TPL  = BASE + "/attachments/vMDEcU/Hackathon_SE_Template.pptx"

GREEN="#3DCD58"; DARK="#1A1A1A"; GREY="#4D4D4D"; LGREY="#E9ECEF"; MGREY="#CED4DA"; WHITE="#FFFFFF"; BLUE="#2B6CB0"
W,H=1000.0,563.0

def canvas():
    fig=plt.figure(figsize=(13.333,7.5),dpi=220)
    ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,W); ax.set_ylim(0,H); ax.axis("off")
    fig.patch.set_alpha(0); ax.set_facecolor("none")
    return fig,ax

def box(ax,x,y,w,h,text,fc=WHITE,ec=GREEN,tc=DARK,fs=10.5,bold=True,lw=1.6,rs=6,align="center"):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f"round,pad=2,rounding_size={rs}",fc=fc,ec=ec,lw=lw,zorder=3))
    if align=="center": ha,hx="center",x+w/2
    else: ha,hx="left",x+8
    ax.text(hx,y+h/2,text,color=tc,fontsize=fs,fontweight="bold" if bold else "normal",va="center",ha=ha,zorder=4,linespacing=1.25)

def arrow(ax,p1,p2,color=GREY,lw=2.0,label=None,ls="-"):
    ax.add_patch(FancyArrowPatch(p1,p2,arrowstyle="-|>",mutation_scale=16,color=color,lw=lw,ls=ls,zorder=2,shrinkA=2,shrinkB=2))
    if label:
        ax.text((p1[0]+p2[0])/2,(p1[1]+p2[1])/2+7,label,color=BLUE,fontsize=7.8,ha="center",va="bottom",fontweight="bold",zorder=5)

# ---------- body drawings (no title/footer) ----------
def body_arch(ax):
    LX,LW=20,600
    for name,y,h in [("FIELD",96,126),("CONTROL",232,82),("EDGE",324,54),("CLOUD",388,54)]:
        ax.add_patch(FancyBboxPatch((LX,y),LW,h,boxstyle="square,pad=0",fc=LGREY,ec=MGREY,lw=1,zorder=0))
        ax.text(LX+6,y+h-10,"LAYER – "+name,color=GREY,fontsize=8,fontweight="bold",va="center")
    box(ax,LX+55,112,150,44,"Pressure / Flow /\nLevel Transmitters",fs=8.5)
    box(ax,LX+225,112,150,44,"ATV630 VFD\n↔ Motor + Pump",fs=8.5)
    box(ax,LX+395,112,160,44,"PowerLogic PM5300\nEnergy Meter",fs=8.5)
    box(ax,LX+120,248,170,46,"Modicon M241\nPLC (IEC 61131-3)",fs=9)
    box(ax,LX+320,248,160,46,"Harmony GTU\nHMI (ISA-101)",fs=9)
    arrow(ax,(LX+290,271),(LX+320,271),color=GREEN,lw=2.2)
    box(ax,LX+160,330,280,42,"Edge Gateway (Harmony IPC)\nLocal historian + analytics",fs=9)
    box(ax,LX+160,394,280,42,"EcoStruxure Machine Advisor\nRemote dashboards • OEE • alerts",fs=9,ec=BLUE)
    arrow(ax,(LX+300,156),(LX+205,246),color=GREY,lw=2,label="Modbus TCP / 4–20 mA")
    arrow(ax,(LX+300,294),(LX+300,328),color=GREY,lw=2,label="Modbus TCP")
    arrow(ax,(LX+300,372),(LX+300,392),color=BLUE,lw=2,label="MQTT / TLS")
    RX=670
    ax.text(RX,432,"Approach",color=DARK,fontsize=14,fontweight="bold",va="center")
    ax.add_patch(FancyBboxPatch((RX,422),92,3,boxstyle="square,pad=0",fc=GREEN,ec="none"))
    for i,b in enumerate([
        "Use case: friction-dominated water\npumping station (30 kW).",
        "VFD speed control replaces valve\nthrottling → cube-law savings (P ∝ N³).",
        "Savings calibrated to the real system\ncurve (static vs. friction head).",
        "Closed loop: SENSE → CONTROL →\nVISUALIZE → ANALYZE → OPTIMIZE →\nACT → LEARN.",
        "Modbus TCP common layer — native to\nall four Schneider devices.",
    ]):
        y=400-i*52
        ax.text(RX,y,"▶",color=GREEN,fontsize=9,va="top",fontweight="bold")
        ax.text(RX+16,y,b,color=GREY,fontsize=9.2,va="top",linespacing=1.3)
    pills=["~46%  Energy ↓","SEC 0.58→0.31 kWh/m³","₹4–6 L / year saved","Payback < 2 years"]
    pw=238;gap=12;x0=20
    for i,p in enumerate(pills):
        box(ax,x0+i*(pw+gap),34,pw,44,p,fc=GREEN,ec=GREEN,tc=WHITE,fs=11.5)

def body_flow(ax):
    nodes=[("SENSE","PM5300 + ATV630\n+ PT / FT / LT"),("CONTROL","PLC PID + SIL 3 STO\n+ sequencing"),
        ("VISUALIZE","ISA-101 HMI\noverview / energy / alarms"),("ANALYZE","SEC + system-curve\n+ pattern detection"),
        ("OPTIMIZE","tune ATV630 Sleep /\nEnergy-Adapt + recos"),("ACT","operator approves\nvia HMI"),
        ("LEARN","baseline + curve\nrefinement")]
    bw,bh=228,66; topy,boty=372,250
    xs=[20+i*(bw+18) for i in range(4)]
    C=[]
    for i,(n,d) in enumerate(nodes):
        x,y=(xs[i],topy) if i<4 else (xs[i-4],boty)
        fc=GREEN if i in (0,4) else WHITE; tc=WHITE if i in (0,4) else DARK
        ax.add_patch(FancyBboxPatch((x,y),bw,bh,boxstyle="round,pad=2,rounding_size=8",fc=fc,ec=GREEN,lw=2,zorder=3))
        ax.text(x+bw/2,y+bh-18,n,color=tc,fontsize=12.5,fontweight="bold",ha="center",va="center",zorder=4)
        ax.text(x+bw/2,y+20,d,color=(WHITE if i in(0,4) else GREY),fontsize=8.6,ha="center",va="center",zorder=4,linespacing=1.2)
        C.append((x,y,bw,bh))
    for i in range(3): arrow(ax,(C[i][0]+bw,C[i][1]+bh/2),(C[i+1][0],C[i+1][1]+bh/2))
    a=C[3]; arrow(ax,(a[0]+bw/2,a[1]),(a[0]+bw/2,boty+bh))
    arrow(ax,(a[0]+bw/2,boty+bh/2),(C[4][0]+bw,boty+bh/2))
    for i in (4,5): arrow(ax,(C[i][0],C[i][1]+bh/2),(C[i+1][0]+bw,C[i+1][1]+bh/2))
    arrow(ax,(C[6][0]+bw/2,C[6][1]+bh),(C[0][0]+bw/2,C[0][1]),color=BLUE,lw=2,ls=(0,(5,4)),label="feedback loop")
    ax.text(20,205,"PLC control sequence:",color=DARK,fontsize=10,fontweight="bold",va="center")
    states=["IDLE","PRE-CHECK","SOFT-START","RUNNING (PID)","SOFT-STOP","FAULT (STO)"]
    sw=152;sx=20
    for i,s in enumerate(states):
        box(ax,sx+i*(sw+10),150,sw,34,s,fc=LGREY,ec=MGREY,tc=DARK,fs=9,lw=1.2)
        if i<5: arrow(ax,(sx+i*(sw+10)+sw,167),(sx+(i+1)*(sw+10),167),color=GREY,lw=1.6)
    ax.add_patch(FancyBboxPatch((20,96),W-40,34,boxstyle="round,pad=2,rounding_size=6",fc=DARK,ec=DARK,zorder=3))
    ax.text(W/2,113,"Covers all 7 objectives:  Comms → Control → HMI → Energy Dashboard → Alarms (ISA-18.2) → Optimization → IoT",
        color=WHITE,fontsize=10.5,ha="center",va="center",fontweight="bold",zorder=4)

def body_tools(ax):
    cols=[("Schneider Hardware",["Modicon M241 — PLC","Harmony GTU — HMI","Altivar Process ATV630 — VFD",
        "   (SIL 3 STO, Sleep Mode,","    embedded energy monitor)","PowerLogic PM5300 — meter",
        "Acti9 iEM3155 — sub-meter","Pressure / Flow / Level Tx","ConneXium managed switch"],GREEN),
        ("Software & Protocols",["EcoStruxure Machine Expert","   (IEC 61131-3 – ST/FBD/SFC/LD)","Vijeo Designer / Operator",
        "   Terminal Expert (HMI)","EcoStruxure Machine Advisor","   (IoT / cloud)","Modbus TCP/RTU • EtherNet/IP",
        "MQTT/TLS • OPC UA • 4–20 mA","Prototype: Node-RED • Grafana","   • Raspberry Pi / ESP32"],BLUE),
        ("Standards Applied",["ISA-101 — High-Perf HMI","ISA-18.2 / IEC 62682 — Alarms","IEC 61131-3 — PLC languages",
        "IEC 61508 — Functional safety","   (Safe Torque Off)","IEEE 519 — Harmonics / THD","ISO 50001 — Energy mgmt",
        "IEC 62443 — OT cybersecurity"],DARK)]
    cw=316;gap=16;x0=20;ytop=430;colh=350
    for i,(head,items,c) in enumerate(cols):
        x=x0+i*(cw+gap)
        ax.add_patch(FancyBboxPatch((x,ytop-colh),cw,colh,boxstyle="round,pad=2,rounding_size=8",fc=WHITE,ec=MGREY,lw=1.4,zorder=2))
        ax.add_patch(FancyBboxPatch((x,ytop-40),cw,40,boxstyle="round,pad=2,rounding_size=8",fc=c,ec=c,zorder=3))
        ax.text(x+cw/2,ytop-20,head,color=WHITE,fontsize=12.5,fontweight="bold",ha="center",va="center",zorder=4)
        yy=ytop-66
        for it in items:
            sub=it.startswith("   ")
            ax.text(x+16,yy,("" if sub else "• ")+it.strip(),color=GREY if sub else DARK,
                fontsize=8.4 if sub else 9.2,va="center",style="italic" if sub else "normal")
            yy-=28
    ax.add_patch(FancyBboxPatch((20,34),W-40,38,boxstyle="round,pad=2,rounding_size=6",fc=LGREY,ec=GREEN,lw=1.4,zorder=2))
    ax.text(W/2,53,"Entire solution built on Schneider Electric's EcoStruxure ecosystem  •  demo-ready via open-source edge stack for Round 2",
        color=DARK,fontsize=10,ha="center",va="center",fontweight="bold",zorder=4)

def render_body(fn,drawer):
    fig,ax=canvas(); drawer(ax)
    tmp=BASE+"/_tmp.png"; fig.savefig(tmp,transparent=True,dpi=220); plt.close(fig)
    im=mpimg.imread(tmp)
    # autocrop to non-transparent bbox
    alpha=im[:,:,3] if im.shape[2]==4 else np.ones(im.shape[:2])
    rows=np.where(alpha.max(axis=1)>0.02)[0]; cols=np.where(alpha.max(axis=0)>0.02)[0]
    pad=8
    r0,r1=max(rows.min()-pad,0),min(rows.max()+pad,im.shape[0]); c0,c1=max(cols.min()-pad,0),min(cols.max()+pad,im.shape[1])
    crop=im[r0:r1,c0:c1]
    out=BASE+"/"+fn; mpimg.imsave(out,crop)
    return out,(c1-c0),(r1-r0)

imgs={}
imgs[2]=render_body("body_arch.png",body_arch)
imgs[3]=render_body("body_flow.png",body_flow)
imgs[4]=render_body("body_tools.png",body_tools)

# ---------- inject into template ----------
prs=Presentation(TPL)
sl=prs.slides

# slide 1 : fill team text
def set_text(shape,txt,size=None,bold=None,color=None):
    tf=shape.text_frame; tf.paragraphs[0].runs
    # clear then set
    p=tf.paragraphs[0]
    for r in list(p.runs): r.text=""
    if p.runs: run=p.runs[0]
    else: run=p.add_run()
    run.text=txt
    if size: run.font.size=Pt(size)
    if bold is not None: run.font.bold=bold
    if color: run.font.color.rgb=RGBColor.from_string(color)

s1=sl[0]
# positions for the 3 member cards (rectangle bg + its text box), laid out in a row
member_pos={  # shape-name -> (left_in, top_in)
    "Rectangle 22":(0.7,5.05),  "TextBox 23":(0.7,5.05),   # Member 1
    "Rectangle 28":(5.2,5.05),  "TextBox 29":(5.2,5.05),   # Member 2
    "Rectangle 25":(9.7,5.05),  "TextBox 26":(9.7,5.05),   # Member 3
}
for sh in s1.shapes:
    nm=sh.name
    if nm in member_pos:
        sh.left=Inches(member_pos[nm][0]); sh.top=Inches(member_pos[nm][1])
    if not sh.has_text_frame: continue
    t=sh.text_frame.text
    if t.startswith("Team Name"): set_text(sh,"Team Name : <Your Team Name>")
    elif t.strip()=="Team Member-1 Name": set_text(sh,"Member 1 : <Name>, <Dept>")
    elif t.strip()=="Team Member-2 Name": set_text(sh,"Member 2 : <Name>, <Dept>")
    elif t.strip()=="Team Member-3 Name": set_text(sh,"Member 3 : <Name>, <Dept>")
# project subtitle placed in clean white space near the bottom (dark header banner fills the top 3.87")
tb=s1.shapes.add_textbox(Inches(1.2),Inches(6.02),Inches(10.93),Inches(0.85))
tf=tb.text_frame; tf.word_wrap=True
p=tf.paragraphs[0]; p.alignment=2; r=p.add_run()
r.text="EcoDrive Intelligence"; r.font.size=Pt(24); r.font.bold=True; r.font.color.rgb=RGBColor.from_string(DARK.strip("#"))
p2=tf.add_paragraph(); p2.alignment=2; r2=p2.add_run()
r2.text="Smart PLC–HMI–VFD–Energy Management for Real-Time Industrial Energy Optimization"
r2.font.size=Pt(12); r2.font.color.rgb=RGBColor.from_string(GREEN.strip("#")); r2.font.bold=True

# slides 2,3,4 : place body image below the title bar
# content zone: top 1.55", bottom 7.05"  -> height 5.5", width 12.8" centred
ZONE_TOP=1.5; ZONE_BOT=7.05; ZONE_L=0.28; ZONE_W=12.77
for idx in (2,3,4):
    s=sl[idx-1]
    path,pw,ph=imgs[idx]
    ar=pw/ph
    w=ZONE_W; h=w/ar
    zh=ZONE_BOT-ZONE_TOP
    if h>zh:
        h=zh; w=h*ar
    left=Inches(ZONE_L+(ZONE_W-w/914400*914400 if False else 0))  # placeholder
    # center horizontally
    left=Inches(ZONE_L+(ZONE_W-w)/2) if w< ZONE_W else Inches(ZONE_L)
    top=Inches(ZONE_TOP+(zh-h)/2)
    s.shapes.add_picture(path,left,top,width=Inches(w),height=Inches(h))

out=BASE+"/EcoDrive_Intelligence_Round1_TEMPLATE.pptx"
prs.save(out)
print("saved",out)
