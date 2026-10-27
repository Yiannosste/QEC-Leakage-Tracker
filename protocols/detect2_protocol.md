# Pre-registered protocol: better leakage detection by explaining away, joint checks, extra channels and calibrated priors

*Project C3, frozen 2026-10-25 before any test-seed shot was simulated. Development used only seed 9001 (5 000 and 20 000 shots, cell p = 2e-3 homogeneous). All data are SYNTHETIC (Stim + leakage_sim.py).*

## Question
Can a better syndrome-based leakage tracker separate leakage from ordinary Pauli noise well enough to recover more of the perfect-flag (oracle) decoding gain than the old trackers, in the noisy regime where they failed (p = 2e-3, 3e-3)?

## Trackers (all feed the same soft-weight MWPM rule p_e ← p_e ⊕ c·π, c = 1/2 time-like, 2/3 return, 1/2 final; π < 0.02 ignored)
- **old HMM**: archived LeakageHMM, lag 0, 2 mean-field passes, given the TRUE p_L (cell mean), τ, ρ (as in all earlier runs).
- **old CNN**: archived CNNTracker, lag 2, trained on 5×10⁴ shots / 6 epochs from the exactly matched simulator (labels).
- **A_h** (ideas 1+3+4): XATracker basis=both, explain=False, final-readout herald, calibrated per-qubit p_L.
- **B_h** (ideas 2+3+4): XATracker basis=z, explain=True, 2 mean-field passes, herald, calibrated per-qubit p_L.
- **ALL_h** (ideas 1+2+3+4): XATracker basis=both, explain=True, 2 mean-field passes, herald, calibrated per-qubit p_L.
- Syndrome-only versions **A, B, ALL** (no herald) for a fair comparison with the old trackers, which see no herald.
- Ablations: **ALL_true** (true parameters, no herald), **ALL_glob** (calibrated global p_L, no herald), **ALL_lag2** (posterior uses rounds ≤ t+2 only, no herald).

Calibration (idea 4) is label-free Baum–Welch, 8 iterations from p_L = 3e-3, p_ret = 0.25, on a separate 20 000-shot calibration sample of the same cell (different seed, no labels; herald included for _h trackers). ρ is fixed at 1/2 (physics: a leaked qubit gives a random outcome), not fitted. All posteriors use full smoothing except ALL_lag2.

Herald (idea 3): at the final data readout, P(h = 1 | leaked) = η = 0.8 and P(h = 1 | not leaked) = 0.01. The tracker is given η and the false-positive rate. These values are illustrative, not taken from a device.

## Cells (test)
d = 5, 25 rounds, SI1000 p ∈ {1e-3, 2e-3, 3e-3}, mean p_L = 1e-3, τ = 8, ρ = 1/2, in two versions:
- **hom**: the same p_L on every data qubit;
- **het**: per-qubit p_L = 1e-3·exp(0.8 z_q − 0.32), with z_q ~ N(0, 1) drawn once (seed 9500) and clipped to [1e-5, 0.02].

50 000 test shots per cell. Seeds: test 9100 + i, calibration 9200 + i, CNN training 9300 + i, herald 9400 + i (i = cell index 0–5).

## Metrics
- **Detection**, against true leakage labels: average precision (AP), AUC, recall and precision at 0.5, Brier score.
- **Decoding**: ε per round, f = (ε_A − ε_X)/(ε_A − ε_B) with a paired bootstrap (2 000 resamples, seed 42), and the change in logical error rate.
- Pairwise exact McNemar tests on identical shots.

## Primary endpoints (syndrome-only tracker ALL vs the old trackers, cells p = 2e-3 and 3e-3, hom and het: 4 cells)
- **P1 (detection)**: AP(ALL) > AP(old HMM) and AP(ALL) > AP(old CNN) in all 4 cells.
- **P2 (decoding)**: pooled over the 4 cells, ALL beats old CNN in a McNemar test (more shots where only ALL is right than shots where only CNN is right, two-sided p < 0.05). ALL must also beat the old HMM the same way.
- **Kill**: if P2 fails against the old CNN, report "better detection, no better decoding than the learned CNN". The comparison with the old HMM and the label-free advantage are still reported.

## Secondary (reported, no claims beyond them)
- Herald gain (ALL_h vs ALL), idea-1 gain (ALL vs B), idea-2 gain (ALL vs A).
- Calibration cost (ALL vs ALL_true), per-qubit prior gain on het cells (ALL vs ALL_glob), online cost (ALL_lag2).
- All of the above also at p = 1e-3.

---
## Amendment 1 (2026-10-25), from development seed 9001 only, BEFORE any test seed was simulated

What development showed (all numbers on the development cell p = 2e-3 homogeneous, 20 000 shots):
1. Two tracker names collided with the plain decoder A and the oracle B. The trackers are renamed **J / J_h** (ideas 1(+3)+4, no explaining away) and **XZ / XZ_h** (ideas 2(+3)+4, Z-type checks only).
2. **Exact noise model.** The tracker now reads the undecomposed DEM. A Y error stays one event that fires X- and Z-checks together; the decomposed DEM split it into two independent events, which mimics the cross-basis leakage fingerprint.
3. **Mean-field between data qubits.** 84 % of the false alarms were neighbours of a truly leaked qubit. Damped Jacobi mean-field fixes this. It was chosen by development AP from the grid {5, 8} passes × {0.5, 0.7} damping: **8 passes, damping 0.5**. AP rose from 0.705 (2 undamped passes) to 0.887; precision from 0.53 to 0.90.
4. **Calibration.** The EM E-step now uses the same damped mean-field. EM runs **12 iterations** (it was still converging at 8) on an **8 000-shot** calibration sample.
   - One EM is run per tracker type (basis, explain), without the herald. The herald variants (_h) reuse those parameters, and ALL_glob uses the mean of the per-qubit fitted p_L.
   - Effect: fitted p_L went from 7.1e-3 (first version) to 1.27e-3 (true 1.0e-3); p_ret from 0.33 to 0.16 (true 0.125).
5. **Test scope**, cut to fit the compute budget: 40 000 test shots per cell. ALL_glob runs only in het cells; ALL_true and ALL_lag2 only in the 4 primary cells.

Development outcome, stated before the test (prediction):
- New tracker ALL, true parameters: AP 0.877 vs 0.75 for the CNN; f = 0.452 vs 0.455; McNemar vs CNN 233 / 234.
- Self-calibrated: AP 0.874, f = 0.415.
- **Expected test result:** P1 (detection) met; P2 (decoding beats the CNN) probably not met, i.e. a tie; ALL beats the old HMM.

Primary endpoints, kill rule and seeds are unchanged.
