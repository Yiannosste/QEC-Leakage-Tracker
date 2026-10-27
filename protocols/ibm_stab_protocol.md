# Pre-registered protocol: the new leakage tracker (ALL) on unseen IBM ibm_berlin stability data

*Project C3. Frozen 2026-10-25, BEFORE any logical outcome (logical_flips.b8) of the stability runs was read. Up to this point only label-free quantities of these runs were looked at: shot counts and the mean detection fraction per run.*

## Why these data are "unseen"
- Data: Lange et al., arXiv:2610.03869, Zenodo 23335425, `ibm_berlin/stability_d3`. It is a d = 3 X-type stability experiment on IBM's square-lattice Nighthawk r1 chip ibm_berlin.
- 17 runs: T = 5, 10, 20, 50, 100 (100 000 shots each), plus a sweep of a coherent pre-readout rotation R_X(α), α ∈ {0.15, 0.3, 0.45, 0.6, 0.8, 1.0}, at T = 20 and T = 100 (50 000 shots each). The rotation raises the measurement-error rate on purpose.
- None of these runs was used in any earlier C3 analysis. The IBM work so far used only the memory runs (q36 for development, q85 as a test set).
- The tracker (xa_tracker.py v2) and every setting were frozen in the synthetic study detect2 (detect2_protocol.md v2). Nothing is tuned on IBM data.

## Circuit and adapter
- The shipped error model `error_model.dem` of every stability run has exactly the error structure (which detectors and observable each mechanism flips) of the authors' stability circuit `circuits/stability_d3_X.stim` (GitHub LangeMoritz/modular-gnn-rnn-decoder). This was checked for T = 10 and T = 20: 823/823 and 1723/1723 mechanisms match. The shipped DEM therefore defines the background noise; the circuit gives the layout.
- Layout: 7 data qubits and 8 measure qubits (6 X-type, 2 Z-type). Each data qubit touches 2 X checks and 1–2 Z checks.
- Adapter: `gen_leaky.py` (GenLeakyCircuit) reads the circuit and builds the same interface as leakage_sim.LeakyCircuit (adjacency, leakage-effect patterns, matcher). `with_dem()` makes the tracker and the matcher use the shipped DEM. All 220 leakage-effect patterns exist in the shipped DEM. xa_tracker.py is not modified.
- Synthetic adapter check (the stability circuit with uniform depolarising noise, injected data-qubit leakage p_L = 1e-3, τ = 8; no IBM data used):

| background p | detection fraction | AP (learned) | f (true params / learned) | note |
|---|---|---|---|---|
| 2e-3 | — | 0.83 | 0.77 / 0.85 | 8 000 shots, few failures |
| 6e-3 | 0.16 | 0.50 | 0.54 / 0.62 | 20 000 shots, A 68 failures |
| 6e-3, no leakage | 0.16 | — | — | EM still fits p_L 0.6–3.7e-3; A and X have 0 failures |
| 1e-2 | 0.24 | 0.23 | −0.15 / −0.24 | 20 000 shots, slight harm |

## Tracker (frozen, as ALL in detect2)
- XATracker(basis = 'both', explain = True), 8 damped Jacobi mean-field passes, damping 0.5, ρ = 1/2, no herald (IBM provides hard bits only), full smoothing.
- Label-free calibration, separately for each run: Baum–Welch on a calibration split, 12 iterations from p_L = 3e-3, p_ret = 0.25, per-qubit p_L, global p_ret, E-step with the same damped mean-field.
- Calibration split: n_cal = min(10 000, round(200 000 / T)) shots, drawn at random (numpy default_rng(2026).permutation). All other shots are test shots (reported in file order of the remaining indices). The calibration shots are never decoded.

## Decoders (all on the same matching graph: PyMatching from the shipped DEM)
PyMatching drops undecomposed 3- and 4-detector mechanisms, the same for all decoders, as in the earlier IBM protocol.
- **A**: plain MWPM.
- **X**: per-shot soft weights from the ALL posteriors with the detect2 rule: time-like edges of the checks adjacent to q get p ⊕ (1/2)·π_{q,t}; return edges p ⊕ (2/3)·π_ret; final-readout edges p ⊕ (1/2)·π_{q,R−1}. Entries with π < 0.02 are ignored.
- **A4 (static control)**: the same rule, but every shot gets the mean posterior over all test shots of the run (per qubit and round). Tests whether per-shot information is needed.
- **P (placebo)**: the same rule, but shot k gets the posteriors of test shot perm(k) (default_rng(0)). Same distribution, wrong shot.
- **X_old (secondary)**: the earlier per-detector IBM tracker (ibm_tracker.py) with its frozen parameters hmm_params_q36T50.json, smoothed (lag 'full'), c = 0.25, threshold 0.02, on the same test shots.

## Metrics
P_fail on test shots with Wilson 95 %; ε = ½(1 − (1 − 2P)^(1/T)); exact two-sided McNemar on discordant shots, per run and pooled; Holm correction across the 17 runs for per-run tests.

## Primary endpoint (pooled over all 17 runs)
**PR1**: X beats A (more shots where only X is right; p < 0.05), **and** X beats A4 (p < 0.05), **and** P is not significantly better than A (pooled p ≥ 0.05 or P worse).

**Kill**: if PR1 fails, report "the frozen label-free tracker gives no per-shot decoding gain on unseen IBM stability data".

## Secondary (reported, no claims beyond them)
1. Families: the T sweep (T = 5–100, α = 0), the α sweep at T = 20, and the α sweep at T = 100.
2. X vs X_old (pooled McNemar).
3. Label-free diagnostics per run: fitted per-qubit p_L and p_ret; log-likelihood per calibration shot at the fitted parameters minus the same with p_L = 1e-6 (evidence for data-qubit leakage); mean π.
4. Trend of the X − A difference with the detection fraction.

## Prediction (stated before the test)
- The synthetic checks show gain at a detection fraction ≈ 0.16 and slight harm at ≈ 0.24. Most IBM runs with α ≥ 0.6 have a detection fraction > 0.24.
- Earlier IBM memory analysis found a persistent hidden state that looked check-like (one detector stays "hot"). The ALL model has no ancilla/check-leakage state, so part of that signal may be absorbed by an inflated p_L.
- Expected outcome: X ≥ A on the T sweep at small T, no gain or harm in the high-α runs, PR1 probably not met. Estimated P(PR1 met) ≈ 0.25.
