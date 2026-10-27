# C3 paper-readiness report, syndrome-inferred leakage posteriors as soft matching weights

Date: 17 October 2026. All experimental numbers are from code run in this project (seeds given); all data are **SYNTHETIC** (Stim + the phenomenological leakage model of `leakage_sim.py`). Papers are cited by arXiv id / DOI with status. "Fact" = computed or read in a primary source; "opinion" is labelled.

## 0. Verdict in one paragraph

**Mechanically, by the pre-registered rules, the result is PAPER-READY** (P1 ∧ P2 ∧ P3 ∧ P4 hold, see §2). **Scientifically, my verdict is "paper-ready after one more round of targeted simulations and a careful re-framing"**, the independent referee pass (§7) says *major revision* for PRX Quantum / npj QI, *accept after fixes* for Quantum, and I agree. The central finding is new and clearly demonstrated inside its model: a small causal 3D-CNN that reads only the syndrome history and outputs per-qubit, per-round leakage posteriors, fed as *continuous* edge probabilities into minimum-weight matching, recovers 60 to 90 % of the gain that a *perfect* leakage flag would give, raises Λ₅/₇ from 1.40 to 2.72 at the central setting (oracle 4.11), and beats every "average-noise" re-calibration we could build. The weak spot, found by us, not hidden, is the regime of per-cycle leakage removal (one-round episodes), where a matched tracker still recovers 43 % [35, 51] of a smaller oracle gain. The claim must therefore be framed by regime (multi-round leakage: absent or imperfect LRU) and the leakage model's severity must be stated next to every headline number. **We were not wrong, and nothing triggered a KILL condition; but the paper is not yet written and the model-realism objections in §7 must be answered before submission.**

 **Addendum after the background scan (§5.1):** the single caveat that must shape the paper is that the tracker's benefit falls with the background detection fraction, from a 56 % to a 12 % reduction of the logical error per round (d = 5) as p goes from 1e-3 to a Sycamore-like 3e-3, and about half of that fall is recoverable with more training data. The claim is therefore a *regime* claim (leakage-dominated budgets, multi-round episodes), and this must be in the abstract, not in a footnote.

## 1. What was done (chronologically, with artifacts)

| Phase | Deliverable | Key fact |
|---|---|---|
| Prior art (28 verified papers) | prior_art_c3.md | Not scooped; "leakage posterior → continuous matching weights" open (closest: belief-matching 2203.04948 for Pauli posteriors; hard leakage flags 1410.8562; hardware heralds 2411.10343, 2511.17460); pilot's "one-round delay kills the gain" must be retracted (Baranes 2026, Suchara 2015). |
| Pre-registration + 2 amendments | c3_preregistration.md, c3_preregistration_amendment1.md | Model parameter ranges from Google 2025 Table S4, Miao 2023, Varbanov 2020; mechanical PAPER-READY / NEEDS-MORE / KILL rules; amendment 1 adds the learned tracker and the soft-weight rule; amendment 2 (compute) trains the d = 7 CNN once at the centre cell. |
| Simulator | leakage_sim.py, validate_* | Hidden-Markov leakage per data qubit on top of exact SI1000 noise (Pauli injection with pre-computed detector patterns; exact for stabiliser circuits). V1: p_L = 0 reproduces Stim bit-for-bit. V2 (hazard form): return rate 0.2517 / 0.1257 / 0.0626 for τ = 4 / 8 / 16 (expected 0.25 / 0.125 / 0.0625). V3: adjacent-detector rate 0.493 vs 0.5 (mean of 60 cells; max deviation 0.115 in low-count cells). V4: detection fraction rises and saturates on the τ time-scale; Λ₅/₇ collapses from ≈ 14 to ≈ 1.5 at p_L = 3e-3 without LRU and recovers with LRU. |
| Trackers | hmm_tracker.py, cnn_tracker.py | HMM: 4-state (L_{t−1}, L_t) chain, exact local emission tables, two mean-field explaining-away iterations. CNN: 3 causal 3×3×3 conv layers, 32 channels, 1×2×2 head onto the data-qubit lattice, two outputs (leak, return), BCE on simulated labels; 5e4 training shots, 6 epochs (G1/G3/G5; the latency track used 6e4/8). |
| Decoders | run_cell.py | A ignore; B oracle; D soft posterior (p_e = p_e⁰ ⊕ c·π, c = ρ for time-like edges of adjacent stabilisers, 2/3 for X/Z data edges at the return round, ρ for the final data edge); E hard threshold 0.5. Per-shot edge re-weighting in PyMatching. Metrics: Wilson 95 % on P_fail, ε = ½[1−(1−2P)^{1/25}], f = (ε_A − ε_X)/(ε_A − ε_B) with paired shot-level bootstrap, McNemar counts. |
| G2 oracle map (63 cells) | oracle_map_report.md | G_B = 0.73 to 0.88 (d = 5 realistic cells), 0.88 to 0.95 (d = 7); P3 holds; time-like edges carry 51 to 64 % of the gain alone, return edges 14 to 15 %. |
| G4 latency (centre cell, d = 5, 7) | latency_report.md | Information-set emulation of streaming: oracle flags delivered D rounds after commit keep 0.83/0.62/0.48/0.34/0.25 (d = 5) and 0.92/0.79/0.65/0.53/0.45 (d = 7) of the gain for D = 1…5; never harmful, never neutral. The pilot's "cliff" was a single-round-erasure artefact. |
| **G1 primary grid (27 cells)** | g1_results.csv, g1_figure.png, final_cells.csv | See §2. |
| G3 robustness + controls | g3_results.csv, control_baselines.csv, g3_figure.png | See §3 to 4. |
| G5 extra cells (referee-requested) | results/G5_*, g5_pscan_figure.png | ρ = 0.7, LRU η = 0.5 and 0.9 with matched CNN, background scan p = 1e-3 / 2e-3 / 3e-3 incl. a 4×-training CNN (§5). |
| Referee pass | referee_report.md | Major revision; list of fatal/major/minor issues; most adopted here (§7). |

## 2. Primary result (grid G1) and the pre-registered rules

Rotated surface code, memory-Z, 25 rounds, SI1000 p = 1e-3, nine realistic cells (p_L ∈ {1e-3, 2e-3, 5e-3} × τ ∈ {4, 8, 16}), 1e5 shots per cell (d = 7 at 1e5 instead of the pre-registered 2e5; smallest decoder-A failure count 382, smallest oracle count 48), seeds 1000 + 100·i_d + 10·i_pL + i_τ. ε-based values (pre-registered definition; the P_fail-based values in g1_results.csv differ by < 0.05 and never change a conclusion).

**Fraction of the oracle gain recovered, f (min / median / max over the 9 cells):**

| d | CNN lag 2 (soft) | CNN lag 0 (soft) | HMM lag 0 (soft) | CNN lag 2 hard (E) | HMM hard (E) | model-average DEM (control A4) | oracle gain G_B |
|---|---|---|---|---|---|---|---|
| 3 | 0.60 / **0.65** / 0.70 | 0.54 / 0.59 / 0.63 | 0.37 / 0.45 / 0.47 | 0.43 / 0.54 / 0.58 | 0.14 / 0.21 / 0.26 |, | 0.51 to 0.73 |
| 5 | 0.66 / **0.70** / 0.75 | 0.58 / 0.65 / 0.70 | 0.44 / 0.49 / 0.56 | 0.47 / 0.65 / 0.72 | 0.15 / 0.21 / 0.29 | 0.12 / 0.23 / 0.33 | 0.71 to 0.89 |
| 7 | 0.71 / **0.81** / 0.90 | 0.68 / 0.75 / 0.87 | 0.56 / 0.64 / 0.75 | 0.69 / 0.74 / 0.83 | 0.31 / 0.40 / 0.60 | 0.17 / 0.34 / 0.45 | 0.88 to 0.96 |

Paired-bootstrap lower bound of f > 0 in 27/27 cells. CNN lag 2 is the best decoder in 27/27 cells. Soft minus hard on the same posterior: CNN +0.04 / +0.12 / +0.26 (d = 3, min/median/max), −0.003 / +0.07 / +0.20 (d = 5), +0.02 / +0.05 / +0.07 (d = 7); HMM +0.20 to +0.27 (d = 3), +0.24 to +0.32 (d = 5), +0.15 to +0.28 (d = 7). f(d = 7) exceeds f(d = 5) with non-overlapping 95 % intervals in 8/9 cells (CNN lag 2); d = 3 → 5 in 5/9.

**Centre cell (p_L = 2e-3, τ = 8), logical error per round ε and Λ:**

| decoder | ε d=3 | ε d=5 | ε d=7 | Λ₃/₅ [95 %] | Λ₅/₇ [95 %] |
|---|---|---|---|---|---|
| A ignore flags | 3.08e-3 | 1.61e-3 | 1.15e-3 | 1.91 [1.81, 2.02] | 1.40 [1.30, 1.50] |
| A4 model-average DEM (no per-shot info) |, | 1.30e-3 | 0.74e-3 |, | 1.76 [1.62, 1.91] |
| D HMM lag 0 (soft) | 2.17e-3 | 0.92e-3 | 0.42e-3 | 2.36 [2.20, 2.53] | 2.17 [1.96, 2.40] |
| D CNN lag 2 (soft) | 1.73e-3 | 0.63e-3 | 0.23e-3 | 2.73 [2.52, 2.96] | 2.72 [2.39, 3.11] |
| E CNN lag 2 (hard) | 1.96e-3 | 0.73e-3 | 0.29e-3 | 2.68 [2.49, 2.89] | 2.54 [2.25, 2.87] |
| B oracle flags | 1.09e-3 | 0.26e-3 | 0.064e-3 | 4.12 [3.67, 4.62] | 4.11 [3.26, 5.17] |

Reading: leakage ignored → bigger codes barely help (Λ₅/₇ = 1.4); the syndrome-only CNN posterior lifts Λ₅/₇ to 2.7; the oracle would reach 4.1; the leakage-free SI1000 reference is ≈ 9.5 (G2 report, 21 failures, rough). The tracker's *distance to the oracle*, ε_CNN/ε_B, grows with d (1.6 → 2.4 → 3.6), so "f grows with d" is partly a property of the metric (the denominator saturates); the referee is right that Λ and ε should be the headline.

**Flag quality at the centre cell (d = 5):** CNN lag 2 recall 0.73, precision 0.86, mean detection delay 0.8 rounds; CNN lag 0 recall 0.51, precision 0.77, delay 2.4; HMM recall 0.68, precision 0.34, delay 1.4. The herald-equivalence map (corrupted oracle flags with controlled recall r and precision q, same shots) gives f = 0.75 at (r, q) = (0.75, 0.90) and 0.68 at (0.75, 0.75), the CNN's f = 0.72 sits exactly where its recall/precision would place a random herald, i.e. its errors are not pathologically correlated with the syndromes. At d = 7 the same map gives 0.79 at (0.75, 0.90) vs CNN 0.84.

**Pre-registered rules (recomputed, see also referee_checks.csv):**
- **P1** (median f* ≥ 0.50 at d = 5 and 7, lower bound > 0 in ≥ 7/9): 0.70 and 0.81; 9/9 and 9/9. **Holds.** (The HMM alone does not pass at d = 5: median 0.49.)
- **P2** (f ≥ 0.30 under all six mismatch settings for the tracker that passed P1): CNN under data mismatch, trained at the centre cell, tested at (1e-3, 8), (2e-3, 4), (2e-3, 16), (5e-3, 8): f = 0.75, 0.67, 0.74, 0.62 (matched: 0.73, 0.69, 0.74, 0.67); tested at ρ = 0.25 and 0.7: 0.61, 0.57. **Holds** (all six ≥ 0.57). HMM under parameter mismatch (p_L ×0.5/×2, τ ×0.5/×2, ρ' = 0.3/0.7): 0.46 to 0.59 at d = 5, 0.62 to 0.73 at d = 7. **Holds.**
- **P3** (G_B ≥ 0.15 at the centre cell, interval of ε_A − ε_B excludes 0): 0.846 [0.828, 0.863] (d = 5), 0.944 [0.935, 0.952] (d = 7). **Holds.**
- **P4** (no prior paper with syndrome-inferred leakage flags → matching at d ≥ 5 with a latency analysis): **holds** per prior_art_c3.md and the referee's own check, with the framing correction that posterior-weighted matching per se is belief-matching (2203.04948) and must be cited as such.
- **KILL conditions:** none triggered (G_B ≥ 0.87 in all d = 7 cells; for the P1-passing tracker, CNN lag 2, f ≥ 0.60 / 0.66 / 0.71 in all d = 3 / 5 / 7 cells; the soft HMM's minimum is 0.37 at d = 3 and 0.56 at d = 7; the hard-flag HMM, which is a control, goes as low as 0.14 at d = 3).

## 3. Robustness (grid G3 + G5)

| Setting (d = 5 unless stated) | HMM lag 0 (soft) | CNN lag 2 (soft) | Note |
|---|---|---|---|
| matched, centre cell | 0.51 [0.48, 0.54] | 0.72 [0.70, 0.74] | reference |
| HMM p_L ×0.5 / ×2 | 0.52 / 0.51 |, (CNN unchanged) | |
| HMM τ ×0.5 / ×2 | 0.46 / 0.49 |, | |
| HMM ρ' = 0.3 / 0.7 | **0.59** / 0.49 |, | a *wrong* ρ beats the matched HMM: the HMM emission model is mis-calibrated (shared stabilisers, two-round measurement-error signature); it is a baseline, not a Bayes-optimal reference |
| d = 7 HMM mismatch (same six) | 0.62 to 0.73 (matched 0.67) |, | |
| CNN trained at centre, tested at (1e-3,8) / (2e-3,4) / (2e-3,16) / (5e-3,8) |, | 0.75 / 0.67 / 0.74 / 0.62 | matched-on-cell CNN: 0.73 / 0.69 / 0.74 / 0.67, essentially no loss |
| simulator ρ = 0.25 (weaker signature); HMM given ρ = 0.25, CNN trained at ρ = 0.5 | 0.33 [0.28, 0.37] | 0.61 [0.58, 0.65] | both trackers lose signal when the signature weakens |
| simulator ρ = 0.7; HMM given 0.7, CNN trained at 0.5 | 0.35 | 0.57 | |
| **LRU η = 0.5 (τ_eff ≈ 1.8), matched HMM and CNN** | 0.32 [0.25, 0.39] | **0.57 [0.52, 0.63]** | G_B = 0.75; hard CNN flag 0.27, hard HMM flag 0.00 |
| **LRU η = 0.9 (τ_eff ≈ 1.1), matched HMM and CNN** | 0.21 [0.11, 0.31] | **0.43 [0.35, 0.51]** | G_B = 0.68; hard CNN flag 0.09; CNN lag-0 recall at θ = 0.5 is 0 yet its soft weights still give 0.40 |
| d = 7, 8 of 9 cells: CNN trained at centre only (amendment 2) |, | 0.71 to 0.90 | conservative for f |

(The HMM in the LRU cells *was* matched: run_cell passes η_lru to the HMM's return rate; the result JSON prints the nominal τ = 8, which misled the referee's F1 remark. The CNN was mismatched in the first η = 0.9 run, f = 0.29, and matched in the re-run reported above.)

**Reading.** Robustness to a factor-2 parameter error (HMM) and to train/test mismatch (CNN) is good. The regime that limits the method is **episode length**: when leakage is removed every cycle (τ_eff ≈ 1), one-round episodes are nearly indistinguishable from measurement errors, hard flags become useless (0.00 to 0.09), and only the *soft* posterior still carries value (0.43 of a 0.68 oracle gain, i.e. ≈ 29 % of the leakage-induced error at d = 5). That is exactly the regime of Google 2023/2025 (DQLR every cycle) and of the Delft built-in-readout LRU (2511.17460, PRX Quantum 2026). The paper's claim therefore applies with full strength to architectures **without** per-cycle LRU, or to the **residual multi-round leakage** an imperfect LRU leaves behind, and with reduced strength (≈ 0.4 to 0.6 of the oracle gain) at τ_eff ≈ 1 to 2.

## 4. Controls: is per-shot information needed, or just better average weights?

Three decoders with **no** per-shot information, same shots (control_baselines.csv, control_diagnostics_d5_centre.json):

| control (d = 5 realistic cells) | f (min to max) | d = 7 | comment |
|---|---|---|---|
| A4: DEM with every leakage-touched edge raised to its *average* leakage probability (model-average) | 0.12 to 0.33 | 0.17 to 0.45 | the fair control; the CNN's gain *beyond* A4 is 52 to 67 % (d = 5) and 56 to 84 % (d = 7) of the remaining gap (referee_checks.csv) |
| A3: uniform rescaling of all DEM probabilities, scale chosen on a calibration sample (sweep 1 to 128; optimum at 8, bracketed) | 0.00 to 0.06 | 0.10 to 0.15 | matching is nearly invariant to a global rescaling |
| A2: DEM re-estimated from leaky syndromes with the pairwise-moment (Spitz 2018) estimator | −0.5 to −4.9 (P_fail 3 to 5× *worse* than ignoring leakage) | −0.35 to −4.9 | **pathology, now diagnosed:** leakage randomises several detectors of one qubit at once, which the pairwise estimator reads as inflated space-like edges (median 2.7×, 90th percentile 6.9× nominal); the boundary-edge residual then goes negative and is clipped to ≈ 0 for 73 % of boundary edges, so the decoder loses its boundary. A naive data-driven DEM is *harmful* under correlated leakage, a useful cautionary result, but not a fair "average-noise" control |

Conclusion (fact): per-shot inference adds 0.3 to 0.5 of the oracle gain on top of the best average-information decoder; a global recalibration adds nothing; a naive moment-based recalibration hurts.

## 5. Model severity and the Sycamore-like check

In the primary model leakage dominates the error budget: at the centre cell ε_A is ≈ 20× (d = 5) and ≈ 140× (d = 7) the leakage-free SI1000 value (G2 report), whereas Google 2025 attributes ≈ 17 % of 1/Λ to leakage + stray interactions. So "the oracle removes 85 to 94 % of the error" is a statement about *leakage-induced* error in a leakage-dominated model, and any flag's benefit on a real device is bounded by the leakage share there. The detection-fraction rise in our model at (1e-3, τ = 10) is 45 % over 25 rounds vs ≈ 12 % measured by Google 2023 at d = 5 without DQLR, the absolute leakage excess (≈ 1.2 vs ≈ 0.9 percentage points) is comparable, but our p = 1e-3 background (2.4 % detection fraction) is ≈ 3× cleaner than Sycamore 2023.

**Sycamore-like background (G5, d = 5, 1e5 shots, matched CNN and HMM).** Raising the SI1000 scale to p = 3e-3 gives a detection fraction of 8.2 to 8.5 % and a leakage-free ε_ref = 2.20e-3 per round (P_fail = 5.2 % over 25 rounds), close to the Google 2023 d = 5 experiment (ε ≈ 3e-3, detection fraction ≈ 9 %). Adding leakage at (p_L, τ) = (1e-3, 4) and (1e-3, 8):

| cell (p = 3e-3) | ε_A | leakage share of ε_A | G_B (oracle) | f soft CNN lag 2 | f hard CNN | f soft HMM | total LER drop, CNN / oracle | CNN recall / precision |
|---|---|---|---|---|---|---|---|---|
| (1e-3, τ = 4) | 3.33e-3 | 34 % | 0.23 | 0.24 | 0.14 | 0.02 | −5.7 % / −24 % | 0.29 / 0.76 |
| (1e-3, τ = 8) | 4.03e-3 | 45 % | 0.27 | 0.30 | 0.29 | 0.10 | −8.4 % / −28 % | 0.48 / 0.79 |
| same cells at p = 1e-3 (G1) | 0.44e-3 / 0.77e-3 | 82 % / 90 % | 0.71 / 0.76 | 0.66 / 0.73 | 0.47 / 0.63 | 0.48 / 0.53 | -47 % / -56 % vs -71 % / -76 % | 0.60 / 0.82 and 0.70 / 0.87 |

This is the single most important caveat found in this turn. At a realistic background the tracker's value shrinks on **both** factors: (i) leakage is a 34 to 45 % share of the error, so even the oracle removes only a quarter of it, and (ii) the tracker's recall drops (0.29 to 0.48 vs 0.60 to 0.70), because the leakage signature (ρ = 1/2 randomisation of ≈ 2 to 4 detectors per round) is harder to separate from a 3.5× denser background of ordinary detection events. The HMM becomes useless (f ≤ 0.10). The net result on a Sycamore-2023-like device would be a 6 to 8 % reduction in logical error per round at d = 5 at the standard training budget (12 % with 4× the training data, §5.1), versus 24 to 28 % with perfect flags. A paper must state this plainly; the headline f ≈ 0.7 to 0.9 is a result at a background 3× cleaner than today's devices, i.e. where leakage dominates. (Whether the recall drop is a training-budget artefact is tested in §5.1: partly yes, 4× more training data lifts f from 0.30 to 0.43.)

### 5.1 Background scan at (p_L, τ) = (1e-3, 8), d = 5, is the drop a training artefact or a signal-to-noise limit?

| p (SI1000) | detection fraction | ε_A | G_B (oracle) | f, CNN lag 2 soft (5e4 train shots) | f, CNN (2e5 shots, 10 epochs) | LER drop CNN / oracle |
|---|---|---|---|---|---|---|
| 1e-3 (G1) | 2.4 % | 0.77e-3 | 0.76 | 0.73 |, | −56 % / −76 % |
| 2e-3 | 6.2 % | 1.89e-3 | 0.47 | 0.47 (recall 0.61, precision 0.80; soft HMM 0.25) |, | −22 % / −47 % |
| 3e-3 | 8.5 % | 4.03e-3 | 0.27 | 0.30 (recall 0.48, precision 0.79) | **0.43** (recall 0.52, precision 0.84; hard 0.34) | −8 % → **−12 %** / −29 % |

Figure: g5_pscan_figure.png. **Both** effects are real: (i) the oracle's own share G_B falls 0.76 → 0.27 because leakage becomes a smaller part of the budget (this is a property of the device, not of the method); (ii) the tracker's recovered fraction f falls 0.73 → 0.30 at a fixed training budget, and **4× more training data brings it back to 0.43** with no change of architecture, so a sizeable part of the drop is a learning-budget effect, the leaked qubit-rounds are only 0.6 % of the data, and at a denser background the CNN needs more positives to separate them. The remaining gap (0.43 vs 0.73) is a genuine signal-to-noise limit at this architecture size. Honest reading for a paper: on a Sycamore-2023-like device the method would remove ≈ 12 % of the logical error per round at d = 5 (perfect flags: 29 %); on a device where leakage is the dominant error (no LRU, or post-LRU residual leakage with τ > 1) it removes 50 to 60 %. The next experiment that most changes the paper is a larger CNN / 1e6-shot training at p = 3e-3, it decides whether f at realistic background can reach ≥ 0.6.



## 6. Latency (grid G4, information-set emulation)

Oracle flags delivered D rounds after their round is committed keep f = 0.83 / 0.62 / 0.48 / 0.34 / 0.25 (d = 5) and 0.92 / 0.79 / 0.65 / 0.53 / 0.45 (d = 7) for D = 1…5 at the centre cell (1e5 shots each); H-harmful false in 0/9 (W, L_f) pairs, H-neutral false in 0/9. The CNN lag-2 tracker at d = 5 gives 0.75 when the decoder waits two rounds (W = 2) and 0.58 at W = 0. This is an **information-set bound** (one global decode whose round-r weights use only information available at r's commit time), not a measured sliding-window decoder; "W ≥ L_f recovers everything" is true by construction. The pilot's single-round-erasure "cliff" is retracted: with multi-round episodes even the pilot's own misattribution rule keeps 89 % / 95 % of the gain at D = 1.

## 7. Referee findings and how each was handled

| id | finding | action |
|---|---|---|
| F1 | LRU regime not covered; claim must be scoped | **Adopted.** G5 LRU cells run with matched trackers (η = 0.5: 0.57; η = 0.9: 0.43). Claim scoped to multi-round leakage / imperfect LRU. (Partial rebuttal: the HMM in the LRU cell was matched via η_lru; the JSON's τ = 8 field is the nominal value.) |
| M1 | leakage dominates budget 20 to 140×; oracle numbers overstate device benefit | **Adopted.** Sycamore-like row added (§5); every oracle number is to be shown next to the leakage share. |
| M2 | use Λ and ε rather than P_fail ratios as headline | **Adopted.** Λ table in §2; ε_X/ε_B growth with d stated. |
| M3 | controls A2/A3 mis-specified | **Adopted with diagnosis.** A4 (model-average DEM) is the fair control; A2's failure mechanism identified (§4) and will be reported as a cautionary result, not as the control. |
| M4 | P2 incomplete for CNN | **Completed.** ρ = 0.25 and 0.7 cells run (0.61, 0.57). |
| M5 | d = 7 CNN mismatched in 8/9 cells | **Partly.** Declared as amendment 2; mismatch is conservative (centre-trained ≈ matched at d = 5). Two matched d = 7 cells remain to run before submission. |
| M6 | latency result is an information-set bound | **Adopted.** Re-labelled; sliding-window decoder listed as future work. |
| minor | ε vs P_fail drift; V2/V3 substitutions; training 5e4/6 vs 6e4/8; return Pauli 1/3 vs 1/4; memory-X not run; cite 2203.04948 | All declared in §8; metrics unified on ε in the final tables (final_cells.csv, final_lambda.csv). |

## 8. Limits and honest declarations

1. **Noise model.** Phenomenological data-qubit leakage only: no measure-qubit leakage, no leakage transport through CZ, no leakage-induced dephasing of neighbours, Stim's CX-based rotated code with SI1000 scaling. The signature parameter ρ = 1/2 is a model choice, bracketed by ρ = 0.25 and 0.7.
2. **Severity.** At p = 1e-3 leakage dominates the error budget (20 to 140× the leakage-free ε). At p = 3e-3 (Sycamore-like) leakage is a 34 to 45 % share and the tracker's benefit falls to an 8 to 12 % LER reduction depending on training budget (§5).
3. **Return Pauli** is uniform over X, Y, Z (1/3 each), not the pre-registered 1/4 (identity included); declared as amendment 3.
4. **Training protocol** 5e4 shots / 6 epochs in all grids (pre-registration said 6e4 / 8); the d = 7 CNN was trained once at the centre cell (amendment 2); d = 7 cells used 1e5 shots.
5. **Metric.** Pre-registration wrote P_fail-based f; all tables now report ε-based f (same ordering, slightly different values); both are in final_cells.csv.
6. **Validation substitutions** V2/V3 (validate_V2_V3.json): the Varbanov and Google comparisons are to published summary numbers, not to re-run reference code.
7. **Not run:** memory-X, transport on, matched d = 7 CNN outside the centre, a real sliding-window decoder, measure-qubit leakage.
8. **Prior art.** Belief-matching (2203.04948) and the Spitz estimator are the correct references for "posterior-weighted matching" and "data-driven DEM"; the novel element is the per-shot, syndrome-inferred, multi-round leakage posterior feeding the weights, at d ≥ 5, with latency and LRU scoping. 2610.03869 and 2601.09921 (neural decoders) must be cited as adjacent; 2609.10666 (Floquet LRU) and 2606.19482 are scope limits.
9. **Open audit items (found by the automated reviewer, not yet fixed).** (i) In `latency_run.py` the final-measurement leak probability for the delayed decoders uses exponent D−1 instead of D (`pi_final = pi_known[:,:,R-D]·a^(D-1)`), so at D = 1 the final data edge is informed by the *undecayed* last-round posterior. The oracle-delay fractions in §6 are therefore slightly optimistic; the affected edge family carries at most the ≈ 20 to 35 % of the oracle gain not attributed to time-like (51 to 64 %) and return (14 to 15 %) edges in G2, so the qualitative conclusion (gradual, never harmful) stands, but the D ≥ 1 numbers must be re-run before publication. (ii) `latency_report.md` says the D ≤ 0 bucket has 10 (W, L_f) pairs; latency_grid.csv has 11, a label miscount with no effect on the result. (iii) The turn-1 `survey_leakage.md` entry for Miao et al. (2211.04728) quotes MLR/DQLR leakage levels (3e-4, > 1.5 %, ≈ 1e-3, < 1e-4, ≈ 5e-3 per cycle) that do not trace to text actually read from the paper; only the abstract's "< 1e-3 device average, ten-fold reduction" and "decay constant ≈ 4.4 cycles" are verified. Re-read the paper before citing any of those numbers.

## 9. What a paper would look like, and what to run before submitting

**Title (working):** *Soft leakage tracking from syndromes alone: per-shot posterior weights for surface-code matching under multi-round leakage.*

**Claims (each with the figure that carries it):**
1. Syndrome-only inference of multi-round data-qubit leakage, fed as soft edge weights to MWPM, recovers 0.60 to 0.90 of the oracle gain across a 27-cell grid at d = 3, 5, 7, and the fraction grows with distance (Fig. 2).
2. Soft weights are the enabling step: with the same posterior, hard flags lose 0.05 to 0.12 (CNN) to 0.15 to 0.32 (HMM); soft weights keep a low-precision tracker useful and keep ≈ 0.4 of the oracle gain even when hard flags are useless (LRU η = 0.9) (Fig. 3).
3. Per-shot information beats the best average-information decoder (A4) by 0.3 to 0.5 of the gap; naive moment-based DEM re-estimation is harmful under correlated leakage (Fig. 5).
4. Late flags degrade gracefully (information-set bound) (Fig. 4).
5. Scope: the benefit scales with the leakage share of the error budget; at Sycamore-like background it is a 12 % LER reduction (29 % with perfect flags) (Fig. 5c), the method targets devices without per-cycle LRU or with residual multi-round leakage.

**Before submission (ordered by value):** (a) a larger CNN (64 to 128 channels) trained on ≥ 1e6 shots at p = 3e-3, plus the same scan at (2e-3, 8) and at d = 7, the one-point scan in §5.1 (0.30 → 0.43 with 4× data) shows claim 5 is a scope statement, not a kill, but how far f can be pushed at realistic background is open; (b) two matched d = 7 CNN cells; (c) measure-qubit leakage + transport in the simulator (the flag-aware decoder then has more to gain and the HMM structure changes); (d) re-run the G4 oracle-delay grid with the pi_final exponent fixed, then a genuine sliding-window decoder with W = 2; (e) memory-X; (f) d = 7 LRU η = 0.9 matched.

**Target venue:** PRX Quantum or npj Quantum Information after (a) to (c); Quantum with (a) alone, framed as a methods paper. If (a) cannot push f above ≈ 0.5 at p = 3e-3, the honest venue is a short methods note and the project's main value becomes the control/negative results (A2 pathology, LRU scoping).


## 10. Addendum (18 October 2026), after the external review and the real-device test

**Verdict revised: the method is correct and the simulation result is robust, but it does not help on any public hardware dataset.** On the Google 2023 d = 3/d = 5 syndromes (no per-cycle data-qubit leakage removal; detection fraction 0.14 to 0.17) soft leakage weights are 0.7 to 1.4 % worse at d = 3 and null at d = 5; the fitted simulator predicts the same null and shows perfect flags would remove only 2.9 % / 9.9 % of the logical error there (real_data_report.md). New simulation cells at 2023-like noise (G6: p = 6e-3, p_L = 2e-3, τ = 8) show the plain decoder at threshold (ε ≈ 0.022 for d = 3…9) and an oracle gain growing 9 → 27 % from d = 3 to 9, available gain that a syndrome-only tracker cannot reach at that detection fraction. Stronger baselines confirm that in the clean regime the gain is per-shot information (belief matching 0.17, best static learned DEM 0.42, CNN 0.72, BM + CNN priors 0.77 at the d = 5 centre cell); statistics are now ratio-aware (Fieller) and Holm-corrected (all 153 comparisons survive); the soft-weight rule is derived and insensitive to its constant (≤ 0.06 for s ∈ [0.5, 1.5]); the "half the shortfall" sentence is retracted (four-fold data closes one fifth); the six flagged citations were read and none kills novelty. **Paper status: a scope/methods paper for Quantum or npj QI, or a complete undergraduate thesis; not PRX Quantum.** Full point-by-point reply: response_to_referee.md.
