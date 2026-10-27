"""run_detect2.py - one cell of the detect2 study (see detect2_protocol.md). Stages are restart-safe (outputs cached).
usage: python code/detect2/run_detect2.py --cell i | --dev  --stage sim|track|cnn|decode|analyze [--procs 10] [--quick]
--quick is NOT part of the frozen protocol: 2 000 test shots, 1 000 calibration shots, CNN stage skipped, outputs in
det2/<cell>_quick/. It only checks that the pipeline runs end to end; its numbers are too noisy to compare with F3.
"""
import os, sys, json, time, argparse
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"): os.environ.setdefault(v, "1")
os.environ.setdefault("KMP_AFFINITY", "disabled"); os.environ.setdefault("KMP_INIT_AT_FORK", "FALSE")
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
import numpy as np, multiprocessing as mp
from leakage_sim import LeakyCircuit, FlagMatcher, per_round

D, ROUNDS, TAU, PL_MEAN, ETA, FH = 5, 25, 8, 1e-3, 0.8, 0.01
CELLS = [(p, het) for het in (0, 1) for p in (1e-3, 2e-3, 3e-3)]
XA_CONFIGS = {   # name: (basis, explain, herald, calib)  calib in {'pq','glob','true'}
    "J_h": ("both", False, True, "pq"), "J": ("both", False, False, "pq"),        # ideas 1(+3)+4, no explaining away
    "XZ_h": ("z", True, True, "pq"), "XZ": ("z", True, False, "pq"),             # ideas 2(+3)+4, Z-type checks only
    "ALL_h": ("both", True, True, "pq"), "ALL": ("both", True, False, "pq"),     # ideas 1+2(+3)+4
    "ALL_true": ("both", True, False, "true"), "ALL_glob": ("both", True, False, "glob"),
    "ALL_lag2": ("both", True, False, "pq")}
PRIMARY = {1, 2, 4, 5}       # p = 2e-3, 3e-3, hom and het


def cell_spec(a):
    if a.dev: return dict(name="dev_p0.002_hom", p=2e-3, het=0, N=20000, ncal=8000, seeds=dict(test=9001, cal=9002, cnn=9003, her=9004))
    p, het = CELLS[a.cell]; i = a.cell
    C = dict(name=f"p{p:g}_{'het' if het else 'hom'}", p=p, het=het, N=40000, ncal=8000,
             seeds=dict(test=9100 + i, cal=9200 + i, cnn=9300 + i, her=9400 + i))
    if a.quick: C.update(name=C["name"] + "_quick", N=2000, ncal=1000)
    return C


def cell_configs(a, C):
    """Configurations run per cell: ALL_glob only where p_L differs per qubit; ALL_true and ALL_lag2 only in primary cells."""
    out = []
    for name in XA_CONFIGS:
        if name == "ALL_glob" and not C["het"]: continue
        if name in ("ALL_true", "ALL_lag2") and not (a.dev or a.cell in PRIMARY): continue
        out.append(name)
    return out


def pl_vector(nq, het):
    if not het: return np.full(nq, PL_MEAN)
    z = np.random.default_rng(9500).standard_normal(nq)
    return np.clip(PL_MEAN * np.exp(0.8 * z - 0.32), 1e-5, 0.02)


def herald_bits(L, seed):
    rng = np.random.default_rng(seed); last = L[:, :, -1].astype(bool); u = rng.random(last.shape)
    return np.where(last, u < ETA, u < FH).astype(np.uint8)


G = {}
def _post_worker(args):
    lo, hi = args; tr = G["tr"]
    if G["kind"] == "old":
        pl, pr, pf = tr.posteriors(G["dets"][lo:hi], lag=0, explain_away=2)
    else:
        her = None if G["her"] is None else G["her"][lo:hi]
        pl, pr, pf = tr.posteriors(G["dets"][lo:hi], her, lag=G["lag"])
    return lo, pl.astype(np.float16), pr.astype(np.float16)

def _stats_worker(args):
    lo, hi = args; her = None if G["cher"] is None else G["cher"][lo:hi]
    return G["tr"].loglik_and_stats(G["cdets"][lo:hi], her, passes=G["tr"].passes)

def _dec_worker(args):
    lo, pl, pr, pf = args
    return lo, G["fm"].decode_with_posteriors(G["dets"][lo:lo + len(pl)], pl.astype(np.float32),
                                               None if pr is None else pr.astype(np.float32),
                                               None if pf is None else pf.astype(np.float32), thresh=0.02)[:, 0]

def chunks(N, size): return [(lo, min(N, lo + size)) for lo in range(0, N, size)]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--cell", type=int); ap.add_argument("--dev", action="store_true")
    ap.add_argument("--stage", required=True); ap.add_argument("--procs", type=int, default=10)
    ap.add_argument("--only", default=None, help="comma-separated subset of tracker names (track/decode stages)")
    ap.add_argument("--quick", action="store_true", help="pipeline check only: 2000 test / 1000 calibration shots, no CNN (not the protocol)")
    a = ap.parse_args(); C = cell_spec(a); out = f"{paths.DET2}/{C['name']}"; os.makedirs(out, exist_ok=True)
    lc = LeakyCircuit(D, ROUNDS, C["p"]); R = ROUNDS; pLv = pl_vector(lc.nq, C["het"])
    simf = f"{out}/sim.npz"
    if a.stage == "sim":
        if os.path.exists(simf): print("sim exists"); return
        dets, obs, L = lc.sample(C["N"], pLv, TAU, seed=C["seeds"]["test"])
        cd, _, cL = lc.sample(C["ncal"], pLv, TAU, seed=C["seeds"]["cal"])
        np.savez_compressed(simf, dets=np.packbits(dets, 1), obs=obs[:, 0], L=L, her=herald_bits(L, C["seeds"]["her"]),
                            cdets=np.packbits(cd, 1), cher=herald_bits(cL, C["seeds"]["her"] + 1000), pLv=pLv, nd=lc.num_detectors)
        print(C["name"], "leaked", L.mean(), "det frac", dets.mean(), "pL range", pLv.min(), pLv.max()); return
    S = np.load(simf); nd = int(S["nd"])
    dets = np.unpackbits(S["dets"], 1)[:, :nd].astype(bool); obs = S["obs"]; L = S["L"]; her = S["her"]
    N = len(obs)

    if a.stage == "track":
        from xa_tracker import XATracker
        from hmm_tracker import LeakageHMM
        cdets = np.unpackbits(S["cdets"], 1)[:, :nd].astype(bool); cher = S["cher"]
        names = ["old_hmm"] + cell_configs(a, C) if a.only is None else a.only.split(",")
        for name in names:
            f = f"{out}/post_{name}.npz"
            if os.path.exists(f): continue
            t0 = time.time(); info = {}
            if name == "old_hmm":
                tr = LeakageHMM(lc, float(pLv.mean()), TAU); G.update(kind="old", tr=tr, dets=dets); size = 2500
            else:
                basis, explain, useh, calib = XA_CONFIGS[name]
                tr = XATracker(lc, basis=basis, explain=explain, herald=(ETA, FH) if useh else None)
                if calib == "true":
                    tr.set_params(pLv, 1.0 / TAU, 0.5); info = dict(p_L=pLv.tolist(), p_ret=1 / TAU)
                else:
                    calf = f"{out}/calib_{basis}_{int(explain)}.json"
                    if os.path.exists(calf):
                        info = json.load(open(calf))
                        pL_ = np.array(info["p_L"]) if calib == "pq" else np.full(lc.nq, float(np.mean(info["p_L"])))
                        tr.set_params(pL_, info["p_ret"], 0.5)
                    else:
                        tr.set_params(3e-3, 0.25, 0.5); hist = []
                        G.update(cdets=cdets, cher=None)
                        for it in range(12):
                            G["tr"] = tr
                            with mp.get_context("fork").Pool(a.procs) as pool: accs = pool.map(_stats_worker, chunks(len(cdets), 500))
                            n01 = sum(x["n01"] for x in accs); occ0 = sum(x["occ0"] for x in accs)
                            n10 = sum(x["n10"] for x in accs); occ1 = sum(x["occ1"] for x in accs); ll = sum(x["ll"] for x in accs)
                            pL = n01 / occ0
                            pr = float(np.clip(n10 / max(occ1, 1e-9), 1e-3, 1.0)); pL = np.clip(pL, 1e-6, 0.2)
                            hist.append(dict(it=it, ll_per_shot=ll / len(cdets), pL_mean=float(pL.mean()), p_ret=pr))
                            print(f"  calib {name} it {it}: ll/shot {ll / len(cdets):.4f} pL mean {pL.mean():.2e} p_ret {pr:.3f}", flush=True)
                            tr.set_params(pL, pr, 0.5)
                        info = dict(p_L=tr.p_L.tolist(), p_ret=tr.p_ret, history=hist); json.dump(info, open(calf, "w"))
                        if calib == "glob": tr.set_params(np.full(lc.nq, float(tr.p_L.mean())), tr.p_ret, 0.5)
                G.update(kind="xa", tr=tr, dets=dets, her=her if useh else None, lag=2 if name == "ALL_lag2" else None)
                size = 500 if explain and basis == "both" else 1500
            PL = np.zeros((N, lc.nq, R), np.float16); PR = np.zeros_like(PL)
            with mp.get_context("fork").Pool(a.procs) as pool:
                for lo, pl, pr in pool.imap_unordered(_post_worker, chunks(N, size)):
                    PL[lo:lo + len(pl)] = pl; PR[lo:lo + len(pl)] = pr
            np.savez(f, pl=PL, pr=PR); json.dump(dict(seconds=time.time() - t0, **{k: v for k, v in info.items() if k != "history"}),
                                                open(f"{out}/post_{name}.json", "w"))
            print(f"{C['name']} {name}: {time.time() - t0:.0f}s", flush=True)

    elif a.stage == "cnn":
        if a.quick: print("quick mode: CNN stage skipped (needs 50 000 labelled training shots and PyTorch)"); return
        f = f"{out}/post_old_cnn.npz"
        if os.path.exists(f): print("cnn exists"); return
        os.environ["OMP_NUM_THREADS"] = str(a.procs)
        from cnn_tracker import CNNTracker
        import torch; torch.set_num_threads(a.procs)
        t0 = time.time(); dtr, _, Ltr = lc.sample(50000, pLv, TAU, seed=C["seeds"]["cnn"])
        tr = CNNTracker(lc, lag=2, threads=a.procs, seed=0)
        tr.fit(tr.lm.to_volume(dtr), tr.lm.labels(Ltr), epochs=6, verbose=True); del dtr, Ltr
        PL = np.zeros((N, lc.nq, R), np.float16); PR = np.zeros_like(PL)
        for lo, hi in chunks(N, 5000):
            pl, pr, pf = tr.posteriors(dets[lo:hi]); PL[lo:hi] = pl; PR[lo:hi] = pr
        np.savez(f, pl=PL, pr=PR); json.dump(dict(seconds=time.time() - t0), open(f"{out}/post_old_cnn.json", "w"))
        print(f"{C['name']} old_cnn: {time.time() - t0:.0f}s", flush=True)

    elif a.stage == "decode":
        fm = FlagMatcher(lc); G.update(fm=fm, dets=dets)
        names = ["A", "B"] + ["old_hmm", "old_cnn"] + cell_configs(a, C) if a.only is None else a.only.split(",")
        with mp.get_context("fork").Pool(a.procs) as pool:
            for name in names:
                f = f"{out}/fail_{name}.npy"
                if os.path.exists(f): continue
                t0 = time.time()
                if name == "A": pred = fm.decode_plain(dets)[:, 0]
                else:
                    if name == "B": PL, PR, PF = L.astype(np.float16), None, None
                    else:
                        pf_ = f"{out}/post_{name}.npz"
                        if not os.path.exists(pf_): print("missing", name); continue
                        z = np.load(pf_); PL, PR = z["pl"], z["pr"]; PF = PL[:, :, -1]
                    pred = np.zeros(N, np.uint8)
                    args = [(lo, PL[lo:hi], None if PR is None else PR[lo:hi], None if PF is None else PF[lo:hi]) for lo, hi in chunks(N, 1000)]
                    for lo, pr_ in pool.imap_unordered(_dec_worker, args): pred[lo:lo + len(pr_)] = pr_
                np.save(f, (pred != obs).astype(np.uint8)); print(f"{C['name']} decode {name}: P_fail {(pred != obs).mean():.4f} ({time.time() - t0:.0f}s)", flush=True)

    elif a.stage == "analyze":
        from detmetrics import det_metrics
        from scipy.stats import binomtest
        res = dict(cell=C["name"], p=C["p"], het=C["het"], N=N, leaked_frac=float(L.mean()), det_frac=float(dets.mean()),
                   pL_range=[float(pLv.min()), float(pLv.max())], trackers={})
        fA, fB = np.load(f"{out}/fail_A.npy"), np.load(f"{out}/fail_B.npy")
        eA, eB = per_round(fA.mean(), R), per_round(fB.mean(), R)
        rng = np.random.default_rng(42); idx = [rng.integers(0, N, N) for _ in range(2000)]
        for name in ["old_hmm", "old_cnn"] + list(XA_CONFIGS):
            ff = f"{out}/fail_{name}.npy"
            if not os.path.exists(ff): continue
            fX = np.load(ff); eX = per_round(fX.mean(), R)
            boots = [(per_round(fA[i].mean(), R) - per_round(fX[i].mean(), R)) / (per_round(fA[i].mean(), R) - per_round(fB[i].mean(), R)) for i in idx]
            z = np.load(f"{out}/post_{name}.npz"); dm = det_metrics(z["pl"].astype(np.float32), L)
            res["trackers"][name] = dict(pfail=float(fX.mean()), eps=eX, f=(eA - eX) / (eA - eB), f_ci=list(np.percentile(boots, [2.5, 97.5])),
                                         ler_drop=1 - eX / eA, det=dm, **json.load(open(f"{out}/post_{name}.json")))
        res.update(pfail_A=float(fA.mean()), pfail_B=float(fB.mean()), eps_A=eA, eps_B=eB, oracle_drop=1 - eB / eA)
        def mcn(x, y):
            fx, fy = np.load(f"{out}/fail_{x}.npy"), np.load(f"{out}/fail_{y}.npy")
            b = int(((fy == 1) & (fx == 0)).sum()); c = int(((fy == 0) & (fx == 1)).sum())
            return dict(x_right_only=b, y_right_only=c, p=float(binomtest(b, b + c, 0.5).pvalue) if b + c else 1.0)
        res["mcnemar"] = {f"{x}_vs_{y}": mcn(x, y) for x, y in [("ALL", "old_cnn"), ("ALL", "old_hmm"), ("ALL_h", "ALL"),
                          ("ALL", "J"), ("ALL", "XZ"), ("ALL", "ALL_true"), ("ALL", "ALL_glob"), ("ALL_lag2", "old_cnn"), ("ALL_h", "old_cnn"), ("J_h", "old_cnn"), ("XZ_h", "old_cnn")]
                          if os.path.exists(f"{out}/fail_{x}.npy") and os.path.exists(f"{out}/fail_{y}.npy")}
        json.dump(res, open(f"{out}/results.json", "w"), indent=1, default=float)
        print(json.dumps({k: (round(v["f"], 3), round(v["det"]["AP"], 3)) for k, v in res["trackers"].items()}))


if __name__ == "__main__":
    main()
