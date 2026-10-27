"""paths.py - the one place where the scripts learn where things are.

Importing this module (a) puts every code/ sub-folder on sys.path, so `from leakage_sim import ...`,
`from xa_tracker import ...`, `from gen_leaky import ...` work from any working directory, and (b) defines the
data and output directories.  All of them can be moved with environment variables:

    LT_DATA   root of the downloaded hardware data   (default: <repo>/data,  see docs/DATA.md)
    LT_OUT    root for large intermediate outputs     (default: <repo>; gives <repo>/det2, <repo>/ibmstab, ...)

Scripts start with the two lines
    import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    import paths
which is all that is needed.  Alternatively set PYTHONPATH as documented in code/README.md.
"""
import os, sys

CODE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(CODE)
DATA = os.path.abspath(os.environ.get("LT_DATA", os.path.join(REPO, "data")))
OUT = os.path.abspath(os.environ.get("LT_OUT", REPO))

# code folders (order matters only for name clashes; there are none)
SUBDIRS = ["sim", "tracker", "detect2", "ibm_stability", "ibm_memory", "miami_v3"]
# the authors' repository for ibm_berlin (provides the `gnnrnn` package: stability circuit + scale_noise)
GNNRNN_REPO = os.path.join(DATA, "modular-gnn-rnn-decoder")

for sub in SUBDIRS + [GNNRNN_REPO]:
    p = sub if os.path.isabs(sub) else os.path.join(CODE, sub)
    if p not in sys.path:
        sys.path.append(p)

# hardware data (docs/DATA.md)
IBM_BERLIN = os.path.join(DATA, "ibm_berlin")                  # Zenodo 23335425, unzipped
IBM_BERLIN_STAB = os.path.join(IBM_BERLIN, "stability_d3")
MIAMI = os.path.join(DATA, "miami", "paper_repo")               # Zenodo 21336494, unzipped
GOOGLE2023 = os.path.join(DATA, "google2023")                   # Zenodo 6804040
WILLOW = os.path.join(DATA, "willow")                           # Zenodo 13273331

# outputs (ignored by git)
DET2 = os.path.join(OUT, "det2")
IBMSTAB = os.path.join(OUT, "ibmstab")
MIAMIREP = os.path.join(OUT, "miamirep")
RESULTS_DATA = os.path.join(REPO, "results", "data")
FIGURES = os.path.join(REPO, "figures")

# small parameter file of the OLD per-detector IBM tracker (used as the X_old control in the stability test)
HMM_PARAMS_OLD = os.path.join(CODE, "ibm_memory", "hmm_params_q36T50.json")


def need(path, what):
    """Fail with a readable message instead of a FileNotFoundError deep inside Stim."""
    if not os.path.exists(path):
        raise SystemExit(f"{what} not found at {path}. See docs/DATA.md (set LT_DATA to move the data root).")
    return path
