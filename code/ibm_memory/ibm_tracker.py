"""Per-detector two-state HMM (N normal / H hot) on IBM detection events + per-shot soft time-like weights.
Syndromes only; no logical labels. See ibm_protocol.md."""
import numpy as np, pymatching, multiprocessing as mp
from scipy.optimize import minimize
from ibm_common import load, chains

def to_cube(det, ch, T=None):
    """det (N, nd) -> X (N, C, T) along chains (padded with -1 where a chain is shorter)."""
    T = T or max(len(c) for c in ch); N = det.shape[0]
    X = -np.ones((N, len(ch), T), np.int8)
    for j, c in enumerate(ch): X[:, j, :len(c)] = det[:, c]
    return X

def emis(X, r, s, q):
    p0 = np.clip(s * r, 1e-4, 0.999)              # (C,T)
    e0 = np.where(X == 1, p0, 1 - p0); e1 = np.where(X == 1, q, 1 - q)
    m = X < 0; e0 = np.where(m, 1.0, e0); e1 = np.where(m, 1.0, e1)
    return e0, e1

def forward(e0, e1, a, b):
    N, C, T = e0.shape; al = np.zeros((N, C, T, 2)); ll = np.zeros((N, C))
    f0, f1 = (1 - a) * e0[..., 0], a * e1[..., 0]
    for t in range(T):
        if t > 0:
            p0, p1 = al[:, :, t - 1, 0], al[:, :, t - 1, 1]
            f0 = (p0 * (1 - a) + p1 * b) * e0[..., t]; f1 = (p0 * a + p1 * (1 - b)) * e1[..., t]
        z = f0 + f1; al[:, :, t, 0] = f0 / z; al[:, :, t, 1] = f1 / z; ll += np.log(z)
    return al, ll

def backward_full(e0, e1, a, b):
    N, C, T = e0.shape; be = np.ones((N, C, T, 2))
    for t in range(T - 2, -1, -1):
        n0 = e0[..., t + 1] * be[:, :, t + 1, 0]; n1 = e1[..., t + 1] * be[:, :, t + 1, 1]
        b0 = (1 - a) * n0 + a * n1; b1 = b * n0 + (1 - b) * n1; z = b0 + b1
        be[:, :, t, 0] = b0 / z; be[:, :, t, 1] = b1 / z
    return be

def posterior(X, r, prm, lag):
    a, b, q, s = prm; e0, e1 = emis(X, r, s, q); al, _ = forward(e0, e1, a, b)
    N, C, T = X.shape
    if lag == 0: return al[..., 1]
    if lag == 'full':
        be = backward_full(e0, e1, a, b); g = al * be; return g[..., 1] / g.sum(-1)
    out = np.empty((N, C, T))
    for t in range(T):
        hi = min(T - 1, t + lag); v0 = np.ones((N, C)); v1 = np.ones((N, C))
        for u in range(hi, t, -1):
            n0 = e0[..., u] * v0; n1 = e1[..., u] * v1
            v0, v1 = (1 - a) * n0 + a * n1, b * n0 + (1 - b) * n1
            z = v0 + v1; v0, v1 = v0 / z, v1 / z
        g0 = al[:, :, t, 0] * v0; g1 = al[:, :, t, 1] * v1; out[:, :, t] = g1 / (g0 + g1)
    return out

def fit(X, r, x0=(0.01, 0.15, 0.6, 0.8)):
    def unpack(z): return [1 / (1 + np.exp(-v)) for v in z[:3]] + [np.exp(z[3])]
    def nll(z):
        a, b, q, s = unpack(z)
        if q < 0.2: return 1e12
        e0, e1 = emis(X, r, s, q); _, ll = forward(e0, e1, a, b); return -ll.sum()
    z0 = [np.log(x / (1 - x)) for x in x0[:3]] + [np.log(x0[3])]
    res = minimize(nll, z0, method='Nelder-Mead', options=dict(maxiter=400, xatol=1e-3, fatol=1.0))
    a, b, q, s = unpack(res.x)
    # null: one-state model (a=0) with free s
    r1 = minimize(lambda z: nll([-30, 0, 0, z[0]]), [np.log(1.0)], method='Nelder-Mead')
    return dict(a=a, b=b, q=q, s=s, nll=float(res.fun), nll_null=float(r1.fun), s_null=float(np.exp(r1.x[0])))

# ---------------- decoding ----------------
_G = {}
def _init(run, P, ch):
    dem, det, obs = load(run)
    m = pymatching.Matching.from_detector_error_model(dem)
    base = {}
    for u, v, d in m.edges():
        if v is None: continue
        base[(min(u, v), max(u, v))] = (float(d['weight']), set(d['fault_ids']))
    tl = []   # time-like edges: (u, v, chain j, round t)
    for j, c in enumerate(ch):
        for t in range(len(c) - 1):
            k = (c[t], c[t + 1])
            if k in base: tl.append((c[t], c[t + 1], j, t))
    _G.update(m=m, base=base, tl=np.array(tl, int), det=det)

def _decode_chunk(args):
    idx, PI, c, thr = args[:4]   # PI: (n, n_tl) edge posteriors for these shots
    pbar = args[4] if len(args) > 4 else None   # per-edge mean posterior -> deflated 'normal-state' base
    m, base, tl, det = _G['m'], _G['base'], _G['tl'], _G['det']
    if pbar is not None and 'pN' not in _G:
        pN = np.zeros(len(tl)); wN = np.zeros(len(tl))
        for e in range(len(tl)):
            w, f = base[(int(tl[e, 0]), int(tl[e, 1]))]; p0 = 1 / (1 + np.exp(w)); pa = c * pbar[e]
            pn = max((p0 - pa) / max(1 - 2 * pa, 1e-9), 1e-5); pN[e] = pn; wN[e] = np.log((1 - pn) / pn)
        _G['pN'] = pN; _G['wN'] = wN
        for e in range(len(tl)):   # install the deflated base permanently in this worker
            u, v = int(tl[e, 0]), int(tl[e, 1]); f = base[(u, v)][1]
            m.add_edge(u, v, fault_ids=f, weight=float(wN[e]), merge_strategy='replace')
        for e in range(len(tl)):
            u, v = int(tl[e, 0]), int(tl[e, 1]); base[(u, v)] = (float(wN[e]), base[(u, v)][1])
    out = np.zeros(len(idx), np.uint8)
    for k, s in enumerate(idx):
        sel = np.nonzero(PI[k] >= thr)[0]; touched = []
        for e in sel:
            u, v = int(tl[e, 0]), int(tl[e, 1]); w, f = base[(u, v)]
            p0 = 1 / (1 + np.exp(w)); pa = c * PI[k, e]; pn = min(p0 + pa - 2 * p0 * pa, 0.5 - 1e-6)
            m.add_edge(u, v, fault_ids=f, weight=float(np.log((1 - pn) / pn)), merge_strategy='replace'); touched.append((u, v))
        out[k] = m.decode(det[s])[0]
        for (u, v) in touched:
            w, f = base[(u, v)]; m.add_edge(u, v, fault_ids=f, weight=w, merge_strategy='replace')
    return out

def edge_post(pi, tl):
    """pi (N,C,T) -> (N, n_tl) with max of the two endpoint posteriors."""
    return np.maximum(pi[:, tl[:, 2], tl[:, 3]], pi[:, tl[:, 2], tl[:, 3] + 1])

def time_like_edges(run, ch):
    _init(run, None, ch); return _G['tl']
