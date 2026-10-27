"""Zero-leakage control for RESET circuits: d=5 rotated memory (detect2 setting) or the ibm_berlin stability circuit.
Usage: zero_leak_reset.py memory|stability p N [T]"""
import sys, json, numpy as np, multiprocessing as mp
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
from leakage_sim import LeakyCircuit, FlagMatcher
from xa_tracker import XATracker
kind, p, N = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
if kind == 'memory': lc = LeakyCircuit(5, 25, p)
else:
    from gnnrnn import circuits; from gen_leaky import GenLeakyCircuit
    lc = GenLeakyCircuit(circuits.stability_circuit(int(sys.argv[4]), p))
R = lc.rounds; ds = lc.base.compile_detector_sampler(seed=99)
dets, obs = ds.sample(N, separate_observables=True); cd = lc.base.compile_detector_sampler(seed=98).sample(max(2000, 200000 // R))
G = {}; P = lambda: mp.get_context('fork').Pool(12)
def stats(a): lo, hi = a; return G['tr'].loglik_and_stats(cd[lo:hi], None, passes=G['tr'].passes)
def post(a): lo, hi = a; pl, pr, pf = G['tr'].posteriors(dets[lo:hi]); return lo, pl, pr
def dec(a): lo, pl, pr = a; return lo, G['fm'].decode_with_posteriors(dets[lo:lo+len(pl)], pl, pr, pl[:, :, -1], thresh=0.02)[:, 0]
fm = FlagMatcher(lc); G['fm'] = fm; A = fm.decode_plain(dets)[:, 0] != obs[:, 0]
tr = XATracker(lc, basis='both', explain=True); G['tr'] = tr; tr.set_params(3e-3, 0.25, 0.5)
for it in range(12):
    with P() as pp: accs = pp.map(stats, [(lo, min(len(cd), lo + 200)) for lo in range(0, len(cd), 200)])
    s = {k: sum(x[k] for x in accs) for k in accs[0]}
    tr.set_params(np.clip(s['n01'] / s['occ0'], 1e-6, 0.2), float(np.clip(s['n10'] / max(s['occ1'], 1e-9), 1e-3, 1)), 0.5)
ch = [(lo, min(N, lo + 250)) for lo in range(0, N, 250)]; PL = np.zeros((N, lc.nq, R), np.float32); PR = np.zeros_like(PL)
with P() as pp:
    for lo, pl, pr in pp.imap_unordered(post, ch): PL[lo:lo+len(pl)] = pl; PR[lo:lo+len(pl)] = pr
X = np.zeros(N, bool)
with P() as pp:
    for lo, pr_ in pp.imap_unordered(dec, [(lo, PL[lo:hi], PR[lo:hi]) for lo, hi in ch]): X[lo:lo+len(pr_)] = pr_ != obs[lo:lo+len(pr_), 0]
print(json.dumps(dict(kind=kind, p=p, N=N, R=R, detfrac=round(float(dets.mean()), 3), em_pL_mean=float(tr.p_L.mean()), em_pL_max=float(tr.p_L.max()),
                      em_pret=round(tr.p_ret, 3), mean_pi=float(PL.mean()), A=float(A.mean()), X=float(X.mean()), X_only_right=int((~X & A).sum()), A_only_right=int((X & ~A).sum()))))
