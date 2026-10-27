# Results: better leakage detection (ideas 1 to 4 combined), held-out simulation test

*Project C3. Protocol: detect2_protocol.md v2 (frozen before any test shot, with Amendment 1). All data are SYNTHETIC (Stim + leakage_sim.py). d = 5 rotated surface code, 25 rounds, SI1000 noise, data-qubit leakage with mean p_L = 1e-3 per round, lifetime τ = 8 rounds (true return probability 0.125). 40 000 test shots per cell, test seeds 9100 + i, never used during development.*

## 1. Question (one line)
Can we tell "a data qubit is leaked" apart from "ordinary Pauli noise happened" better than our old trackers, and does better detection give better decoding?

## 2. Trackers compared
All trackers give a probability π that each data qubit is leaked in each round. The decoder uses π the same way for every tracker (soft MWPM weights, p_e ← p_e ⊕ c·π).

| name | what it uses | idea(s) |
|---|---|---|
| old HMM | archived tracker, sees each check's detection events as independent, lag 0, given the TRUE p_L |, |
| old CNN | small 3D CNN, trained with true leakage labels from the exact simulator, lag 2 |, |
| J | all neighbouring checks, both X and Z, no explaining away | 1 + 4 |
| XZ | explaining away, Z checks only | 2 + 4 |
| **ALL** | both bases + explaining away + damped mean-field between neighbours | 1 + 2 + 4 |
| _h suffix | same, plus the final-readout herald (η = 0.8, false rate 0.01) | + 3 |
| ALL_true | ALL with the true parameters instead of learned ones | ablation |
| ALL_glob | ALL with one global p_L instead of per-qubit p_L (het cells) | ablation |
| ALL_lag2 | ALL using only rounds ≤ t + 2 (online, same lag as the CNN) | ablation |

"Explaining away" (idea 2) means that the hidden state also includes the measurement-error bit of each neighbouring check. A detection pair caused by one measurement error (two flips in time on the same check) is then explained by that bit and not by leakage. Idea 4 (priors) means that p_L per qubit and the return probability are learned from unlabelled syndrome data by Baum to Welch (EM).

## 3. Primary endpoints (pre-registered; 4 cells: p = 2e-3, 3e-3 × hom, het)

**P1 (detection): MET.** The average precision (AP) of ALL is higher than both old trackers in all 4 cells.

| cell | AP ALL | AP old CNN | AP old HMM |
|---|---|---|---|
| p = 2e-3 hom | 0.877 | 0.752 | 0.431 |
| p = 3e-3 hom | 0.818 | 0.647 | 0.392 |
| p = 2e-3 het | 0.880 | 0.763 | 0.427 |
| p = 3e-3 het | 0.826 | 0.683 | 0.396 |

**P2 (decoding): MET.** Pooled McNemar over the 4 cells (shots where only one of the two decoders is right):
- ALL vs old CNN: **2840 vs 2551, p = 8.7 × 10⁻⁵**.
- ALL vs old HMM: 3919 vs 2939, p = 2.4 × 10⁻³².

**Prediction check.** Before the test we predicted "P1 met, P2 probably a tie". P1 came out as predicted. P2 did not: the new tracker won.

## 4. Where the decoding win comes from (read this before quoting P2)

1. **It comes from the high-noise cells only.** At p = 2e-3 ALL and the CNN tie: 462/477 (p = 0.65) hom and 498/501 (p = 0.95) het. At p = 3e-3 ALL wins: 930/760 (p = 4 × 10⁻⁵) hom and 950/813 (p = 0.001) het. f is 0.41 for ALL vs 0.22 to 0.27 for the CNN. The CNN's detection drops faster with noise than the new tracker's (Fig. a).
2. **Part of the win comes from seeing the future.** ALL uses the whole 25-round record (offline smoothing); the CNN waits only 2 rounds. With the same 2-round lag, **ALL_lag2 ties the CNN: 2621 vs 2661, p = 0.59** (pooled over the 4 cells). So for a real-time decoder with a short lag, the fair statement is "as good as the CNN, without any labels". The CNN was never tested with full smoothing, so we cannot say whether a full-smoothing CNN would also improve.
3. **No labels needed.** The CNN needs true leakage labels from a simulator that matches the device exactly. ALL learns its parameters from unlabelled syndromes. This is the real practical advantage, because on hardware no exact simulator and no labels exist.

## 5. What each idea adds (secondary; pooled McNemar over the 4 primary cells)

| step | Δf (mean over 4 cells) | McNemar (new-only right / old-only right) |
|---|---|---|
| + explaining away (ALL vs J) | ≈ +1.0 | 7230 / 3769, p ≈ 10⁻²⁴² |
| + X-type checks (ALL vs XZ) | ≈ +0.23 | 3127 / 2290, p = 5 × 10⁻³⁰ |
| + herald (ALL_h vs ALL) | ≈ +0.06 | 648 / 430, p = 3 × 10⁻¹¹ |
| learned vs true parameters (ALL vs ALL_true) | ≈ −0.03 | 648 / 763, p = 0.002 (small cost) |
| per-qubit vs global p_L (ALL vs ALL_glob, 2 het cells) | ≈ 0 | 812 / 805, p = 0.88 (no gain) |
| online lag 2 vs full smoothing (ALL_lag2 vs ALL) | ≈ −0.09 | see §4 |

Plain reading:
- **Explaining away (idea 2) is the key idea.** Without it (J, J_h) the tracker reads measurement errors as leakage. It learns p_L ≈ 1.0 to 1.25 × 10⁻² (10× too high) and return ≈ 0.32 to 0.37, and then it *harms* decoding: f from −0.22 to −0.74 in every cell. Adding the X checks without explaining away only adds more false alarms.
- **Both bases (idea 1) help only together with explaining away.** A leaked data qubit randomises both its X and Z neighbours; one Pauli error mostly fires one type. This difference only helps once measurement errors are explained away.
- **Herald (idea 3) gives a small but clear extra gain.** It acts only at the final readout, so it mostly helps the last rounds. Its values (η = 0.8, false rate 0.01) are illustrative, not measured on a device.
- **Per-qubit priors (idea 4) give nothing measurable** for this spread of p_L (log-normal, σ = 0.8). Learned parameters are close to the truth: p_L 1.1 to 1.4 × 10⁻³ (true 1.0 × 10⁻³) and return 0.15 to 0.18 (true 0.125). The leftover bias costs about 0.03 in f.

## 6. Secondary cells p = 1e-3 (not primary)
ALL ties the CNN on decoding (hom 159/160, het 156/175 p = 0.32) and has higher AP (0.926 to 0.930 vs 0.847 to 0.861). At low noise the CNN is already near its ceiling.

## 7. Full tables
See det2_tables.md (AP and f with 95 % CI for every tracker and cell; P_fail of the no-flag decoder A and the perfect-flag oracle; all pooled McNemar tests).

## 8. Limits (honest list)
- **Simulation only.** The leakage model is phenomenological (ρ = 1/2 randomisation, random Pauli on return). Real leakage (IBM, Google) also has leaked ancillas, transport of leakage and drift. Earlier, every hardware test of our trackers was null.
- **Offline vs online** (§4.2): the decoding win needs the full record.
- **CNN budget**: 5 × 10⁴ training shots and 6 epochs, fixed by the archived design. A larger CNN or more data could close the gap at p = 3e-3. We did not tune it, to keep the pre-registered comparison.
- **Herald values are assumed**, not measured.
- **Cost**: ALL takes about 450 s per 40 000 shots on 12 CPU cores (Python/NumPy); not real-time.
- Development tuning (DEM exactness, damping, EM iterations) used one development seed (9001, p = 2e-3 hom) only. The p = 3e-3 and het cells, where the win appears, were never seen during development.

## 9. One-sentence conclusion
Combining all four ideas, with explaining away as the key one, gives a label-free leakage tracker that detects leakage much better than our old HMM and CNN (AP 0.82 to 0.88 vs 0.65 to 0.76 for the CNN and 0.39 to 0.43 for the old HMM, in the 4 primary cells) and decodes better than the CNN at p = 3e-3 when it may use the whole record; with the CNN's 2-round lag it only ties the CNN, but it needs no labels.

## 10. Next step
Apply ALL (frozen settings, EM on the device's own syndromes) to unseen IBM ibm_berlin runs with a new frozen protocol. This is the first time the tracker does not need a matched simulator, so a hardware test is now meaningful.
