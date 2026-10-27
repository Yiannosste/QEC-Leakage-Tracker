# Pilot pre-registration (written BEFORE any pilot is run)

Common rules for every pilot
- Data: Stim-simulated (SYNTHETIC) unless the pilot says it uses the REAL Google d3 data (Zenodo 13273331, patch d3_at_q6_7, tarball artifact google_d3_at_q6_7.tar.gz). Label every number by its source.
- Decoder: PyMatching 2.4 (MWPM) unless stated. Stim 1.16. Seeds fixed and printed. Compute cap: about 1.5 CPU-hours, at most 2 worker processes (16 cores are shared by 9 pilots).
- Uncertainty: Wilson 95% intervals for error rates; standard error over seeds for tracking metrics. Report 'signal' only if the pre-registered success criterion is met with the interval excluding the null.
- No tuning until it works: hyperparameters are fixed below; one pre-declared sweep each. If a criterion is not met, the verdict is 'no signal' or 'inconclusive' (if compute/implementation ran out), never 'needs more tuning'.
- Verdict vocabulary: SIGNAL / NO SIGNAL / INCONCLUSIVE.

## P1 - C1 Jump-aware tracking of DEM edge probabilities (Kalman / IMM vs sliding window)
Setup: Stim rotated surface code memory_z, d=3 (and d=5 if time), 25 rounds, SI1000-like p=3e-3. Use drift_sim.py: edges from the DEM; sample 400 batches of 500 shots; ONE data-qubit-related set of pair edges (all pair edges touching one chosen data qubit) driven by a two-state telegraph process (factor 1x -> 5x, mean dwell 40 batches, seed-fixed); other edges static. Per batch: Spitz estimate of all pair edges. Trackers: (a) static nominal DEM, (b) sliding window W in {5, 20, 80}, (c) per-edge scalar Kalman with q in {1e-7, 1e-6, 1e-5} and R from the Spitz variance formula, (d) two-model IMM (quiet q_small / jump q_large), (e) oracle (true p(t)). Decode each batch with each tracked DEM.
Metrics: RMSE of p_hat on the driven edges; mean logical error over batches; detection lag after each jump.
SUCCESS (signal): the best jump-aware tracker (IMM or Kalman) attains lower RMSE than the best fixed window AND its logical error lies closer to the oracle than the best window's by at least 3 standard errors across 5 seeds. Also required: oracle < static, else the drift is too weak to matter (then INCONCLUSIVE).
KILL (no signal): no tracker is closer to the oracle than the best window within error bars.

## P2 - C2 Calibrated change-point detection and localisation from syndrome streams (+ REAL d3 data check)
Setup A (synthetic): d=3, 25 rounds, SI1000-like p=2e-3, 100 batches of 500 shots; at batch 50 one data qubit's error mechanisms are multiplied by factor F in {2, 3, 5, 10}; 20 seeds each. Detector: two-sided CUSUM on each detector's event rate, threshold h calibrated on 20 stationary runs to <=1 false alarm / 100 batches. Metrics: detection delay (batches), localisation accuracy (alarming detectors adjacent to the perturbed qubit).
Setup B (REAL): the 50k-shot d3 files (X and Z, all round counts): per-shot detection counts in blocks of 1000 shots; run the same CUSUM and Bayesian online change-point detection; report number and position of change points; compare with the stationarity statistic (variance ratio) already measured.
SUCCESS: in A, median delay < 10 batches for F >= 3 with correct localisation in >= 80% of seeds; in B, at least one change point detected at a false-alarm level calibrated on shuffled data (<= 1 per file).
KILL: F = 5 is not detected within 50 batches in most seeds, or real-data alarms are not above the shuffled-data false-alarm rate.

## P3 - C3 Imperfect-erasure requirement map for leakage-like episodes
Setup: d=3 and d=5, 25 rounds, uniform circuit noise p=1e-3, plus heralded erasure-like episodes on data qubits via HERALDED_ERASE with rate p_e in {2e-3, 5e-3} per round per data qubit (oracle flags from the herald detectors). Decoders (PyMatching): (A) ignore flags; (B) perfect flags: per shot, set weights of edges touching an erased qubit-round to ~0 (group shots by flag pattern or rebuild per shot); (C) corrupted flags: recall r in {1, 0.8, 0.5}, precision q in {1, 0.8, 0.5}, delay D in {0, 1, 3} rounds; 2e4 shots per setting.
Metrics: logical error vs (r, q, D).
SUCCESS: (B) beats (A) by > 20% relative at both p_e (intervals disjoint) AND a clear 'cliff' exists (some corrupted setting is worse than ignoring flags) - i.e. the map is informative.
KILL: perfect flags give < 10% gain (then leakage-like erasures at this rate do not matter for matching, project premise fails at this scale).

## P4 - C4 Controller comparison on the sign-blind detection-rate plant
Setup (pure Python, no Stim): plant p_det(u,t) = p0 + k (u - u*(t))^2, p0=0.01, k=1; observation Binomial(N=2000, p_det) per epoch; u*(t) = A sin(2 pi f t), A=0.1, f in {1/1000, 1/300, 1/100, 1/30, 1/10} epochs^-1, 3000 epochs, 5 seeds. Controllers at equal shots per epoch: (i) Gaussian-policy Monte-Carlo gradient (population 8, as in Sivak et al. 2025/2026), (ii) extremum-seeking (dither a=0.02, high-pass + integrator, gain fixed), (iii) finite-difference gradient + PI, (iv) EKF tracking the vertex. Then one Stim check (d=3 repetition code, 15 min): map u to a CZ-related Pauli rate and confirm detection fraction is quadratic in u.
Metrics: suppression of output fluctuation power (dB) vs f; mean excess error <p_det - p0>.
SUCCESS: at least one classical controller matches or beats the MC-gradient agent in excess error at equal shot budget for f <= 1/100 with a > 2 sigma difference over seeds, and the corner frequencies differ measurably.
KILL: all controllers are indistinguishable within 2 sigma at all f.

## P5 - C5 Optimiser vs objective for decoder-prior fitting (sample cost)
Setup: d=3, 5 rounds, SI1000-like p=3e-3; planted mismatch: one CZ depolarising rate x3, one ancilla measurement error x2. Decoder prior = nominal DEM re-weighted by 8 mechanism-class scale factors. Fixed offline dataset of 2e5 labelled shots. Optimisers on the LER objective: CMA-ES (pop 10), Gaussian-policy MC gradient (pop 10), Nelder-Mead; 3 seeds each; log LER vs cumulative shots evaluated. Also: Spitz pairwise-moment DEM (closed form, no optimisation) and the true planted DEM (oracle).
Metrics: shots to reach within 10% of the oracle LER; final LER.
SUCCESS: the closed-form Spitz estimate reaches within 10% of the oracle LER and the optimisers differ in shots-to-converge by > 3x; OR an optimiser beats Spitz by > 10% relative (shows the LER objective carries information beyond moments).
KILL: all methods, including the nominal prior, are within error bars of the oracle (planted mismatch too weak to matter at d=3) -> INCONCLUSIVE; or no optimiser converges within the budget.

## P6 - C6 Decoder latency as a closed loop (state-dependent service time)
Setup: d=5, 25 rounds, p in {1e-3, 2e-3, 3e-3, 5e-3}; time PyMatching per shot (2e4 shots per p) and fit service time S = a + b N (N = detection events). Mean-field loop: window of d rounds, T_window = d x 1 us x speed factor s so utilisation rho_0 ranges 0.3..1.2; iterate W -> extra idle depolarising eps = W/T1 (T1=100 us) on data qubits -> new N -> new S, until fixed point or divergence. Then a stochastic Lindley-recursion simulation at 3 values of rho_0.
Metrics: slope b with standard error; fixed-point waiting time and effective logical error vs rho_0; predicted vs observed stability boundary.
SUCCESS: b > 0 at > 3 sigma AND the closed-loop stability boundary differs from the open-loop rho_0 = 1 by a measurable amount (> 5%) that the mean-field formula predicts within error bars.
KILL: b is consistent with 0 (service time does not depend on syndrome density for PyMatching at this size) -> loop gain is zero, premise fails.

## P7 - C7 Decoder confidence calibration under drift and re-calibration budget
Setup: d=5, 11 rounds, prior DEM from uniform circuit noise p0=2e-3. True noise: p_true/p0 in {1, 1.5, 2, 3} and one 'bad qubit' case (one data qubit at 5 p0). MWPM complementary gap per shot (decode with the observable as an extra detector forced 0 and 1). 1e5 shots per setting.
Metrics: logical error; reliability curve P(error | gap) and fitted slope alpha; expected calibration error (ECE); post-selected logical error at 50% acceptance using (i) raw gap, (ii) temperature-rescaled gap fitted on n_cal in {1e2, 1e3, 1e4} labelled shots, (iii) gap from a Spitz-re-estimated DEM with the same n_cal shots.
SUCCESS: ECE increases monotonically with mismatch (> 3 sigma between p_true/p0 = 1 and 3) AND temperature rescaling with n_cal = 1e3 recovers >= 50% of the post-selection loss.
KILL: ECE does not change with mismatch within error bars (the gap is already robust) -> no signal.

## P8 - C8 IQM star-architecture [[4,2,2]]: resonator hook errors as a silent correlated channel
Setup: Stim circuit of the [[4,2,2]] star experiment (arXiv 2503.12869, Appendix I) with the resonator as a 7th qubit, MOVE = SWAP, noise from the paper's quoted numbers (CZ error ~1%, 1q ~0.1%, readout ~1-2%, idling from T1 ~30-40 us). 1e6 shots, N = 1..10 cycles. Then add X_ERROR(p_res) on the resonator after each MOVE, p_res in {0, 0.25, 0.5, 1, 2}%.
Metrics: survival fraction per cycle and logical error per cycle vs published values; rejection rate and undetected logical error vs p_res; Spitz-type estimability of p_res from detector statistics (pairwise moments) under a drifting p_res(t).
SUCCESS: baseline within a factor 1.5 of the published survival (~0.67 per cycle, from the paper; 'not verified' until read) AND the hook channel raises undetected logical error by > 2x at p_res = 1% while changing rejection by < 20% relative (i.e. it is 'silent') AND p_res is recoverable from syndrome moments within 30%.
KILL: the hook channel is not silent (rejection rises as fast as logical error) - then it is just ordinary noise and the candidate collapses to a reproduction.

## P9 - C9 Layered Nishimori mismatch with an exact ML decoder
Setup: repetition code d in {5, 7, 9}, phenomenological noise, T = 20 rounds + perfect final round; data bit-flip rate p_d(t) time-varying (step: doubles at T/2; square wave period 4; sinusoid), same time average p_bar in {0.03, 0.05, 0.08}; measurement error p_m = p_bar. Exact ML decoder by transfer matrix over the 2^d cumulative data-error states (numpy). Decoders: ML-oracle (true p_d(t)), ML-averaged (single p_bar), ML-windowed (W in {2, 5}), MWPM with p_bar. 2e4 shots per setting, 3 seeds.
Metrics: logical error of each decoder; mismatch cost = LER(averaged) / LER(oracle) - 1.
SUCCESS: mismatch cost > 10% with disjoint intervals for at least one profile and grows with the drift amplitude; the windowed decoder interpolates between the two.
KILL: averaged and oracle are within error bars for all profiles (time-averaging is harmless at these sizes) -> no signal.
