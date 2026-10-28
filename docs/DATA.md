# Data needed to reproduce the hardware results

None of the hardware data are included in this repository. Download them into `data/` as below.

| dataset | record | file(s) | expected path | used for |
|---|---|---|---|---|
| IBM ibm_berlin (Lange et al., arXiv:2610.03869) | https://zenodo.org/records/23335425 | `ibm_berlin.zip` (200 MB) | `data/ibm_berlin/` (unzip, e.g. with Python `zipfile`) | pre-registered stability test (positive result), earlier memory test (null) |
| authors' circuits for ibm_berlin | https://github.com/LangeMoritz/modular-gnn-rnn-decoder | repository clone | `data/modular-gnn-rnn-decoder/` | stability circuit `circuits/stability_d3_X.stim` (layout for the adapter) |
| IBM ibm_miami (Drouet et al., arXiv:2607.12118) | https://zenodo.org/records/21336494 | `qec-defective-components.zip` (600 MB) | `data/miami/paper_repo/` | label-free checks and synthetic no-reset scenarios only (needs `qiskit` to unpickle `circuits.pkl`) |
| Google 2023 Sycamore | https://zenodo.org/records/6804040 | surface-code memory folders | `data/google2023/` | null result |
| Google 2025 Willow | https://zenodo.org/records/13273331 | `google_105Q_surface_code_d3_d5_d7.zip` (5.7 GB) | `data/willow/` | scope-null result |

Simulation results need no download: every script regenerates its data from Stim with the seeds written in the protocols.
