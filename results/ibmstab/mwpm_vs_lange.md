# Adapter check: our plain MWPM against the MWPM numbers of Lange et al. (review round 2)

Lange et al. ship `results/ibm_stability_d3.json` in their GitHub repository: PyMatching on the shipped p_ij model, evaluated on their test split (10 000 shots per run at alpha = 0, 5 000 per rotated run). Our decoder A is PyMatching on the same shipped model, evaluated on all shots except the calibration shots (90 000 to 98 000 at alpha = 0, 40 000 to 48 000 rotated). The two shot sets overlap, so z is only a rough scale: z = (ours minus theirs) / sqrt(their std^2 + our binomial variance).

| run | our shots | our A P_fail | Lange MWPM P_fail | Lange shots | Lange std | z |
|---|---|---|---|---|---|---|
| T5 | 90000 | 0.1105 | 0.1124 | 10002 | 0.0032 | -0.57 |
| T10 | 90000 | 0.0736 | 0.0694 | 10002 | 0.0025 | +1.56 |
| T20 | 90000 | 0.0588 | 0.0547 | 10001 | 0.0023 | +1.69 |
| T50 | 96000 | 0.0394 | 0.0389 | 10000 | 0.0019 | +0.24 |
| T100 | 98000 | 0.0228 | 0.0204 | 10000 | 0.0014 | +1.63 |
| T20_alpha0.15 | 40000 | 0.0657 | 0.0654 | 5002 | 0.0035 | +0.08 |
| T20_alpha0.3 | 40000 | 0.0721 | 0.0738 | 5000 | 0.0037 | -0.43 |
| T20_alpha0.45 | 40000 | 0.0803 | 0.0786 | 5000 | 0.0038 | +0.41 |
| T20_alpha0.6 | 40000 | 0.1057 | 0.1070 | 5000 | 0.0044 | -0.28 |
| T20_alpha0.8 | 40000 | 0.1788 | 0.1856 | 5000 | 0.0055 | -1.17 |
| T20_alpha1.0 | 40000 | 0.3327 | 0.3234 | 5000 | 0.0066 | +1.32 |
| T100_alpha0.15 | 48000 | 0.0287 | 0.0240 | 5000 | 0.0022 | +2.04 |
| T100_alpha0.3 | 48000 | 0.0300 | 0.0294 | 5000 | 0.0024 | +0.24 |
| T100_alpha0.45 | 48000 | 0.0356 | 0.0372 | 5000 | 0.0027 | -0.55 |
| T100_alpha0.6 | 48000 | 0.0466 | 0.0478 | 5000 | 0.0030 | -0.38 |
| T100_alpha0.8 | 48000 | 0.0844 | 0.0814 | 5000 | 0.0039 | +0.74 |
| T100_alpha1.0 | 48000 | 0.2064 | 0.2052 | 5000 | 0.0057 | +0.20 |

All 17 runs agree: |z| <= 2.04, mean z = +0.40, 11 of 17 within one standard deviation. Baseline A is not mis-weighted.

## Where the shipped p_ij model comes from, and why its detection fraction is too high

The shipped `error_model.dem` is estimated from the detection-event correlations of the same run with the authors' `scripts/calibrate_dem.py` (closed-form correlator ratios for error mechanisms flipping up to four detectors, Appendix E of arXiv:2502.17722, on the template circuit `gnnrnn.circuits.stability_circuit`). It is not a device-calibration model.

Check: running that script on the detection events as we read them reproduces every term of the shipped file: 373 of 373 at T = 5 and 1723 of 1723 at T = 20, maximum absolute difference below 1e-6. So the data path (b8 reading, detector order) is right.

The over-prediction of the detection fraction is a property of the calibrated model itself. Sampling the shipped file with Stim's own sampler (no code of ours) gives 0.176 at T = 5 against 0.142 in the data and 0.231 at T = 20 against 0.161. Keeping only the one- and two-detector terms gives 0.099 at T = 5, so the three- and four-detector terms carry the excess. The method matches correlators, not marginals, and with correlated noise beyond its error set (which is what a leaked qubit produces) the hyperedge estimates come out too large. The GNN-RNN stage of Lange et al. is trained on top of this model and does not need it to be exact; plain MWPM only uses the ratios of weights, which is why A still matches their MWPM numbers.

Consequence for the null check (F9): the null shots come from a model whose first moment is already 25 to 50 % too high, so the real minus null evidence gap cannot be attributed to leakage alone. The comparison with the shipped MWPM numbers shows the baseline is fine; it does not make the null clean.
