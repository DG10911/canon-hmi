#!/usr/bin/env python3
"""Convert DOSSIER.md -> styled HTML for Chrome print-to-PDF."""
import re, html as ihtml

md = open("DOSSIER.md", encoding="utf-8").read()

def inline(s):
    s = ihtml.escape(s)
    # links [t](u)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'<a href="\2">\1</a>', s)
    # bold **x**
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    # inline code `x`
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    return s

lines = md.split("\n")
out = []
i = 0
n = len(lines)
def flush_para(buf):
    if buf:
        out.append("<p>"+inline(" ".join(buf))+"</p>")
        buf.clear()

para = []
in_list = False
while i < n:
    ln = lines[i]
    # table: header line followed by |---| separator
    if ln.strip().startswith("|") and i+1 < n and re.match(r'^\s*\|[\s:|-]+\|\s*$', lines[i+1]):
        flush_para(para)
        if in_list: out.append("</ul>"); in_list=False
        header = [c.strip() for c in ln.strip().strip("|").split("|")]
        rows = []
        i += 2
        while i < n and lines[i].strip().startswith("|"):
            rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
            i += 1
        t = ["<table><thead><tr>"] + [f"<th>{inline(h)}</th>" for h in header] + ["</tr></thead><tbody>"]
        for r in rows:
            t.append("<tr>"+"".join(f"<td>{inline(c)}</td>" for c in r)+"</tr>")
        t.append("</tbody></table>")
        out.append("".join(t))
        continue
    m = re.match(r'^(#{1,4})\s+(.*)$', ln)
    if m:
        flush_para(para)
        if in_list: out.append("</ul>"); in_list=False
        lvl = len(m.group(1)); out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
        i += 1; continue
    if re.match(r'^\s*---+\s*$', ln):
        flush_para(para)
        if in_list: out.append("</ul>"); in_list=False
        out.append("<hr/>"); i += 1; continue
    lm = re.match(r'^\s*[-*]\s+(.*)$', ln)
    if lm:
        flush_para(para)
        if not in_list: out.append("<ul>"); in_list=True
        out.append("<li>"+inline(lm.group(1))+"</li>"); i += 1; continue
    if ln.strip()=="":
        flush_para(para)
        if in_list: out.append("</ul>"); in_list=False
        i += 1; continue
    para.append(ln.strip()); i += 1
flush_para(para)
if in_list: out.append("</ul>")
body = "\n".join(out)

CSS = """
@page { size: A4; margin: 16mm 14mm 16mm 14mm; }
*{box-sizing:border-box}
body{font-family:'Helvetica Neue',Arial,sans-serif;color:#1a2430;font-size:10.5px;line-height:1.5;margin:0}
.cover{background:linear-gradient(135deg,#0d3320,#0a2418);color:#fff;padding:60px 44px;border-radius:0;margin:-0 0 26px 0}
.cover h1{font-size:34px;margin:0 0 6px;color:#fff;letter-spacing:-.5px}
.cover .g{color:#3DCD58}
.cover .sub{font-size:14px;color:#bfe9d8;margin-top:4px}
.cover .meta{margin-top:22px;font-size:11px;color:#9fd8bb;line-height:1.7}
.cover .badge{display:inline-block;background:#3DCD58;color:#04160d;font-weight:800;padding:4px 12px;border-radius:20px;font-size:11px;margin-bottom:14px;letter-spacing:.5px}
h1{font-size:19px;color:#0d3320;border-bottom:2px solid #3DCD58;padding-bottom:4px;margin:22px 0 10px}
h2{font-size:15px;color:#12402a;margin:18px 0 8px}
h3{font-size:12.5px;color:#1a5636;margin:14px 0 6px}
h4{font-size:11px;color:#2a6b46;margin:10px 0 5px}
p{margin:6px 0}
ul{margin:6px 0 6px 18px;padding:0} li{margin:3px 0}
strong{color:#0d3320}
code{background:#eef3f0;border:1px solid #d5e2da;border-radius:3px;padding:0 4px;font-family:'SFMono-Regular',Consolas,monospace;font-size:9.5px;color:#0a6b3a}
a{color:#1f7a45;text-decoration:none;word-break:break-all}
hr{border:none;border-top:1px solid #d5e2da;margin:14px 0}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:9.3px}
th{background:#0d3320;color:#fff;text-align:left;padding:5px 7px;font-weight:700}
td{border:1px solid #d5e2da;padding:5px 7px;vertical-align:top}
tbody tr:nth-child(even){background:#f4f8f6}
h1,h2,h3{page-break-after:avoid}
table,tr{page-break-inside:avoid}
"""

COVER = """
<div class="cover">
  <div class="badge">SCHNEIDER HMI HACKATHON 2026 · PS2</div>
  <h1>CANON<span class="g">.</span> — Master Research Dossier</h1>
  <div class="sub">Dynamic HMI generation at runtime + machine control via HMI</div>
  <div class="meta">
    Team DigiSeva · Devansh Goenka · Panshul Arora · Tanmay Singh<br/>
    Compiled from a 6-agent / 4-model deep-research swarm (Opus · Sonnet · Haiku · Fable)<br/>
    Coverage: competitive landscape · standards &amp; machine-context models · prior-art &amp; patents ·
    ROI &amp; market · datasets &amp; data sources · technical build stack<br/>
    Evidence labelled VERIFIED / STRONG / INFERENCE · September 2026
  </div>
</div>
"""

full = f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{COVER}{body}</body></html>"
open("CANON_PS2_Research_Dossier.html","w",encoding="utf-8").write(full)
print("HTML written:", len(full), "bytes")
