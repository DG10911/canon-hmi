#!/usr/bin/env python3
"""Build EcoDrive Intelligence 4-slide deck -> PDF (matplotlib) for Schneider HMI Hackathon Round 1."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.backends.backend_pdf import PdfPages

# Brand palette
GREEN = "#3DCD58"      # Schneider Life Green
DARK  = "#1A1A1A"
GREY  = "#4D4D4D"
LGREY = "#E9ECEF"
MGREY = "#CED4DA"
WHITE = "#FFFFFF"
BLUE  = "#2B6CB0"

W, H = 1000.0, 563.0  # 16:9 canvas units

def newpage():
    fig = plt.figure(figsize=(13.333, 7.5), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H)
    ax.axis("off"); ax.set_facecolor(WHITE)
    fig.patch.set_facecolor(WHITE)
    return fig, ax

def band(ax):
    ax.add_patch(FancyBboxPatch((0, H-14), W, 14, boxstyle="square,pad=0",
                fc=GREEN, ec="none", zorder=1))
    ax.add_patch(FancyBboxPatch((0, 0), W, 22, boxstyle="square,pad=0",
                fc=DARK, ec="none", zorder=1))

def foot(ax, page):
    ax.text(16, 11, "Confidential Property of Schneider Electric  |  Schneider Electric HMI Hackathon 2026",
            color=WHITE, fontsize=8.5, va="center", ha="left")
    ax.text(W-16, 11, f"Page {page}", color=WHITE, fontsize=8.5, va="center", ha="right")

def title(ax, txt):
    ax.text(28, H-40, txt, color=DARK, fontsize=25, fontweight="bold", va="center")
    ax.add_patch(FancyBboxPatch((28, H-56), 150, 4, boxstyle="square,pad=0", fc=GREEN, ec="none"))

def box(ax, x, y, w, h, text, fc=WHITE, ec=GREEN, tc=DARK, fs=10.5, bold=True,
        lw=1.6, round=0.02, align="center"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=2,rounding_size={round*300}",
                fc=fc, ec=ec, lw=lw, zorder=3))
    ha = {"center": ("center", x+w/2), "left": ("left", x+8)}[align]
    ax.text(ha[1], y+h/2, text, color=tc, fontsize=fs, fontweight="bold" if bold else "normal",
            va="center", ha=ha[0], zorder=4, linespacing=1.25)

def arrow(ax, p1, p2, color=GREY, lw=2.0, label=None, ls="-"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=16,
                color=color, lw=lw, ls=ls, zorder=2, shrinkA=2, shrinkB=2))
    if label:
        mx, my = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
        ax.text(mx, my+7, label, color=BLUE, fontsize=7.8, ha="center", va="bottom",
                fontweight="bold", zorder=5)

pdf = PdfPages("/Users/devanshgoenka/conductor/workspaces/dgrfrfeerf/santo-domingo/.context/EcoDrive_Intelligence_Round1.pdf")

# ================= SLIDE 1 : TITLE =================
fig, ax = newpage(); band(ax)
ax.add_patch(FancyBboxPatch((0, 150), W, 250, boxstyle="square,pad=0", fc=LGREY, ec="none", zorder=0))
ax.text(W/2, 360, "EcoDrive Intelligence", color=DARK, fontsize=46, fontweight="bold", ha="center", va="center")
ax.text(W/2, 315, "Smart PLC – HMI – VFD – Energy Management System",
        color=GREEN, fontsize=19, fontweight="bold", ha="center", va="center")
ax.text(W/2, 290, "for Real-Time Industrial Energy Optimization", color=GREY, fontsize=15, ha="center", va="center")
ax.text(W/2, 250, "Schneider Electric HMI Hackathon  —  Round 1 Proposed Solution",
        color=DARK, fontsize=12, ha="center", va="center", style="italic")
# team block
box(ax, 250, 95, 500, 42, "Team Name :  <Your Team Name>", fc=DARK, ec=GREEN, tc=WHITE, fs=15)
ax.text(W/2, 68, "Member 1 : <Name>, <Dept>          Member 2 : <Name>, <Dept>          Member 3 : <Name>, <Dept>",
        color=DARK, fontsize=10.5, ha="center", va="center")
ax.text(W/2, 46, "Departments: EIE / ECE / CSE (interdisciplinary)   •   Batch 2027–2030",
        color=GREY, fontsize=9, ha="center", va="center")
foot(ax, 1); pdf.savefig(fig); plt.close(fig)

# ================= SLIDE 2 : ARCHITECTURE / APPROACH =================
fig, ax = newpage(); band(ax); title(ax, "Architecture / Approach"); foot(ax, 2)
# layer backgrounds (left ~58%)
LX, LW = 28, 560
layers = [("FIELD", 96, 126), ("CONTROL", 232, 82), ("EDGE", 324, 54), ("CLOUD", 388, 54)]
for name, y, h in layers:
    ax.add_patch(FancyBboxPatch((LX, y), LW, h, boxstyle="square,pad=0", fc=LGREY, ec=MGREY, lw=1, zorder=0))
    ax.text(LX+6, y+h-10, "LAYER – "+name, color=GREY, fontsize=8, fontweight="bold", va="center")
# Field devices
box(ax, LX+50, 112, 140, 44, "Pressure / Flow /\nLevel Transmitters", fs=8.5)
box(ax, LX+210, 112, 140, 44, "ATV630 VFD\n↔ Motor + Pump", fs=8.5)
box(ax, LX+370, 112, 150, 44, "PowerLogic PM5300\nEnergy Meter", fs=8.5)
# Control
box(ax, LX+110, 248, 160, 46, "Modicon M241\nPLC (IEC 61131-3)", fs=9)
box(ax, LX+300, 248, 150, 46, "Harmony GTU\nHMI (ISA-101)", fs=9)
arrow(ax, (LX+270, 271), (LX+300, 271), color=GREEN, lw=2.2)
# Edge / Cloud
box(ax, LX+150, 330, 260, 42, "Edge Gateway (Harmony IPC)\nLocal historian + analytics", fs=9)
box(ax, LX+150, 394, 260, 42, "EcoStruxure Machine Advisor\nRemote dashboards • OEE • alerts", fs=9, ec=BLUE)
# vertical arrows w/ protocol labels
arrow(ax, (LX+280, 156), (LX+190, 246), color=GREY, lw=2, label="Modbus TCP / 4–20 mA")
arrow(ax, (LX+280, 294), (LX+280, 328), color=GREY, lw=2, label="Modbus TCP")
arrow(ax, (LX+280, 372), (LX+280, 392), color=BLUE, lw=2, label="MQTT / TLS")
# Right column : approach
RX = 632
ax.text(RX, 430, "Approach", color=DARK, fontsize=14, fontweight="bold", va="center")
ax.add_patch(FancyBboxPatch((RX, 420), 92, 3, boxstyle="square,pad=0", fc=GREEN, ec="none"))
bullets = [
    "Use case: friction-dominated water pumping\nstation (30 kW, variable demand).",
    "VFD speed control replaces valve throttling\n→ cube-law savings (P ∝ N³).",
    "Savings calibrated to the real system curve\n(static vs. friction head) — honest, verifiable.",
    "Closed loop: SENSE → CONTROL → VISUALIZE →\nANALYZE → OPTIMIZE → ACT → LEARN.",
    "Modbus TCP common layer — native to all four\nSchneider devices.",
]
yy = 398
for b in bullets:
    ax.text(RX, yy, "▶", color=GREEN, fontsize=9, va="top", fontweight="bold")
    ax.text(RX+16, yy, b, color=GREY, fontsize=9.3, va="top", linespacing=1.3)
    yy -= 47
# headline KPI strip (bottom, clear of diagram)
pills = ["~46%  Energy ↓", "SEC 0.58→0.31 kWh/m³", "₹4–6 L / year saved", "Payback < 2 years"]
pw = 224; gap = 12; x0 = 28
for i, p in enumerate(pills):
    box(ax, x0+i*(pw+gap), 38, pw, 42, p, fc=GREEN, ec=GREEN, tc=WHITE, fs=11.5)
pdf.savefig(fig); plt.close(fig)

# ================= SLIDE 3 : OVERALL SEQUENCE FLOW =================
fig, ax = newpage(); band(ax); title(ax, "Overall Sequence Flow"); foot(ax, 3)
nodes = [
    ("SENSE", "PM5300 + ATV630\n+ PT / FT / LT"),
    ("CONTROL", "PLC PID + SIL 3 STO\n+ sequencing"),
    ("VISUALIZE", "ISA-101 HMI\noverview / energy / alarms"),
    ("ANALYZE", "SEC + system-curve\n+ pattern detection"),
    ("OPTIMIZE", "tune ATV630 Sleep /\nEnergy-Adapt + recos"),
    ("ACT", "operator approves\nvia HMI"),
    ("LEARN", "baseline + curve\nrefinement"),
]
# two rows: 4 on top, 3 on bottom, serpentine
bw, bh = 200, 66
topy, boty = 380, 250
xs_top = [28 + i*(bw+16) for i in range(4)]
xs_bot = [28 + i*(bw+16) for i in range(3)]
centers = []
for i, (name, det) in enumerate(nodes):
    if i < 4:
        x, y = xs_top[i], topy
    else:
        x, y = xs_bot[i-4], boty
    ax.add_patch(FancyBboxPatch((x, y), bw, bh, boxstyle="round,pad=2,rounding_size=8",
                fc=GREEN if i in (0,4) else WHITE, ec=GREEN, lw=2, zorder=3))
    ax.text(x+bw/2, y+bh-18, name, color=WHITE if i in (0,4) else DARK, fontsize=12.5,
            fontweight="bold", ha="center", va="center", zorder=4)
    ax.text(x+bw/2, y+20, det, color=WHITE if i in (0,4) else GREY, fontsize=8.6,
            ha="center", va="center", zorder=4, linespacing=1.2)
    centers.append((x, y, bw, bh))
# arrows top row L->R
for i in range(3):
    a = centers[i]; b = centers[i+1]
    arrow(ax, (a[0]+a[2], a[1]+bh/2), (b[0], b[1]+bh/2), color=GREY, lw=2)
# down arrow 4->5 (node4 top-right area to node5 bottom-right)
a = centers[3]; b = centers[4]
arrow(ax, (a[0]+a[2]/2, a[1]), (a[0]+a[2]/2, boty+bh), color=GREY, lw=2)
arrow(ax, (a[0]+a[2]/2, boty+bh/2), (b[0]+b[2], boty+bh/2), color=GREY, lw=2)  # into node5 right side
# bottom row R->L : 5->6->7
for i in (4,5):
    a = centers[i]; b = centers[i+1]
    arrow(ax, (a[0], a[1]+bh/2), (b[0]+b[2], b[1]+bh/2), color=GREY, lw=2)
# LEARN -> SENSE feedback (dashed up-left)
a = centers[6]; b = centers[0]
arrow(ax, (a[0]+a[2]/2, a[1]+bh), (b[0]+b[2]/2, b[1]), color=BLUE, lw=2, ls=(0,(5,4)), label="feedback loop")
# PLC state strip
ax.text(28, 205, "PLC control sequence:", color=DARK, fontsize=10, fontweight="bold", va="center")
states = ["IDLE","PRE-CHECK","SOFT-START","RUNNING (PID)","SOFT-STOP","FAULT (STO)"]
sw = 140; sx = 28
for i, s in enumerate(states):
    box(ax, sx+i*(sw+10), 150, sw, 34, s, fc=LGREY, ec=MGREY, tc=DARK, fs=9, lw=1.2)
    if i < len(states)-1:
        arrow(ax, (sx+i*(sw+10)+sw, 167), (sx+(i+1)*(sw+10), 167), color=GREY, lw=1.6)
# coverage callout
ax.add_patch(FancyBboxPatch((28, 96), W-56, 34, boxstyle="round,pad=2,rounding_size=6",
            fc=DARK, ec=DARK, zorder=3))
ax.text(W/2, 113, "Covers all 7 objectives:  Comms → Control → HMI → Energy Dashboard → Alarms (ISA-18.2) → Optimization → IoT",
        color=WHITE, fontsize=10.5, ha="center", va="center", fontweight="bold", zorder=4)
pdf.savefig(fig); plt.close(fig)

# ================= SLIDE 4 : TOOLS USED =================
fig, ax = newpage(); band(ax); title(ax, "Tools Used"); foot(ax, 4)
cols = [
    ("Schneider Hardware", [
        "Modicon M241 — PLC",
        "Harmony GTU — HMI",
        "Altivar Process ATV630 — VFD",
        "   (SIL 3 STO, Sleep Mode,",
        "    embedded energy monitor)",
        "PowerLogic PM5300 — meter",
        "Acti9 iEM3155 — sub-meter",
        "Pressure / Flow / Level Tx",
        "ConneXium managed switch",
    ], GREEN),
    ("Software & Protocols", [
        "EcoStruxure Machine Expert",
        "   (IEC 61131-3 – ST/FBD/SFC/LD)",
        "Vijeo Designer / Operator",
        "   Terminal Expert (HMI)",
        "EcoStruxure Machine Advisor",
        "   (IoT / cloud)",
        "Modbus TCP/RTU • EtherNet/IP",
        "MQTT/TLS • OPC UA • 4–20 mA",
        "Prototype: Node-RED • Grafana",
        "   • Raspberry Pi / ESP32",
    ], BLUE),
    ("Standards Applied", [
        "ISA-101 — High-Perf HMI",
        "ISA-18.2 / IEC 62682 — Alarms",
        "IEC 61131-3 — PLC languages",
        "IEC 61508 — Functional safety",
        "   (Safe Torque Off)",
        "IEEE 519 — Harmonics / THD",
        "ISO 50001 — Energy mgmt",
        "IEC 62443 — OT cybersecurity",
    ], DARK),
]
cw = 300; gap = 20; x0 = 28; ytop = 400; colh = 330
for i, (head, items, c) in enumerate(cols):
    x = x0 + i*(cw+gap)
    ax.add_patch(FancyBboxPatch((x, ytop-colh), cw, colh, boxstyle="round,pad=2,rounding_size=8",
                fc=WHITE, ec=MGREY, lw=1.4, zorder=2))
    ax.add_patch(FancyBboxPatch((x, ytop-40), cw, 40, boxstyle="round,pad=2,rounding_size=8",
                fc=c, ec=c, zorder=3))
    ax.text(x+cw/2, ytop-20, head, color=WHITE, fontsize=12.5, fontweight="bold", ha="center", va="center", zorder=4)
    yy = ytop-64
    for it in items:
        sub = it.startswith("   ")
        ax.text(x+16, yy, ("" if sub else "• ")+it.strip(), color=GREY if sub else DARK,
                fontsize=9.2 if not sub else 8.4, va="center",
                style="italic" if sub else "normal")
        yy -= 27
# bottom note
ax.add_patch(FancyBboxPatch((28, 44), W-56, 36, boxstyle="round,pad=2,rounding_size=6",
            fc=LGREY, ec=GREEN, lw=1.4, zorder=2))
ax.text(W/2, 62, "Entire solution built on Schneider Electric's EcoStruxure ecosystem  •  demo-ready via open-source edge stack for Round 2",
        color=DARK, fontsize=10, ha="center", va="center", fontweight="bold", zorder=4)
pdf.savefig(fig); plt.close(fig)

pdf.close()
print("PDF written.")
