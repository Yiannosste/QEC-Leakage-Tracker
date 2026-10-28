# Null check for the label-free evidence (C7)

Method: for each run, leak-free shots were sampled from the run's own shipped noise model (the p_ij DEM, Stim sampler, seed 1000+seed), same number of calibration shots as the real protocol (min(10 000, 200 000/T)), then the frozen 12-iteration Baum-Welch calibration was run on them exactly as on the real shots. 'Evidence' = log-likelihood of the calibration shots under the fitted model minus under the no-leakage model, in nats per shot. Script: code/ibm_stability/null_evidence.py; raw JSON in results/data/ibmstab/<run>/null_evidence_seed<s>.json.

| run | seed | null evidence | real evidence | null per round | real per round | null p_ret | real p_ret | null det. frac. | real det. frac. |
|---|---|---|---|---|---|---|---|---|---|
| T5 | 1 | 0.51 | 0.97 | 0.101 | 0.193 | 0.478 | 0.017 | 0.175 | 0.143 |
| T10 | 1 | 0.97 | 1.75 | 0.097 | 0.175 | 0.509 | 0.013 | 0.199 | 0.148 |
| T20 | 1 | 1.67 | 3.14 | 0.084 | 0.157 | 0.453 | 0.025 | 0.231 | 0.161 |
| T50 | 1 | 3.17 | 5.93 | 0.063 | 0.119 | 0.407 | 0.030 | 0.282 | 0.187 |
| T100 | 1 | 5.01 | 8.16 | 0.050 | 0.082 | 0.372 | 0.033 | 0.318 | 0.212 |
| T20_alpha0.6 | 1 | 0.81 | 1.37 | 0.041 | 0.068 | 0.418 | 0.009 | 0.295 | 0.241 |
| T100_alpha0.6 | 1 | 2.85 | 2.55 | 0.028 | 0.026 | 0.353 | 0.023 | 0.365 | 0.279 |
| T100_alpha1.0 | 1 | 0.50 | -0.06 | 0.005 | -0.001 | 0.267 | 0.479 | 0.459 | 0.389 |
| T20 | 2 | 1.60 | 3.14 | 0.080 | 0.157 | 0.467 | 0.025 | 0.230 | 0.161 |
| T100 | 2 | 4.85 | 8.16 | 0.048 | 0.082 | 0.369 | 0.033 | 0.317 | 0.212 |
| T20 | 3 | 1.61 | 3.14 | 0.080 | 0.157 | 0.471 | 0.025 | 0.231 | 0.161 |
| T100 | 3 | 4.79 | 8.16 | 0.048 | 0.082 | 0.373 | 0.033 | 0.317 | 0.212 |

## Reading

1. The null is not near zero. On leak-free data the fitted two-state model still gains 0.5 to 5.0 nats per shot (T = 5 to 100, alpha = 0), which is 50 to 60 % of the real value. The raw evidence number is therefore not proof of leakage; only the comparison with the null means something. Three seeds agree within 0.1 nats at T = 20 (1.60 to 1.67) and within 0.25 nats at T = 100 (4.79 to 5.01).
2. The real minus null gap at alpha = 0 is +0.46, +0.77, +1.47, +2.77, +3.14 nats per shot (T = 5, 10, 20, 50, 100). At T = 20 alpha = 0.6 it is +0.56. At T = 100 alpha = 0.6 it is -0.29 and at T = 100 alpha = 1.0 it is -0.57 (real below null). The gap does not track the decoding gain: at T = 100, alpha = 0.6 the evidence is below its null and the tracker still cuts failures by 6.4 % [4.1, 8.5] and beats A4; at T = 20, alpha = 0.6 it is above its null and the tracker gains nothing. A per-run likelihood-versus-null switch (G2 type) would have turned the tracker off in a run where it helped. The evidence for per-shot information stays X > A4 and P < A.
3. The clearest label-free difference is the fitted episode length. On null data the fit returns p_ret = 0.27 to 0.51 (episodes of 2 to 4 rounds: the extra state only absorbs short correlations the approximate background model misses). On real alpha <= 0.6 data it returns 0.009 to 0.033 (30 to 110 rounds). On real T = 100 alpha = 1.0 it returns 0.48, i.e. null-like, and there the tracker changed nothing (X = A).
4. Caveat. The shipped model over-predicts the detection fraction on every run (null 0.17 to 0.46 vs real 0.14 to 0.39), so the null is sampled from a model that does not match the data in the first place. The gap in point 2 can therefore not be cleanly attributed to leakage; part of it may be model mismatch of another kind. A proper test needs leak-free hardware data from the same chip, which does not exist in this dataset.
5. Why the null is positive at all (my reading): the tracker's no-leakage likelihood is computed with the same approximate (mean-field, per-qubit) machinery, and the extra state can absorb any correlation that approximation misses. Two fitted parameters alone would not give 5 nats per shot; the approximation does.
6. Where the fitted p_L lands. On the null shots the fit spreads p_L over all seven data qubits (0.45 to 2.7e-3) and the top two change from run to run and seed to seed (indices 1 and 6, 6 and 2, 0 and 6, ...). On the real alpha <= 0.6 runs it concentrates on indices 1 and 5 every time (at T = 5 the other five are <= 0.14e-3). But on a leak-free, uniform-noise simulation of the same circuit (scenario N4 of the v3 work, dev_v3_diag.jsonl) the fit also puts qubits 1 and 5 on top, 3.3 and 3.7e-3 against <= 0.8e-3 for the rest. So part of the repetition is circuit geometry (those two positions are the most exposed), and the repetition alone does not prove a physical cause.
