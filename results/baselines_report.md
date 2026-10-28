# Stronger baselines for soft leakage tracking (project C3), baselines_report.md

Date: 18 Oct 2026. All data are SYNTHETIC (Stim 1.16 + `leakage_sim.py`, rotated surface code memory-Z, 25 rounds, SI1000 p = 1e-3, phenomenological multi-round data-qubit leakage, ρ = 1/2). Every new decoder was run on the *same shots* as the archived decoders (cells regenerated with the pre-registration seed; the regenerated A-decoder failure array matched the archived one bit for bit on every cell). f is the fraction of the oracle gain recovered, f = (p_A − p_X)/(p_A − p_B), with a paired shot-level bootstrap (2000 resamples, seed 42); when a new decoder was run on fewer shots, the archived decoders are re-evaluated on exactly those shots so the comparison stays paired.

## 1. Headline

At the d = 5 centre cell (p_L = 2e-3, τ = 8, 1e5 shots): **belief matching alone captures 0.17 [0.13, 0.20] of the oracle gain; CNN soft weights add 0.61 on top** (belief matching with the CNN lag-2 posterior folded into the DEM priors reaches f = 0.77 [0.75, 0.80], versus f = 0.72 [0.70, 0.74] for CNN soft weights with plain MWPM).
At d = 3 (100000 shots): belief matching alone 0.24 [0.22, 0.27]; belief matching + CNN priors 0.69 [0.67, 0.72]; CNN soft weights + MWPM on the same shots 0.67 [0.64, 0.70].
At d = 7 (30000 shots): belief matching alone 0.13 [0.06, 0.19]; belief matching + CNN priors 0.85 [0.82, 0.88]; CNN soft weights + MWPM on the same shots 0.83 [0.79, 0.86].

Ordering by f at the d = 5 centre cell (computed from the tables below): belief matching alone (0.17) < count heuristic w=4 + soft rule (0.35) < static data-fitted DEM (A2'learn) (0.42) < HMM soft (0.51) < CNN soft (0.72) < belief matching + CNN priors (0.77). Note that belief matching without leakage information ranks below the static leaky-data DEM fit and below the count heuristic: handling correlations in the circuit model is not a substitute for knowing *which* qubit is leaked *in this shot*; the per-shot posterior is what carries the gain.

## 2. Results per cell (identical shots within each table)

### G1_d3_pL0.002_tau8  (d = 3, p_L = 0.002, τ = 8)

All rows on the same 1e5 shots ('not available' = control decoder not in the archived tarball for this cell).

| decoder | shots | failures | p_fail [Wilson 95%] | f = (p_A−p_X)/(p_A−p_B) [paired bootstrap 95%] | recall / precision (thr 0.5) |
|---|---|---|---|---|---|
| A: ignore leakage (MWPM, circuit DEM) | 100000 | 7146 | 0.0715 [0.0699, 0.0731] | to | to |
| B: oracle flags + soft rule | 100000 | 2658 | 0.0266 [0.0256, 0.0276] | to | to |
| A4: model-averaged DEM | to | to | not available | to | to |
| A2 (old): Spitz pairwise DEM, unrestricted | to | to | not available | to | to |
| A2'corr: pairwise-correlation DEM on circuit graph | 100000 | 5492 | 0.0549 [0.0535, 0.0563] | 0.37 [0.34, 0.39] | to |
| A2'learn: per-class edge factors fitted on leaky data | 100000 | 5054 | 0.0505 [0.0492, 0.0519] | 0.47 [0.44, 0.49] | to |
| A2'corr+learn: both | 100000 | 5229 | 0.0523 [0.0509, 0.0537] | 0.43 [0.40, 0.45] | to |
| belief matching, leakage-free DEM | 100000 | 6049 | 0.0605 [0.0590, 0.0620] | 0.24 [0.22, 0.27] | to |
| count heuristic w=3 (lag 2) + soft rule | 100000 | 5491 | 0.0549 [0.0535, 0.0563] | 0.37 [0.34, 0.40] | 0.31 / 0.54 |
| HMM tracker (lag 0) + soft rule | 100000 | 5130 | 0.0513 [0.0499, 0.0527] | 0.45 [0.42, 0.48] | to |
| CNN tracker (lag 2) + soft rule | 100000 | 4139 | 0.0414 [0.0402, 0.0426] | 0.67 [0.64, 0.70] | to |
| CNN tracker (lag 2), hard flags | 100000 | 4677 | 0.0468 [0.0455, 0.0481] | 0.55 [0.53, 0.57] | to |
| belief matching + CNN lag-2 soft priors | 100000 | 4041 | 0.0404 [0.0392, 0.0416] | 0.69 [0.67, 0.72] | to |

### G1_d5_pL0.002_tau8  (d = 5, p_L = 0.002, τ = 8)

All rows on the same 1e5 shots ('not available' = control decoder not in the archived tarball for this cell).

| decoder | shots | failures | p_fail [Wilson 95%] | f = (p_A−p_X)/(p_A−p_B) [paired bootstrap 95%] | recall / precision (thr 0.5) |
|---|---|---|---|---|---|
| A: ignore leakage (MWPM, circuit DEM) | 100000 | 3870 | 0.0387 [0.0375, 0.0399] | to | to |
| B: oracle flags + soft rule | 100000 | 658 | 0.0066 [0.0061, 0.0071] | to | to |
| A4: model-averaged DEM | 100000 | 3133 | 0.0313 [0.0303, 0.0324] | 0.23 [0.21, 0.25] | to |
| A2 (old): Spitz pairwise DEM, unrestricted | 100000 | 12756 | 0.1276 [0.1255, 0.1296] | -2.77 [-2.91, -2.64] | to |
| A2'corr: pairwise-correlation DEM on circuit graph | 100000 | 3670 | 0.0367 [0.0356, 0.0379] | 0.06 [0.04, 0.09] | to |
| A2'learn: per-class edge factors fitted on leaky data | 100000 | 2521 | 0.0252 [0.0243, 0.0262] | 0.42 [0.39, 0.45] | to |
| A2'corr+learn: both | 100000 | 2499 | 0.0250 [0.0240, 0.0260] | 0.43 [0.40, 0.45] | to |
| belief matching, leakage-free DEM | 100000 | 3339 | 0.0334 [0.0323, 0.0345] | 0.17 [0.13, 0.20] | to |
| count heuristic w=3 (lag 2) + soft rule | 100000 | 2781 | 0.0278 [0.0268, 0.0288] | 0.34 [0.31, 0.37] | 0.29 / 0.71 |
| HMM tracker (lag 0) + soft rule | 100000 | 2236 | 0.0224 [0.0215, 0.0233] | 0.51 [0.48, 0.53] | to |
| CNN tracker (lag 2) + soft rule | 100000 | 1557 | 0.0156 [0.0148, 0.0164] | 0.72 [0.70, 0.74] | to |
| CNN tracker (lag 2), hard flags | 100000 | 1796 | 0.0180 [0.0172, 0.0188] | 0.65 [0.62, 0.67] | to |
| belief matching + CNN lag-2 soft priors | 100000 | 1384 | 0.0138 [0.0131, 0.0146] | 0.77 [0.75, 0.80] | to |

### G1_d7_pL0.002_tau8  (d = 7, p_L = 0.002, τ = 8)

Belief-matching rows for this cell were run on the first 30000 shots (compute budget); archived decoders are shown on the same 30000 shots. Rows marked * (count heuristic, static DEM controls) were run on all 1e5 shots and their f is relative to A and B on those 1e5 shots.

| decoder | shots | failures | p_fail [Wilson 95%] | f = (p_A−p_X)/(p_A−p_B) [paired bootstrap 95%] | recall / precision (thr 0.5) |
|---|---|---|---|---|---|
| A: ignore leakage (MWPM, circuit DEM) | 30000 | 818 | 0.0273 [0.0255, 0.0292] | to | to |
| B: oracle flags + soft rule | 30000 | 45 | 0.0015 [0.0011, 0.0020] | to | to |
| A4: model-averaged DEM | 30000 | 528 | 0.0176 [0.0162, 0.0192] | 0.38 [0.33, 0.42] | to |
| A2 (old): Spitz pairwise DEM, unrestricted | 30000 | 4622 | 0.1541 [0.1500, 0.1582] | -4.92 [-5.38, -4.53] | to |
| A2'corr: pairwise-correlation DEM on circuit graph | 100000 * | 2534 | 0.0253 [0.0244, 0.0263] | 0.10 [0.07, 0.13] | to |
| A2'learn: per-class edge factors fitted on leaky data | 100000 * | 1248 | 0.0125 [0.0118, 0.0132] | 0.59 [0.56, 0.61] | to |
| A2'corr+learn: both | 100000 * | 1211 | 0.0121 [0.0115, 0.0128] | 0.60 [0.58, 0.63] | to |
| belief matching, leakage-free DEM | 30000 | 718 | 0.0239 [0.0223, 0.0257] | 0.13 [0.06, 0.19] | to |
| count heuristic w=3 (lag 2) + soft rule | 100000 * | 1644 | 0.0164 [0.0157, 0.0172] | 0.44 [0.41, 0.47] | 0.35 / 0.70 |
| HMM tracker (lag 0) + soft rule | 30000 | 321 | 0.0107 [0.0096, 0.0119] | 0.64 [0.60, 0.69] | to |
| CNN tracker (lag 2) + soft rule | 30000 | 179 | 0.0060 [0.0052, 0.0069] | 0.83 [0.79, 0.86] | to |
| CNN tracker (lag 2), hard flags | 30000 | 202 | 0.0067 [0.0059, 0.0077] | 0.80 [0.76, 0.83] | to |
| belief matching + CNN lag-2 soft priors | 30000 | 159 | 0.0053 [0.0045, 0.0062] | 0.85 [0.82, 0.88] | to |

Rows on all 1e5 shots:

| decoder | shots | failures | p_fail [Wilson 95%] | f = (p_A−p_X)/(p_A−p_B) [paired bootstrap 95%] | recall / precision (thr 0.5) |
|---|---|---|---|---|---|
| A: ignore leakage (MWPM, circuit DEM) | 100000 | 2802 | 0.0280 [0.0270, 0.0291] | to | to |
| B: oracle flags + soft rule | 100000 | 161 | 0.0016 [0.0014, 0.0019] | to | to |
| A2'corr: pairwise-correlation DEM on circuit graph | 100000 | 2534 | 0.0253 [0.0244, 0.0263] | 0.10 [0.07, 0.13] | to |
| A2'learn: per-class edge factors fitted on leaky data | 100000 | 1248 | 0.0125 [0.0118, 0.0132] | 0.59 [0.56, 0.61] | to |
| count heuristic w=3 (lag 2) + soft rule | 100000 | 1644 | 0.0164 [0.0157, 0.0172] | 0.44 [0.41, 0.47] | 0.35 / 0.70 |
| HMM tracker (lag 0) + soft rule | 100000 | 1044 | 0.0104 [0.0098, 0.0111] | 0.67 [0.64, 0.69] | to |
| CNN tracker (lag 2) + soft rule | 100000 | 577 | 0.0058 [0.0053, 0.0063] | 0.84 [0.83, 0.86] | to |

### G1_d5_pL0.001_tau4  (d = 5, p_L = 0.001, τ = 4)

Belief-matching rows for this cell were run on the first 50000 shots (compute budget); archived decoders are shown on the same 50000 shots. Rows marked * (count heuristic, static DEM controls) were run on all 1e5 shots and their f is relative to A and B on those 1e5 shots.

| decoder | shots | failures | p_fail [Wilson 95%] | f = (p_A−p_X)/(p_A−p_B) [paired bootstrap 95%] | recall / precision (thr 0.5) |
|---|---|---|---|---|---|
| A: ignore leakage (MWPM, circuit DEM) | 50000 | 543 | 0.0109 [0.0100, 0.0118] | to | to |
| B: oracle flags + soft rule | 50000 | 158 | 0.0032 [0.0027, 0.0037] | to | to |
| A4: model-averaged DEM | 50000 | 497 | 0.0099 [0.0091, 0.0108] | 0.12 [0.07, 0.17] | to |
| A2 (old): Spitz pairwise DEM, unrestricted | 50000 | 482 | 0.0096 [0.0088, 0.0105] | 0.16 [0.08, 0.24] | to |
| A2'corr: pairwise-correlation DEM on circuit graph | 100000 * | 992 | 0.0099 [0.0093, 0.0106] | 0.11 [0.06, 0.17] | to |
| A2'learn: per-class edge factors fitted on leaky data | 100000 * | 799 | 0.0080 [0.0075, 0.0086] | 0.37 [0.31, 0.43] | to |
| A2'corr+learn: both | 100000 * | 830 | 0.0083 [0.0078, 0.0089] | 0.33 [0.26, 0.39] | to |
| belief matching, leakage-free DEM | 50000 | 436 | 0.0087 [0.0079, 0.0096] | 0.28 [0.17, 0.38] | to |
| count heuristic w=3 (lag 2) + soft rule | 100000 * | 842 | 0.0084 [0.0079, 0.0090] | 0.31 [0.24, 0.38] | 0.26 / 0.68 |
| HMM tracker (lag 0) + soft rule | 50000 | 349 | 0.0070 [0.0063, 0.0077] | 0.50 [0.41, 0.59] | to |
| CNN tracker (lag 2) + soft rule | 50000 | 297 | 0.0059 [0.0053, 0.0067] | 0.64 [0.56, 0.71] | to |
| CNN tracker (lag 2), hard flags | 50000 | 379 | 0.0076 [0.0069, 0.0084] | 0.43 [0.35, 0.50] | to |
| belief matching + CNN lag-2 soft priors | 50000 | 261 | 0.0052 [0.0046, 0.0059] | 0.73 [0.65, 0.82] | to |

Rows on all 1e5 shots:

| decoder | shots | failures | p_fail [Wilson 95%] | f = (p_A−p_X)/(p_A−p_B) [paired bootstrap 95%] | recall / precision (thr 0.5) |
|---|---|---|---|---|---|
| A: ignore leakage (MWPM, circuit DEM) | 100000 | 1079 | 0.0108 [0.0102, 0.0114] | to | to |
| B: oracle flags + soft rule | 100000 | 318 | 0.0032 [0.0028, 0.0035] | to | to |
| A2'corr: pairwise-correlation DEM on circuit graph | 100000 | 992 | 0.0099 [0.0093, 0.0106] | 0.11 [0.06, 0.17] | to |
| A2'learn: per-class edge factors fitted on leaky data | 100000 | 799 | 0.0080 [0.0075, 0.0086] | 0.37 [0.31, 0.43] | to |
| count heuristic w=3 (lag 2) + soft rule | 100000 | 842 | 0.0084 [0.0079, 0.0090] | 0.31 [0.24, 0.38] | 0.26 / 0.68 |
| HMM tracker (lag 0) + soft rule | 100000 | 712 | 0.0071 [0.0066, 0.0077] | 0.48 [0.42, 0.55] | to |
| CNN tracker (lag 2) + soft rule | 100000 | 576 | 0.0058 [0.0053, 0.0062] | 0.66 [0.61, 0.71] | to |

### G1_d5_pL0.005_tau16  (d = 5, p_L = 0.005, τ = 16)

Belief-matching rows for this cell were run on the first 50000 shots (compute budget); archived decoders are shown on the same 50000 shots. Rows marked * (count heuristic, static DEM controls) were run on all 1e5 shots and their f is relative to A and B on those 1e5 shots.

| decoder | shots | failures | p_fail [Wilson 95%] | f = (p_A−p_X)/(p_A−p_B) [paired bootstrap 95%] | recall / precision (thr 0.5) |
|---|---|---|---|---|---|
| A: ignore leakage (MWPM, circuit DEM) | 50000 | 8094 | 0.1619 [0.1587, 0.1651] | to | to |
| B: oracle flags + soft rule | 50000 | 1271 | 0.0254 [0.0241, 0.0268] | to | to |
| A4: model-averaged DEM | 50000 | 5951 | 0.1190 [0.1162, 0.1219] | 0.31 [0.30, 0.33] | to |
| A2 (old): Spitz pairwise DEM, unrestricted | 50000 | 13813 | 0.2763 [0.2724, 0.2802] | -0.84 [-0.89, -0.79] | to |
| A2'corr: pairwise-correlation DEM on circuit graph | 100000 * | 15268 | 0.1527 [0.1505, 0.1549] | 0.05 [0.04, 0.07] | to |
| A2'learn: per-class edge factors fitted on leaky data | 100000 * | 10223 | 0.1022 [0.1004, 0.1041] | 0.43 [0.41, 0.44] | to |
| A2'corr+learn: both | to | to | not available | to | to |
| belief matching, leakage-free DEM | 50000 | 7344 | 0.1469 [0.1438, 0.1500] | 0.11 [0.09, 0.13] | to |
| count heuristic w=3 (lag 2) + soft rule | 100000 * | 13097 | 0.1310 [0.1289, 0.1331] | 0.21 [0.20, 0.23] | 0.30 / 0.65 |
| HMM tracker (lag 0) + soft rule | 50000 | 4978 | 0.0996 [0.0970, 0.1022] | 0.46 [0.44, 0.48] | to |
| CNN tracker (lag 2) + soft rule | 50000 | 3499 | 0.0700 [0.0678, 0.0722] | 0.67 [0.66, 0.69] | to |
| CNN tracker (lag 2), hard flags | 50000 | 3505 | 0.0701 [0.0679, 0.0724] | 0.67 [0.66, 0.69] | to |
| belief matching + CNN lag-2 soft priors | 50000 | 3113 | 0.0623 [0.0602, 0.0644] | 0.73 [0.71, 0.75] | to |

Rows on all 1e5 shots:

| decoder | shots | failures | p_fail [Wilson 95%] | f = (p_A−p_X)/(p_A−p_B) [paired bootstrap 95%] | recall / precision (thr 0.5) |
|---|---|---|---|---|---|
| A: ignore leakage (MWPM, circuit DEM) | 100000 | 15999 | 0.1600 [0.1577, 0.1623] | to | to |
| B: oracle flags + soft rule | 100000 | 2484 | 0.0248 [0.0239, 0.0258] | to | to |
| A2'corr: pairwise-correlation DEM on circuit graph | 100000 | 15268 | 0.1527 [0.1505, 0.1549] | 0.05 [0.04, 0.07] | to |
| A2'learn: per-class edge factors fitted on leaky data | 100000 | 10223 | 0.1022 [0.1004, 0.1041] | 0.43 [0.41, 0.44] | to |
| count heuristic w=3 (lag 2) + soft rule | 100000 | 13097 | 0.1310 [0.1289, 0.1331] | 0.21 [0.20, 0.23] | 0.30 / 0.65 |
| HMM tracker (lag 0) + soft rule | 100000 | 9967 | 0.0997 [0.0978, 0.1015] | 0.45 [0.43, 0.46] | to |
| CNN tracker (lag 2) + soft rule | 100000 | 7038 | 0.0704 [0.0688, 0.0720] | 0.66 [0.65, 0.67] | to |

## 3. Belief matching (referee point 3.3: 'correlated/belief matching on the same data')

Implementation: `beliefmatching` 0.2.0 (Higgott et al. 2023) with `ldpc` 2.4.1, product-sum BP, **10 iterations** (the Higgott default is 20; on a 1000-shot probe 10 and 20 iterations gave identical logical error, and 10 halves the run time, 37 vs 72 ms per shot at d = 5). BP runs on the full hyperedge DEM of the leakage-free circuit; when BP does not converge the BP marginals re-weight the matching graph and MWPM finishes the shot. `BM + CNN priors`: before BP, the prior of every hyperedge that leakage can flip is raised per shot with the same rule as decoder D, p_h' = p_h XOR c·π (c = ρ for the time-like hyperedges of the stabilisers adjacent to a leaked qubit, 2/3 for the X and Z return hyperedges, ρ for the final data hyperedge; π < 0.02 ignored), using `BpDecoder.update_channel_probs`. Every one of the simulator's leakage mechanisms maps onto an existing hyperedge column (0 missing at d = 3, 5, 7), so no new hyperedges were needed.

**Leakage-free control.** On the same base-noise realisation with p_L = 0 (50000 shots), belief matching lowers the logical error from 0.00188 (MWPM) to 0.00134, a relative reduction of 29%. With leakage (p_L = 2e-3) the relative reduction is 14%, i.e. belief matching's gain under leakage is of the same kind as its generic gain on Y-type correlated errors; it does not specifically track leakage.

BP convergence fraction (shots where BP alone found a consistent correction): G1_d3_pL0.002_tau8 BM_CNN_lag2_it10: 0.75; G1_d3_pL0.002_tau8 BM_it10: 0.66; G1_d5_pL0.002_tau8 BM_CNN_lag2_it10: 0.38; G1_d5_pL0.002_tau8 BM_it10: 0.29; G1_d7_pL0.002_tau8 BM_CNN_lag2_it10: 0.13; G1_d7_pL0.002_tau8 BM_it10: 0.09; G1_d5_pL0.001_tau4 BM_CNN_lag2_it10: 0.52; G1_d5_pL0.001_tau4 BM_it10: 0.50; G1_d5_pL0.005_tau16 BM_CNN_lag2_it10: 0.14; G1_d5_pL0.005_tau16 BM_it10: 0.06.

## 4. Heuristic detection-count tracker

For each data qubit q and round r the tracker counts detection events on the detectors of the stabilisers adjacent to q in the window of w rounds ending at round r + 2 (lag 2, the same look-ahead as the CNN lag-2 comparator). The posterior is a logistic function of the count, σ(a + b·count), fitted by maximum likelihood on 2e4 simulated shots with known labels (seed 101 + cell seed, the CNN training seed). π_ret = max(0, π_{r−1} − π_r) and π_final = π_{R−1} as in the HMM path; the posterior then goes through the identical soft-weight rule (thr 0.02).

| cell | w | a | b | recall | precision | mean delay (rounds) | f |
|---|---|---|---|---|---|---|---|
| G1_d3_pL0.002_tau8 | 3 | -6.49 | 1.34 | 0.31 | 0.54 | 1.27 | 0.37 [0.34, 0.40] |
| G1_d5_pL0.002_tau8 | 2 | -6.14 | 1.43 | 0.15 | 0.66 | 1.90 | 0.13 [0.09, 0.16] |
| G1_d5_pL0.002_tau8 | 3 | -6.90 | 1.29 | 0.29 | 0.71 | 1.26 | 0.34 [0.31, 0.37] |
| G1_d5_pL0.002_tau8 | 4 | -7.21 | 1.11 | 0.37 | 0.70 | 1.51 | 0.35 [0.32, 0.38] |
| G1_d7_pL0.002_tau8 | 3 | -7.17 | 1.30 | 0.35 | 0.70 | 1.09 | 0.44 [0.41, 0.47] |
| G1_d5_pL0.001_tau4 | 3 | -8.07 | 1.47 | 0.26 | 0.68 | 0.72 | 0.31 [0.24, 0.38] |
| G1_d5_pL0.005_tau16 | 3 | -5.51 | 1.01 | 0.30 | 0.65 | 1.70 | 0.21 [0.20, 0.23] |

At the d = 5 centre cell the count heuristic reaches f = 0.35 [0.32, 0.38] (w = 4) against 0.51 [0.48, 0.53] for the HMM and 0.72 [0.70, 0.74] for the CNN on the same 1e5 shots. Its recall at threshold 0.5 is low (0.15 to 0.37) because a leaked qubit randomises each adjacent outcome only with probability ρ = 1/2 and the count does not know the base detection rate of each stabiliser; the HMM and CNN use the spatial pattern (which stabilisers, X or Z type) and the temporal persistence, which the count discards.

## 5. Fair data-driven static DEM (control A2')

Two estimates from leaky calibration syndromes (separate seed 777 + cell seed, no labels), each producing ONE static matching graph that is then used for all test shots with plain MWPM:

* **A2'corr**, pairwise-correlation edge estimate (Spitz 2018 / Chen 2021 / Google 2023) restricted to the circuit matching graph, 1e5 calibration shots; an edge whose estimate is invalid (negative radicand or non-positive correlation) keeps its circuit value instead of being clipped to ~0 (that clipping is what made the old A2 harmful, f = −3.2 at d = 5).
* **A2'learn**, the circuit edge probabilities multiplied by one factor per edge class (time-like Z-type, time-like X-type, space-like, final space-like, diagonal space-time, boundary, final boundary), factors chosen on a grid {0.25 … 30} by coordinate descent (3 sweeps) to minimise the logical error on 2e4 calibration shots. This is a learned per-edge-weight fit of the kind Remm et al. use for dataset-averaged weights, with the objective being the decoding error itself rather than detector moments.

| cell | A4 model-avg (archived) | A2'corr f | A2'corr median p/p₀: time_Z / space / diag | A2'learn f | A2'learn factors: time_Z / space / diag / boundary |
|---|---|---|---|---|---|
| G1_d3_pL0.002_tau8 | to | 0.37 [0.34, 0.39] | 2.05 / 2.4 / 3.69 | 0.47 [0.44, 0.49] | 9.0 / 3.0 / 3.0 / 0.5 |
| G1_d5_pL0.002_tau8 | 0.23 [0.21, 0.25] | 0.06 [0.04, 0.09] | 2.21 / 2.31 / 3.85 | 0.42 [0.39, 0.45] | 6.0 / 0.35 / 0.25 / 0.25 |
| G1_d7_pL0.002_tau8 | 0.38 [0.35, 0.40] | 0.10 [0.07, 0.13] | 2.38 / 2.29 / 3.86 | 0.59 [0.56, 0.61] | 6.0 / 0.25 / 0.5 / 0.25 |
| G1_d5_pL0.001_tau4 | 0.12 [0.09, 0.16] | 0.11 [0.06, 0.17] | 1.43 / 1.47 / 2.08 | 0.37 [0.31, 0.43] | 3.0 / 0.35 / 0.5 / 0.35 |
| G1_d5_pL0.005_tau16 | 0.29 [0.28, 0.31] | 0.05 [0.04, 0.07] | 5.0 / 5.31 / 9.82 | 0.43 [0.41, 0.44] | 20.0 / 1.0 / 1.4 / 1.0 |

**What the static fit learns.** The pairwise-correlation estimate inflates *every* edge class by 1.4 to 3.9× (time-like and space-like alike, because a leaked qubit's randomised outcomes create detector pairs at every separation), which barely helps MWPM (f ≈ 0.05 to 0.11 at d = 5; 0.37 at d = 3 where the graph is tiny). The error-minimising fit instead makes the time-like Z-stabiliser edges 3 to 20× more probable *relative to* the space-like, diagonal and boundary edges (the X-stabiliser factor stays at 1 because X-type detectors do not enter the Z-memory decoding graph). In words: a static decoder can learn that 'measurement-like' errors are far more common than the circuit model says, and that alone recovers f ≈ 0.37 to 0.47, more than the archived A4 model-average control (0.12 to 0.33 at d = 5) and the right number to quote as the no-per-shot-information baseline. It still leaves more than half of the oracle gain on the table, and the fitted factors are at the edge of the grid (time_Z = 20 at p_L = 5e-3, τ = 16), i.e. the static model is trying to approximate a per-shot effect with a global constant.

## Derivation of the soft-weight rule  p_e = p_e0 XOR (c * pi)

**Setting.** A matching-graph edge `e` is a set of one or two detectors (plus possibly the logical observable) that one
physical fault flips. In the leakage-free circuit model the edge flips with probability `p_e0` (from the Stim detector
error model). Leakage adds a *second, independent* way to flip the same edge, but only while a hidden binary state is
on: `L = 1` means "data qubit q is leaked at round r".

**Flip probability given the leakage state.** Write `q_e = P(leakage mechanism flips e | L = 1)`:

| edge class | leakage mechanism in the simulator | q_e |
|---|---|---|
| time-like edge of a stabiliser adjacent to q, round r (detectors (m, r), (m, r+1)) | outcome of m at round r randomised, flipped with probability rho | `rho` (= 1/2 default) |
| X data edge and Z data edge of q at the return round | random Pauli X, Y or Z with probability 1/3 each; X-edge flips for X or Y, Z-edge flips for Y or Z | `2/3` each |
| final data edge of q (leaked during the last data measurement) | data outcome flipped with probability rho | `rho` |

Two independent flips of the same edge combine by exclusive-or: `a XOR b := a + b - 2ab` (the edge is flipped if exactly one of
the two mechanisms fires). So

    P(e flips | L = 1) = p_e0 XOR q_e,        P(e flips | L = 0) = p_e0.

**Marginalising the hidden state.** The tracker gives a posterior `pi = P(L = 1 | syndromes seen so far)`. The decoder does not
know `L`, so it must use the marginal flip probability:

    p_e = (1 - pi) * p_e0 + pi * (p_e0 XOR q_e)
        = p_e0 + pi * q_e - 2 * pi * q_e * p_e0
        = p_e0 XOR (pi * q_e).                                             (1)

Equation (1) is exact for one edge and one hidden state, and it is the rule implemented in `FlagMatcher._set_edge`
(`p_add = c * pi` with `c = q_e`). The matching weight is then the usual `w_e = log((1 - p_e) / p_e)`. For the oracle decoder
`pi` is 0 or 1 and (1) reduces to the two conditional values above.

**Approximations hidden in (1) when it is applied to the whole graph.**
1. *Independence across edges.* A leaked qubit flips the time-like edges of *all* its adjacent stabilisers (two or four
   of them) over *several consecutive rounds*, and a Y return error flips the X and Z data edges together. These are
   correlated multi-edge (hyperedge) events. Equation (1) keeps only the marginal probability of each edge and lets the
   matcher treat them as independent; this is the same approximation MWPM already makes for Y errors in the base model.
2. *Independence across rounds.* `L_r` and `L_{r+1}` are strongly correlated (geometric lifetime tau), so the flips of the
   time-like edges at rounds r and r+1 are correlated. Plugging in `pi_r` and `pi_{r+1}` separately ignores this.
3. *Return probability.* The exact quantity for the return edges is `P(L_{r-1} = 1, L_r = 0)`. The pipeline uses the CNN's
   second output head for this (trained on the true return labels); the HMM and the count tracker use
   `max(0, pi_{r-1} - pi_r)`, which is the exact value only when the posteriors are nested (no new leakage at r).
4. *Double use of the syndrome.* `pi` is computed from the same detection events that the matcher explains. The
   randomised stabiliser outcomes therefore enter twice: once as evidence for `pi`, once as defects to be matched.
   Within the independence approximation this is harmless (the weight is the marginal flip probability), but it
   is one reason why the optimal scale of `c` need not be exactly 1.
5. *Threshold.* Posteriors below 0.02 are left at `p_e0` (speed); the neglected `pi * q_e <= 0.01` is of the same order as
   `p_e0` for time-like edges (~ 5p = 0.005), so the threshold is not negligible in principle, only in effect.
6. *Hyperedges created by leakage are not added.* Mechanisms whose detector set is not already a graph edge (none in
   this simulator: every leakage effect is a single Pauli at a circuit location, so all land on existing edges or
   boundary edges) would need new edges.

**Why scan the scale s.** If the posterior is calibrated and the approximations are benign, the optimum of the scanned
rule `p_e = p_e0 XOR (s * c * pi)` should be at `s = 1`. An optimum at `s > 1` says that the decoder benefits from
*over*-trusting the flags (typically because the independence approximation 1 under-weights the joint event); `s < 1`
says the flags are over-confident or that the double-counting in 4 hurts. The scan therefore measures how far the
pipeline is from the "right" rule and how sensitive the headline fraction `f` is to that choice.


### Scan of the scale factor s at the d = 5 centre cell (CNN lag-2 posterior, first 5e4 shots)

| edge class scaled | s = 0.5 | 0.75 | 1.0 (archived D_CNN_lag2, same shots) | 1.25 | 1.5 |
|---|---|---|---|---|---|
| time-like (c = ρ) | 0.66 [0.62, 0.69] | 0.71 [0.68, 0.74] | 0.72 [0.69, 0.75] | 0.72 [0.69, 0.75] | 0.72 [0.69, 0.75] |
| return (c = 2/3) | 0.69 [0.66, 0.72] | 0.71 [0.68, 0.74] | 0.72 [0.69, 0.75] | 0.73 [0.70, 0.76] | 0.73 [0.70, 0.76] |
| final (c = ρ) | 0.72 [0.68, 0.75] | 0.72 [0.69, 0.75] | 0.72 [0.69, 0.75] | 0.72 [0.69, 0.75] | 0.72 [0.69, 0.75] |

Reading: all scanned values lie within about ±0.07 of the s = 1 value, and the intervals overlap. Halving the time-like constant costs the most (the time-like edges carry most of the gain, cf. the G2 oracle map), while a 1.5× constant is as good as or marginally better than s = 1, the direction expected when the independence approximation (item 1 above) under-weights the joint flips of several adjacent time-like edges. The headline f is therefore not the product of a tuned constant.

## 6. Deviations from the task specification and provenance

* belief matching at G1_d7_pL0.002_tau8 run on 30000 of 1e5 shots
* belief matching at G1_d5_pL0.001_tau4 run on 50000 of 1e5 shots
* belief matching at G1_d5_pL0.005_tau16 run on 50000 of 1e5 shots
* c-scan run on the first 5e4 of 1e5 shots (12 soft decodes); the s = 1 reference is the archived D_CNN_lag2 array on the same 5e4 shots (verified bit-identical when regenerated)
* belief propagation with 10 iterations instead of the package default 20 (identical error on a 1000-shot probe; 2× faster)
* leakage-free BM control on 5e4 shots
* count heuristic: w ∈ {2,3,4} scanned at the d = 5 centre cell only; w = 3 run at the other four cells
* A2'corr+learn (correlation estimate followed by class factors) missing at G1_d5_pL0.005_tau16 (run interrupted by a host restart; A2'corr and A2'learn for that cell are complete)
* the host restarted once during the runs (all chains killed and relaunched); every result file was produced by a complete run after the restart or before it

Scripts: `baselines_common.py` (cell regeneration + paired statistics), `run_bm.py`, `heuristic_tracker.py`, `run_soft.py` (count tracker and c-scan), `run_dem.py` (A2'), `build_report.py` (→ `baselines_results.csv`), `figure_baselines.py` (→ `baselines_figure.png`), `gen_report.py` (this file). Per-shot failure arrays and result JSONs: `baselines_results_pershot.tar.gz`.
