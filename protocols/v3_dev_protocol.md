# Tracker v3: development rules (written 25 Oct 2026, before any v3 result)

**Why.** The frozen tracker v2 (ALL) invents leakage on leak-free simulated data and makes decoding worse (miami_precheck.md): +20 % failures on a reset d = 5 memory (0.0174 → 0.0208), and +15 % to +89 % on ibm_miami's no-reset circuits (d = 3 exact model 0.031 → 0.044; with 1.7× noise 0.089 → 0.168, or 0.089 → 0.110 after rescaling; d = 5 with 1.5× noise 0.365 → 0.418).
**Data.** v3 is developed on SIMULATED data only. No ibm_miami outcome is read until v3 is frozen. ibm_berlin outcomes are known, so ibm_berlin is never used to choose anything.

## Development scenarios (synthetic, development seeds 7000+)
| id | circuit | background noise | injected hidden state | role |
|---|---|---|---|---|
| N1 | reset d=3 memory (Stim rotated, SI1000 p = 2e-3, 25 rounds) | exact | none | null |
| L1 | same | exact | data-qubit leakage, p_L = 1e-3 on every qubit, τ = 8 | leakage |
| H1 | same | exact | 2 "hot" data qubits, p_L = 3e-3, τ = 40 (ibm_berlin-like) | long episodes |
| N2 | ibm_miami d=3 memory (fig10, placement 5, Z, depth 16), authors' noise model | exact | none | null, no reset |
| L2 | same | exact | p_L = 1e-3, τ = 8 | leakage, no reset |
| N3 | same | real = 1.7 × model, model rescaled label-free | none | null with mismatch |
| H3 | same | real = 1.7 × model, model rescaled label-free | 2 hot qubits, p_L = 3e-3, τ = 40 | hidden state with mismatch |

## Candidate changes
- **G0**: none (v2 as frozen).
- **G1**: during calibration, cap the return probability at p_ret ≤ 0.25, i.e. episodes of at least 4 rounds. Physical prior: the hidden states this method targets last several rounds.
- **G2**: switch-off test. After calibration, compare the log-likelihood on a held-out half of the calibration shots with the fitted parameters and with p_L = 0. Keep a data qubit only if its own gain is larger than the 99th percentile of the same gain on data simulated from the background model without leakage (label-free, per circuit).
- **G1 + G2** together.
- **R** (no-reset circuits only): explain away readout errors that fire the same check two rounds apart. Use the probability of a readout flip at round t − 2 (from the forward pass) in the background distribution at round t.

## Selection rule (fixed now)
1. **No harm in null scenarios.** In N1, N2 and N3, X must not be worse than A: a McNemar test of A vs X must not favour A at p < 0.05.
2. **Among the variants that pass 1**, choose the one with the largest summed decoding gain (A-only-right minus X-only-right, as a fraction of A's failures) over L1, H1, L2 and H3.
3. **Ties** (within 2 % of summed gain): prefer the simpler variant (fewer changes).
4. **Confirmation.** Re-run all seven scenarios with NEW seeds (8000+) for the chosen variant. If rule 1 fails there, report it and do not use v3 on hardware.
5. Freeze v3 (code + this file + the results table), then write the ibm_miami protocol before reading any outcome.

## Amendment 1 (written after the first dev results for N1, L1, H1, N2; before any G2b result)
- **Observation.** On leak-free data simulated from the exact model, the fitted leakage model still gains 0.1–0.5 nats per shot per qubit. So the tracker's internal background approximation is itself imperfect, and the size of this gain differs strongly between qubits. G2's single threshold (largest leak-free gain over all qubits) therefore misses real hot qubits (H1: the two true hot qubits gain 1300 and 1327 vs a threshold of 1855).
- **New candidate G2b.** For each data qubit i, compare its per-shot held-out gain on the real calibration half with the same qubit's per-shot gain on leak-free data simulated from the model: z_i = (mean_real,i − mean_null,i) / sqrt(var_real,i/n + var_null,i/n). Keep qubit i only if z_i > 3.
- G2b enters the same selection rule. G1 and G1 + G2 are dropped (G1 failed rule 1 on N1).
- Oracle check (true flags) for scale: H1 0.066 → 0.061; L1 0.085 → 0.064.
