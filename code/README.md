# code/

I first wrote these scripts for one flat working folder. To make them work in this layout, every script now
starts with

```python
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
```

`code/paths.py` adds `code/sim`, `code/tracker`, `code/detect2`, `code/ibm_stability`, `code/ibm_memory`,
`code/miami_v3` and `data/modular-gnn-rnn-decoder` (the authors' `gnnrnn` package, see `docs/DATA.md`) to
`sys.path`, and defines where data and outputs live:

| name in `paths.py` | default | environment variable |
|---|---|---|
| `DATA` | `<repo>/data` | `LT_DATA` |
| `OUT` (parent of `det2/`, `ibmstab/`, `miamirep/`) | `<repo>` | `LT_OUT` |
| `IBM_BERLIN`, `IBM_BERLIN_STAB`, `MIAMI`, `GOOGLE2023`, `WILLOW` | under `DATA` | |
| `RESULTS_DATA`, `FIGURES` | `<repo>/results/data`, `<repo>/figures` | |

So `python code/detect2/run_detect2.py --help` and `python code/ibm_stability/run_ibm_stab.py --help` work from
any directory with nothing set.

If you import the modules yourself (notebook, tests), set this from the repository root:

```bash
export PYTHONPATH=code:code/sim:code/tracker:code/detect2:code/ibm_stability:code/ibm_memory:code/miami_v3:data/modular-gnn-rnn-decoder
```

I tested both ways: `--help` of both runners, and `import run_detect2, run_ibm_stab, run_cell, dev_v3, miami_io, run_miami`
with that `PYTHONPATH`.

Module map:

| folder | file | role |
|---|---|---|
| sim | `leakage_sim.py` | Stim circuit plus the leakage model; `FlagMatcher` (MWPM with per-shot soft edge weights); `per_round`, `wilson` |
| sim | `hmm_tracker.py`, `cnn_tracker.py` | the old trackers (F2); the CNN needs PyTorch |
| sim | `detmetrics.py` | AP, AUC, precision, recall and Brier score of leakage posteriors against the true flags |
| sim | `run_cell.py` | one grid-G1 cell (F2) |
| tracker | `xa_tracker.py` | `XATracker`, the ALL tracker (v2): explaining away, both bases, mean-field, Baum-Welch |
| tracker | `xa_tracker_r.py` | variant R (readout explaining away for no-reset circuits), part of v3 |
| tracker | `gen_leaky.py`, `gen_leaky2.py` | adapters that give any Stim circuit the `LeakyCircuit` interface (with reset / without reset) |
| detect2 | `run_detect2.py`, `aggregate_detect2.py`, `fig_detect2.py` | F3 |
| ibm_stability | `run_ibm_stab.py`, `aggregate_ibmstab.py`, `ibmstab_figdata.py`, `fig_ibmstab.py`, `robust_dec.py`, `synth_stab.py` | F5 |
| ibm_memory | `ibm_common.py`, `ibm_tracker.py`, `run_ibm.py`, `stats_ibm.py`, `diag.py`, `hmm_params_q36T50.json` | F4 (old per-detector tracker; its parameters are also the X_old control in F5) |
| miami_v3 | `zero_leak_reset.py`, `synth_miami.py`, `dev_v3.py`, `dev_v3b.py`, `confirm_v3.py`, `oracle_check.py`, `miami_io.py`, `run_miami.py` | F6; `run_miami.py` was never run on real ibm_miami outcomes |
| | `figstyle.py` | matplotlib settings for the two figure scripts |
