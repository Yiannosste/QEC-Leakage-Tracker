# Results: the new leakage tracker on unseen IBM ibm_berlin stability data

*Project C3. Pre-registered protocol: ibm_stab_protocol.md (frozen before any logical outcome of these runs was read). Data: Lange et al., arXiv:2610.03869, Zenodo 23335425, d = 3 X-type stability experiment on IBM's Nighthawk r1 chip ibm_berlin. 17 runs, 50 000 to 100 000 shots each. None of these runs was used before in C3. Tracker settings come unchanged from the synthetic study detect2.*

## 1. Question
Does the label-free tracker ALL (both bases + explaining away + damped mean-field + Baum-Welch calibration on the run's own syndromes) improve decoding of real hardware data it has never seen? Is the gain per-shot information, rather than a static re-weighting?

## 2. Primary endpoint: MET
Pooled over all 17 runs (test shots only; the calibration shots are never decoded):

| comparison | only first right | only second right | exact p |
|---|---|---|---|
| X (tracker) vs A (plain MWPM) | 11 374 | 8 502 | 1.7 × 10⁻⁹² |
| X vs A4 (static average of the same posteriors) | 10 389 | 8 859 | 2.8 × 10⁻²⁸ |
| P (posteriors of the wrong shot) vs A | 3 346 | 4 959 | placebo is **worse** |

All three conditions of PR1 hold.

**Prediction check.** Before the test we predicted "PR1 probably not met" (P ≈ 0.25), with harm at high readout error. Both predictions were wrong.

## 3. What the result looks like

1. **The gain grows with run length.** At α = 0 the change in logical failure X vs A is −0.5 % (T = 5), −0.6 % (T = 10), −5.8 % (T = 20), −15 % (T = 50) and −20 % (T = 100). At T = 100: P_fail 0.0228 → 0.0182. In a stability experiment the number of rounds plays the role of the code distance, so long runs are where time-like error chains, and therefore persistent hidden states, matter most.
2. **Per-shot information is needed.** At α = 0 the static control A4 helps a little (−4.4 % at T = 5 down to −1.0 % at T = 100). The tracker beats A4 in the pooled test and in 11 of the 17 runs (one of them, T = 20 with α = 0.8, only by 2 shots to 0). It loses to A4 in 3 short or noisy runs (T = 5, T = 10, T = 20 with α = 0.6). In the other 3 runs (α = 1.0 at T = 20; α = 0.8 and 1.0 at T = 100) they are exactly equal. The wrong-shot placebo goes from −0.5 % (T = 5) to +12 % (T = 100), i.e. it makes long runs clearly worse. So the posteriors carry information about *that* shot.
3. **No harm at high readout error.** With a large pre-readout rotation (α ≥ 0.8) the label-free calibration fits almost no hidden state: mean p_L 0.7 to 5 × 10⁻⁴, return 0.2 to 0.5, evidence ≈ 0 nats/shot. Almost no posterior passes the 0.02 threshold, so X equals A (at most 2 shots differ per run). At α = 0.6 the gain is 0 (T = 20) and −6 % (T = 100). When the rotated readout buries the signal, the label-free fit returns near-zero leakage and the decoder falls back to MWPM. It is the same chip, so the hidden state is presumably still there; the tracker just cannot see it.
4. **Label-free evidence for a persistent hidden state, read next to its null.** The fitted model beats a no-leakage model by 1.0 to 8.2 nats per calibration shot (α = 0), more for longer runs. On its own that number proves little: the same fit on leak-free shots sampled from each run's shipped noise model still gains 0.5 to 5.0 nats (50 to 60 % of the real value; `ibmstab/null_evidence_summary.md`), and the gap does not track the decoding gain (at T = 100, α = 0.6 the evidence is below its null and the tracker still cuts failures by 6 %). What does differ is the fitted episode length: return probabilities of 0.013 to 0.033 per round at α = 0 (episodes of 30 to 77 rounds; 0.009 to 0.033, 30 to 110 rounds, over all 13 runs with α ≤ 0.6) against 0.27 to 0.51 (2 to 4 rounds) on the null shots. In every run with α ≤ 0.6 the two data qubits with the largest fitted p_L are the same (index 1 and 5 of the seven; 2 to 9 × 10⁻³ per round at α = 0), while on the null shots the top two change from run to run. But a leak-free, uniform-noise simulation of the same circuit also puts qubits 1 and 5 on top (3.3 and 3.7 × 10⁻³), so part of that repetition is circuit geometry, and a systematic error of the given model on those qubits would repeat across runs too. The evidence for per-shot information is X > A4 and P < A, not the repeated indices.
5. **The old IBM tracker (per-detector, frozen in the memory study) harms decoding here**: +13 % to +15 % at T = 5 to 10. Pooled, X_old loses to A (24 972 vs 32 003). The new tracker beats it by 33 401 vs 23 498.

## 4. Robustness check (exploratory, added after the test)
Baseline A drops the 3- and 4-detector mechanisms of the shipped DEM (a PyMatching limitation). This makes A weaker than it could be. We rebuilt the matching graph with these mechanisms split into edges (using the authors' circuit) and decoded again with the *same* posteriors:
- The stronger baseline A_dec is better than A (16 363 vs 15 877 discordant shots in its favour, pooled).
- The tracker on top of it still wins: **X_dec vs A_dec 10 116 vs 7 334, p = 8 × 10⁻⁹⁹**. At T = 100: 0.0223 → 0.0180 (−19 %).
So the gain does not come from compensating a weak baseline.

## 5. Full per-run table
See ibmstab_tables.md.

## 6. What the result does NOT show (limits)
- **It is not proven to be leakage.** The model calls the hidden state "data-qubit leakage", but it detects any long-lived state of a data qubit that randomises its neighbouring checks: leakage, a two-level-system defect, a frequency collision, etc. Episodes of 30 to 77 rounds (α = 0) are long for transmon leakage without reset. Only IQ readout data, which this dataset does not contain, could tell these apart.
- **Only the stability experiment.** The memory runs could not be used: their shipped DEM does not match a published circuit (the authors' memory template is not in the repository), and they were already used in earlier C3 work.
- **One chip, one patch, one day.** All 17 runs are from one d = 3 patch on ibm_berlin.
- **Baseline.** We compare with MWPM on the authors' calibrated DEM. We did not compare with the authors' neural decoder (GNN-RNN), which may already capture this effect.
- **Robustness check is post hoc** (§4), and the per-qubit pattern (§3.4) was noticed after the test.
- **Cost**: tracking plus calibration took about 15 min per T = 100 run on 12 CPU cores, i.e. offline, not real-time.

## 7. One-sentence conclusion
On 17 unseen IBM stability runs, the frozen label-free tracker found a persistent hidden state on two specific data qubits. Using it per shot lowered the logical failure by up to 20 % at T = 100. It beat both a static control and a stronger MWPM baseline, and it switched itself off where the data gave no evidence. This is the first positive real-hardware result of project C3.

## 8. Next steps
1. Test on a second chip, patch or day (new IBM data, or other public stability/memory data with a published circuit).
2. Ask the authors for the memory-circuit template (or IQ data) to test memory runs and to tell leakage from TLS-like defects.
3. Compare with the GNN-RNN decoder on the same test shots.
