# IBM ibm_berlin real-data test of syndrome-only hidden-state tracking (project C3)

*21 Oct 2026. Data: Zenodo 23335425 (Lange et al., arXiv:2610.03869), `ibm_berlin.zip`, surface-code memory, 100 000 shots per run. Protocol frozen before decoding: ibm_protocol.md (v1 original, v2 adds amendment 1). Every number below was computed in this session from the files listed at the end.*

## 1. Verdict

**KILL by the pre-registered rule, for both tracker variants.** Pooled over the 10 held-out runs (d = 3 and d = 5 on qubit set 85, T = 5 to 50), the per-shot tracker does not beat matching on the shipped calibrated DEM: X is even with it (A wrong & X right / X wrong & A right = 84805 / 85268, p = 0.26) and the reallocation variant X' is worse (79689 / 82471). Both lose to the static average-information control A4 (X vs A4: 49389 / 53169). The placebo, which gives each shot another shot's posteriors, does not help (58354 / 59296). The test therefore has no leak.

**What is real.** The hardware has a strong, persistent per-detector hidden state that the static p_ij DEM does not represent (Fig. a). This is the multi-round fingerprint C3 was designed for. But in this data, knowing it per shot buys no more than a static re-weighting of the time-like edges does.

!`IBM results`

*Figure. (a) Probability that a detector fires again after k consecutive firings. Solid lines are hardware; dotted lines are shots sampled from the calibrated DEM of the same run. All runs are T = 50, 100 000 shots, all detector chains pooled; DEM points with fewer than 50 runs are dropped. (b) Held-out logical error per round of each decoder divided by that of MWPM on the shipped DEM, with paired bootstrap 95 % intervals. Runs with P_fail ≥ 0.5 are saturated and have no defined ratio.*

## 2. What was done
1. **Baseline.** MWPM (PyMatching 2.4) on the shipped p_ij DEM of each run; P_fail 0.11 to 0.50.
2. **Diagnostics, before any tracker decoding.** The detection fraction rises with memory length (d = 5: 0.17 at T = 5; 0.28 averaged over T = 50; 0.35 to 0.37 in the last rounds). The continuation probability rises with k on hardware, from 0.31 to 0.39 at k = 1 to 0.60 to 0.72 at k = 12 to 14 on the two qubit-85 runs and to 0.54 on the tuning run (qubits 36). Under the DEM it stays flat at 0.33 to 0.46.
3. **Tracker.** A per-detector two-state hidden-Markov model, fitted by maximum likelihood on 20 000 tuning shots (d = 3, qubits 36, T = 50; syndromes only). Fitted values: a = 0.028 per round into the hot state, b = 0.062 out of it (mean episode ≈ 16 rounds), hot firing probability q = 0.48, normal-state scale s = 0.52. The likelihood gain over a one-state model is 8.8 nats per shot. Posterior → time-like edges: p_e ⊕ c·π.
4. **Tuning** on qubit set 36 only (5 T values × 6 configurations). The frozen rule selected the smoothed posterior with c = 0.25, which was already net −115 of 250 000 tuning shots. **Amendment 1** (X') replaced "add on top" by "reallocate". Reason: the shipped DEM was calibrated on the same leaky data and already contains the average hot contribution. X' was +650 of 250 000 on tuning and was frozen with α halved to 0.025.
5. **Held-out:** 10 runs, decoders A, X or X', A4, P; paired statistics; Holm correction across runs.

## 3. Held-out results, X (pre-registered)
| run | P_fail A | X | A4 | P | ε ratio X/A [95 %] | ε ratio A4/A | X vs A (b/c) | Holm p | X vs A4 (b/c) |
|---|---|---|---|---|---|---|---|---|---|
| d3_q85_T5 | 0.1130 | 0.1395 | 0.1183 | 0.1246 | 1.268 [1.243, 1.294] | 1.052 | 4581/7232 | 1.9e-131 | 2086/4210 |
| d3_q85_T10 | 0.2126 | 0.2705 | 0.2458 | 0.2466 | 1.391 [1.366, 1.416] | 1.214 | 9821/15614 | 2.6e-290 | 5030/7502 |
| d3_q85_T20 | 0.3318 | 0.3197 | 0.3233 | 0.3248 | 0.938 [0.926, 0.949] | 0.956 | 7504/6293 | 3.9e-24 | 4699/4346 |
| d3_q85_T30 | 0.3978 | 0.3900 | 0.3907 | 0.3928 | 0.955 [0.940, 0.971] | 0.958 | 9695/8914 | 4.3e-08 | 5998/5932 |
| d3_q85_T50 | 0.4556 | 0.4506 | 0.4542 | 0.4561 | 0.957 [0.932, 0.982] | 0.987 | 12003/11500 | 0.0021 | 8396/8035 |
| d5_q85_T5 | 0.1279 | 0.1128 | 0.1160 | 0.1220 | 0.869 [0.856, 0.882] | 0.897 | 4240/2734 | 2.6e-72 | 2027/1706 |
| d5_q85_T10 | 0.2734 | 0.2480 | 0.2488 | 0.2626 | 0.870 [0.859, 0.881] | 0.874 | 8244/5699 | 1.3e-102 | 3903/3816 |
| d5_q85_T20 | 0.4092 | 0.3993 | 0.3986 | 0.4039 | 0.942 [0.929, 0.956] | 0.938 | 7920/6929 | 2.2e-15 | 4578/4649 |
| d5_q85_T30 | 0.4733 | 0.4685 | 0.4679 | 0.4708 | 0.946 [0.916, 0.975] | 0.940 | 9789/9304 | 0.0014 | 5931/5985 |
| d5_q85_T50 | 0.4960 | 0.4964 | 0.4939 | 0.4959 | 1.021 [0.868, 1.257] | 0.918 | 11008/11049 | 0.79 | 6741/6988 |

## 4. Held-out results, X' (amendment 1)
| run | P_fail A | X' | A4' | P' | ε ratio X'/A [95 %] | ε ratio A4/A | X' vs A (b/c) | Holm p | X' vs A4' (b/c) |
|---|---|---|---|---|---|---|---|---|---|
| d3_q85_T5 | 0.1130 | 0.1395 | 0.1162 | 0.1245 | 1.268 [1.244, 1.294] | 1.052 | 4492/7146 | 9.5e-134 | 2079/4412 |
| d3_q85_T10 | 0.2126 | 0.2651 | 0.2386 | 0.2389 | 1.351 [1.328, 1.374] | 1.214 | 9853/15101 | 1e-242 | 4950/7600 |
| d3_q85_T20 | 0.3318 | 0.3204 | 0.3247 | 0.3416 | 0.941 [0.930, 0.952] | 0.956 | 7104/5963 | 1.1e-22 | 5172/4749 |
| d3_q85_T30 | 0.3978 | 0.3917 | 0.3917 | 0.4060 | 0.964 [0.950, 0.979] | 0.958 | 9059/8445 | 1.8e-05 | 6985/6981 |
| d3_q85_T50 | 0.4556 | 0.4527 | 0.4538 | 0.4624 | 0.974 [0.949, 1.001] | 0.987 | 11444/11151 | 0.16 | 9833/9722 |
| d5_q85_T5 | 0.1279 | 0.1145 | 0.1188 | 0.1440 | 0.883 [0.871, 0.896] | 0.897 | 3967/2626 | 1.1e-60 | 2471/2034 |
| d5_q85_T10 | 0.2734 | 0.2591 | 0.2575 | 0.3002 | 0.925 [0.914, 0.937] | 0.874 | 7298/5860 | 3.2e-35 | 4623/4774 |
| d5_q85_T20 | 0.4092 | 0.4062 | 0.4038 | 0.4175 | 0.981 [0.968, 0.995] | 0.938 | 7213/6905 | 0.039 | 5496/5733 |
| d5_q85_T30 | 0.4733 | 0.4715 | 0.4716 | 0.4745 | 0.978 [0.947, 1.008] | 0.940 | 9045/8860 | 0.33 | 7314/7297 |
| d5_q85_T50 | 0.4960 | 0.4980 | 0.4966 | 0.4976 | 1.134 [0.938, 1.475] | 0.918 | 10214/10414 | 0.33 | 8620/8753 |

## 5. Reading (exploratory; not covered by the pre-registration)
- **Short d = 3 memories are badly harmed** (X/A = 1.27 at T = 5, 1.39 at T = 10). The hot-state parameters were fitted at T = 50, where about a third of detector-rounds are hot. With s = 0.52, every ordinary detection pair looks like a hot episode in short runs. This is a calibration failure of a single global model, not evidence against a hidden state.
- **d = 5 and long memories gain 4 to 13 % in ε against the shipped DEM**, significant after Holm. But A4, a *static* boost of time-like edges by their average posterior, gets the same gain. The shipped p_ij DEM under-weights time-like (measurement-like) errors in these runs; a static correction recovers it. This repeats the simulation finding that a static learned DEM captures about 0.4 of the leakage gain.
- **Per-shot information beyond A4 is visible only in a few runs.** The clearest are d = 5 T = 5 (X 0.1128 vs A4 0.1160) and d = 3 T = 20/50. These are not enough to offset the short-run harm, and no claim is made from them.
- **Why per-shot fails even though the hidden state is strong:** the background detection fraction is 0.11 to 0.37, above the ≈ 0.06 at which C3's simulations already lost most of the gain. At d = 5 the code is above threshold (P_fail ≈ 0.5 by T = 30). A detector that fires half the time over many rounds is identified by the tracker, but in this noise its correct weight is close to what a static average already gives.

## 6. What would be a fair next test (not run)
A tracker re-fitted per run on syndromes only (no labels), or with round-dependent hot-state priors. This would remove the T = 5 / 10 calibration failure. It must be tested on **data not used here**: the `stability_d3` runs in the same archive, or a new IBM dataset. Both memory patches have now been used, one for tuning and one for evaluation, so a third variant tuned on them would carry real overfitting risk.

## 7. Files
ibm_protocol.md (v2), ibm_results_figure.png, ibm_stats.json, ibm_ratio_table.json, hmm_params_q36T50.json, diag_memory_*_T50.json, baseline_A.json, scripts (ibm_common.py, ibm_tracker.py, run_ibm.py, stats_ibm.py, diag.py), per-shot failure arrays (ibm_pershot.tar.gz).
