"""Relative change in logical failure probability vs A per run, with paired bootstrap 95% CI (2000 resamples, seed 42)."""
import json, os, numpy as np, sys
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
from run_ibm_stab import RUNS
rng = np.random.default_rng(42); out = {}
for r in RUNS:
    d = f"{paths.IBMSTAB}/{r}"; F = {n: np.load(f"{d}/fail_{n}.npy").astype(bool) for n in ["A", "X", "A4", "P", "Xold", "Adec", "Xdec"] if os.path.exists(f"{d}/fail_{n}.npy")}
    res = json.load(open(f"{d}/results.json")); N = len(F["A"]); B = rng.integers(0, N, (2000, N)) if N <= 100000 else None
    row = dict(T=res["T"], detfrac=res["detfrac"], pL=res["pL_mean"], p_ret=res["p_ret"], dLL=res["dLL_per_shot"], mean_pi=res["mean_pi"])
    for n, base in [("X", "A"), ("A4", "A"), ("P", "A"), ("Xold", "A"), ("Xdec", "Adec"), ("Adec", "A")]:
        if n not in F or base not in F: continue
        a, x = F[base], F[n]; rel = x.mean() / a.mean() - 1
        bs = []
        for k in range(0, 2000, 200):
            idx = B[k:k + 200]; bs.append(x[idx].mean(1) / a[idx].mean(1) - 1)
        bs = np.concatenate(bs); row[f"{n}_vs_{base}"] = [float(rel), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
    out[r] = row
json.dump(out, open(f"{paths.RESULTS_DATA}/ibmstab_figdata.json", "w"), indent=1)
for r, v in out.items(): print(r, {k: [round(x, 3) for x in vv] if isinstance(vv, list) else round(vv, 4) for k, vv in v.items()})
