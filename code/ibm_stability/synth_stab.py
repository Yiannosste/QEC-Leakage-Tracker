import sys, time, json, numpy as np, multiprocessing as mp
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
from gnnrnn import circuits
from gen_leaky import GenLeakyCircuit
from leakage_sim import FlagMatcher
from xa_tracker import XATracker
from detmetrics import det_metrics
T, p, N, pL, tau = int(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
lc = GenLeakyCircuit(circuits.stability_circuit(T, p))
dets, obs, L = lc.sample(N, pL, tau, seed=777)
G = {}
def post(a):
    lo, hi = a; pl, pr, pf = G['tr'].posteriors(dets[lo:hi]); return lo, pl, pr
def dec(a):
    lo, pl, pr = a; return lo, G['fm'].decode_with_posteriors(dets[lo:lo+len(pl)], pl, pr, None, thresh=0.02)[:, 0]
def stats(a):
    lo, hi = a; return G['tr'].loglik_and_stats(cd[lo:hi], None, passes=G['tr'].passes)
ch = [(lo, min(N, lo+250)) for lo in range(0, N, 250)]
fm = FlagMatcher(lc); G['fm'] = fm
A = (fm.decode_plain(dets)[:, 0] != obs[:, 0])
res = dict(T=T, p=p, N=N, pL=pL, detfrac=round(float(dets.mean()),3), leaked_frac=float(L.mean()), A=float(A.mean()))
if True:
    P = lambda: mp.get_context('fork').Pool(12)
    B = np.zeros(N, bool)
    with P() as pool:
     for lo, pr_ in pool.imap_unordered(dec, [(lo, L[lo:hi].astype(np.float32), None) for lo, hi in ch]): B[lo:lo+len(pr_)] = pr_ != obs[lo:lo+len(pr_), 0]
    res['B'] = float(B.mean())
    for mode in ['true', 'em']:
        tr = XATracker(lc, basis='both', explain=True); G['tr'] = tr
        if mode == 'true': tr.set_params(max(pL,1e-6), 1/tau, 0.5)
        else:
            cd, _, _ = lc.sample(4000, pL, tau, seed=778); globals()['cd'] = cd
            tr.set_params(3e-3, 0.25, 0.5)
            for it in range(12):
                with P() as pool: accs = pool.map(stats, [(lo, min(4000, lo+250)) for lo in range(0, 4000, 250)])
                n01 = sum(x['n01'] for x in accs); occ0 = sum(x['occ0'] for x in accs); n10 = sum(x['n10'] for x in accs); occ1 = sum(x['occ1'] for x in accs)
                tr.set_params(np.clip(n01/occ0, 1e-6, 0.2), float(np.clip(n10/max(occ1,1e-9), 1e-3, 1)), 0.5)
            res['em_pL'] = tr.p_L.round(5).tolist(); res['em_pret'] = round(tr.p_ret, 3)
        t0 = time.time(); PL = np.zeros((N, lc.nq, T), np.float32); PR = np.zeros_like(PL)
        with P() as pool:
         for lo, pl, pr in pool.imap_unordered(post, ch): PL[lo:lo+len(pl)] = pl; PR[lo:lo+len(pl)] = pr
        X = np.zeros(N, bool)
        with P() as pool:
         for lo, pr_ in pool.imap_unordered(dec, [(lo, PL[lo:hi], PR[lo:hi]) for lo, hi in ch]): X[lo:lo+len(pr_)] = pr_ != obs[lo:lo+len(pr_), 0]
        dm = det_metrics(PL, L); f = (A.mean() - X.mean()) / max(A.mean() - B.mean(), 1e-9)
        res[mode] = dict(X=float(X.mean()), f=float(f), AP=round(dm['AP'], 3), prec=round(dm['precision'], 2), rec=round(dm['recall'], 2), sec=round(time.time()-t0))
print(json.dumps(res))
