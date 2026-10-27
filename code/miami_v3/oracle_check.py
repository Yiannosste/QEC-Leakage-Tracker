import sys, json, numpy as np, multiprocessing as mp
import dev_v3 as D
from leakage_sim import FlagMatcher
from scipy.stats import binomtest
name, seed = sys.argv[1], int(sys.argv[2])
S = D.scenario(name, seed); lc = S['model']; dets, obs, L = S['data']
fm = FlagMatcher(lc); A = fm.decode_plain(dets)[:, 0] != obs
D.G.update(fm=fm, td=dets); N = len(dets)
def run(PL):
    X = np.zeros(N, bool)
    with D.pool() as p:
        for lo, pr_ in p.imap_unordered(D._dec, [(lo, PL[lo:hi], np.zeros_like(PL[lo:hi])) for lo, hi in D.chunks(N, 250)]): X[lo:lo+len(pr_)] = pr_ != obs[lo:lo+len(pr_)]
    b, c = int((~X & A).sum()), int((X & ~A).sum()); return dict(P=float(X.mean()), X_only=b, A_only=c, p=float(binomtest(b, b+c).pvalue) if b+c else 1)
Lf = L.astype(np.float32)
prev = np.concatenate([np.zeros_like(Lf[:, :, :1]), Lf[:, :, :-1]], 2); RET = np.clip(prev - Lf, 0, 1)
# oracle with true return flags
X = np.zeros(N, bool)
with D.pool() as p:
    for lo, pr_ in p.imap_unordered(D._dec, [(lo, Lf[lo:hi], RET[lo:hi]) for lo, hi in D.chunks(N, 250)]): X[lo:lo+len(pr_)] = pr_ != obs[lo:lo+len(pr_)]
b, c = int((~X & A).sum()), int((X & ~A).sum())
print(json.dumps(dict(scenario=name, A=float(A.mean()), leaked_frac=float(L.mean()), oracle=dict(P=float(X.mean()), X_only=b, A_only=c, p=float(binomtest(b, b+c).pvalue)))))
