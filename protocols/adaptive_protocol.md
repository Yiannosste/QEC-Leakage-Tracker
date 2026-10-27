# Pre-registered protocol: causal adaptive-weight matching on Willow syndromes

*Project C3, Willow real-signal track. Frozen on 20 Oct 2026 before any held-out shot was decoded with an adaptive decoder. Everything below is fixed; the results document (`adaptive_results.md`) will list every departure from it under "Deviations".*

## 0. The question in one sentence

Can a decoder that **only looks backwards in time** — it sets the matching weights for shot k using the detection events of shots 1 … k−1 and nothing else — lower the logical error rate of minimum-weight perfect matching (MWPM) on Google's Willow d = 3, 5, 7 surface-code data, compared with the same MWPM using one fixed prior for all shots?

## 1. What the diagnostics already told us (prior expectation)

From `willow_diagnostics.md` (same eight runs, same shot order):

* The detection-event rate drifts across shots in every run, and the next 500-shot block is 20–52 % predictable from the past in 7 of 8 runs. The drift is carried by a few measure qubits whose rate rises 1.1–2.3× for 250–8 500 shots.
* But the *logical* failure rate per block is stationary in 6 of 8 runs. Only **d7 Z r30** shows a drift of the failure rate that a causal predictor can see (R² = 0.16 for Libra, 0.26 for MWPM at 1 000-shot blocks). An oracle that refitted the prior per 1 000-shot block could remove at most 10–20 % of ε in the second half of that run and about nothing elsewhere.

**Pre-registered expectation:** a null result (ε ratio 1.00 ± 0.02) on seven runs; a possible small gain (ratio 0.90–0.98) on d7 Z r30 only. A "gain" on a run whose failure rate is stationary would be evidence of a protocol leak, not of a discovery.

## 2. Data

Zenodo 13273331, `google_105Q_surface_code_d3_d5_d7`, eight runs of 50 000 shots each, already pulled and verified (`willow_d357_r30_r50_data.tar.gz`, `willow_step1_verify.csv`):

| role | runs |
|---|---|
| tuning set | `d3_at_q6_7/Z/r30`, `d3_at_q6_7/X/r30` |
| held-out set | `d3_at_q6_7/X/r50`, `d3_at_q6_7/Z/r50`, `d5_at_q6_5/X/r30`, `d5_at_q6_5/Z/r30`, `d7_at_q6_7/X/r30`, `d7_at_q6_7/Z/r30` |

Shot order = file order, treated as acquisition order (assumption carried over from the diagnostics; the README does not state the order). The shipped files provide `detection_events.b8`, `obs_flips_actual.b8`, two detector error models (DEMs: the RL-optimised prior and the SI1000 prior) and the shipped predictions of three decoders (correlated matching, Harmony, Libra) for each prior.

## 3. The decoder family (fixed)

### 3.1 Static reference, decoder A

PyMatching 2.4 MWPM on the shipped RL-optimised DEM. PyMatching merges the DEM's decomposed hyperedges into a graph of 2-detector edges and boundary edges with probabilities p_e and weights w_e = ln((1−p_e)/p_e); we extract this edge list once per run and rebuild the graph from it (verified: identical predictions to PyMatching's own construction on d3 Z r30, 50 000/50 000 shots).

### 3.2 Causal adaptive MWPM, decoder C

For each shot k the decoder uses the static edge list and a vector of **per-unit rate ratios** r_u(k) computed from shots < k:

1. **Unit.** A unit u is either one *measure qubit* (all detectors with that (x, y) coordinate, all rounds, pooled; 8 / 24 / 48 units at d = 3 / 5 / 7) or one *detector* (one measure qubit at one round; 240–1 440 units). Which one is used is a tuning choice.
2. **Per-shot observation.** x_u(k) = fraction of unit u's detectors that fired in shot k.
3. **Causal reference.** m_u(k) = mean of x_u over shots 1 … k−1 (cumulative, strictly causal).
4. **Causal recent rate.** EWMA_u(k) = λ·EWMA_u(k−1) + (1−λ)·x_u(k−1), started at m_u(K) at the end of burn-in. Memory ≈ 1/(1−λ) shots.
5. **Ratio and clip.** r_u(k) = clip(EWMA_u(k) / m_u(k), 1/3, 3).
6. **Edge rule.** For an edge e touching detector set D_e (one or two detectors), f_e = (∏_{i∈D_e} r_{u(i)})^{α/|D_e|}; p_e'(k) = min(p_e · f_e, 0.49); w_e'(k) = ln((1−p_e')/p_e'). So a time-like edge inside one hot measure qubit is scaled by r^α; a space-like edge between a hot and a normal qubit by r^{α/2}; the boundary edge of a hot detector by r^α. α is a tuning choice.
7. **Burn-in.** The first K = 1 000 shots of every run are decoded with the static weights (r_u ≡ 1) while m_u and EWMA_u are being initialised. These shots are *included* in every failure count so that all decoders are scored on identical shots.
8. **Update interval.** The graph is rebuilt for every shot (update interval 1 shot) for MWPM. This costs 2–5 ms per shot and is the only computational difference from A.

Tuning grid (Section 4): λ ∈ {0.9, 0.95, 0.98, 0.99, 0.995, 0.998, 0.999} (memory 10–1 000 shots; the brief named 0.9–0.995, the two longer values are added because the diagnostics place the structure at 250–1 000 shots), α ∈ {0.5, 1, 2}, unit ∈ {measure qubit, detector}; 42 configurations. The clip [1/3, 3] is fixed.

Not included, by decision taken now: a trailing-window *pairwise* (Spitz-type) per-edge estimate. With edge probabilities 0.001–0.03 a ≤ 1 000-shot window holds 1–30 coincidences per edge, so its estimation noise (≥ 20 %) is as large as the ≤ 2× drift we are trying to track; the per-unit ratio above is the shrunken version of the same idea.

### 3.3 Other decoders run on the same shots

| label | decoder | causal? | purpose |
|---|---|---|---|
| A | MWPM, static RL-prior DEM | yes (no adaptation) | the paired reference for every ratio |
| A_si | MWPM, static SI1000 DEM | yes | second static prior |
| Libra | shipped Libra predictions (RL prior) | yes | state-of-the-art reference row; not paired against C |
| C | causal adaptive MWPM, frozen (λ, α, unit) | **yes** | the hypothesis |
| C_placebo | C run on the same shots in a **shuffled order** (one fixed permutation per run, `numpy.random.default_rng(42)`); failures counted on the same shots | yes, but time order destroyed | must give ratio 1.00 ± noise. Any gain here is regularisation or a leak, not time structure |
| U | same family as C, but r_u for shot k is computed from the 1 000-shot block **containing k** (in-sample, non-causal), with the frozen (α, unit) and the run-wide mean as reference | **no (cheating)** | ceiling of this decoder family |
| H2 | "episode mode": unit = measure qubit, frozen λ; if r_u > 1.3 then only the *time-like* edges inside u (both detectors in u) are scaled by r_u (α = 1); every other edge unchanged | yes | sub-hypothesis H2 (per-qubit TLS episodes), one fixed setting |
| CL | "single-round leakage clique": static weights, but if ≥ 3 of the 4 detectors adjacent to a data qubit fire in the same bulk round t, the space-like edges joining pairs of those detectors at round t have p multiplied by c = 4 (weight lowered by ln 4) | yes (within-shot) | sub-hypothesis, one fixed setting; shuffling the order cannot change it, so it has no placebo row |
| BM_A | belief matching (BP, 20 iterations, then MWPM) on the static RL DEM | yes | stronger static baseline |
| BM_C | belief matching whose DEM has every error probability scaled by the same f_e rule (geometric mean of r over the error's detectors, hyperedges included), rebuilt every 100 shots from shots < block start | yes | does the adaptation survive a stronger decoder? |
| BM_C_placebo | BM_C in shuffled order | yes, order destroyed | placebo for BM_C (d3 r50 only, cost) |

Belief matching costs 12 ms/shot at d = 3 and 227 ms/shot at d = 7. **Fixed in advance:** BM rows at d = 3 use all 50 000 shots; at d = 5 and d = 7 the BM rows (BM_A and BM_C) are scored on the 10 000 shots with index ≡ 0 (mod 5), i.e. every fifth shot across the whole run, so that the second half (where the d7 Z drift lives) is covered. The adaptive tracker still updates on every shot; only the decoding is subsampled. BM_A and BM_C are paired on the same 10 000 shots. BM_C_placebo is run on d3 r50 only.

## 4. Tuning and freezing

1. Run C for all 42 configurations on the two tuning runs (d3 Z r30, d3 X r30), acquisition order.
2. Score = mean over the two runs of ε_C / ε_A.
3. Pick the configuration with the lowest score. Tie-break: longer memory (larger λ), then smaller α, then unit = measure qubit.
4. Run C_placebo with the chosen configuration on both tuning runs. If its ratio is outside [0.98, 1.02] on either run, the next-best configuration is taken, and this is reported.
5. Freeze (λ, α, unit). The frozen λ also fixes H2. Nothing is tuned on any held-out run.

The tuning runs are reported for completeness but are **not** confirmatory.

## 5. Statistics (fixed)

* **Logical error per round:** ε = ½ (1 − (1 − 2P)^{1/R}), P = failure fraction over the scored shots, R = 30 or 50 as in the run.
* **Effect size:** ratio ε_X / ε_A on identical shots.
* **Interval:** paired shot-level bootstrap, 2 000 resamples, `numpy.random.default_rng(42)`, percentile 2.5 / 97.5 of the ratio. The same resample indices are used for every comparison within a run.
* **Test:** McNemar exact two-sided test on the discordant shots (X fails & A succeeds vs A fails & X succeeds).
* **Multiplicity:** Holm correction. Primary family = the 6 held-out runs × decoder C vs A (6 tests). Secondary families, each Holm-corrected separately: H2 vs A (6), CL vs A (6), BM_C vs BM_A (6), C_placebo vs A (6).
* **Decode time** per shot (wall clock, this machine, one thread) is recorded for every decoder.

## 6. Success and kill rules (fixed)

* **PRIMARY endpoint:** d7 Z r30, decoder C vs A: ratio < 1 with Holm-corrected McNemar p < 0.05 **and** C_placebo on d7 Z r30 within [0.98, 1.02] **and** no held-out run where C is significantly *worse* than A (Holm p < 0.05 with ratio > 1).
* **SECONDARY:** the same three conditions on each of the other five held-out runs; expected null.
* **KILL:** primary not met. In that case the verdict is "no real causal gain within this decoder family on Willow", and the ceiling U says how much was there to be had.
* **Leak alarm:** a placebo ratio outside [0.98, 1.02] on any run, or a significant C gain on a run whose per-block failure rate was stationary in the diagnostics (all except d7 Z r30), triggers an audit before any claim.

## 7. Outputs

`adaptive_results.md` (tables, one figure, verdict, deviations), `adaptive_results.csv` (one row per run × decoder: P, ε, ratio, CI, discordant counts, raw and Holm p, ms/shot), `adaptive_tuning.csv` (42 × 2 rows), `adaptive_decoder.py` / `run_adaptive.py` / `analyze_adaptive.py` (scripts), `adaptive_pershot.tar.gz` (per-shot prediction arrays for every decoder and run).

## 8. Compute plan

Environment `qec` (stim 1.16, PyMatching 2.4, beliefmatching). Each job is one (run, decoder) process holding < 0.5 GB; jobs run in parallel (≤ 8 at a time) in the background with a per-job checkpoint file; a job that is interrupted is re-run from scratch (every job is < 1 h).
