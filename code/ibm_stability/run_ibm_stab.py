"""run_ibm_stab.py - frozen protocol ibm_stab_protocol.md: ALL tracker on unseen IBM ibm_berlin stability runs.
usage: python code/ibm_stability/run_ibm_stab.py --run T20 --stage calib|track|decode|analyze --procs 12
(data: docs/DATA.md; outputs go to <LT_OUT>/ibmstab/<run>/)
Stages calib/track read detection events only; decode/analyze read the logical outcomes."""
import sys, os, json, time, argparse, numpy as np, multiprocessing as mp
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
import stim
from gen_leaky import GenLeakyCircuit
from leakage_sim import FlagMatcher

ROOT, OUT = paths.IBM_BERLIN_STAB, paths.IBMSTAB
ALPHAS = ["0.15", "0.3", "0.45", "0.6", "0.8", "1.0"]
RUNS = ["T5", "T10", "T20", "T50", "T100"] + [f"T20_alpha{a}" for a in ALPHAS] + [f"T100_alpha{a}" for a in ALPHAS]
THR = 0.02
G = {}


def T_of(run): return int(run.split("_")[0][1:])


def setup(run):
    T = T_of(run)
    paths.need(f"{ROOT}/{run}/error_model.dem", f"ibm_berlin stability run {run}")
    paths.need(paths.GNNRNN_REPO, "authors' repository (gnnrnn package)")
    from gnnrnn import circuits
    dem = stim.DetectorErrorModel.from_file(f"{ROOT}/{run}/error_model.dem")
    lc0 = GenLeakyCircuit(circuits.stability_circuit(T, 1e-3)); lc = lc0.with_dem(dem)
    dets = stim.read_shot_data_file(path=f"{ROOT}/{run}/detection_events.b8", format="b8",
                                    num_detectors=dem.num_detectors).astype(bool)
    N = len(dets); ncal = min(10000, round(200000 / T))
    perm = np.random.default_rng(2026).permutation(N)
    return T, dem, lc, dets, np.sort(perm[:ncal]), np.sort(perm[ncal:])


def chunks(N, size): return [(lo, min(N, lo + size)) for lo in range(0, N, size)]
def _stats(a): lo, hi = a; return G["tr"].loglik_and_stats(G["cd"][lo:hi], None, passes=G["tr"].passes)
def _post(a):
    lo, hi = a; pl, pr, pf = G["tr"].posteriors(G["td"][lo:hi]); return lo, pl.astype(np.float16), pr.astype(np.float16)
def _dec(a):
    lo, pl, pr = a
    return lo, G["fm"].decode_with_posteriors(G["td"][lo:lo + len(pl)], pl.astype(np.float32), pr.astype(np.float32),
                                              pl[:, :, -1].astype(np.float32), thresh=THR)[:, 0]
def pool(n): return mp.get_context("fork").Pool(n)


def static_matcher(fm, pl, pr, pf):
    """Apply the X rule once with shot-independent posteriors (same order as decode_with_posteriors, no restore)."""
    lc = fm.lc; rho = lc.rho
    for i, r in zip(*np.nonzero(pl > THR)):
        for d, o in lc.leak_edges(lc.data_qubits[i], r): fm._set_edge(d, o, rho * pl[i, r])
    for i, r in zip(*np.nonzero(pr > THR)):
        for d, o in lc.return_edges(lc.data_qubits[i], r): fm._set_edge(d, o, (2 / 3) * pr[i, r])
    for i in np.nonzero(pf > THR)[0]:
        for d, o in lc.final_edge(lc.data_qubits[i]): fm._set_edge(d, o, rho * pf[i])
    return fm


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True, choices=RUNS); ap.add_argument("--stage", required=True, choices=["calib", "track", "decode", "analyze"]); ap.add_argument("--procs", type=int, default=12)
    a = ap.parse_args(); out = f"{OUT}/{a.run}"; os.makedirs(out, exist_ok=True)
    T, dem, lc, dets, cal, test = setup(a.run)
    from xa_tracker import XATracker
    if a.stage == "calib":
        f = f"{out}/calib.json"
        if os.path.exists(f): return
        t0 = time.time(); tr = XATracker(lc, basis="both", explain=True); tr.set_params(3e-3, 0.25, 0.5)
        G.update(tr=tr, cd=dets[cal]); hist = []; ch = chunks(len(cal), max(50, 25000 // T))
        def estep():
            with pool(a.procs) as p: accs = p.map(_stats, ch)
            return {k: sum(x[k] for x in accs) for k in accs[0]}
        for it in range(12):
            s = estep(); pL = np.clip(s["n01"] / s["occ0"], 1e-6, 0.2); pr = float(np.clip(s["n10"] / max(s["occ1"], 1e-9), 1e-3, 1.0))
            hist.append(dict(it=it, ll_per_shot=float(s["ll"]) / len(cal), pL_mean=float(pL.mean()), p_ret=pr))
            print(f"  {a.run} calib it {it}: ll/shot {s['ll'] / len(cal):.4f} pL mean {pL.mean():.2e} p_ret {pr:.3f}", flush=True)
            tr.set_params(pL, pr, 0.5)
        ll_fit = float(estep()["ll"]) / len(cal); fitted = (tr.p_L.copy(), tr.p_ret)
        tr.set_params(1e-6, fitted[1], 0.5); ll_null = float(estep()["ll"]) / len(cal)
        json.dump(dict(p_L=fitted[0].tolist(), p_ret=fitted[1], ll_fit=ll_fit, ll_null=ll_null, ncal=len(cal), ntest=len(test),
                       seconds=time.time() - t0, history=hist), open(f, "w"))
        print(f"{a.run} calib: pL {fitted[0].mean():.2e} p_ret {fitted[1]:.3f} dLL/shot {ll_fit - ll_null:.3f} ({time.time() - t0:.0f}s)", flush=True)
    elif a.stage == "track":
        f = f"{out}/post.npz"
        if os.path.exists(f): return
        info = json.load(open(f"{out}/calib.json")); tr = XATracker(lc, basis="both", explain=True)
        tr.set_params(np.array(info["p_L"]), info["p_ret"], 0.5); G.update(tr=tr, td=dets[test])
        t0 = time.time(); N = len(test); PL = np.zeros((N, lc.nq, T), np.float16); PR = np.zeros_like(PL)
        with pool(a.procs) as p:
            for lo, pl, pr in p.imap_unordered(_post, chunks(N, max(50, 25000 // T))): PL[lo:lo + len(pl)] = pl; PR[lo:lo + len(pl)] = pr
        np.savez(f, pl=PL, pr=PR); print(f"{a.run} track: mean pi {PL.astype(np.float32).mean():.4f} ({time.time() - t0:.0f}s)", flush=True)
    elif a.stage == "decode":
        obs = stim.read_shot_data_file(path=f"{ROOT}/{a.run}/logical_flips.b8", format="b8", num_detectors=0,
                                       num_observables=1)[:, 0].astype(bool)
        ot = obs[test]; td = dets[test]; N = len(test)
        z = np.load(f"{out}/post.npz"); PL, PR = z["pl"], z["pr"]
        def save(name, pred):
            np.save(f"{out}/fail_{name}.npy", (pred != ot).astype(np.uint8)); print(f"{a.run} {name}: P_fail {(pred != ot).mean():.4f}", flush=True)
        if not os.path.exists(f"{out}/fail_A.npy"): save("A", FlagMatcher(lc).decode_plain(td)[:, 0].astype(bool))
        for name in ["X", "P"]:
            if os.path.exists(f"{out}/fail_{name}.npy"): continue
            if name == "P":
                pm = np.random.default_rng(0).permutation(N); PLu, PRu = PL[pm], PR[pm]
            else: PLu, PRu = PL, PR
            G.update(fm=FlagMatcher(lc), td=td); pred = np.zeros(N, bool)
            with pool(a.procs) as p:
                for lo, pr_ in p.imap_unordered(_dec, [(lo, PLu[lo:hi], PRu[lo:hi]) for lo, hi in chunks(N, 500)]): pred[lo:lo + len(pr_)] = pr_
            save(name, pred)
        if not os.path.exists(f"{out}/fail_A4.npy"):
            plm = PL.astype(np.float32).mean(0); prm = PR.astype(np.float32).mean(0)
            fm = static_matcher(FlagMatcher(lc), plm, prm, plm[:, -1]); save("A4", fm.matching.decode_batch(td)[:, 0].astype(bool))
        if not os.path.exists(f"{out}/fail_Xold.npy"):
            import ibm_tracker as otr
            from ibm_common import chains
            prm_ = json.load(open(paths.HMM_PARAMS_OLD)); prm_ = (prm_["a"], prm_["b"], prm_["q"], prm_["s"])
            P_, ch = chains(dem); r = dets.mean(0); Tc = max(len(c) for c in ch); Rm = np.zeros((len(ch), Tc))
            for j, c in enumerate(ch): Rm[j, :len(c)] = r[c]
            otr._init(f"stability_d3/{a.run}", P_, ch); tl = otr._G["tl"]; PI = np.zeros((N, len(tl)), np.float32)
            for lo, hi in chunks(N, 10000):
                PI[lo:hi] = otr.edge_post(otr.posterior(otr.to_cube(td[lo:hi], ch, Tc), Rm, prm_, "full"), tl)
            idx = np.array_split(np.arange(N), a.procs * 4)
            with pool(a.procs) as p: res = p.map(otr._decode_chunk, [(test[ix], PI[ix], 0.25, THR) for ix in idx])
            save("Xold", np.concatenate(res).astype(bool))
    elif a.stage == "analyze":
        from scipy.stats import binomtest
        F = {n: np.load(f"{out}/fail_{n}.npy").astype(bool) for n in ["A", "X", "A4", "P", "Xold"]}
        info = json.load(open(f"{out}/calib.json")); z = np.load(f"{out}/post.npz")
        def mc(x, y):
            b = int((~F[x] & F[y]).sum()); c = int((F[x] & ~F[y]).sum())
            return dict(x_right_only=b, y_right_only=c, p=float(binomtest(b, b + c, 0.5).pvalue) if b + c else 1.0)
        eps = lambda P: 0.5 * (1 - (1 - 2 * P) ** (1 / T)) if P < 0.5 else float("nan")
        res = dict(run=a.run, T=T, ntest=len(test), detfrac=float(dets.mean()), mean_pi=float(z["pl"].astype(np.float32).mean()),
                   pL_mean=float(np.mean(info["p_L"])), p_L=info["p_L"], p_ret=info["p_ret"], dLL_per_shot=info["ll_fit"] - info["ll_null"],
                   pfail={n: float(v.mean()) for n, v in F.items()}, eps={n: eps(float(v.mean())) for n, v in F.items()},
                   mcnemar={"X_vs_A": mc("X", "A"), "X_vs_A4": mc("X", "A4"), "P_vs_A": mc("P", "A"), "X_vs_Xold": mc("X", "Xold"),
                            "A4_vs_A": mc("A4", "A"), "Xold_vs_A": mc("Xold", "A")})
        json.dump(res, open(f"{out}/results.json", "w"), indent=1)
        print(json.dumps({k: res[k] for k in ["run", "pfail"]}), {k: (v["x_right_only"], v["y_right_only"]) for k, v in res["mcnemar"].items()})


if __name__ == "__main__":
    main()
