"""smoke_test.py - a one-minute end-to-end check of the leakage tracker (SYNTHETIC data only).

Steps: simulate a d = 3 rotated surface-code memory with injected data-qubit leakage (Stim + leakage_sim),
calibrate the ALL tracker label-free on separate calibration shots (Baum-Welch), compute per-shot leakage
posteriors, decode with (A) plain MWPM, (B) the oracle that knows the true leakage, (X) MWPM with the
tracker's soft edge weights, and print the numbers.  Exit code 0 means the pipeline runs; the numbers are
noisy (1 000 shots) and are NOT comparable with the paper's tables.
usage: python scripts/smoke_test.py [--shots 1000] [--cal 500] [--rounds 10] [--p 2e-3] [--pL 5e-3] [--tau 8] [--iters 4]
"""
import os, sys, time, argparse
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"): os.environ.setdefault(v, "1")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
import paths  # noqa: F401  (puts code/sim and code/tracker on sys.path)
import numpy as np
from scipy.stats import binomtest
from leakage_sim import LeakyCircuit, FlagMatcher, per_round
from xa_tracker import XATracker
from detmetrics import det_metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", type=int, default=1000); ap.add_argument("--cal", type=int, default=500)
    ap.add_argument("--d", type=int, default=3); ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--p", type=float, default=2e-3); ap.add_argument("--pL", type=float, default=5e-3)
    ap.add_argument("--tau", type=float, default=8); ap.add_argument("--iters", type=int, default=4)
    a = ap.parse_args(); t0 = time.time()

    lc = LeakyCircuit(a.d, a.rounds, a.p)
    dets, obs, L = lc.sample(a.shots, a.pL, a.tau, seed=1)          # test shots (labels L used only for B and AP)
    cdets, _, _ = lc.sample(a.cal, a.pL, a.tau, seed=2)             # calibration shots: syndromes only
    obs = obs[:, 0]
    print(f"[sim]    d={a.d} rounds={a.rounds} p={a.p:g} p_L={a.pL:g} tau={a.tau:g}: {a.shots} test + {a.cal} calibration shots, "
          f"{lc.num_detectors} detectors, leaked fraction {L.mean():.4f}, detection fraction {dets.mean():.4f}")

    tr = XATracker(lc, basis="both", explain=True)                 # the ALL tracker (F1)
    tr.set_params(3e-3, 0.25, 0.5)                                  # label-free Baum-Welch, same loop as run_detect2.py
    for it in range(a.iters):                                       # (E-step with the damped mean-field passes)
        s = tr.loglik_and_stats(cdets, None, passes=tr.passes)
        pL = np.clip(s["n01"] / s["occ0"], 1e-6, 0.2); p_ret = float(np.clip(s["n10"] / max(s["occ1"], 1e-9), 1e-3, 1.0))
        tr.set_params(pL, p_ret, 0.5)
    print(f"[calib]  {a.iters} EM iterations: mean p_L {tr.p_L.mean():.2e} (true {a.pL:g}), "
          f"p_ret {tr.p_ret:.3f} (true {1 / a.tau:.3f}), log-lik/shot {s['ll'] / a.cal:.3f}")

    pl, pr, pf = tr.posteriors(dets)                                # per shot, per data qubit, per round
    dm = det_metrics(pl, L)
    print(f"[track]  posterior mean {pl.mean():.4f}; detection AP {dm['AP']:.3f} (base rate {dm['base_rate']:.4f}), recall@0.5 {dm['recall']:.3f}")

    fm = FlagMatcher(lc)
    fA = fm.decode_plain(dets)[:, 0] != obs
    fB = fm.decode_with_posteriors(dets, L.astype(np.float32), None, None, thresh=0.02)[:, 0] != obs
    fX = fm.decode_with_posteriors(dets, pl, pr, pf, thresh=0.02)[:, 0] != obs
    R = a.rounds; eA, eB, eX = (per_round(f.mean(), R) for f in (fA, fB, fX))
    f_rec = (eA - eX) / (eA - eB) if eA > eB else float("nan")
    b, c = int((~fX & fA).sum()), int((fX & ~fA).sum())
    pval = binomtest(b, b + c, 0.5).pvalue if b + c else 1.0
    print(f"[decode] P_fail  A (plain MWPM) {fA.mean():.4f} | B (oracle flags) {fB.mean():.4f} | X (tracker soft weights) {fX.mean():.4f}")
    print(f"[decode] fraction of oracle gain recovered f = {f_rec:.2f}; McNemar X vs A {b} / {c} (p = {pval:.2g})")
    print(f"[done]   {time.time() - t0:.1f} s")
    assert np.isfinite(fX.mean()) and len(fX) == a.shots
    return 0


if __name__ == "__main__":
    sys.exit(main())
