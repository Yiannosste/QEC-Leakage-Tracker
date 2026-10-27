"""EXPLORATORY (post hoc, not in the frozen protocol): A and X on a stronger matching graph in which the shipped
3-/4-detector mechanisms are decomposed into graph edges using the decomposition of the authors' template circuit.
Tracker posteriors are reused unchanged from post.npz.  Usage: python code/ibm_stability/robust_dec.py --run T20 --procs 12"""
import sys, os, json, numpy as np, argparse, multiprocessing as mp
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
import stim
from gnnrnn import circuits
import run_ibm_stab as R
from leakage_sim import FlagMatcher
from scipy.stats import binomtest

def decomposed_dem(shipped, T):
    tmpl = circuits.stability_circuit(T, 1e-3).detector_error_model(decompose_errors=True)
    dec = {}
    for ins in tmpl.flattened():
        if ins.type != "error": continue
        comps, cur = [], []
        for t in ins.targets_copy():
            if t.is_separator(): comps.append(cur); cur = []
            else: cur.append(t)
        comps.append(cur)
        dets = frozenset(t.val for t in ins.targets_copy() if t.is_relative_detector_id())
        obs = frozenset(t.val for t in ins.targets_copy() if t.is_logical_observable_id())
        if len(comps) > 1: dec.setdefault((dets, obs), comps)
    out = stim.DetectorErrorModel(); nsplit = nmiss = 0
    for ins in shipped.flattened():
        if ins.type != "error": out.append(ins); continue
        tg = ins.targets_copy()
        key = (frozenset(t.val for t in tg if t.is_relative_detector_id()), frozenset(t.val for t in tg if t.is_logical_observable_id()))
        nd = len(key[0])
        if nd > 2 and key in dec:
            tl = []
            for i, c in enumerate(dec[key]):
                if i: tl.append(stim.target_separator())
                tl += c
            out.append("error", ins.args_copy(), tl); nsplit += 1
        else:
            if nd > 2: nmiss += 1
            out.append(ins)
    return out, nsplit, nmiss

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run"); ap.add_argument("--procs", type=int, default=12); a = ap.parse_args()
    out = f"{R.OUT}/{a.run}"; f = f"{out}/robust_dec.json"
    if os.path.exists(f): sys.exit()
    T, dem, lc, dets, cal, test = R.setup(a.run)
    ddem, nsplit, nmiss = decomposed_dem(dem, T); lcd = lc._lc.with_dem(ddem)
    obs = stim.read_shot_data_file(path=f"{R.ROOT}/{a.run}/logical_flips.b8", format="b8", num_detectors=0, num_observables=1)[:, 0].astype(bool)
    ot, td, N = obs[test], dets[test], len(test)
    z = np.load(f"{out}/post.npz"); PL, PR = z["pl"], z["pr"]
    A = FlagMatcher(lcd).decode_plain(td)[:, 0].astype(bool) != ot
    R.G.update(fm=FlagMatcher(lcd), td=td); pred = np.zeros(N, bool)
    with R.pool(a.procs) as p:
        for lo, pr_ in p.imap_unordered(R._dec, [(lo, PL[lo:hi], PR[lo:hi]) for lo, hi in R.chunks(N, 500)]): pred[lo:lo + len(pr_)] = pr_
    X = pred != ot
    A0 = np.load(f"{out}/fail_A.npy").astype(bool)
    def mc(x, y):
        b = int((~x & y).sum()); c = int((x & ~y).sum()); return [b, c, float(binomtest(b, b + c, 0.5).pvalue) if b + c else 1.0]
    res = dict(run=a.run, nsplit=nsplit, nmiss=nmiss, pfail=dict(A=float(A0.mean()), Adec=float(A.mean()), Xdec=float(X.mean())),
               Xdec_vs_Adec=mc(X, A), Adec_vs_A=mc(A, A0))
    np.save(f"{out}/fail_Adec.npy", A.astype(np.uint8)); np.save(f"{out}/fail_Xdec.npy", X.astype(np.uint8))
    json.dump(res, open(f, "w")); print(json.dumps(res))
