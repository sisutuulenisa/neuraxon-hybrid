#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "$ROOT_DIR/scripts/claim_gate.py" \
  --raw-dir "$ROOT_DIR/benchmarks/results/raw" \
  --protocol-doc "$ROOT_DIR/docs/TEST_PROTOCOL_PHASE1_2.md" \
  --claim-eval-doc "$ROOT_DIR/docs/CLAIM_EVAL_002.md" \
  --out "$ROOT_DIR/benchmarks/results/summary/claim_gate.json" \
  --strict-exit
