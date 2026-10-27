#!/usr/bin/env bash
# Reproduce one cell of the detect2 simulation study (results section F3; figures/detect2_figure.png).
# Usage: scripts/reproduce_sim_detect2.sh CELL [PROCS] [--quick]
#   CELL  0..5 = p=1e-3 hom, 2e-3 hom, 3e-3 hom, 1e-3 het, 2e-3 het, 3e-3 het   (primary cells: 1 2 4 5)
#   PROCS number of worker processes (default 10)
#   --quick  pipeline check only (2 000 test / 1 000 calibration shots, no CNN) - not the frozen protocol
# Full cell: ~40 000 test shots, ~450 s for the ALL tracker on 12 cores plus the other 8 tracker variants and the CNN
# (PyTorch); allow a few hours per cell. Outputs: det2/<cell>/ (restart-safe, cached per stage).
# All six cells, then:  python code/detect2/aggregate_detect2.py && python code/detect2/fig_detect2.py
set -euo pipefail
cd "$(dirname "$0")/.."
CELL="${1:?usage: $0 CELL [PROCS] [--quick]}"; PROCS="${2:-10}"; shift $(( $# > 1 ? 2 : 1 ))
EXTRA="$*"
for STAGE in sim track cnn decode analyze; do
  echo "== cell $CELL stage $STAGE"
  python code/detect2/run_detect2.py --cell "$CELL" --stage "$STAGE" --procs "$PROCS" $EXTRA
done
