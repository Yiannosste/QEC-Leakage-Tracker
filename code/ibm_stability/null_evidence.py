"""C7 check: null distribution of the label-free evidence. For one ibm_berlin stability run, sample leak-free shots from the
SHIPPED p_ij DEM, run the frozen calibration (12 Baum-Welch iterations, same settings as run_ibm_stab.py) and report
ll_fit - ll_null per shot, next to the real-data value from ibmstab/<run>/calib.json.
Usage: python3 code/ibm_stability/null_evidence.py --run T20 --seed 1 --procs 12
Output: <LT_OUT>/ibmstab/<run>/null_evidence_seed<seed>.json (summary: results/ibmstab/null_evidence_summary.md)."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
import json, time, argparse, numpy as np, multiprocessing as mp
import stim
import run_ibm_stab as R
from xa_tracker import XATracker
G = R.G
def _stats(a): lo, hi = a; return G["tr"].loglik_and_stats(G["cd"][lo:hi], None, passes=G["tr"].passes)
ap = argparse.ArgumentParser(); ap.add_argument("--run"); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--procs", type=int, default=12)
a = ap.parse_args(); out = f"{paths.IBMSTAB}/{a.run}/null_evidence_seed{a.seed}.json"
if os.path.exists(out): sys.exit()
T, dem, lc, dets, cal, test = R.setup(a.run); ncal = len(cal)
nul = dem.compile_sampler(seed=1000 + a.seed).sample(ncal)[0].astype(bool)
t0 = time.time(); tr = XATracker(lc, basis="both", explain=True); tr.set_params(3e-3, 0.25, 0.5)
G.update(tr=tr, cd=nul); ch = R.chunks(ncal, max(50, 25000 // T))
def estep():
    with R.pool(a.procs) as p: accs = p.map(_stats, ch)
    return {k: sum(x[k] for x in accs) for k in accs[0]}
for it in range(12):
    s = estep(); pL = np.clip(s["n01"] / s["occ0"], 1e-6, 0.2); pr = float(np.clip(s["n10"] / max(s["occ1"], 1e-9), 1e-3, 1.0)); tr.set_params(pL, pr, 0.5)
ll_fit = float(estep()["ll"]) / ncal; fitted = (tr.p_L.copy(), tr.p_ret)
tr.set_params(1e-6, fitted[1], 0.5); ll_null = float(estep()["ll"]) / ncal
real = json.load(open(f"{paths.IBMSTAB}/{a.run}/calib.json"))
res = dict(run=a.run, T=T, seed=a.seed, ncal=ncal, null_detfrac=float(nul.mean()), real_detfrac=float(dets[cal].mean()),
           null_dLL=ll_fit - ll_null, real_dLL=real["ll_fit"] - real["ll_null"], null_pL=fitted[0].tolist(), null_p_ret=fitted[1],
           real_pL=real["p_L"], real_p_ret=real["p_ret"], seconds=time.time() - t0)
json.dump(res, open(out, "w")); print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.items() if k not in ("null_pL", "real_pL")}), flush=True)
