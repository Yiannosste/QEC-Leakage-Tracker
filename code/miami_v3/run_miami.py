"""run_miami.py - replication of the frozen ALL tracker on IBM ibm_miami (Zenodo 21336494), protocol miami_protocol.md.
usage: python code/miami_v3/run_miami.py --group fig10:5,Z --stage calib|track|decode|analyze --procs 12
A group = all depths of one (figure, case-without-depth). Calibration (label-free Baum-Welch, frozen settings) pools
the calibration shots of all depths of the group; per-qubit p_L and global p_ret are shared across depths.
Stages calib/track read detection events only; decode/analyze read the logical outcomes."""
import sys, os, json, time, argparse, numpy as np, multiprocessing as mp
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
from miami_io import load, case_list
from gen_leaky2 import NoResetLeakyCircuit
from leakage_sim import FlagMatcher
from xa_tracker import XATracker

OUT = paths.MIAMIREP; THR = 0.02; CAL_FRAC = 0.25
G = {}


def groups(fig):
    out = {}
    for i, c in enumerate(case_list(fig)):
        key = ",".join(str(x) for x in c[:-1]); out.setdefault(key, []).append(i)
    return out


def split(N, unit):
    perm = np.random.default_rng(2026 + unit_seed(unit)).permutation(N)
    ncal = int(round(CAL_FRAC * N)); return np.sort(perm[:ncal]), np.sort(perm[ncal:])


def unit_seed(unit):  # deterministic, platform-independent
    return sum((k + 1) * ord(ch) for k, ch in enumerate(unit)) % 100000


def chunks(N, size): return [(lo, min(N, lo + size)) for lo in range(0, N, size)]
def pool(n): return mp.get_context("fork").Pool(n)
def _stats(a):
    j, lo, hi = a; tr, cd = G["units"][j]; return tr.loglik_and_stats(cd[lo:hi], None, passes=tr.passes)
def _post(a):
    lo, hi = a; pl, pr, pf = G["tr"].posteriors(G["td"][lo:hi]); return lo, pl.astype(np.float16), pr.astype(np.float16)
def _dec(a):
    lo, pl, pr = a
    return lo, G["fm"].decode_with_posteriors(G["td"][lo:lo + len(pl)], pl.astype(np.float32), pr.astype(np.float32),
                                              pl[:, :, -1].astype(np.float32), thresh=THR)[:, 0]


def static_matcher(fm, pl, pr, pf):
    lc = fm.lc; rho = lc.rho
    for i, r in zip(*np.nonzero(pl > THR)):
        for d, o in lc.leak_edges(lc.data_qubits[i], r): fm._set_edge(d, o, rho * pl[i, r])
    for i, r in zip(*np.nonzero(pr > THR)):
        for d, o in lc.return_edges(lc.data_qubits[i], r): fm._set_edge(d, o, (2 / 3) * pr[i, r])
    for i in np.nonzero(pf > THR)[0]:
        for d, o in lc.final_edge(lc.data_qubits[i]): fm._set_edge(d, o, rho * pf[i])
    return fm


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--group"); ap.add_argument("--stage"); ap.add_argument("--procs", type=int, default=12)
    a = ap.parse_args(); fig, key = a.group.split(":", 1); idxs = groups(fig)[key]
    gdir = f"{OUT}/{fig}_{key.replace(',', '_').replace(' ', '').replace('|', '').replace('>', '')}"; os.makedirs(gdir, exist_ok=True)
    if a.stage == "calib":
        f = f"{gdir}/calib.json"
        if os.path.exists(f): return
        units = []; t0 = time.time()
        for i in idxs:
            sc, det = load(fig, i); lc = NoResetLeakyCircuit(sc); cal, test = split(len(det), f"{fig}_{i}")
            tr = XATracker(lc, basis="both", explain=True); tr.set_params(3e-3, 0.25, 0.5); units.append((tr, det[cal]))
        dq = units[0][0].lc.data_qubits
        assert all(u[0].lc.data_qubits == dq for u in units), "data qubits differ across depths"
        G["units"] = units; jobs = [(j, lo, hi) for j, (tr, cd) in enumerate(units) for lo, hi in chunks(len(cd), max(20, 4000 // tr.R))]
        def estep():
            with pool(a.procs) as p: accs = p.map(_stats, jobs)
            return {k: sum(x[k] for x in accs) for k in accs[0]}
        hist = []; ncal = sum(len(cd) for _, cd in units)
        for it in range(12):
            s = estep(); pL = np.clip(s["n01"] / s["occ0"], 1e-6, 0.2); pr = float(np.clip(s["n10"] / max(s["occ1"], 1e-9), 1e-3, 1.0))
            hist.append(dict(it=it, ll_per_shot=float(s["ll"]) / ncal, pL_mean=float(pL.mean()), p_ret=pr))
            print(f"  {fig}:{key} calib it {it}: ll/shot {s['ll'] / ncal:.4f} pL mean {pL.mean():.2e} p_ret {pr:.3f}", flush=True)
            for tr, _ in units: tr.set_params(pL, pr, 0.5)
        ll_fit = float(estep()["ll"]) / ncal; fitted = (units[0][0].p_L.copy(), units[0][0].p_ret)
        for tr, _ in units: tr.set_params(1e-6, fitted[1], 0.5)
        ll_null = float(estep()["ll"]) / ncal
        json.dump(dict(p_L=fitted[0].tolist(), data_qubits=list(map(int, dq)), p_ret=fitted[1], ll_fit=ll_fit, ll_null=ll_null,
                       ncal=ncal, seconds=time.time() - t0, history=hist), open(f, "w"))
        print(f"{fig}:{key} calib: pL {fitted[0].mean():.2e} p_ret {fitted[1]:.3f} dLL/shot {ll_fit - ll_null:.3f} ({time.time() - t0:.0f}s)", flush=True)
        return
    info = json.load(open(f"{gdir}/calib.json"))
    for i in idxs:
        unit = f"{fig}_{i}"; udir = f"{gdir}/{i}"; os.makedirs(udir, exist_ok=True)
        if a.stage == "track":
            f = f"{udir}/post.npz"
            if os.path.exists(f): continue
            sc, det = load(fig, i); lc = NoResetLeakyCircuit(sc); cal, test = split(len(det), unit)
            tr = XATracker(lc, basis="both", explain=True); tr.set_params(np.array(info["p_L"]), info["p_ret"], 0.5)
            G.update(tr=tr, td=det[test]); N = len(test); PL = np.zeros((N, lc.nq, lc.rounds), np.float16); PR = np.zeros_like(PL)
            with pool(a.procs) as p:
                for lo, pl, pr in p.imap_unordered(_post, chunks(N, max(20, 4000 // lc.rounds))): PL[lo:lo + len(pl)] = pl; PR[lo:lo + len(pl)] = pr
            np.savez(f, pl=PL, pr=PR); print(f"{unit} track: mean pi {PL.astype(np.float32).mean():.4f}", flush=True)
        elif a.stage == "decode":
            sc, det, obs = load(fig, i, want_obs=True); lc = NoResetLeakyCircuit(sc); cal, test = split(len(det), unit)
            td, ot, N = det[test], obs[test], len(test)
            def save(name, pred): np.save(f"{udir}/fail_{name}.npy", (pred != ot).astype(np.uint8))
            if not os.path.exists(f"{udir}/fail_A_all.npy"):   # pipeline check vs published numbers (all shots)
                np.save(f"{udir}/fail_A_all.npy", (FlagMatcher(lc).decode_plain(det)[:, 0] != obs).astype(np.uint8))
            if not os.path.exists(f"{udir}/fail_A.npy"): save("A", FlagMatcher(lc).decode_plain(td)[:, 0].astype(bool))
            z = np.load(f"{udir}/post.npz"); PL, PR = z["pl"], z["pr"]
            for name in ["X", "P"]:
                if os.path.exists(f"{udir}/fail_{name}.npy"): continue
                if name == "P": pm = np.random.default_rng(0).permutation(N); PLu, PRu = PL[pm], PR[pm]
                else: PLu, PRu = PL, PR
                G.update(fm=FlagMatcher(lc), td=td); pred = np.zeros(N, bool)
                with pool(a.procs) as p:
                    for lo, pr_ in p.imap_unordered(_dec, [(lo, PLu[lo:hi], PRu[lo:hi]) for lo, hi in chunks(N, 200)]): pred[lo:lo + len(pr_)] = pr_
                save(name, pred)
            if not os.path.exists(f"{udir}/fail_A4.npy"):
                plm = PL.astype(np.float32).mean(0); prm = PR.astype(np.float32).mean(0)
                save("A4", static_matcher(FlagMatcher(lc), plm, prm, plm[:, -1]).matching.decode_batch(td)[:, 0].astype(bool))
            print(f"{unit} decoded", flush=True)
        elif a.stage == "analyze":
            from scipy.stats import binomtest
            F = {n: np.load(f"{udir}/fail_{n}.npy").astype(bool) for n in ["A", "X", "A4", "P"]}
            sc, det = load(fig, i); z = np.load(f"{udir}/post.npz")
            def mc(x, y):
                b = int((~F[x] & F[y]).sum()); c = int((F[x] & ~F[y]).sum())
                return dict(x_right_only=b, y_right_only=c, p=float(binomtest(b, b + c, 0.5).pvalue) if b + c else 1.0)
            res = dict(unit=unit, fig=fig, group=key, depth=int(case_list(fig)[i][-1]), ntest=int(len(F["A"])), detfrac=float(det.mean()),
                       mean_pi=float(z["pl"].astype(np.float32).mean()), pfail={n: float(v.mean()) for n, v in F.items()},
                       pfail_A_all=float(np.load(f"{udir}/fail_A_all.npy").mean()),
                       mcnemar={"X_vs_A": mc("X", "A"), "X_vs_A4": mc("X", "A4"), "P_vs_A": mc("P", "A"), "A4_vs_A": mc("A4", "A")})
            json.dump(res, open(f"{udir}/results.json", "w"), indent=1)


if __name__ == "__main__":
    main()
