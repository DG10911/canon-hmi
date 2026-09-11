#!/usr/bin/env bash
# Batch-ingest every downloaded CSV into the CANON corpus as OBSERVED/CANDIDATE data.
# Run AFTER pull_datasets.sh (which needs huggingface-cli + kaggle auth).
#   ./ingest_all.sh ./downloads
set -euo pipefail
cd "$(dirname "$0")"
DL="${1:-./downloads}"
[ -d "$DL" ] || { echo "no such dir: $DL — run ./pull_datasets.sh ./downloads first"; exit 1; }
n=0
find "$DL" -type f \( -iname '*.csv' -o -iname '*.txt' \) | sort | while read -r f; do
  sid="EXT-$(basename "$f" | sed 's/\.[^.]*$//' | tr ' /.' '___')"
  echo ">> $f  ->  $sid"
  python3 ingest_external.py --csv "$f" --source-id "$sid" --name "$(basename "$f")" --sep , \
    || echo "   (skipped — non-comma or unparseable)"
  n=$((n+1))
done
echo "done — CANDIDATE/OBSERVED data written to ../out_external/  (never authoritative, §62)"
