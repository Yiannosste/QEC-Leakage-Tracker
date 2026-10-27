# Referee report, "Syndrome-inferred leakage posteriors as soft edge weights for surface-code matching"

**Role:** adversarial referee for a planned submission to PRX Quantum / npj Quantum Information / Quantum.
**What I did:** read every evidence file listed in the brief (pre-registration + two amendments, prior-art table, simulator and tracker code, G1/G2/G3/G4 results, control baselines, herald map, validation files) and recomputed the headline numbers from the CSV/JSON. I ran **no** new simulations.
**Audience:** written plainly for the author (4th-year ECE, first quantum course). "ε" = logical error per round, "f" = fraction of the oracle gain recovered, "A" = decoder that ignores leakage, "B" = oracle flags, "D" = soft inferred posterior, "E" = hard-thresholded posterior.

Companion file: `referee_checks.csv` (my per-cell recomputation: ε-based and P_fail-based G_B and f, tracker/oracle ratios ε_X/ε_B, Λ_{5/7} per decoder, gain relative to the model-average baseline).

---

## 1. Summary of the evidence (what the files actually show)

| Claim in the brief | Evidence | My reading |
|---|---|---|
| Inferred soft posteriors recover a large fraction of the oracle gain | G1: CNN lag-2 f* median 0.69 (d=5), 0.81 (d=7); HMM lag-0 median 0.48 (d=5), 0.64 (d=7). Lower bootstrap bound > 0 in 27/27 cells. | **Supported** inside the model. Note the HMM alone does **not** pass the pre-registered 0.50 bar at d=5 (median 0.48); only the CNN does. |
| f grows with code distance | CNN lag-2 per cell: d=5→7 interval-separated in 8/9 cells, d=3→5 in 6/9. HMM: 9/9 and 5/9. | **Supported as stated**, but partly a property of the metric (see §5): the tracker's *absolute* distance to the oracle, ε_X/ε_B, **grows** with d (CNN lag-2 at the centre cell: 1.6× at d=3, 2.4× at d=5, 3.6× at d=7). |
| Soft weights beat hard flags | D vs E, same posterior: CNN lag-2 soft − hard = +0.02 to +0.26 (interval-separated in 7 to 8 of 9 cells per d; one cell at d=5, (5e-3,16), is −0.003); HMM soft − hard = +0.15 to +0.32, all cells. | **Supported**; the effect is large for the low-precision HMM (0.34 precision) and small (≈ +0.05 at d=7) for the high-precision CNN. The honest statement is "soft weights make low-precision trackers usable", not a uniform advantage. |
| Late flags lose value gradually, no cliff | G4: oracle f = 0.83/0.62/0.48/0.34/0.25 (d=5) and 0.92/0.79/0.65/0.53/0.45 (d=7) for D = 1…5; H-harmful false 0/9, H-neutral false 0/9. | **Supported** for the oracle at τ = 8. Not tested for the trackers at d=7, not tested for τ ≤ 2 (where it will be much steeper, as the report itself notes), and the "streaming" decoder is an information-set emulation, not a windowed decoder. |
| Robust to tracker mismatch | G3: HMM under 6 mismatch settings f = 0.46 to 0.59 (d=5), 0.62 to 0.73 (d=7), matched 0.51/0.67. CNN under train/test mismatch (4 cells, d=5) f = 0.62 to 0.75. | **Supported for the HMM**, but note ρ' = 0.3 *beats* the matched HMM (0.59 vs 0.51 at d=5, 0.73 vs 0.67 at d=7). A wrong parameter beating the right one means the "matched" HMM is not well calibrated, so robustness is partly "insensitivity of an under-tuned tracker". CNN ρ-mismatch was not run. |
| Average-noise recalibration recovers much less | Controls: A4 (model-average DEM) f = 0.12 to 0.30 (d=5), 0.17 to 0.42 (d=7); A3 (uniform rescaling) f ≤ 0.15; A2 (Spitz re-estimated DEM) f = −0.35 to −4.9. | **Direction supported**, but two of the three controls are mis-specified (A2 is catastrophically worse than ignoring leakage; A3's optimum sits on the sweep boundary in 15/18 cells). Relative to the fair baseline A4, the CNN still recovers 52 to 67 % (d=5) and 56 to 84 % (d=7) of the remaining gap. |
| LRU regime (η_lru = 0.9) | G3: G_B = 0.68; D-HMM 0.21 [0.11, 0.31], D-CNN lag-2 0.29 [0.20, 0.36]; hard flags E ≈ 0 or slightly negative. Recall 0.04 to 0.24. | **Weak and both trackers were mismatched** (HMM assumed τ = 8, CNN trained at τ = 8; true episode length ≈ 1.1 rounds). This is the regime every current transmon QEC experiment operates in (DQLR/LRU every cycle). |

**Pre-registered rules, recomputed mechanically from the CSVs:**

- **P1** (median f* ≥ 0.50 at d=5 and d=7; lower bound > 0 in ≥ 7/9): d=5 median 0.692, d=7 median 0.813, lower bound > 0 in 9/9 at both. **Holds.** (d=3, not required: 0.641.)
- **P2** (f ≥ 0.30 under all six mismatch settings for the tracker that achieved P1): the P1 tracker is the CNN in 27/27 cells. For the **HMM** all six settings pass (min 0.462 at d=5, 0.617 at d=7). For the **CNN** only four train/test-mismatch cells exist (p_L ×0.5, ×2.5, τ ×0.5, ×2; all ≥ 0.62) and the two ρ' settings were **not run**. By the letter of amendment 1 item 6, P2 is **not mechanically complete** for the tracker that passed P1. By any reasonable reading it will pass (the HMM, which is far more fragile, passes with margin), but it must be run.
- **P3** (G_B ≥ 0.15 at the centre cell, both d, interval of ε_A − ε_B excludes 0): 0.846 [0.828, 0.863] and 0.944 [0.935, 0.952]. **Holds by a factor ≈ 6.**
- **P4** (no prior paper with syndrome-inferred leakage flags → matching at d ≥ 5 with a latency analysis): **holds** on the prior-art table and on my own checks (§4), with one framing correction (belief-matching).

**Mechanical verdict:** PAPER-READY is *not yet* formally reached (P2 incomplete for the CNN); it is one cheap run away. No KILL condition is anywhere near triggered.

**Signs of tuning after results / criteria drift / cherry-picking:**

1. **Metric definition drift (minor but must be fixed).** The pre-registration (§4) defines G_B and f in terms of ε (per-round error). `g1_results.csv` computes both from the 25-round P_fail. The difference is up to 0.046 in f and 0.042 in G_B (largest at the heaviest cells), always in the conservative direction (file f < ε-based f), so no conclusion changes. But the G2 and G4 reports use the ε-based definition, so the same centre cell appears as G_B = 0.830 (G1 file) and 0.835 to 0.846 (G2/G4). One definition, everywhere.
2. **Validation criteria substituted after the fact.** `validate_V2_V3.json`: V2 as pre-registered ("mean episode length = τ ± 5 %") *fails* (5.28 vs 8 for τ=8, 3.41 vs 4) and is replaced by a hazard-rate test (0.1257 vs 0.125, passes). The replacement is the correct estimator (truncation bias), but the file should say "pre-registered V2 criterion not met as written; replaced by…". V3 as pre-registered ("±0.02") also fails on the max deviation (0.115 over 60 cells) while the mean passes (0.493 vs 0.5). Say so, and say whether the 0.115 cells are low-count.
3. **Training protocol inconsistency across documents.** Amendment 1 fixes the CNN protocol as 6e4 shots / 8 epochs; amendment 2 says "5e4 training shots, 6 epochs, as in amendment 1"; `run_cell.py` defaults are 5e4 / 6; the G4 report says 6e4 / 8. I could not determine which was used for G1. This is not a result-driven change, but a referee will ask.
4. **Return-Pauli model differs from the pre-registration.** Pre-registration: on return "uniformly random Pauli (I, X, Y, Z each 1/4)" = full depolarisation. Code (`leakage_sim.py` line 9, 209 to 216): X, Y or Z each 1/3, never I, harsher, and the soft-weight constant c = 2/3 in amendment 1 matches the code, not the pre-registration (which would give c = 1/2). Declare it as an amendment.
5. **Best-of-two lag selection** (f* = best of ℓ ∈ {0, 2}) is done on the same test shots. With two candidates and 1e5 shots the optimism is negligible (< 0.01), and lag 2 wins in 27/27 cells anyway, so this is fine; just report ℓ = 2 as the primary and drop "best of".
6. **No cherry-picking of cells detected**: all 27 G1 cells, all 63 G2 cells and all 82 G3 rows are reported; the stopping rule was never triggered; seeds follow the pre-registered formula (I checked 1133/1233 for the centre cells and that G1 and G4 share identical decoder-A failure counts, 3870 and 2802, confirming identical shots).

---

## 2. Verdict

**Major revision** for PRX Quantum / npj QI. Not reject: the study is pre-registered, internally consistent, the statistics are done properly (paired bootstrap on identical shots, Wilson intervals, McNemar counts), and the central result, a syndrome-only tracker feeding continuous MWPM weights recovers 70 to 90 % of the oracle gain in a circuit-level leakage model at d ≤ 7, is new and clearly demonstrated *inside its model*. Not accept-with-minor-revisions: the regime that matters to the hardware groups the paper targets (leakage removed every cycle by an LRU/DQLR, τ ≈ 1) is exactly where the evidence is weakest and the trackers were run mismatched; the leakage model is 3 to 10× more severe than Sycamore-class syndrome statistics; and two of three "average-noise" controls are mis-specified. For *Quantum* the bar on hardware realism is lower and the pre-registration/statistics are above the norm; there I would say accept after the fixes in §3 (major list).

---

## 3. Issues

### Fatal (would sink the paper if not resolved before submission)

None of the present results is wrong. One issue is *conditionally* fatal:

- **F1. The LRU regime.** `g3_results.csv` rows `lru0.9`: oracle gain 0.684 but D-HMM 0.214 [0.113, 0.309], D-CNN lag-2 0.285 [0.202, 0.361], and the hard-flag decoders E are at or below zero (−0.012 [−0.091, 0.065], −0.069 [−0.146, 0.003]). Both trackers assumed τ = 8 while the true effective lifetime is ≈ 1.1 rounds (the HMM `hmm` column literally reads `tau: 8.0`). Google 2023/2025, Delft (Xin 2026), and He et al. (PRL 135, 260601, 2025) all run LRUs every cycle, so **the paper's "transmon-like" claim rests on a regime no leading experiment is in**. If a *matched* tracker still recovers only ≈ 0.3 at η_lru = 0.9, the paper must be re-framed as "for architectures without per-cycle LRU, or for the residual multi-round leakage an imperfect LRU leaves behind", publishable, but a different and smaller paper. If a matched tracker reaches ≳ 0.5, F1 disappears. This single run decides the title. (Author notes a matched-CNN run is in progress; the HMM must also be matched: τ_eff = 1/(1 − (1 − 1/τ)(1 − η_lru)) ≈ 1.1.)

### Major

- **M1. Leakage dominates the error budget far more than on hardware.** Oracle report §5: leakage raises ε_A by ≈ 20× (d=5) and ≈ 140× (d=7) over p_L = 0; Google 2025 attributes ≈ 17 % of 1/Λ to leakage + stray interactions. From `validate_rise.csv` at (p_L = 1e-3, τ = 10, no LRU) the detection fraction rises 45 % from round 1 to round 24 (2.70 % → 3.92 %); Google 2023 (no DQLR) measured ≈ 12 % at d=5. The absolute leakage excess (≈ 1.2 % vs ≈ 0.9 %) is comparable, but the SI1000 p = 1e-3 background (≈ 2.4 % detection fraction) is ≈ 3× cleaner than Sycamore 2023 (≈ 7 to 8 %). Hence G_B ≈ 0.85 to 0.94 is a model artefact; any flag looks heroic when leakage is 95 % of the error. **Fix:** add a "Sycamore-like" row (p = 3e-3 background, p_L ≈ 5e-4 to 1e-3, τ ≈ 4 to 8) and report absolute ε and Λ there. Report G_B in the abstract only together with the leakage share of ε_A.
- **M2. Headline metric.** f normalises by (ε_A − ε_B), which → ε_A as G_B → 1, so f → 1 − ε_X/ε_A and "f grows with d" is partly bookkeeping. In the same cells ε_X/ε_B (how far the tracker is from the oracle) **worsens** with d: CNN lag-2 1.58 → 2.39 → 3.60 at the centre cell, HMM 1.98 → 3.45 → 6.54. Λ_{5/7} at the centre cell: A 1.40, HMM 2.17, CNN lag-2 2.72, oracle 4.11, leakage-free ≈ 9.5 (point estimate, 21 failures). **Fix:** make Λ and absolute ε the headline (Λ_{5/7} 1.4 → 2.7 is a strong, hardware-legible statement), keep f as a secondary, and replace "f grows with d" by "Λ improves from 1.40 to 2.72 but the gap to the oracle widens with d". Give Λ intervals (the oracle report already does this via Wilson endpoints; do it for D/E too).
- **M3. Two of three average-noise controls are mis-specified** (`control_baselines.csv`). A2 (Spitz re-estimated DEM) gives P_fail 3 to 5× *worse* than ignoring leakage (f = −0.5 to −4.9, e.g. centre d=5: 0.128 vs 0.039). A properly estimated DEM cannot be that much worse than the prior DEM unless the estimator produced inconsistent/negative edge probabilities from non-Markov, hyperedge-like leakage correlations, or there is a bug. Either explain and show the pathology, or fix it; as it stands a referee will suspect a broken baseline and discount the whole "re-calibration recovers much less" claim. A3 (uniform rescaling) sits at the sweep maximum 8.0 in 15/18 cells, the optimum was not bracketed. Only A4 (model-average DEM) is a fair control: it recovers 0.12 to 0.42, and the tracker's gain *relative to A4* is 52 to 84 % of the remaining gap (my `fprime_cnn` column). Report that number; it is the honest "value of per-shot information".
- **M4. P2 not completed for the tracker that passed P1** (see §1). Run the CNN under ρ' = 0.3/0.7 (and ideally the HMM with τ' at the LRU cell). Also, the matched HMM is beaten by its own ρ' = 0.3 variant at both distances, the HMM emission model (P(defect | L) = ρ ⊕ p_det0, independent detectors) is evidently mis-calibrated for the actual leaky-defect statistics (two-detector signature of a flipped measurement, shared stabilisers). Say so; the HMM is a baseline, not the Bayes-optimal reference, and the paper should not imply the CNN "beats the HMM" in a Bayesian sense.
- **M5. d = 7 CNN is train/test-mismatched in 8/9 cells (amendment 2) and all d = 7 cells use 1e5 not 2e5 shots.** Declared, conservative for f, but the paper's "f grows with d" comparison then compares matched d=5 CNNs with mismatched d=7 CNNs. A matched d=7 CNN at two more cells (e.g. (1e-3, 4) with only 382 A-failures and 48 B-failures, and (5e-3, 16)) would settle whether the d-trend is understated or overstated.
- **M6. The latency result is not a decoder result.** G4 uses an information-set emulation (one global decode with time-dependent knowledge) and the true τ to extrapolate; it measures information value, not sliding-window performance. The abstract must say "information-set bound"; the statement "W ≥ L_f recovers everything" is true by construction and should not be quoted as a decoder property. The pilot-misattribution rule *beating* the soft Markov-discounted rule at D = 1 (0.89 vs 0.83 at d=5, non-overlapping intervals) also shows the a^D discount is too conservative, i.e. the soft rule itself is not optimal; a one-line fix (do not discount, or learn the discount) belongs in the paper.
- **M7. Model realism (see §4 below), in particular no measure-qubit leakage, no transport, ρ = 1/2 on all adjacent checks, onset at round start, CX instead of CZ.** None threatens the qualitative claim; several threaten the quantitative numbers. One additional simulation (§4) is required.

### Minor

- m1. Unify G_B / f definitions (ε-based, as pre-registered) across G1/G2/G3/G4 and the controls (which use P_fail).
- m2. Declare the return-Pauli change (X/Y/Z each 1/3 vs 1/4 each) and the resulting c = 2/3 as an amendment.
- m3. Declare the V2/V3 criterion substitutions explicitly; report the low-count explanation (or not) for the 0.115 deviation.
- m4. Fix the training-protocol numbers (5e4/6 vs 6e4/8) in the text to what was actually run; store `cnn_params` in the paper's data release.
- m5. `validate_ler.csv` runs with rounds = d and τ = 10, not the production R = 25 / τ grid, and the d = 7 rows have 1 to 16 failures (uninformative). The V1 check "p_L = 0 reproduces SI1000" is trivially true here (identical failure counts for A and B); an *independent* SI1000 reference (e.g. Stim's own generator numbers from the literature) should be quoted. Otherwise V1 proves only that the leakage code path is a no-op at p_L = 0.
- m6. The P_fail → ε mapping ε = ½[1 − (1 − 2P)^{1/R}] assumes per-round independence; with τ = 16 episodes spanning most of the 25-round window that is not exact. Fine as a convention; state it.
- m7. Report the tracker's recall/precision/delay in the same table as f, and the herald map (`herald_G1_d5_pL0.002_tau8.csv`) alongside: the CNN lag-2 at (recall 0.735, precision 0.881) gives f = 0.72, and the random-corruption herald at (0.75, 0.90) gives 0.748, this near-match is a genuinely useful result (tracker errors are only mildly syndrome-correlated) and is currently buried.
- m8. Figures: panel (c) of the G1 figure plots ε on a log scale with D_HMM between A and the CNN, good; add the leakage-free reference line. The G3 panel (b) mixes CNN and HMM markers; add the matched-HMM point at each cell for comparison.
- m9. Memory-X was pre-registered as a check at the centre cell and was not run in any track.
- m10. 25 rounds for all d (pre-registered) is standard, but the `rounds = d` validation and the `R = 25` production should not be mixed in one figure.

---

## 4. Model-realism attack (what a Google/IQM physicist would say)

| Objection | Threatens qualitative claim? | Threatens quantitative claim? | Comment |
|---|---|---|---|
| ρ = 1/2 randomisation of *every* adjacent check, independently per round | No | Yes | On hardware the leaked-qubit/ancilla CZ imparts a conditional phase (Miao: ≈ 0.65π) so the defect rate is ≈ 0.5 for some checks and much less for others, and is correlated across rounds. Your ρ = 0.25 sensitivity (CNN f drops 0.72 → 0.61, HMM 0.51 → 0.33) already shows the trackers lose signal when the signature weakens. Hardware is probably between 0.25 and 0.5 and *anisotropic*. |
| Return applies a Pauli with certainty (X/Y/Z each 1/3) | No | Yes (direction unclear) | Real DQLR/decay returns |2⟩ → |1⟩, so the error is a deterministic X-like flip plus dephasing, closer to your model than to full depolarisation, actually. But natural decay is to |1⟩ at an unknown time inside a round. |
| No measure-qubit leakage | No | Yes | Measure-qubit leakage is ≈ 3e-4/cycle with MLR and produces two-round defect signatures identical to your single-round data-leak false positives. It is the main source of *false alarms* for a syndrome-only tracker and was omitted. |
| No transport (leakage hopping data ↔ measure qubit) | No | Yes | Transport shortens τ (McEwen: 2.4× faster decay with reset) and moves the signature to the ancilla; pre-registered as optional, never run. |
| No |3⟩ | No | Marginal | Matters only for LRU imperfection (P(3→2) = 0.5). |
| Onset at round start, fixed signature for the whole round | No | Yes | Leakage happens mid-round at a CZ; in that round only the checks *after* the leaking gate are affected. Tracker delay is quoted in rounds; a half-round offset is 50 % of the lag-0 budget. |
| SI1000 with CX instead of CZ | No | No (declared) | Pauli-equivalent for the stabiliser simulation; mention that the leakage signature in CZ hardware is phase-like. |
| Leakage = 95 % of the error budget (20 to 140× the leakage-free ε) | **Yes, for the framing** | Yes | See M1. A gain of "85 to 94 %" on an error that is 17 % of the real budget is at most ≈ 15 % of the real ε. State this arithmetic in the paper. |
| No LRU in the primary model | **Yes** | Yes | See F1. |
| Twirled/incoherent leakage (Manabe 2025) | No | Possibly | Coherent leakage can give *lower* logical error than its twirled approximation; the oracle gain could be overstated. State as caveat (already in §9 of pre-reg). |

**Single most important additional simulation:** the *matched-tracker LRU/DQLR cell*, η_lru ∈ {0.5, 0.9, 0.99} at the centre p_L with the HMM given τ_eff and the CNN trained on the same LRU data, at d = 5 and 7, with measure-qubit leakage switched on (p_L^m = p_L, lifetime 1 round, as pre-registered optional). This answers in one grid whether the method has anything to offer the devices that actually exist (F1) and whether false alarms from measure-qubit leakage destroy the precision the CNN currently enjoys (0.88). Second choice: a "Sycamore-like" background (p = 3e-3) row to deflate M1.

---

## 5. Statistics attack

- **Paired bootstrap on identical shots, 2000 resamples, seed 42**: correct and the right tool; the implementation via the four paired-outcome counts is exact for a two-decoder comparison. For f (a ratio of two paired differences) the bootstrap is also right. Fine.
- **Wilson intervals**: fine for P_fail. Λ intervals from Wilson endpoints are conservative; acceptable.
- **Power**: the weakest G1 cell is (d=7, 1e-3, 4) with 382 A-failures and **48 B-failures**; f intervals there are ±0.07 (CNN) and ±0.08 (HMM). The stopping rule counts A-failures only, so B-failure starvation is not caught; at d=7 the oracle has 48 to 261 failures in 6/9 cells. State that the *upper* end of f is poorly determined there. The G2 d=7 reference run has 21 failures (Λ_{5/7} = 9.5 is ±≈ 40 %); don't quote it to two digits.
- **Seeds**: one simulator seed per cell. Everything is paired so this is fine for *differences*, but the between-cell "f grows with d" comparison is between independent samples, the per-cell interval separation test I ran (8/9 cells for the CNN at 5→7) is the right one and should be in the paper instead of comparing medians.
- **Is "fraction of oracle gain" a fair headline?** No (M2). It is fair as a *tracker quality* metric at fixed cell (and it maps nicely onto the herald map), but it is unfair as a *scaling* metric because its denominator saturates. Headline: Λ and ε with intervals; secondary: f; tertiary: ε_X/ε_B.
- **d-dependence with intervals**: supported for 5→7 (8/9 CNN, 9/9 HMM) and weaker for 3→5 (6/9, 5/9); the d=7 points are mismatched CNNs (M5). Report it as "f_D increases from d=5 to 7 in 8/9 cells with non-overlapping 95 % intervals", not as a law.
- **Multiple comparisons**: 27 cells × 5 decoders × intervals, no correction, but every lower bound is far from 0 (min 0.37 for E_HMM at d=7), so nothing hinges on it.
- **Mis-specification**: the HMM "matched" parameters are mis-calibrated (ρ' = 0.3 beats matched), so "HMM vs CNN" is "under-tuned Bayes filter vs learned filter". Say so.

---

## 6. Novelty attack

**Is S4 (leakage posterior → continuous MWPM weights) open?** Narrowly yes, with one correction to the framing. Posterior-marginal → edge-weight re-weighting of MWPM is *belief-matching* (Higgott, Bohdanowicz, Kubica, Flammia, Campbell, "Improved decoding of circuit noise and fragile boundaries of tailored surface codes", Phys. Rev. X 13, 031007 (2023) = arXiv:2203.04948; venue/volume taken from a reference-list entry and the arXiv html seen in this session): BP marginals of Pauli error mechanisms set the matching weights. AlphaQubit's "soft matching" does the same for readout posteriors. What is new here is the **source** of the posterior (a temporal hidden-state tracker for leakage, from syndromes only) and the **ablation soft vs hard** on the same posterior. The paper must cite belief-matching and position itself as "belief-matching where the belief is a leakage-state posterior". The prior-art table's S4 row should say so. Also cite "Experimentally informed decoding of stabilizer codes based on syndrome correlations" (Jan 2026, d=3, leakage channels in correlation-estimated MWPM weights) as the closest *average-noise* re-weighting of leakage, it is the correct reference for what your A2 control attempts.

**Colleague's suggested ids** (the arXiv API was unreachable from this sandbox, see §10, so each id was checked by web search: 2610.03869, 2609.10666 and 2606.19482 against their arXiv abstract pages; 2601.09921 against the arXiv monthly listing and a ResearchGate record carrying the id, title, authors and date; 2511.17460 against the prior-art table's earlier API verification):

| id | What it is | Must cite? |
|---|---|---|
| 2610.03869 | Lange, Fjeldså, Jonasson Johansson, Granath (2 Oct 2026): modular graph-recurrent neural decoder, pretrained in simulation and fine-tuned on IBM Nighthawk-generation hardware and Google below-threshold data; stability and ZZ-merge experiments. No leakage tracking. | Cite in the "learned decoders" paragraph (sim-to-hardware fine-tuning is the route your CNN tracker would need). Not a scoop. |
| 2601.09921 | Zhang, Yi et al. (Tsinghua, 14 Jan 2026): "Learning to Decode in Parallel: Self-Coordinating Neural Network for Real-Time QEC", parallel windowed neural decoding with AlphaQubit-level accuracy. | Cite in the latency/streaming discussion (M6): it is the kind of windowed decoder your information-set emulation stands in for. Not a scoop. |
| 2609.10666 | Westerheim, Sahay, Puri (9 Sep 2026): walking honeycomb Floquet code circuits as zero-overhead LRUs; four leakage models incl. skip-gate; leaked qubit measured → random outcome. | Cite in the leakage-model and LRU discussion; their four-model table is a good template for your realism caveats. Not a scoop. |
| 2606.19482 | Gu, Noszko, Steffan, Eberhardt, Roffe, Eisert, Koutsioumpas (17 Jun 2026): directional tile codes, planar qLDPC with nearest-neighbour iSWAP. No leakage content visible in the abstract. | Optional (outlook: "trackers for non-matching codes"). Not required. |
| 2511.17460 | Xin et al. (Delft), PRX Quantum 2026: LRU built into transmon readout, 3-state readout heralds, NN decoder, d=3. Already in your prior-art table. | Must cite (hardware herald baseline for S5). |
| T. He, W. Lin, R. Wang et al., PRL 135, 260601 (2025) | "Experimental quantum error correction below the surface code threshold via all-microwave leakage suppression", seen during this check only as reference [2] in arXiv:2606.11496, not on its own page; not in the prior-art table. | Should cite after checking the record: a second below-threshold experiment whose leakage handling is an LRU every cycle, reinforces F1. **Bibliographic details not independently verified.** |
| "Experimentally informed decoding of stabilizer codes based on syndrome correlations" (Jan 2026) | Correlation-estimated MWPM weights incl. leakage channels, d=3. | Should cite next to your A2 control. Full record not retrieved; **could not verify** authors/venue. |

Other 2025 to 2026 learned-leakage-detection work: the prior-art table already has Wang et al. 2604.14269 (GNN, atom loss) and Nishio et al. 2607.29603 (offline loss inference). I found no 2025 to 2026 paper that trains a tracker on transmon syndromes to output per-qubit per-round leakage posteriors and feeds them to a matching decoder. **S4 and the S2×S3 requirement map for inferred transmon flags remain open as of this check; S1 (the idea) is Varbanov 2020 and must not be claimed.**

---

## 7. Five most important additional experiments (value / cost)

1. **Matched trackers in the LRU regime** (η_lru ∈ {0.5, 0.9, 0.99}, d = 5 and 7; HMM with τ_eff, CNN trained on LRU data; include measure-qubit leakage p_L^m = p_L). Decides F1 and the title. Cost: ≈ 3 to 6 CPU-h (one CNN training per setting at d=5; reuse d=7 centre protocol). **Highest value.**
2. **Sycamore-like background row** (p = 3e-3, p_L ∈ {5e-4, 1e-3}, τ ∈ {4, 8}, d = 5) reporting absolute ε, Λ_{3/5} and the leakage share of ε_A. Deflates M1 and gives a number a hardware reader can compare to Google 2023's 12 % detection rise. Cost: ≈ 2 CPU-h.
3. **Fix the controls**: debug A2 (show the estimated edge probabilities; a negative-f control is not publishable unexplained), widen the A3 sweep to ≥ 32, and make A4 the headline control with the tracker's gain *relative to A4*. Cost: < 1 CPU-h.
4. **Complete P2 for the CNN** (ρ' = 0.3, 0.7 at d = 5 and 7) and run two matched d = 7 CNN cells to check amendment 2's downward-bias claim. Cost: ≈ 5 CPU-h at d = 7.
5. **One real sliding-window decode** at the centre cell, d = 5, W ∈ {2, 5}, CNN lag 2, to replace the information-set emulation with a measured boundary effect (M6). Cost: implementation effort, ≈ 1 CPU-h compute.

(Lower priority but cheap: ρ = 0.25 + measure-qubit leakage for false-alarm rate; memory-X check; transport on.)

---

## 8. Suggested title and abstract framing

**Title (conditional on experiment 1 failing to rescue the LRU regime):** *Soft leakage posteriors from syndrome histories as matching weights: how much of the oracle-flag gain a syndrome-only tracker recovers in a surface code with multi-round transmon leakage.*

**Title (if experiment 1 succeeds):** *Syndrome-inferred leakage posteriors recover most of the value of hardware leakage flags in surface-code matching, with and without leakage reduction units.*

**Abstract framing a careful referee would accept (one paragraph):** In superconducting surface codes a data qubit that leaks out of the computational subspace randomises its neighbouring stabiliser outcomes for several rounds; a matching decoder that knew exactly where and when this happened (an oracle flag) would remove most of the resulting logical error. We ask how much of that oracle gain can be recovered without any hardware leakage detection, using only the syndrome history. In a phenomenological multi-round leakage model on top of SI1000 circuit noise (rotated surface code, d = 3 to 7, 25 rounds), we infer per-qubit, per-round leakage posteriors with a per-qubit hidden Markov filter and with a small causal 3D convolutional network, and feed them as continuous edge probabilities into minimum-weight matching. Across nine pre-registered leakage settings the learned tracker recovers 66 to 75 % (d = 5) and 71 to 89 % (d = 7) of the oracle gain, raising Λ_{5/7} from 1.4 (leakage ignored) to 2.7 (oracle: 4.1) at the central setting, while a decoder re-calibrated to the average leakage statistics recovers 12 to 42 %. Soft weights outperform hard-thresholded flags, decisively for the low-precision HMM and modestly for the CNN; a flag delivered D rounds after its round is committed loses value gradually (83 % / 92 % of the oracle gain kept at D = 1 for d = 5 / 7). We give the trade-off between tracker recall, precision and lag, and show that the tracker's gain is close to that of a randomly corrupted herald with the same recall and precision. The gain is largest when leakage lives several rounds; in a regime with per-cycle leakage removal (one-round episodes) the oracle gain is smaller and the trackers recover [matched result here]. All results are from a pre-registered simulation study; the leakage model omits measure-qubit leakage, transport and coherent effects, and leakage dominates the error budget more strongly than on current devices, so the absolute numbers are upper bounds on the hardware benefit.

---

## 9. Over-claims to delete or soften

1. "Transmon-like leakage" → "a phenomenological multi-round data-qubit leakage model" unless the LRU/measure-qubit/transport cells are added.
2. "Recovers 85 to 94 % of the leakage-induced error" (any oracle number in the abstract without the leakage share of ε_A next to it).
3. "The fraction of the oracle gain grows with code distance" as a scaling law → report Λ and note ε_X/ε_B grows with d.
4. "Soft weights beat hard flags" as a uniform claim → "soft weights make a low-precision tracker usable; for the high-precision CNN the advantage is ≈ 0.05 in f".
5. "Robust to tracker mismatch" → "the HMM's gain is insensitive to ×2 parameter errors (and is not at its optimum when matched)"; add the CNN ρ-mismatch before claiming robustness for the CNN.
6. "Average-noise recalibration recovers much less" based on A2/A3 → base it on A4 only until A2 is fixed.
7. "Late flags are never harmful" → "in an information-set emulation at τ = 8 with the true τ known to the decoder".
8. "W ≥ L_f recovers the full gain" as a decoder property (true by construction).
9. Any statement that HMM-based syndrome-only leakage detection, leakage-aware matching, or imperfect-flag decoding is new.
10. "Matched CNN" at d = 7 (8/9 cells are centre-trained).

---

## 10. What I could not check

- The arXiv API (`export.arxiv.org`) was unreachable from this sandbox (proxy: host in a private/reserved range); the five ids were checked by web search instead (three against arXiv abstract pages, 2601.09921 against the arXiv listing + a ResearchGate record, 2511.17460 via the prior-art table). The Jan-2026 "syndrome correlations" paper's authors/venue were not retrieved.
- Two journal citations in §6, Higgott et al. PRX 13, 031007 (2023) and He et al. PRL 135, 260601 (2025), were seen only as reference-list entries inside other search hits, not on the publisher's or arXiv's own page; the author should confirm them before citing.
- Which CNN training protocol (5e4/6 or 6e4/8) was actually used for G1 (`cnn_params` lives in result JSONs not provided).
- Whether the V3 max deviation of 0.115 comes from low-count detector cells.
- V1 against an independent SI1000 reference (not in the files).
- The G2 heat-map CSVs (`oracle_map_cells.csv`) and the G4 CSVs were not provided; I checked G2/G4 numbers against the reports and against the shared centre-cell counts in `g1_results.csv` only.
- The in-progress matched-CNN LRU run.
- I did not re-derive the detector-flip patterns of `leakage_sim.py` or audit `hmm_tracker.py` line by line; I read the sampling and edge-weight code and the trackers' docstrings/interfaces.

**Deviations from the brief:** none in scope (all listed files were read; no simulations run, as instructed). One substitution: web search in place of the arXiv API for id verification.
