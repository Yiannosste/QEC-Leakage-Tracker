# Pre-registered protocol: syndrome-only hidden-state tracking on IBM ibm_berlin surface-code memory data

*Project C3, IBM real-data test. Frozen on 21 Oct 2026, after model-free diagnostics (no decoder run with a tracker yet) and BEFORE any tracker-based decoding of any shot.*

## 0. Data and why this test
Zenodo 23335425 (Lange et al., arXiv:2610.03869), `ibm_berlin.zip`: rotated surface-code memory on IBM `ibm_berlin`, patches `memory_d3_q36`, `memory_d3_q85`, `memory_d5_q85`, T = 5, 10, 20, 30, 50 rounds, 100 000 shots each, detection events (stim b8), logical flips, and a calibrated p_ij detector error model (DEM) per run (calibrated by the dataset authors from the same detection events). IBM circuits have no data-qubit leakage removal and do not reset measure qubits.

Diagnostics done before this protocol (no decoding): (i) the detection fraction rises with T (d = 5: 0.17 at T = 5, 0.28 averaged over T = 50; last rounds 0.35-0.37). (ii) Within a shot, the continuation probability c_k = P(a detector fires again | it already fired k consecutive rounds) climbs on hardware from 0.31-0.39 (k = 1) to 0.60-0.72 (k = 12-14) in all three T = 50 runs, while it stays flat (0.33-0.46) in shots sampled from the calibrated DEM. This is a persistent per-detector hidden state that the static pairwise DEM does not represent.

## 1. Decoders (all plain PyMatching on the shipped DEM graph; same shots)
- **A**: MWPM on the shipped p_ij DEM, static.
- **X (tracker)**: per-detector two-state hidden-Markov model (state N "normal", state H "hot"). Emissions: N fires with probability s * r_i (r_i = marginal detection rate of detector i in the run being decoded, no labels used — the same level of in-sample information the shipped DEM already uses); H fires with probability q. Transitions: P(N->H) = a, P(H->N) = b; initial state N. Global parameters (a, b, q, s) fitted by maximum likelihood on syndromes only (no logical labels) from 20 000 shots of the tuning run memory_d3_q36/T50, then frozen for every other run. Posterior pi[i, t] = P(H at t | syndromes), computed with lag L. For every time-like edge (i_t, i_{t+1}) of the matching graph: p_e <- p_e XOR (c * pi_e) with pi_e = max(pi[i,t], pi[i,t+1]); entries pi_e < 0.02 ignored; no other edges changed.
- **A4 (static average-information control)**: same rule as X but pi_e replaced by its average over all shots of the run (per edge). Tests whether per-shot information is needed.
- **P (placebo)**: same rule as X but each shot k receives the posteriors of shot perm(k) (fixed random permutation, seed 0). Same posterior distribution, wrong shot.

## 2. Tuning (tuning patch memory_d3_q36 ONLY, all five T, 50 000 shots each)
Grid: L in {0 (filtered), 2 (fixed lag 2), full (smoothed over the whole shot)} x c in {0.25, 0.5} = 6 configurations. Selection rule: the configuration with the largest pooled net discordant count (A wrong & X right minus X wrong & A right, summed over the five tuning runs). Ties broken by smaller c, then smaller L. Frozen afterwards.

## 3. Held-out evaluation (10 runs, never used for any choice)
memory_d3_q85 T5/10/20/30/50 and memory_d5_q85 T5/10/20/30/50, all 100 000 shots, in file order, decoders A, X, A4, P.

## 4. Statistics
P_fail with Wilson 95 %; eps = 0.5(1-(1-2P)^(1/T)); paired shot-level bootstrap (2000 resamples, seed 42) on the eps ratio X/A; McNemar exact binomial on discordant shots per run; Holm correction across the 10 held-out runs for each comparison family (X vs A, X vs A4, P vs A).

## 5. Success / kill rules (fixed)
- **PRIMARY**: pooled over the 10 held-out runs, X has more (A wrong & X right) than (X wrong & A right) with exact two-sided binomial p < 0.05, **and** X beats A4 in the same pooled test (p < 0.05), **and** the placebo P is not significantly better than A (pooled p >= 0.05 or P worse).
- **SECONDARY**: per-run eps ratio X/A with Holm-corrected McNemar; reported for all 10 runs, including runs where P_fail is close to 0.5 (saturated) where no decoder can show a gain.
- **KILL**: primary not met -> "no syndrome-only hidden-state gain on IBM data within this decoder family".
- **Leak alarm**: P significantly better than A on the pooled test -> audit before any claim.

## 6. Declared limits
Single dataset family; no oracle exists on hardware (no ground-truth hidden state); the tracker uses the run's own detector marginals (no labels); file order is assumed to be acquisition order (irrelevant here: the tracker is within-shot).

---
## Amendment 1 (21 Oct 2026) — frozen BEFORE any held-out shot was decoded with this variant

**Why.** The original decoder X *adds* the per-shot term c·π on top of the shipped p_ij DEM. But that DEM was calibrated by its authors on the same leaky detection events, so its time-like edges already contain the *average* contribution of the hot episodes. Adding the per-shot term double-counts. On the tuning patch the original X was net −115 of 250 000 shots (harm at T = 5 and 50). This diagnosis was made before the held-out results of the original X were seen. Those results are running and will be reported unchanged under the original protocol.

**Variant X' (reallocation).** For every time-like edge e: p_e^N = (p_e − c·π̄_e)/(1 − 2c·π̄_e), where π̄_e is the mean edge posterior over all shots of the run (syndromes only, no labels), floored at 1e-5. Then per shot, p_e(shot) = p_e^N ⊕ c·π_e(shot). Averaged over shots this reproduces the shipped DEM; it only moves weight toward the shots whose detectors are hot. Same HMM parameters (fitted on q36 T50), same 0.02 threshold.

**Tuning (q36 only, 5 × 50 000 shots, same 6-configuration grid and selection rule).** Selected: smoothed posterior (L = full), c = 0.25. Net pooled discordant count = +650 of 250 000. Per T, P_fail of A → X': T5 0.1103 → 0.1245, T10 0.2479 → 0.2331, T20 0.3229 → 0.3201, T30 0.4272 → 0.4184, T50 0.4213 → 0.4205. Known risk declared in advance: harm at T = 5.

**Held-out evaluation.** The same 10 held-out runs, 100 000 shots each, decoders A, X', A4' and P'. A4' uses the same deflated base with π̄_e added back, so it reconstructs A up to the floor. P' uses the same deflated base with posteriors from a permuted shot (seed 0).

**Primary rule for X'.** The same three conditions as §5, with the significance threshold halved to 0.025. This is a Bonferroni factor of 2, because two variants (X and X') are tested on the held-out set. X' must beat A, must beat A4', and P' must not beat A. Secondary and kill rules are unchanged.


---
## Erratum (21 Oct 2026, added after the held-out runs; it does not change any frozen rule)
§0 (ii) said c_k reaches 0.60–0.72 at k = 12–14 "in all three T = 50 runs". That is true for two of the three runs: d = 3 qubits 85 (0.60 / 0.66 / 0.72 at k = 12 / 13 / 14) and d = 5 qubits 85 (0.65 / 0.69 / 0.71). On the tuning run, d = 3 qubits 36, c_k reaches only 0.47 / 0.53 / 0.54 at k = 12–14, with a maximum of 0.54 over k = 1–15. That is still clearly above its DEM null (0.36–0.56, noisy), but it is not in the 0.60–0.72 range.
