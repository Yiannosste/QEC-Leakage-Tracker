"""run_cell.py - one pre-registered grid cell: simulate, track (HMM + CNN), decode (A, B, D-HMM, D-CNN, E), report.
Memory-bounded (chunked tracking/decoding) and restart-safe (each decoder's per-shot outcomes are checkpointed to
results/<name>_<decoder>.npy and skipped on re-run; CNN models are saved to models/ and reloaded).

usage: python run_cell.py --d 5 --pL 2e-3 --tau 8 --shots 100000 --tag G1 [--rounds 25] [--lags 0,2] [--hmm-lags 0]
       [--train-shots 50000] [--epochs 6] [--cnn-model models/prefix (load instead of train)]
       [--hmm-pL x --hmm-tau y --hmm-rho z] [--rho 0.5] [--eta-lru 0] [--threads 3] [--no-hmm] [--no-cnn]
       [--seed-sim N] [--chunk 20000] [--suffix s]
All data SYNTHETIC (Stim + leakage_sim). Sim seed from the pre-registration formula unless --seed-sim is given.
"""
import os, sys, json, time, argparse
os.environ.setdefault("KMP_AFFINITY", "disabled")
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
import numpy as np
from leakage_sim import LeakyCircuit, FlagMatcher, wilson, per_round
from hmm_tracker import LeakageHMM, flag_metrics

PL_GRID = [1e-4, 3e-4, 1e-3, 2e-3, 5e-3, 1e-2]; TAU_GRID = [1, 2, 4, 8, 16]; D_GRID = [3, 5, 7]

def seed_formula(d, pL, tau):
    i_d = D_GRID.index(d) if d in D_GRID else 9
    i_p = min(range(len(PL_GRID)), key=lambda k: abs(PL_GRID[k] - pL)); i_t = min(range(len(TAU_GRID)), key=lambda k: abs(TAU_GRID[k] - tau))
    return 1000 + 100 * i_d + 10 * i_p + i_t

G = {}
def _worker(args):
    """Runs in a forked worker created BEFORE torch is imported (OpenMP + fork is unsafe otherwise)."""
    sub, d_, pl_, pr_, pf_, th_ = args
    pred = G["fm"].decode_with_posteriors(d_, pl_, pr_, pf_, thresh=th_)
    return sub, pred[:, 0]

def paired_bootstrap_f(errA, errB, errX, n=2000, seed=42):
    rng = np.random.default_rng(seed); N = len(errA); out = []
    A, B, X = errA.astype(np.int8), errB.astype(np.int8), errX.astype(np.int8)
    for _ in range(n):
        idx = rng.integers(0, N, N); a, b, x = A[idx].mean(), B[idx].mean(), X[idx].mean()
        out.append((a - x) / (a - b) if a > b else np.nan)
    out = np.array(out); out = out[~np.isnan(out)]
    return (float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))) if len(out) else (None, None)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d", type=int, required=True); ap.add_argument("--pL", type=float, required=True); ap.add_argument("--tau", type=float, required=True)
    ap.add_argument("--shots", type=int, default=100000); ap.add_argument("--rounds", type=int, default=25); ap.add_argument("--tag", default="G1")
    ap.add_argument("--lags", default="0,2"); ap.add_argument("--hmm-lags", default=None)
    ap.add_argument("--train-shots", type=int, default=50000); ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--cnn-model", default=None)
    ap.add_argument("--hmm-pL", type=float, default=None); ap.add_argument("--hmm-tau", type=float, default=None); ap.add_argument("--hmm-rho", type=float, default=None)
    ap.add_argument("--rho", type=float, default=0.5); ap.add_argument("--eta-lru", type=float, default=0.0); ap.add_argument("--threads", type=int, default=3)
    ap.add_argument("--no-hmm", action="store_true"); ap.add_argument("--no-cnn", action="store_true"); ap.add_argument("--seed-sim", type=int, default=None)
    ap.add_argument("--explain-away", type=int, default=2); ap.add_argument("--p", type=float, default=1e-3); ap.add_argument("--suffix", default="")
    ap.add_argument("--thresh", type=float, default=0.02); ap.add_argument("--chunk", type=int, default=20000); ap.add_argument("--procs", type=int, default=4)
    a = ap.parse_args()
    t0 = time.time(); os.makedirs("results", exist_ok=True); os.makedirs("models", exist_ok=True)
    name = f"{a.tag}_d{a.d}_pL{a.pL:g}_tau{a.tau:g}{a.suffix}"
    seed = a.seed_sim if a.seed_sim is not None else seed_formula(a.d, a.pL, a.tau)
    lags = [int(x) for x in a.lags.split(",")]; hmm_lags = [int(x) for x in a.hmm_lags.split(",")] if a.hmm_lags else lags
    lc = LeakyCircuit(a.d, a.rounds, a.p, noise="si1000", rho=a.rho); fm = FlagMatcher(lc)
    dets, obs, L = lc.sample(a.shots, a.pL, a.tau, eta_lru=a.eta_lru, seed=seed)
    R = a.rounds; N = a.shots; ok = obs[:, 0]
    meta_path = f"results/{name}_meta.json"
    res = json.load(open(meta_path)) if os.path.exists(meta_path) else dict(
        cell=dict(d=a.d, pL=a.pL, tau=a.tau, rho=a.rho, eta_lru=a.eta_lru, rounds=R, p=a.p, shots=N, seed_sim=seed, tag=a.tag,
                  leaked_frac=float(L.mean()), det_frac=float(dets.mean()), data="SYNTHETIC"), decoders={}, flags={}, timing={})
    errs = {}
    def ck(key): return f"results/{name}_{key}.npy"
    def have(key):
        if os.path.exists(ck(key)):
            errs[key] = np.load(ck(key)); return True
        return False
    def record(key, err, extra=None):
        errs[key] = err; np.save(ck(key), err); k = int(err.sum()); lo, hi = wilson(k, N)
        res["decoders"][key] = dict(failures=k, pfail=k / N, pfail_lo=lo, pfail_hi=hi, eps=per_round(k / N, R), eps_lo=per_round(lo, R), eps_hi=per_round(hi, R))
        if extra: res["decoders"][key].update(extra)
        json.dump(res, open(meta_path, "w"), indent=1)
        print(f"  {key:14s} pfail={k/N:.5f} [{lo:.5f},{hi:.5f}]  ({time.time()-t0:.0f}s)", flush=True)
    def chunks():
        for s in range(0, N, a.chunk): yield slice(s, min(N, s + a.chunk))
    import multiprocessing as mp
    G["fm"] = fm
    wpool = mp.get_context("fork").Pool(a.procs) if a.procs > 1 else None   # forked now, before any torch import
    def decode_soft(post_fn, thresh=a.thresh, hard=False):
        """post_fn(slice) -> (pi_leak, pi_ret, pi_final) for that chunk; decoding of each chunk is split over
        a.procs forked workers (posteriors are computed in the parent). Returns err array and pooled flag metrics."""
        err = np.zeros(N, bool); fm_acc = []
        for sl in chunks():
            pl, pr, pf = post_fn(sl)
            if hard: pl, pr, pf = (pl > 0.5).astype(np.float32), None, None
            n = sl.stop - sl.start; step = (n + a.procs - 1) // a.procs
            subs = [slice(s, min(n, s + step)) for s in range(0, n, step)]
            jobs = [(sub, dets[sl][sub], pl[sub], None if pr is None else pr[sub], None if pf is None else pf[sub], thresh) for sub in subs]
            results_ = wpool.map(_worker, jobs) if wpool is not None else [_worker(j) for j in jobs]
            for sub, p in results_:
                err[sl.start + sub.start: sl.start + sub.stop] = p != ok[sl.start + sub.start: sl.start + sub.stop]
            if not hard: fm_acc.append(flag_metrics(pl, L[sl]))
        return err, fm_acc
    def pool(fm_acc):
        if not fm_acc: return None
        keys = fm_acc[0].keys(); out = {}
        for k in keys:
            vals = [m[k] for m in fm_acc if m[k] == m[k]]
            out[k] = float(np.mean(vals)) if vals else None
        return out
    # ---- A, B
    if not have("A_ignore"):
        record("A_ignore", fm.decode_plain(dets)[:, 0] != ok)
    if not have("B_oracle"):
        err, _ = decode_soft(lambda sl: (L[sl].astype(np.float32), None, None)); record("B_oracle", err)
    # ---- HMM
    if not a.no_hmm:
        hp = dict(p_L=a.hmm_pL or a.pL, tau=a.hmm_tau or a.tau, rho=a.hmm_rho); res["hmm_params"] = hp
        hmm = None
        for lag in hmm_lags:
            keyD, keyE = f"D_HMM_lag{lag}", f"E_HMM_lag{lag}"
            if have(keyD) and (lag != 0 or have(keyE)): continue
            if hmm is None: hmm = LeakageHMM(lc, hp["p_L"], hp["tau"], eta_lru=a.eta_lru, rho=hp["rho"])
            cache = {}
            def post(sl, lag=lag, cache=cache):
                if sl.start not in cache:
                    cache.clear(); cache[sl.start] = hmm.posteriors(dets[sl], lag=lag, explain_away=a.explain_away)
                return cache[sl.start]
            if not have(keyD):
                t = time.time(); err, fma = decode_soft(post); res["flags"][f"HMM_lag{lag}"] = pool(fma); record(keyD, err, dict(seconds=time.time() - t))
            if lag == 0 and not have(keyE):
                err, _ = decode_soft(post, hard=True); record(keyE, err)
    # ---- CNN
    if not a.no_cnn:
        from cnn_tracker import CNNTracker, LatticeMap
        import torch
        lm = LatticeMap(lc); Vtr = Ytr = None
        for lag in lags:
            keyD, keyE = f"D_CNN_lag{lag}", f"E_CNN_lag{lag}"
            if have(keyD) and (lag != max(lags) or have(keyE)): continue
            mpath = (a.cnn_model + f"_lag{lag}.pt") if a.cnn_model else f"models/{name}_cnn_lag{lag}.pt"
            tr = CNNTracker(lc, lag=lag, threads=a.threads, seed=0); ttrain = 0.0
            if os.path.exists(mpath):
                tr.load(mpath)
            else:
                if Vtr is None:
                    dtr, _, Ltr = lc.sample(a.train_shots, a.pL, a.tau, eta_lru=a.eta_lru, seed=101 + seed)
                    Vtr, Ytr = lm.to_volume(dtr), lm.labels(Ltr); del dtr, Ltr
                t = time.time(); tr.fit(Vtr, Ytr, epochs=a.epochs, verbose=False); ttrain = time.time() - t; tr.save(mpath)
            cache = {}
            def post(sl, tr=tr, cache=cache):
                if sl.start not in cache:
                    cache.clear(); pl, pr, pf = tr.posteriors(dets[sl]); cache[sl.start] = (pl.astype(np.float32), pr.astype(np.float32), pf.astype(np.float32))
                return cache[sl.start]
            if not have(keyD):
                t = time.time(); err, fma = decode_soft(post); res["flags"][f"CNN_lag{lag}"] = pool(fma)
                record(keyD, err, dict(train_seconds=ttrain, seconds=time.time() - t, model=mpath))
            if lag == max(lags) and not have(keyE):
                err, _ = decode_soft(post, hard=True); record(keyE, err)
        res["cnn_params"] = dict(train_shots=a.train_shots, epochs=a.epochs, model=a.cnn_model)
    # ---- derived
    eA, eB = errs["A_ignore"], errs["B_oracle"]
    res["oracle_gain_G_B"] = float(1 - eB.mean() / eA.mean()) if eA.mean() > 0 else None
    rng = np.random.default_rng(42); diffs = [eA[idx].mean() - eB[idx].mean() for idx in (rng.integers(0, N, N) for _ in range(500))]
    res["G_B_pfail_diff_ci"] = [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]
    for key, eX in errs.items():
        if key.startswith(("D_", "E_")):
            f = float((eA.mean() - eX.mean()) / (eA.mean() - eB.mean())) if eA.mean() > eB.mean() else None
            lo, hi = paired_bootstrap_f(eA, eB, eX)
            res["decoders"].setdefault(key, {}).update(f_recovered=f, f_lo=lo, f_hi=hi,
                mcnemar_A_wrong_X_right=int((eA & ~eX).sum()), mcnemar_X_wrong_A_right=int((~eA & eX).sum()))
    Ds = [k for k in errs if k.startswith("D_")]
    res["best_D"] = max(Ds, key=lambda k: res["decoders"][k].get("f_recovered") or -9) if Ds else None
    if wpool is not None: wpool.close(); wpool.join()
    res["timing"]["total_last_run"] = time.time() - t0
    json.dump(res, open(f"results/{name}.json", "w"), indent=1)
    print(json.dumps({k: round(v.get("f_recovered", v.get("pfail")), 4) for k, v in res["decoders"].items() if isinstance(v, dict)}), "total %.0fs" % res["timing"]["total_last_run"])

if __name__ == "__main__":
    main()
