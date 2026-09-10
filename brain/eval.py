#!/usr/bin/env python3
"""
CANON brain — evaluation against held-out machines.

Metrics that matter for CANON (not just token loss):
  • JSON-valid rate        — did it emit parseable JSON?
  • Binding-validity rate  — do ALL refs exist in the machine model?
  • Hallucination rate     — % outputs that invented ≥1 tag (the number to drive to ~0)
  • Widget-F1 vs teacher   — overlap with the compiler's correct widget set

  python eval.py --base Qwen/Qwen2.5-Coder-7B-Instruct --adapter out/canon-brain --data data/eval.jsonl
  # or evaluate a served endpoint:  python eval.py --endpoint http://localhost:11434/v1 --model canon-brain
"""
import argparse, json, re

def refs_in_user(user):
    names=set()
    for ln in user.splitlines():
        ln=ln.strip()
        if ln.startswith("- "): names.add(ln[2:].split(" ")[0])
    for m in re.findall(r"command:[^\s]+", user): names.add(m)
    return names

def wset(widgets):
    return {(w.get("type"),w.get("ref","")) for w in widgets}

def gen_local(base, adapter, prompts):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    tok=AutoTokenizer.from_pretrained(base)
    m=AutoModelForCausalLM.from_pretrained(base, device_map="auto", torch_dtype=torch.bfloat16)
    if adapter: m=PeftModel.from_pretrained(m, adapter)
    outs=[]
    for msgs in prompts:
        ids=tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").to(m.device)
        o=m.generate(ids, max_new_tokens=512, do_sample=False)
        outs.append(tok.decode(o[0][ids.shape[1]:], skip_special_tokens=True))
    return outs

def gen_endpoint(base_url, model, prompts):
    import httpx
    outs=[]
    with httpx.Client(timeout=90) as c:
        for msgs in prompts:
            r=c.post(f"{base_url}/chat/completions", json={"model":model,"messages":msgs,"temperature":0})
            outs.append(r.json()["choices"][0]["message"]["content"])
    return outs

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base"); ap.add_argument("--adapter"); ap.add_argument("--endpoint"); ap.add_argument("--model")
    ap.add_argument("--data", default="data/eval.jsonl"); ap.add_argument("--n", type=int, default=100)
    a=ap.parse_args()
    rows=[json.loads(l) for l in open(a.data)][:a.n]
    prompts=[r["messages"][:2] for r in rows]
    gens=(gen_endpoint(a.endpoint,a.model,prompts) if a.endpoint else gen_local(a.base,a.adapter,prompts))

    jok=bok=halluc=0; f1s=[]
    for r,g in zip(rows,gens):
        names=refs_in_user(r["messages"][1]["content"])
        gold=wset(json.loads(r["messages"][2]["content"])["widgets"])
        try:
            j=re.search(r"\{.*\}", g, re.S).group(0); pred=json.loads(j); jok+=1
        except Exception:
            continue
        w=pred.get("widgets",[])
        invalid=[x.get("ref") for x in w if x.get("ref") and x["ref"] not in names]
        if not invalid: bok+=1
        else: halluc+=1
        pset=wset(w)
        inter=len(pset&gold); prec=inter/len(pset) if pset else 0; rec=inter/len(gold) if gold else 1
        f1s.append(2*prec*rec/(prec+rec) if (prec+rec) else 0)
    n=len(rows)
    print(f"n={n}")
    print(f"JSON-valid      : {jok/n*100:5.1f}%")
    print(f"Binding-valid   : {bok/n*100:5.1f}%   (all refs exist in model)")
    print(f"Hallucination   : {halluc/n*100:5.1f}%   (drive to ~0)")
    print(f"Widget-F1 vs teacher: {sum(f1s)/max(1,len(f1s)):.3f}")

if __name__=="__main__": main()
