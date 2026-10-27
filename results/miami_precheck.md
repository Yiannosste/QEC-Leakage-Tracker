# ibm_miami replication: pre-test checks (25 Oct 2026). No logical outcome of ibm_miami has been read.

## 1. What the dataset contains (Zenodo 21336494, arXiv:2607.12118)
The repo's folder numbers differ from the paper's figure numbers (repo fig8 = paper Fig. 10, repo fig10 = paper Fig. 8).

| repo folder | experiment | circuits × shots | usable? |
|---|---|---|---|
| fig3, fig8 "defects ignored" | stability (16 data, 17 ancillas), depth 2 to 12 / 2 to 40 | 6 + 9 × 4 096 | **no**: published MWPM failure 0.45 to 0.49 at every depth (random; the paper's point that the defect must be excluded) |
| fig3, fig8 "defects removed" | stability with merged checks around the defect | 6 + 9 × 4 096 | partly: some checks are measured only every second round, which the tracker handles only approximately |
| fig10 | d = 3 memory, 3 placements × Z/X, depth 2 to 32 | 30 × 2 048 | yes (published failure 0.06 → 0.26 to 0.38) |
| fig7 | d = 5 memory, 3 strategies × 4 states, depth 2 to 32 | 60 × 4 096 | yes |
| fig4 | d = 5/3 memory with raw IQ data | 50 circuits | mechanism test (leakage labels from 3-state IQ classification) |

Circuits: no-reset syndrome extraction (ancillas never reset, noiseless reference readouts at the start), one M instruction per qubit, noise model from the day's calibration.

## 2. Adapter (gen_leaky2.py)
New adapter for no-reset circuits: rounds from measurement moments, detector rounds from their measurement records, ancilla-state-flip markers ("m"), data markers, final-readout markers, and a one-marker-at-a-time fallback for degenerate markers. Structural checks pass on fig3, fig7, fig8 and fig10: adjacency matches the code, and 90 to 95 % of "m" markers fire consecutive rounds (the rest are first or last rounds; in the "defects removed" circuits the merged checks fire two rounds apart).

## 3. Label-free look at the real shots (detection events only)
- Real detection fractions are **1.5 to 1.7× higher** than the authors' calibration model predicts (d = 3 memory: 0.08 to 0.14 vs 0.05 to 0.07; d = 5: 0.13 to 0.21 vs 0.09 to 0.13).
- Real detection fractions **rise with depth** (e.g. d = 3, placement 5: 0.084 → 0.107 from depth 2 to 32), while the model's stay flat. This matches the hidden-state fingerprint seen on ibm_berlin.

## 4. Synthetic checks of the frozen tracker on these circuits (the decisive part)
"A" = MWPM with the circuit's noise model; "X" = tracker. Counts are shots where only X / only A is right.

| circuit | real noise / model | injected leakage | fitted p_L (mean, max) | p_ret | A → X | X-only / A-only |
|---|---|---|---|---|---|---|
| d=3 memory, depth 16 | 1.0 | 1e-3, τ=8 |, |, | f = +0.32 | 226 / 185 |
| d=3 memory, depth 16 | 1.0 | **none** | 1.2e-3, 3.5e-3 | 0.42 | 0.031 → 0.044 | 77 / 225 |
| d=3 memory, depth 16 | 1.7 | 1e-3 | 8.4e-3, 2.6e-2 | 0.30 | 0.105 → 0.166 | 510 / 1240 |
| d=3 memory, depth 16 | 1.7 | none | 7.4e-3, 2.6e-2 | 0.40 | 0.089 → 0.168 | 359 / 1299 |
| same, model rescaled label-free (fitted s = 1.69) | 1.7 | none | 1.6e-3, 5.6e-3 | 0.32 | 0.089 → 0.110 | 174 / 417 |
| d=5 memory, depth 16 | 1.0 | 1e-3 | 1.4e-3, 4.7e-3 | 0.15 | f = −0.28 | 232 / 253 |
| d=5 memory, depth 16 | 1.5 | none | 1.1e-2, 6.7e-2 | 0.37 | 0.365 → 0.418 | 864 / 1178 |
| stability "defects removed", depth 12 | 1.0 | 1e-3 | 2.8e-3, 1.1e-2 | 0.22 | f = −0.15 | 74 / 85 |
| **reset** d=5 memory (detect2 setting, p = 2e-3) | 1.0 | **none** | 1.1e-3, 1.7e-3 | **0.98** | 0.0174 → 0.0208 | 47 / 81 |

## 5. What this means
1. **The frozen tracker invents leakage when there is none**, and this harms decoding. It happens on reset circuits too (last row): calibration fits p_L ≈ 1e-3 with one-round "episodes" (p_ret ≈ 1) that soak up ordinary noise. On no-reset circuits it is worse, probably because a readout error there fires the same check two rounds apart, which the model cannot explain away.
2. **A noise model that is too weak makes it much worse**, and a single label-free rescaling does not remove the problem.
3. On ibm_berlin the fitted episodes were long (p_ret 0.01 to 0.03), and the gain survived the static control and the placebo, so that result is not explained by this failure mode. But the paper must report it, and the method needs a guard.
4. **Running the frozen tracker on ibm_miami now would predictably harm decoding**, for reasons we already understand. That test would not be informative, so it was not run.

## 6. Proposed next step (development on synthetic data only, then freeze)
Tracker v3:
- (a) A guard against false leakage, e.g. a minimum episode length (cap p_ret during calibration) or a likelihood-ratio test against the no-leakage model that switches the tracker off. Tuned only on synthetic zero-leakage and leakage cases, for reset and no-reset circuits.
- (b) For no-reset circuits, explaining away of readout errors that fire two rounds apart.

Then freeze v3, re-run the zero-leakage controls on new seeds, and pre-register the ibm_miami test (d = 3 and d = 5 memory primary). v3 on ibm_berlin is reported only as secondary, because those outcomes have been seen.
