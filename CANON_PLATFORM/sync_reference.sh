#!/usr/bin/env bash
# Part B — pull the reference corpus (939 OBSERVED signals from 23 real ICS/sensor
# datasets) from the acquisition run on the DGX into seed/. Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")"
HOST="${DGX_HOST:-dgx}"
REMOTE="${DGX_ACQ:-~/CANON_ACQUISITION}"

echo "Building compact reference bundle on $HOST ..."
ssh "$HOST" "cd $REMOTE && python3 - <<'PY'
import json
sig=[json.loads(l) for l in open('out/06_signals.jsonl')]
ext=[s for s in sig if s.get('origin')=='external-reference' or (s.get('kind')=='observed-series' and s.get('knowledge_state')=='CANDIDATE')]
keep={s.get('source') for s in ext}
src=[json.loads(l) for l in open('out/01_sources.jsonl') if json.loads(l).get('source_id') in keep]
cols=('signalId','column','observedMin','observedMax','samples','source','kind','knowledge_state')
open('out/reference_signals.jsonl','w').write(''.join(json.dumps({k:s.get(k) for k in cols})+'\n' for s in ext))
open('out/reference_sources.jsonl','w').write(''.join(json.dumps({k:s.get(k) for k in ('source_id','title','publisher','license','source_url')})+'\n' for s in src))
json.dump(json.load(open('out/corpus_manifest.json')).get('reference_datasets',{}),open('out/reference_meta.json','w'),indent=1)
print('reference:',len(ext),'signals /',len(src),'datasets')
PY"

echo "Pulling into seed/ ..."
scp -q "$HOST:$REMOTE/out/reference_signals.jsonl" \
       "$HOST:$REMOTE/out/reference_sources.jsonl" \
       "$HOST:$REMOTE/out/reference_meta.json" seed/
echo "Done. $(wc -l < seed/reference_signals.jsonl) reference signals in seed/."
