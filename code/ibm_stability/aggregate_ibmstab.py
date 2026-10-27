"""Apply the frozen rules of ibm_stab_protocol.md to c3/ibmstab/*/results.json."""
import json, os, sys
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
from scipy.stats import binomtest
from run_ibm_stab import RUNS
R = {r: json.load(open(f"{paths.IBMSTAB}/{r}/results.json")) for r in RUNS if os.path.exists(f"{paths.IBMSTAB}/{r}/results.json")}
FAM = {"T_sweep": ["T5", "T10", "T20", "T50", "T100"], "alpha_T20": [r for r in RUNS if r.startswith("T20_alpha")],
       "alpha_T100": [r for r in RUNS if r.startswith("T100_alpha")], "all": RUNS}
def pooled(key, runs):
    runs = [r for r in runs if r in R]
    x = sum(R[r]["mcnemar"][key]["x_right_only"] for r in runs); y = sum(R[r]["mcnemar"][key]["y_right_only"] for r in runs)
    return dict(x_right_only=x, y_right_only=y, p=float(binomtest(x, x + y, 0.5).pvalue) if x + y else 1.0, n_runs=len(runs))
out = dict(runs_done=list(R), pooled={}, per_run={})
for fam, runs in FAM.items():
    out["pooled"][fam] = {k: pooled(k, runs) for k in ["X_vs_A", "X_vs_A4", "P_vs_A", "X_vs_Xold", "A4_vs_A", "Xold_vs_A"]}
a = out["pooled"]["all"]
c1 = a["X_vs_A"]["x_right_only"] > a["X_vs_A"]["y_right_only"] and a["X_vs_A"]["p"] < 0.05
c2 = a["X_vs_A4"]["x_right_only"] > a["X_vs_A4"]["y_right_only"] and a["X_vs_A4"]["p"] < 0.05
c3 = not (a["P_vs_A"]["x_right_only"] > a["P_vs_A"]["y_right_only"] and a["P_vs_A"]["p"] < 0.05)
out["PR1"] = dict(X_beats_A=c1, X_beats_A4=c2, placebo_clean=c3, met=bool(c1 and c2 and c3 and len(R) == 17))
# Holm per-run for X vs A
ps = sorted((R[r]["mcnemar"]["X_vs_A"]["p"], r) for r in R); m = len(ps)
holm = {}; running = 0
for k, (p, r) in enumerate(ps): running = max(running, min(1, (m - k) * p)); holm[r] = running
for r in R:
    x = R[r]
    out["per_run"][r] = dict(T=x["T"], detfrac=round(x["detfrac"], 3), pL=round(x["pL_mean"], 5), p_ret=round(x["p_ret"], 3), dLL=round(x["dLL_per_shot"], 3),
                             mean_pi=round(x["mean_pi"], 4), pfail={k: round(v, 4) for k, v in x["pfail"].items()},
                             X_vs_A=(x["mcnemar"]["X_vs_A"]["x_right_only"], x["mcnemar"]["X_vs_A"]["y_right_only"], round(x["mcnemar"]["X_vs_A"]["p"], 4), round(holm[r], 4)),
                             X_vs_A4=(x["mcnemar"]["X_vs_A4"]["x_right_only"], x["mcnemar"]["X_vs_A4"]["y_right_only"], round(x["mcnemar"]["X_vs_A4"]["p"], 4)))
json.dump(out, open(f"{paths.RESULTS_DATA}/ibmstab_aggregate.json", "w"), indent=1)
print("runs", len(R), "PR1", out["PR1"])
for fam in FAM: print(fam, {k: (v["x_right_only"], v["y_right_only"], f"{v['p']:.2g}") for k, v in out["pooled"][fam].items()})
for r, v in out["per_run"].items(): print(r, v["detfrac"], v["pL"], v["p_ret"], v["dLL"], v["pfail"], v["X_vs_A"], v["X_vs_A4"])
