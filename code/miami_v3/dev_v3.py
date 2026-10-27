"""dev_v3.py - synthetic development harness for tracker v3 (rules: v3_dev_protocol.md).
Usage: python3 dev_v3.py SCENARIO SEED   (SCENARIO in N1 L1 H1 N2 L2 N3 H3) -> one JSON line per guard on stdout."""
import sys, os, json, time, pickle, numpy as np, multiprocessing as mp
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
from leakage_sim import LeakyCircuit, FlagMatcher
from gen_leaky2 import NoResetLeakyCircuit, fit_noise_scale
from xa_tracker import XATracker
from scipy.stats import binomtest

PROCS = 12; G = {}
TrackerCls = XATracker   # dev_v3b sets this to XATrackerR for variant R
HOT = (2, 6)   # data-qubit indices that carry the long-lived state in H scenarios


def pool(): return mp.get_context("fork").Pool(PROCS)
def chunks(N, size): return [(lo, min(N, lo + size)) for lo in range(0, N, size)]


def scenario(name, seed):
    """Returns dict(model=lc used by tracker+decoder, data=(test dets, obs, L), cal=cal dets, null=fn(n, seed) -> leak-free dets from the MODEL)."""
    rng_seed = seed
    if name in ("N1", "L1", "H1"):
        lc = LeakyCircuit(3, 25, 2e-3); data_lc = lc; Ntest, Ncal = 20000, 8000
    elif name in ("N4", "H4"):   # diagnostic only: ibm_berlin stability circuit, T = 50, uniform p = 6e-3 (reset)
        from gnnrnn import circuits as _c; from gen_leaky import GenLeakyCircuit
        lc = GenLeakyCircuit(_c.stability_circuit(50, 6e-3)); data_lc = lc; Ntest, Ncal = 20000, 4000
    else:
        C = pickle.load(open(os.path.join(paths.MIAMI, 'inputs', 'fig10', 'circuits.pkl'), 'rb'))
        sc = C['codes'][3][1]; Ntest, Ncal = 12000, 3000
        if name in ("N3", "H3"):
            from gnnrnn.circuits import scale_noise
            data_lc = NoResetLeakyCircuit(scale_noise(sc, 1.7)); lc = None
        else:
            data_lc = NoResetLeakyCircuit(sc); lc = data_lc
    nq = data_lc.nq
    if name[0] == "N": pL, tau = np.zeros(nq), 8.0
    elif name[0] == "L": pL, tau = np.full(nq, 1e-3), 8.0
    else: pL = np.zeros(nq); pL[list(HOT)] = 3e-3; tau = 40.0
    def samp(lcx, n, s):
        if pL.max() == 0:
            d, o = lcx.base.compile_detector_sampler(seed=s).sample(n, separate_observables=True); return d, o, np.zeros((n, lcx.nq, lcx.rounds), np.uint8)
        return lcx.sample(n, pL, tau, seed=s)
    dets, obs, L = samp(data_lc, Ntest, rng_seed); cal = samp(data_lc, Ncal, rng_seed + 1)[0]
    info = {}
    if lc is None:   # label-free rescaling of the background model, fitted on calibration shots
        from gnnrnn.circuits import scale_noise
        s_fit = fit_noise_scale(sc, cal); info["s_fit"] = s_fit; lc = NoResetLeakyCircuit(scale_noise(sc, s_fit))
    null = lambda n, s: lc.base.compile_detector_sampler(seed=s).sample(n)
    return dict(model=lc, data=(dets, obs[:, 0], L), cal=cal, null=null, info=info, pL=pL, tau=tau)


def _stats(a): lo, hi = a; return G["tr"].loglik_and_stats(G["cd"][lo:hi], None, passes=G["tr"].passes)
def _post(a): lo, hi = a; pl, pr, pf = G["tr"].posteriors(G["td"][lo:hi]); return lo, pl, pr
def _qll(a):
    lo, hi = a; tr = G["tr"]; d = G["cd"][lo:hi]
    prev = tr.posteriors(d, None, passes=tr.passes)[0].astype(np.float64)
    return np.array([tr._run_qubit(q, d, None, prev)["ll"].sum() for q in tr.lc.data_qubits])
def _dec(a):
    lo, pl, pr = a; return lo, G["fm"].decode_with_posteriors(G["td"][lo:lo + len(pl)], pl, pr, pl[:, :, -1], thresh=0.02)[:, 0]


def em(lc, cd, cap=None):
    tr = TrackerCls(lc, basis="both", explain=True); tr.set_params(3e-3, 0.25, 0.5); G.update(tr=tr, cd=cd)
    for it in range(12):
        with pool() as p: accs = p.map(_stats, chunks(len(cd), max(20, 5000 // lc.rounds)))
        s = {k: sum(x[k] for x in accs) for k in accs[0]}
        pr = float(np.clip(s["n10"] / max(s["occ1"], 1e-9), 1e-3, 1.0))
        if cap is not None: pr = min(pr, cap)
        tr.set_params(np.clip(s["n01"] / s["occ0"], 1e-6, 0.2), pr, 0.5); G["tr"] = tr
    return tr


def qgain(tr, cd):
    """Per-qubit held-out log-likelihood gain of the fitted p_L over p_L = 1e-6 (same p_ret)."""
    pL, pr = tr.p_L.copy(), tr.p_ret; G.update(tr=tr, cd=cd)
    with pool() as p: fit = sum(p.map(_qll, chunks(len(cd), max(20, 5000 // tr.R))))
    tr.set_params(1e-6, pr, 0.5); G["tr"] = tr
    with pool() as p: nul = sum(p.map(_qll, chunks(len(cd), max(20, 5000 // tr.R))))
    tr.set_params(pL, pr, 0.5)
    return fit - nul


def evaluate(lc, tr, dets, obs, A):
    G.update(tr=tr, td=dets, fm=FlagMatcher(lc)); N = len(dets); R = lc.rounds
    PL = np.zeros((N, lc.nq, R), np.float32); PR = np.zeros_like(PL)
    with pool() as p:
        for lo, pl, pr in p.imap_unordered(_post, chunks(N, max(20, 5000 // R))): PL[lo:lo + len(pl)] = pl; PR[lo:lo + len(pl)] = pr
    X = np.zeros(N, bool)
    with pool() as p:
        for lo, pr_ in p.imap_unordered(_dec, [(lo, PL[lo:hi], PR[lo:hi]) for lo, hi in chunks(N, 250)]): X[lo:lo + len(pr_)] = pr_ != obs[lo:lo + len(pr_)]
    b = int((~X & A).sum()); c = int((X & ~A).sum())
    return dict(X=float(X.mean()), X_only=b, A_only=c, p=float(binomtest(b, b + c, 0.5).pvalue) if b + c else 1.0, mean_pi=float(PL.mean()))


def main():
    global TrackerCls
    name, seed = sys.argv[1], int(sys.argv[2]); t0 = time.time()
    TAG = os.environ.get('TRACKER', 'base')
    if TAG == 'R':
        from xa_tracker_r import XATrackerR; TrackerCls = XATrackerR
    S = scenario(name, seed); lc = S["model"]; dets, obs, L = S["data"]; cal = S["cal"]
    A = FlagMatcher(lc).decode_plain(dets)[:, 0] != obs
    base = dict(scenario=name, seed=seed, tracker=TAG, A=float(A.mean()), detfrac=round(float(dets.mean()), 4), **S["info"])
    h1, h2 = cal[: len(cal) // 2], cal[len(cal) // 2:]
    nul = S["null"](len(cal), seed + 2); n1, n2 = nul[: len(nul) // 2], nul[len(nul) // 2:]
    for cap in (None, 0.25):
        tr_full = em(lc, cal, cap)
        r = evaluate(lc, tr_full, dets, obs, A)
        print(json.dumps(dict(base, guard="G0" if cap is None else "G1", pL=tr_full.p_L.round(5).tolist(), p_ret=round(tr_full.p_ret, 3), **r)), flush=True)
        # G2: per-qubit held-out gain vs the maximum per-qubit gain on leak-free data simulated from the model
        g_real = qgain(em(lc, h1, cap), h2); g_null = qgain(em(lc, n1, cap), n2); thr = float(g_null.max())
        keep = g_real > thr; pLk = np.where(keep, tr_full.p_L, 1e-6)
        tr_full.set_params(pLk, tr_full.p_ret, 0.5)
        r = evaluate(lc, tr_full, dets, obs, A) if keep.any() else dict(X=float(A.mean()), X_only=0, A_only=0, p=1.0, mean_pi=0.0)
        print(json.dumps(dict(base, guard="G2" if cap is None else "G12", keep=keep.astype(int).tolist(), gain=g_real.round(2).tolist(),
                              thr=round(thr, 2), pL=pLk.round(5).tolist(), p_ret=round(tr_full.p_ret, 3), **r)), flush=True)
    print(json.dumps(dict(base, guard="done", seconds=round(time.time() - t0))), flush=True)


if __name__ == "__main__":
    main()
