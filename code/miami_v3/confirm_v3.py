"""Rule 4 of v3_dev_protocol.md: re-run the chosen variant (R + G2) on new seeds. Usage: confirm_v3.py SCENARIO SEED"""
import sys, os, json, time, numpy as np
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
import dev_v3 as D
from xa_tracker_r import XATrackerR
from leakage_sim import FlagMatcher
D.TrackerCls = XATrackerR
name, seed = sys.argv[1], int(sys.argv[2]); t0 = time.time()
S = D.scenario(name, seed); lc = S["model"]; dets, obs, L = S["data"]; cal = S["cal"]
A = FlagMatcher(lc).decode_plain(dets)[:, 0] != obs
h1, h2 = cal[: len(cal) // 2], cal[len(cal) // 2:]
nul = S["null"](len(cal), seed + 2); n1, n2 = nul[: len(nul) // 2], nul[len(nul) // 2:]
trf = D.em(lc, cal)
g_real = D.qgain(D.em(lc, h1), h2); g_null = D.qgain(D.em(lc, n1), n2); thr = float(g_null.max())
keep = g_real > thr; trf.set_params(np.where(keep, trf.p_L, 1e-6), trf.p_ret, 0.5)
r = D.evaluate(lc, trf, dets, obs, A) if keep.any() else dict(X=float(A.mean()), X_only=0, A_only=0, p=1.0, mean_pi=0.0)
print(json.dumps(dict(scenario=name, seed=seed, variant="R+G2", A=float(A.mean()), keep=keep.astype(int).tolist(), thr=round(thr, 1),
                      p_ret=round(trf.p_ret, 3), seconds=round(time.time() - t0), **S["info"], **r)), flush=True)
