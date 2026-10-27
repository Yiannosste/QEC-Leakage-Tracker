#!/usr/bin/env bash
# Reproduce the pre-registered IBM ibm_berlin stability test (results section F5; figures/ibmstab_figure.png).
# Needs the data of docs/DATA.md in data/ibm_berlin/ and the authors' repository in data/modular-gnn-rnn-decoder/.
# Usage: scripts/reproduce_ibm_stability.sh [PROCS] [RUN ...]     (default: all 17 runs, 12 processes)
# Stages calib and track read only detection events; decode and analyze read the logical outcomes (as in the
# frozen protocol protocols/ibm_stab_protocol.md). ~15 min per T = 100 run on 12 cores. Outputs: ibmstab/<run>/.
set -euo pipefail
cd "$(dirname "$0")/.."
PROCS="${1:-12}"; shift || true
RUNS=("$@")
if [ ${#RUNS[@]} -eq 0 ]; then
  RUNS=(T5 T10 T20 T50 T100)
  for A in 0.15 0.3 0.45 0.6 0.8 1.0; do RUNS+=("T20_alpha$A" "T100_alpha$A"); done
fi
for RUN in "${RUNS[@]}"; do
  for STAGE in calib track decode analyze; do
    echo "== run $RUN stage $STAGE"
    python code/ibm_stability/run_ibm_stab.py --run "$RUN" --stage "$STAGE" --procs "$PROCS"
  done
done
python code/ibm_stability/aggregate_ibmstab.py        # pooled McNemar counts, pre-registered rules -> results/data/ibmstab_aggregate.json
python code/ibm_stability/ibmstab_figdata.py          # per-run relative changes with bootstrap CIs -> results/data/ibmstab_figdata.json
python code/ibm_stability/fig_ibmstab.py              # figures/ibmstab_figure.png
# optional, facts.md F9: null check of the label-free evidence (about 2 to 6 min per run)
# for RUN in T5 T10 T20 T50 T100 T20_alpha0.6 T100_alpha0.6 T100_alpha1.0; do python code/ibm_stability/null_evidence.py --run $RUN --seed 1 --procs "$PROCS"; done
