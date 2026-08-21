#!/usr/bin/env bash
# Everything that must pass before content ships.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=.

echo "== tests =="
python3 -m pytest tests/ -q

echo
echo "== provenance gate =="
python3 tools/provenance_gate.py

echo
echo "== corpus drift =="
python3 - <<'EOF'
from tools.generate_corpus import CORPUS, stale_open
from tools.open_shelf import stems
drift = stale_open(CORPUS)
print("open shelf:", ", ".join(sorted(stems())))
print("corpus is current" if not drift else "STALE: " + ", ".join(drift))
EOF

echo
echo "== reading folios =="
python3 -m tools.build_folios
