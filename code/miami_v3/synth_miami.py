"""Synthetic check of the frozen tracker on an ibm_miami circuit (authors' calibration noise + injected data leakage).
Usage: synth_miami.py FIG INDEX N pL tau"""
import sys, time, json, pickle, numpy as np, multiprocessing as mp
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
from gen_leaky2 import NoResetLeakyCircuit
from leakage_sim import FlagMatcher
from xa_tracker import XATracker
from detmetrics import det_metrics
fig, ci, N, pL, tau = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
C = pickle.load(open(f'{paths.MIAMI}/inputs/{fig}/circuits.pkl', 'rb')); d, sc = C['codes'][ci][:2]
lc = NoResetLeakyCircuit(sc); R = lc.rounds
import os
SCALE = float(os.environ.get('SCALE', '1'))
if SCALE != 1:   # sample from a circuit whose every noise probability is multiplied by SCALE; decode with the original model
    from gnnrnn.circuits import scale_noise
    lcs = NoResetLeakyCircuit(scale_noise(sc, SCALE))
else: lcs = lc
dets, obs, L = lcs.sample(N, pL, tau, seed=4242) if pL > 0 else (*lcs.base.compile_detector_sampler(seed=4242).sample(N, separate_observables=True), np.zeros((N, lc.nq, R), np.uint8))
G = {}; P = lambda: mp.get_context('fork').Pool(12)
def post(a): lo, hi = a; pl, pr, pf = G['tr'].posteriors(dets[lo:hi]); return lo, pl, pr
def dec(a): lo, pl, pr = a; return lo, G['fm'].decode_with_posteriors(dets[lo:lo+len(pl)], pl, pr, None if pr is None else pl[:, :, -1], thresh=0.02)[:, 0]
def stats(a): lo, hi = a; return G['tr'].loglik_and_stats(G['cd'][lo:hi], None, passes=G['tr'].passes)
ch = [(lo, min(N, lo + 100)) for lo in range(0, N, 100)]
fm = FlagMatcher(lc); G['fm'] = fm
A = fm.decode_plain(dets)[:, 0] != obs[:, 0]
res = dict(scale=SCALE, fig=fig, case=str((C.get('case_index') or C.get('code_index') or C.get('index'))[ci]), depth=d, R=R, N=N, pL=pL, tau=tau, detfrac=round(float(dets.mean()), 3), A=float(A.mean()))
B = np.zeros(N, bool)
with P() as p:
    for lo, pr_ in p.imap_unordered(dec, [(lo, L[lo:hi].astype(np.float32), None) for lo, hi in ch]): B[lo:lo+len(pr_)] = pr_ != obs[lo:lo+len(pr_), 0]
res['B'] = float(B.mean())
tr = XATracker(lc, basis='both', explain=True); G['tr'] = tr
cd = lcs.sample(max(1000, 100000 // R), pL, tau, seed=4243)[0] if pL > 0 else lcs.base.compile_detector_sampler(seed=4243).sample(max(1000, 100000 // R))
if os.environ.get('FIT_SCALE') == '1':   # label-free rescaling of the background model, fitted on the calibration shots
    from gen_leaky2 import fit_noise_scale
    from gnnrnn.circuits import scale_noise
    s_fit = fit_noise_scale(sc, cd); res['s_fit'] = round(s_fit, 3)
    lc = NoResetLeakyCircuit(scale_noise(sc, s_fit)); fm = FlagMatcher(lc); G['fm'] = fm
    A = fm.decode_plain(dets)[:, 0] != obs[:, 0]; res['A_scaled'] = float(A.mean())
    tr = XATracker(lc, basis='both', explain=True); G['tr'] = tr
G['cd'] = cd; tr.set_params(3e-3, 0.25, 0.5); t0 = time.time()
for it in range(12):
    with P() as p: accs = p.map(stats, [(lo, min(len(cd), lo + 50)) for lo in range(0, len(cd), 50)])
    s = {k: sum(x[k] for x in accs) for k in accs[0]}
    tr.set_params(np.clip(s['n01'] / s['occ0'], 1e-6, 0.2), float(np.clip(s['n10'] / max(s['occ1'], 1e-9), 1e-3, 1)), 0.5)
res.update(em_pL_mean=float(tr.p_L.mean()), em_pL_max=float(tr.p_L.max()), em_pret=round(tr.p_ret, 3), em_sec=round(time.time() - t0))
PL = np.zeros((N, lc.nq, R), np.float32); PR = np.zeros_like(PL)
with P() as p:
    for lo, pl, pr in p.imap_unordered(post, ch): PL[lo:lo+len(pl)] = pl; PR[lo:lo+len(pl)] = pr
X = np.zeros(N, bool)
with P() as p:
    for lo, pr_ in p.imap_unordered(dec, [(lo, PL[lo:hi], PR[lo:hi]) for lo, hi in ch]): X[lo:lo+len(pr_)] = pr_ != obs[lo:lo+len(pr_), 0]
res['X'] = float(X.mean()); res['f'] = float((A.mean() - X.mean()) / max(A.mean() - B.mean(), 1e-9)) if pL > 0 else None
res['X_only_right'] = int((~X & A).sum()); res['A_only_right'] = int((X & ~A).sum())
if pL > 0: dm = det_metrics(PL, L); res.update(AP=round(dm['AP'], 3), prec=round(dm['precision'], 2), rec=round(dm['recall'], 2))
print(json.dumps(res))
