#!/usr/bin/env bash
# One-minute end-to-end check (synthetic d = 3 memory): simulate, calibrate, track, decode, print numbers.
# Usage: scripts/smoke_test.sh            (activate the conda env first: conda activate qec)
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/smoke_test.py "$@"
