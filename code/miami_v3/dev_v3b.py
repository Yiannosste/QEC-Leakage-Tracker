"""dev_v3b.py - like dev_v3.py but caches calibration fits and per-shot per-qubit gains, and evaluates G0, G2, G2b.
Usage: python3 dev_v3b.py SCENARIO SEED"""
import sys, os, json, time, numpy as np
import dev_v3 as D
from leakage_sim import FlagMatcher
from xa_tracker import XATracker

def _qll_shots(a):
    lo, hi = a; tr = D.G["tr"]; d = D.G["cd"][lo:hi]
    prev = tr.posteriors(d, None, passes=tr.passes)[0].astype(np.float64)
    return lo, np.stack([tr._run_qubit(q, d, None, prev)["ll"] for q in tr.lc.data_qubits], 1)

def qgain_shots(tr, cd):
    pL, pr = tr.p_L.copy(), tr.p_ret; out = {}
    for tag, pl in (("fit", pL), ("nul", 1e-6)):
        tr.set_params(pl, pr, 0.5); D.G.update(tr=tr, cd=cd); M = np.zeros((len(cd), tr.lc.nq))
        with D.pool() as p:
            for lo, m in p.imap_unordered(_qll_shots, D.chunks(len(cd), max(20, 5000 // tr.R))): M[lo:lo + len(m)] = m
        out[tag] = M
    tr.set_params(pL, pr, 0.5); return out["fit"] - out["nul"]

def main():
    name, seed = sys.argv[1], int(sys.argv[2]); t0 = time.time()
    TAG = os.environ.get("TRACKER", "base")
    if TAG == "R":
        from xa_tracker_r import XATrackerR; D.TrackerCls = XATrackerR
    S = D.scenario(name, seed); lc = S["model"]; dets, obs, L = S["data"]; cal = S["cal"]
    A = FlagMatcher(lc).decode_plain(dets)[:, 0] != obs
    base = dict(scenario=name, seed=seed, tracker=TAG, A=float(A.mean()), **S["info"])
    cache = f"dev_cache/{name}_{seed}{'_R' if TAG == 'R' else ''}.npz"; os.makedirs("dev_cache", exist_ok=True)
    if os.path.exists(cache):
        z = np.load(cache); pL_full, pr_full, gr, gn = z["pL_full"], float(z["pr_full"]), z["gr"], z["gn"]
    else:
        h1, h2 = cal[: len(cal) // 2], cal[len(cal) // 2:]
        nul = S["null"](len(cal), seed + 2); n1, n2 = nul[: len(nul) // 2], nul[len(nul) // 2:]
        trf = D.em(lc, cal); pL_full, pr_full = trf.p_L.copy(), trf.p_ret
        gr = qgain_shots(D.em(lc, h1), h2); gn = qgain_shots(D.em(lc, n1), n2)
        np.savez(cache, pL_full=pL_full, pr_full=pr_full, gr=gr, gn=gn)
    tr = D.TrackerCls(lc, basis="both", explain=True)
    zsc = (gr.mean(0) - gn.mean(0)) / np.sqrt(gr.var(0) / len(gr) + gn.var(0) / len(gn))
    rules = {"G0": np.ones(lc.nq, bool), "G2": gr.sum(0) > gn.sum(0).max(), "G2b": zsc > 3}
    for g, keep in rules.items():
        tr.set_params(np.where(keep, pL_full, 1e-6), pr_full, 0.5)
        r = D.evaluate(lc, tr, dets, obs, A) if keep.any() else dict(X=float(A.mean()), X_only=0, A_only=0, p=1.0, mean_pi=0.0)
        print(json.dumps(dict(base, guard=g, keep=keep.astype(int).tolist(), z=zsc.round(1).tolist(), pL=np.where(keep, pL_full, 0).round(5).tolist(), p_ret=round(pr_full, 3), **r)), flush=True)
    print(json.dumps(dict(base, guard="done", seconds=round(time.time() - t0))), flush=True)

if __name__ == "__main__":
    main()
