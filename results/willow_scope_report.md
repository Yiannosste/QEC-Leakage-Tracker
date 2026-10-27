# Willow scope-null test: Google 2025 d = 3 memory-Z run (Zenodo 13273331)

**Question.** Project C3 predicts that syndrome-only leakage tracking can only help a matching decoder when the device has a visible, long-lived population of leaked data qubits. On the 2023 Sycamore data (no data-qubit leakage removal, detection fraction 0.14 to 0.17) the trackers were already null. The 2025 Willow experiment uses data-qubit leakage removal (DQLR) every round, so the prediction is a **null with no detectable leakage signal**. This report tests that on one d = 3 run.

**Answer in one line.** Predicted null **confirmed**: the per-round detection fraction is flat to ±0.001, the phenomenological leakage model is bounded to ≤ 0.1 % leaked qubit-rounds for lifetimes τ ≥ 2 (and cannot be bounded by the curve at τ = 1), and every soft-weight decoder (HMM, CNN lag 0/2, static A4) changes the real logical error rate by −2 % to +1 %, none significant after multiple-comparison correction, while the same decoders gain 12 to 26 % on the matched simulator.

---

## 1. Data

| item | value |
|---|---|
| record / file | Zenodo 13273331, `google_105Q_surface_code_d3_d5_d7.zip` (5.72 GB; 9 959 members) |
| run used | `d3_at_q6_7/Z/r30`, centre d = 3 patch, memory-Z, **30 rounds** (the record has r01, r10, r13, r30, r50, …; there is no r25) |
| shots | 50 000; 240 detectors (4 at round 0, 8 × 29 bulk rounds, 4 final); 1 observable |
| circuit | XZZX rotated surface code, CZ + H, dynamical-decoupling X/Y on data qubits, `M(0.005)` inline measurement flips; 20 qubits in file (9 data, 8 measure, 3 idle) |
| files pulled | circuit_ideal.stim, circuit_noisy_si1000.stim, detection_events.b8, obs_flips_actual.b8, measurements.b8, sweep_bits.b8, metadata.json, 5 decoding pathways (error_model.dem + obs_flips_predicted.b8), README |
| how | Zenodo API listing → one 64 kB range request for the zip64 end-of-central-directory → one 1.8 MB range request for the central directory → one 1.7 MB range request covering the whole contiguous `r30` folder → local inflate with length check. Total download time < 10 s (the server honoured all range requests). |

## 2. Reproducing the shipped decoders

PyMatching (plain MWPM) on each shipped `error_model.dem` versus the shipped `obs_flips_predicted.b8`, 50 000 shots:

| pathway | shipped P_fail | PyMatching on same DEM | shot agreement |
|---|---|---|---|
| correlated matching, SI1000 prior | 0.2302 | 0.2536 | 81.0 % |
| correlated matching, RL-optimised prior | 0.2123 | 0.2498 | 81.6 % |
| Harmony, SI1000 prior | 0.2133 | 0.2536 | 82.0 % |
| Harmony, RL-optimised prior | 0.2024 | 0.2498 | 81.2 % |
| Libra, RL-optimised prior | 0.1978 | 0.2498 | 81.4 % |

Plain MWPM is 2 to 5 points worse than the shipped correlated/ensemble decoders, as expected; our baseline A is therefore *our own* MWPM on the shipped DEM, and every comparison below is paired against it on the same shots. Per-round logical error ε = ½(1 − (1 − 2P_fail)^(1/30)): ε_A = 1.17 % (SI1000 prior) and 1.14 % (RL prior).

Note on scale: P_fail ≈ 0.25 after 30 rounds is a hard decoding regime (near-random observable); this is one patch in one basis and is not the paper's averaged d = 3 number.

## 3. Per-round detection fraction (the leakage signal)

!`detection fraction, profile, signatures`

*Panel a*: device detection fraction per round (black, 95 % Wilson bars smaller than the markers) with the scaled SI1000 model (grey), the shipped RL-optimised DEM sampled with Stim (blue dashed) and one excluded leaky model (orange). *Panel b*: Δχ² of the curve **shape** (rounds 2 to 28, mean removed because the scale factor absorbs the level) versus p_L for each lifetime τ. *Panel c*: two lifetime-independent correlation statistics as a function of the leaked fraction at τ = 1, for both base models, with the device values as horizontal lines.

* Device: mean detection fraction 0.0753 overall, **0.0763 in rounds 1 to 28**; round 0 = 0.0358, round 29 = 0.0804, final round 30 = 0.0474.
* Weighted linear slope over rounds 1 to 28: **−2.4 × 10⁻⁵ ± 1.0 × 10⁻⁵ per round**; rounds 15 to 28 minus round 1: **−0.0010 ± 0.0004**. In the 2023 data the same quantity was +0.006 to +0.020. The curve is flat, as expected under DQLR.
* Shape χ² of the flat scaled-SI1000 model: 34.7 for 26 degrees of freedom (acceptable); the round-29 point (last bulk round, +0.004 above the bulk) was excluded from the fit as a boundary-structure round, like rounds 0, 1 and 30.

## 4. Fitted leakage (p_L, τ) with interval

**Method (2023 fit, adapted; all changes declared).** The shipped `circuit_noisy_si1000.stim` is a *generic* SI1000 model at p = 10⁻³ (detection fraction 0.026, device 0.075), not a device-calibrated model as in 2023. Every noise probability is therefore multiplied by one scale factor s, fitted by bisection for every (τ, p_L) so that the simulated mean detection fraction over rounds 2 to 29 equals the device's; the leakage parameters are then constrained only by the **shape** of the curve. Grid: τ ∈ {1, 2, 3, 4, 8, 16}, p_L ∈ {0, 1, 3, 10, 20, 30, 50, 100, 200, 300} × 10⁻⁴; 50 000 simulated shots per point; 95 % interval = Δχ² ≤ 3.84 at fixed τ. Grid points where leakage alone exceeds the device level (s at the bisection floor) are invalid and excluded.

| τ (rounds) | best p_L | 95 % upper limit p_L | leaked qubit-rounds at the limit | scale s at p_L = 0 |
|---|---|---|---|---|
| 1 | 3 × 10⁻⁴ | **not bounded** (flat up to 10⁻², the last valid grid point) | ≤ 1.0 % | 3.01 |
| 2 | 3 × 10⁻⁴ | 3 × 10⁻⁴ | 0.06 % | |
| 3 | 3 × 10⁻⁴ | 3 × 10⁻⁴ | 0.08 % | |
| 4 | 3 × 10⁻⁴ | 3 × 10⁻⁴ | 0.11 % | |
| 8 | 0 | < 1 × 10⁻⁴ | < 0.06 % | |
| 16 | 0 | < 1 × 10⁻⁴ | < 0.09 % | |

Reading: any leakage that survives more than one round is limited to about **0.1 % of data-qubit-rounds** (2023 fits gave 0.2 to 1.2 %). A one-round lifetime (τ = 1, i.e. DQLR removes it before the next round) leaves no mark on the curve at all, so the curve cannot bound it; that regime is bounded only by correlation statistics (panel c), which disagree with each other: the ≥3-of-4 clique rate (device 0.0105) would need ≈ 0.7 % leaked qubit-rounds on the RL-DEM base, whereas the time-pair rate (device 0.0163) is already exceeded at ≈ 0.3 %. The shipped RL-optimised DEM, which has the *same* hyperedge set as the SI1000 DEM with re-fitted probabilities, reproduces the device 4-of-4 clique rate exactly (0.00425 vs 0.00423), so most of the clique excess is re-weighted Pauli mechanisms, not leakage. The 95 % *interval* for τ ≥ 2 is therefore [0, 3 × 10⁻⁴] in p_L; for τ = 1 it is [0, ≈ 10⁻²] from the curve and ≲ 3 × 10⁻³ from the time-pair statistic. The interval was obtained by profiling over the grid (the task allowed either a 10-fit bootstrap or a profile).

## 5. Decoders on the real syndromes

Two training points were used, bracketing what the data allow: **T1** = (τ = 1, p_L = 8 × 10⁻³, 0.79 % leaked, s = 2.10), the largest short-lived leakage compatible with the curve and the clique rate; **T2** = (τ = 4, p_L = 3 × 10⁻⁴, 0.10 % leaked, s = 2.93), the 95 % upper limit of the long-lived regime the tracker was designed for. HMM base rates = device per-detector detection fractions. CNN (3-layer causal 3×3×3, 5 × 10⁴ training shots, 6 epochs) trained on T1 only, on a 50/50 mixture of scaled-SI1000 and RL-DEM base noise with injected leakage. Each decoder was run with both shipped priors (SI1000 and RL-optimised DEM). Statistics as in the 2023 report: Wilson 95 % on P_fail, paired shot-level bootstrap (2 000, seed 42) on the ε ratio vs A, McNemar discordant counts with exact binomial p. R = 30 in the ε conversion.

**Real data, 50 000 shots** (ratio = ε_X / ε_A, < 1 is an improvement):

| point | prior | decoder | P_fail | ε (%) | ratio [95 % CI] | McNemar b / c | p | flag frac |
|---|---|---|---|---|---|---|---|---|
|, | SI1000 | A (MWPM) | 0.2536 | 1.166 | 1 | | | |
| T1 | SI1000 | A4 static avg | 0.2548 | 1.173 | 1.007 [1.003, 1.010] | 116 / 174 | 0.0008 (worse) | |
| T1 | SI1000 | D HMM soft lag 0 | 0.2551 | 1.176 | 1.009 [0.988, 1.029] | 4356 / 4431 | 0.43 | 0.0015 |
| T1 | SI1000 | D CNN soft lag 0 | 0.2532 | 1.163 | 0.997 [0.977, 1.017] | 4194 / 4171 | 0.81 | 0 |
| T1 | SI1000 | E CNN hard lag 0 | 0.2536 | 1.166 | 1.000 (no flags) | 0 / 0 | 1 | 0 |
| T1 | SI1000 | D CNN soft lag 2 | 0.2500 | 1.142 | 0.980 [0.960, 0.999] | 4206 / 4026 | 0.049 | 0.0006 |
| T2 | SI1000 | A4 static avg | 0.2537 | 1.166 | 1.000 [0.999, 1.001] | 13 / 16 | 0.71 | |
| T2 | SI1000 | D HMM soft lag 0 | 0.2531 | 1.162 | 0.997 [0.983, 1.010] | 1928 / 1902 | 0.69 | 0.0009 |
|, | RL | A (MWPM) | 0.2498 | 1.141 | 1 | | | |
| T1 | RL | A4 static avg | 0.2486 | 1.133 | 0.993 [0.983, 1.002] | 952 / 889 | 0.15 | |
| T1 | RL | D HMM soft lag 0 | 0.2493 | 1.137 | 0.997 [0.978, 1.016] | 3929 / 3900 | 0.75 | 0.0013 |
| T1 | RL | D CNN soft lag 0 | 0.2480 | 1.129 | 0.990 [0.971, 1.009] | 3994 / 3904 | 0.32 | 0 |
| T1 | RL | D CNN soft lag 2 | 0.2476 | 1.126 | 0.987 [0.968, 1.007] | 4021 / 3909 | 0.21 | 0.0006 |
| T2 | RL | A4 static avg | 0.2499 | 1.141 | 1.000 [0.998, 1.002] | 39 / 42 | 0.82 | |
| T2 | RL | D HMM soft lag 0 | 0.2504 | 1.144 | 1.003 [0.990, 1.016] | 1696 / 1722 | 0.67 | 0.0005 |

b = shots A wrong / X right, c = shots X wrong / A right. Twelve real-data comparisons: the only p < 0.05 are the A4 *worsening* (p = 0.0008) and CNN lag 2 with the SI1000 prior (p = 0.049, −2.0 %). With Holm correction over the 12 tests the thresholds are 0.0042 and 0.0045 respectively, so the CNN-lag-2 effect is **not significant**, and it is not reproduced with the better (RL) prior (0.987 [0.968, 1.007]). The ±2 % band is the same "nothing to track" band seen on the 2023 data.

**Simulated test sets of the fitted models, 20 000 shots** (what the same decoders do when the leakage really is there; f = fraction of the oracle gain):

| point | prior | oracle B ε ratio | HMM lag 0 f | CNN lag 0 f | CNN lag 2 f |
|---|---|---|---|---|---|
| T1 (τ = 1, 0.79 %) | SI1000 | 0.448 | 0.22 [0.16, 0.28] | 0.35 [0.30, 0.40] | 0.45 [0.40, 0.49] |
| T1 | RL | 0.463 | 0.31 [0.26, 0.37] | 0.40 [0.35, 0.45] | 0.49 [0.44, 0.53] |
| T2 (τ = 4, 0.10 %) | SI1000 | 0.956 | −0.46 [−1.1, 0.08] |, |, |
| T2 | RL | 0.951 | −0.01 [−0.49, 0.44] |, |, |

So at T1 the trackers would have removed 12 to 26 % of ε had the device matched the model, and they remove nothing on the device. At T2 even the oracle is worth only 4 to 5 % of ε, below what 50 000 shots can resolve (the 95 % CI half-width on the ratio is ≈ 1.5 %), so T2 is "not testable" by construction.

Flag plausibility (2023 check): the lag-0 CNN raised no posterior above 0.5 on any real shot (0 flags in 50 000 × 9 × 30 cells); the lag-2 CNN flagged 0.06 % of cells, the HMM 0.13 to 0.15 %, all below the 0.79 % the T1 model would produce, i.e. the trackers themselves see less leakage than T1 assumes.

## 6. What this means for the scope figure

The Willow d = 3 point lands where the scope argument says it should: with per-round DQLR the data-qubit leakage population that survives into the next round is ≤ 0.1 % of qubit-rounds (95 %), the detection-fraction curve carries no leakage signature (slope −2.4 ± 1.0 × 10⁻⁵ per round, versus the +0.006 to 0.020 rise on 2023 Sycamore), and the oracle itself would be worth ≤ 5 % of ε. Every syndrome-only tracker (HMM, CNN lag 0/2, static A4) is null on the real syndromes, −2 % to +1 %, none surviving multiple-comparison correction, while the same trackers recover 22 to 49 % of the oracle gain on the matched simulator. **Predicted null: confirmed.** The point should be drawn on the scope figure at (leaked fraction ≲ 10⁻³, oracle gain ≲ 5 %, tracker gain 0 ± 2 %), with the caveat that this is one patch, one basis, 30 rounds, and that the τ = 1 regime (leakage removed within the same round) is bounded only indirectly.

## 7. Deviations (declared)

1. **Rounds.** No 25-round run exists in the record; the 30-round run (nearest, with r13 the other neighbour) was used. All ε values use R = 30.
2. **One run only**, as specified: `d3_at_q6_7/Z/r30`. No pooling over the eight d = 3 patches or the X basis.
3. **Base noise.** The shipped SI1000 circuit is generic (p = 10⁻³); a single global scale factor s was fitted jointly with the leakage parameters (s ≈ 3.0 at p_L = 0). The 2023 fit used a device-calibrated Pauli model with no free scale. Consequence: only the *shape* of the detection-fraction curve constrains (p_L, τ); the level is absorbed. Rounds 0, 1, 29, 30 were excluded from the shape fit (rounds 0/1/30 as in 2023; round 29 additionally, because the last bulk round of this circuit sits +0.004 above the bulk and the generic model does not reproduce it).
4. **Interval method.** Profile over the (τ, p_L) grid (Δχ² ≤ 3.84), not a 10-fit bootstrap. Simulation noise of 50 000 shots per grid point is included in the χ² variance.
5. **Measurement noise rewrite.** `M(p)` inline flips were rewritten as `X_ERROR(p)` + `M` (identical statistics; verified detection fraction 0.02634 vs 0.02637 at s = 1) so that the marker-circuit edge lookup sees a noiseless measurement.
6. **Lattice map.** Final-round detectors list data-qubit coordinates first; the measure-qubit coordinate (last triple) is used for the CNN lattice. Detector coordinates have 6 entries after round 0; only (row, col, t) are used.
7. **CNN training set** = 50/50 mixture of scaled-SI1000 base and shipped RL-DEM base with the same injected leakage, trained on T1 only (5 × 10⁴ shots, 6 epochs, per-epoch checkpoints because the sandbox restarted several times). The 2023 script mixed the fitted simulators of several patches. **No CNN was trained at T2** (budget; at T2 the oracle gain is 4 to 5 %, below the resolution of 50 000 shots, so a CNN result there would be uninformative).
8. **HMM at T1 uses τ = 1** (return probability 1), the tracker's degenerate regime; its simulated f of 0.22 to 0.31 shows it still extracts posterior information from the same-round signature.
9. **A4 at T1** uses the model-average leaked fraction 0.79 %, which is an upper estimate; it degrades the SI1000-prior decoder by 0.7 % (significant), confirming that the real data do not contain that much leakage-like signal.
10. Decoder reproduction is of the shipped predictions by plain MWPM on the shipped DEM (81 to 82 % shot agreement); the correlated-matching / Harmony / Libra decoders themselves were not re-implemented.
11. Download budget: 2 h allowed, < 10 s used; nothing was skipped for budget reasons except the T2 CNN (item 7).

## 8. Files

* `willow_scope_report.md`, this report.
* `willow_results.csv`, every decoder row (real and simulated sets, both priors, both training points) with Wilson, bootstrap, McNemar and flag statistics.
* `willow_fit_grid.csv`, `willow_fit_profile.csv`, `fit_leakage_willow.json`, `willow_signatures.json`, leakage fit grid, profile limits, raw curves, correlation statistics.
* `willow_detection_fraction.png` + `make_willow_figure.py`, the figure.
* `leakage_sim_willow.py`, `fit_leakage_willow.py`, `train_cnn_willow.py`, `run_willow.py`, `analyze_willow.py`, scripts (run in env `qec`, `PYTHONPATH=$PWD`, with the 2023 `leakage_sim.py`, `leakage_sim_real.py`, `hmm_tracker.py`, `cnn_tracker.py` alongside).
* `willow_d3_q6_7_Z_r30_data.tar.gz`, the pulled run (1.7 MB) and dataset README.
* `willow_results_pershot.tar.gz`, per-shot error arrays and meta JSONs; `willow_models.tar.gz`, trained CNN weights (T1, lag 0 and 2); `willow_t1_meta.json`, `willow_t2_meta.json`.
