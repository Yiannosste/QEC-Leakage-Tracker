# Real-device test: soft leakage tracking on the Google 2023 surface-code syndromes

*C3 project, real-data track. Data: Zenodo record 6804040 (Google Quantum AI, "Suppressing quantum errors by scaling a surface code logical qubit", Nature 2023). All numbers below were produced by the scripts listed at the end; nothing is quoted from the paper except where stated.*

## 1. Verdict in one paragraph

On the real hardware syndromes, **per-shot soft leakage weights give no gain**. Pooled over the eight d = 3 patches (400 000 shots), the soft decoders make the logical error per round *worse* by 0.7-1.4 % (HMM: ratio 1.014 [1.006, 1.021], McNemar p = 0.0004; CNN lag 0: 1.007 [1.000, 1.014], p = 0.04; CNN lag 2: 1.008 [1.001, 1.016], p = 0.03). At d = 5 (100 000 shots) they are null (ratios 1.000-1.011, every interval contains 1). Hard flags (E) are null everywhere. The only decoder that beats plain matching is the **static control A4** (no per-shot information, every leakage-touched edge raised by the model-average leakage probability): -0.5 % at d = 3 (ratio 0.995 [0.990, 1.000], p = 0.06) and -1.4 % at d = 5 (0.986 [0.973, 0.997], p = 0.017). This is a **null result for the tracker, not a failure of the test**: a simulator with the leakage model fitted to each experiment predicts the same null, because on this device the oracle itself (perfect knowledge of every leaked qubit-round) would remove only 2.9 % (d = 3) or 9.9 % (d = 5) of the logical error per round. The 2023 device sits in the regime where the earlier synthetic study already predicted f near 0: background detection fraction 0.14-0.17 per detector (above the Sycamore-like p = 3e-3 case, which had 8.5 %), and leakage on about 1 % of data-qubit-rounds. The flags themselves do mark something real (Section 6), they just do not help matching here.

!`Figure 1`

*Figure 1. (a) Per-round detection fraction (mean over all detectors of one round) for the hardware (black), the supplied device Pauli model alone (grey), and that model plus the fitted data-qubit leakage (red); solid d = 5 Z basis, dashed d = 3 Z basis centre (3,5). (b) Hardware: logical error per round of each decoder divided by that of plain MWPM on the supplied DEM, pooled over the eight d = 3 patches (blue) and the two d = 5 experiments (orange); bars = paired shot-level bootstrap 95 % interval (2000 resamples, seed 42). (c) Same on a 20 000-shot-per-experiment simulated test set drawn from the fitted model, where the oracle decoder B is available. Lower is better.*

## 2. What was done (plain language)

1. **Load and check.** For each of the ten 25-round experiments (four d = 3 patches x two bases, one d = 5 patch x two bases; 50 000 shots each) the detection events and observable flips were read with Stim and decoded with PyMatching using the dataset's own `circuit_detector_error_model.dem`. This reproduces the dataset's shipped PyMatching predictions shot-by-shot (99.8-99.98 % agreement at d = 3, 96.9-97.1 % at d = 5; the small d = 5 difference is tie-breaking/version noise) and gives P_fail inside the Wilson interval in all ten cases (Table 1). The data-derived `pij` DEMs agree with the shipped predictions much less (71-89 %), so the shipped decoder used the circuit DEM; **decoder A = MWPM on the circuit DEM** throughout.
2. **Fit a leakage model to each experiment.** The device Pauli model (`circuit_noisy.stim`) reproduces the hardware detection fraction at round 1 (within 0.003) but is flat in time, whereas the hardware detection fraction keeps rising, by +0.006 to +0.020 absolute between rounds 1 and 24 (Table 2, Figure 1a). The C3 leakage model (each data qubit leaks with probability p_L per round, stays leaked for a geometric time of mean tau rounds, randomises adjacent stabiliser outcomes with rho = 1/2, is depolarised on return) was fitted per experiment by matching the simulated rise to the measured rise (bisection on p_L for each tau in {1, 2, 4, 8, 16, 32}, pick the tau with the smallest squared residual over rounds 1-24). Result: d = 5, p_L = 2.0-2.1e-3, tau = 8 (1.2 % of qubit-rounds leaked); d = 3, p_L = 2.4e-4 to 1.5e-3, tau = 8-32 (0.2-1.2 % leaked). **tau is poorly identified** above 8 (residuals nearly flat), so the HMM lifetime parameter is uncertain by a factor 2-4.
3. **Train the trackers.** The causal CNN (3 layers, 32 channels, 3x3x3, unchanged architecture) was trained on simulated data from the fitted models: one model per (distance, basis, lag) on 50 000 shots (equal mixture of the four patches at d = 3), 6 epochs, Adam 1e-3. The 4-state HMM was instantiated per experiment with the fitted (p_L, tau), rho = 1/2, two explain-away iterations, and **per-detector base rates measured on the real data** (not simulated).
4. **Decode the real syndromes** with A, A4, D-HMM (lag 0), D-CNN (lag 0 and 2, soft weights p_e <- p_e XOR c pi, posteriors below 0.02 ignored), E-CNN (hard flags, threshold 0.5), and the same decoders on a 20 000-shot simulated test set from the fitted model (where the oracle B exists). Per-round error eps = 0.5 (1 - (1 - 2 P_fail)^(1/25)); every comparison with A is paired (same shots): bootstrap interval on the eps ratio, McNemar discordant counts and exact binomial p.

## 3. Sanity check: decoder A reproduces the dataset (Table 1)

| experiment | shots | det. fraction | P_fail dataset PyMatching [Wilson 95%] | P_fail our MWPM, circuit DEM | shot agreement circuit DEM | shot agreement pij DEM |
|---|---|---|---|---|---|---|
| bX d3 c3_5 | 50000 | 0.1492 | 0.4342 [0.4298, 0.4385] | 0.4341 | 99.89 % | 78.4 % |
| bX d3 c5_3 | 50000 | 0.1456 | 0.4432 [0.4388, 0.4475] | 0.4431 | 99.89 % | 75.4 % |
| bX d3 c5_7 | 50000 | 0.1371 | 0.4306 [0.4263, 0.4350] | 0.4307 | 99.98 % | 78.2 % |
| bX d3 c7_5 | 50000 | 0.1349 | 0.4299 [0.4256, 0.4343] | 0.4300 | 99.96 % | 70.9 % |
| bZ d3 c3_5 | 50000 | 0.1509 | 0.4328 [0.4284, 0.4371] | 0.4328 | 99.79 % | 86.7 % |
| bZ d3 c5_3 | 50000 | 0.1458 | 0.4344 [0.4301, 0.4388] | 0.4344 | 99.90 % | 86.5 % |
| bZ d3 c5_7 | 50000 | 0.1354 | 0.4302 [0.4258, 0.4345] | 0.4301 | 99.98 % | 81.2 % |
| bZ d3 c7_5 | 50000 | 0.1359 | 0.4273 [0.4229, 0.4316] | 0.4272 | 99.96 % | 88.8 % |
| bX d5 c5_5 | 50000 | 0.1593 | 0.4510 [0.4467, 0.4554] | 0.4497 | 96.87 % | 75.7 % |
| bZ d5 c5_5 | 50000 | 0.1600 | 0.4386 [0.4342, 0.4429] | 0.4380 | 97.08 % | 78.8 % |

P_fail of 0.43-0.45 after 25 rounds corresponds to eps = 0.037-0.044 per round; the paper's headline figures (eps about 3.0 % at d = 3 and 2.9 % at d = 5) were obtained with a better decoder (tensor network / belief matching) and a fit across round numbers, so they are not directly comparable to a single-point PyMatching number. Our interest is the *relative* change against A.

## 4. Fitted leakage model (Table 2)

| experiment | rise of detection fraction, round 1 to 24 (hardware) | fitted p_L per round | fitted tau (rounds) | leaked qubit-rounds (model) | P_fail hardware (A) | P_fail fitted simulator (A) |
|---|---|---|---|---|---|---|
| bX d3 c3_5 | +0.0203 | 1.11e-03 | 32 | 1.10 % | 0.4341 | 0.4278 |
| bX d3 c5_3 | +0.0095 | 5.51e-04 | 16 | 0.44 % | 0.4431 | 0.4251 |
| bX d3 c5_7 | +0.0090 | 5.51e-04 | 16 | 0.44 % | 0.4307 | 0.4245 |
| bX d3 c7_5 | +0.0064 | 1.04e-03 | 8 | 0.59 % | 0.4300 | 0.4207 |
| bZ d3 c3_5 | +0.0178 | 1.45e-03 | 16 | 1.16 % | 0.4328 | 0.4326 |
| bZ d3 c5_3 | +0.0083 | 5.51e-04 | 16 | 0.44 % | 0.4344 | 0.4157 |
| bZ d3 c5_7 | +0.0074 | 2.40e-04 | 32 | 0.24 % | 0.4301 | 0.4197 |
| bZ d3 c7_5 | +0.0083 | 1.18e-03 | 8 | 0.66 % | 0.4272 | 0.4148 |
| bX d5 c5_5 | +0.0180 | 2.02e-03 | 8 | 1.16 % | 0.4497 | 0.4384 |
| bZ d5 c5_5 | +0.0177 | 2.08e-03 | 8 | 1.20 % | 0.4380 | 0.4253 |

Plain MWPM on simulated data from the device Pauli model *alone* gives P_fail = 0.394 (bX d5), 0.394 (bZ d5) and 0.419 (bZ d3 c3_5) (20 000 shots each), i.e. the Pauli model under-predicts the hardware logical error by 0.01-0.06. Adding the fitted leakage closes part of that gap at d = 5 (0.438 / 0.425 vs hardware 0.450 / 0.438) and all of it for the d = 3 patch with the largest rise (bZ d3 c3_5: 0.4326 vs 0.4328). For the other d = 3 patches the fitted simulator still under-predicts the hardware by 0.006-0.019, so the leakage model explains the detection-rate rise but not all of the excess logical error; the remainder is error the model does not contain (crosstalk, non-Markovian noise, measurement-qubit leakage, correlated events).

## 5. Results on the real syndromes

### 5.1 Pooled d = 3 (eight patches, 400 000 shots)

| decoder | failures / shots | P_fail [Wilson 95%] | eps per round | eps ratio vs A [paired bootstrap 95%] | A wrong & X right | X wrong & A right | McNemar p |
|---|---|---|---|---|---|---|---|
| A: plain MWPM, supplied DEM | 173117 / 400000 | 0.4328 [0.4313, 0.4343] | 0.03857 | 1 (reference) | - | - | - |
| A4: static model-average re-weighting (control) | 172857 / 400000 | 0.4321 [0.4306, 0.4337] | 0.03839 | 0.9954 [0.9905, 1.0001] | 9903 | 9643 | 0.064 |
| D-HMM: soft weights, HMM posterior, lag 0 | 173869 / 400000 | 0.4347 [0.4331, 0.4362] | 0.03909 | 1.0136 [1.0061, 1.0208] | 22146 | 22898 | 0.0004 |
| D-CNN: soft weights, CNN posterior, lag 0 | 173505 / 400000 | 0.4338 [0.4322, 0.4353] | 0.03884 | 1.0070 [1.0003, 1.0136] | 17908 | 18296 | 0.042 |
| D-CNN: soft weights, CNN posterior, lag 2 | 173583 / 400000 | 0.4340 [0.4324, 0.4355] | 0.03889 | 1.0084 [1.0010, 1.0157] | 23151 | 23617 | 0.032 |
| E-CNN: hard flags (posterior > 0.5), lag 0 | 173149 / 400000 | 0.4329 [0.4313, 0.4344] | 0.03859 | 1.0006 [0.9974, 1.0039] | 4406 | 4438 | 0.74 |

### 5.2 Pooled d = 5 (both bases, 100 000 shots)

| decoder | failures / shots | P_fail [Wilson 95%] | eps per round | eps ratio vs A [paired bootstrap 95%] | A wrong & X right | X wrong & A right | McNemar p |
|---|---|---|---|---|---|---|---|
| A: plain MWPM, supplied DEM | 44389 / 100000 | 0.4439 [0.4408, 0.4470] | 0.04189 | 1 (reference) | - | - | - |
| A4: static model-average re-weighting (control) | 44202 / 100000 | 0.4420 [0.4389, 0.4451] | 0.04129 | 0.9856 [0.9734, 0.9970] | 3120 | 2933 | 0.017 |
| D-HMM: soft weights, HMM posterior, lag 0 | 44459 / 100000 | 0.4446 [0.4415, 0.4477] | 0.04212 | 1.0055 [0.9831, 1.0267] | 10276 | 10346 | 0.63 |
| D-CNN: soft weights, CNN posterior, lag 0 | 44530 / 100000 | 0.4453 [0.4422, 0.4484] | 0.04235 | 1.0111 [0.9884, 1.0334] | 10040 | 10181 | 0.32 |
| D-CNN: soft weights, CNN posterior, lag 2 | 44389 / 100000 | 0.4439 [0.4408, 0.4470] | 0.04189 | 1.0000 [0.9765, 1.0240] | 11847 | 11847 | 1 |
| E-CNN: hard flags (posterior > 0.5), lag 0 | 44429 / 100000 | 0.4443 [0.4412, 0.4474] | 0.04202 | 1.0031 [0.9901, 1.0162] | 3595 | 3635 | 0.65 |

### 5.3 Basis split at d = 3

X basis (four patches, 200 000 shots):

| decoder | failures / shots | P_fail [Wilson 95%] | eps per round | eps ratio vs A [paired bootstrap 95%] | A wrong & X right | X wrong & A right | McNemar p |
|---|---|---|---|---|---|---|---|
| A: plain MWPM, supplied DEM | 86893 / 200000 | 0.4345 [0.4323, 0.4366] | 0.03903 | 1 (reference) | - | - | - |
| A4: static model-average re-weighting (control) | 86907 / 200000 | 0.4345 [0.4324, 0.4367] | 0.03905 | 1.0005 [0.9931, 1.0078] | 5458 | 5472 | 0.9 |
| D-HMM: soft weights, HMM posterior, lag 0 | 87451 / 200000 | 0.4373 [0.4351, 0.4394] | 0.03983 | 1.0205 [1.0086, 1.0325] | 12538 | 13096 | 0.0005 |
| D-CNN: soft weights, CNN posterior, lag 0 | 87152 / 200000 | 0.4358 [0.4336, 0.4379] | 0.03940 | 1.0094 [0.9986, 1.0203] | 10931 | 11190 | 0.083 |
| D-CNN: soft weights, CNN posterior, lag 2 | 87174 / 200000 | 0.4359 [0.4337, 0.4380] | 0.03943 | 1.0102 [0.9982, 1.0227] | 14054 | 14335 | 0.097 |
| E-CNN: hard flags (posterior > 0.5), lag 0 | 86946 / 200000 | 0.4347 [0.4326, 0.4369] | 0.03911 | 1.0019 [0.9966, 1.0071] | 2509 | 2562 | 0.47 |

Z basis (four patches, 200 000 shots):

| decoder | failures / shots | P_fail [Wilson 95%] | eps per round | eps ratio vs A [paired bootstrap 95%] | A wrong & X right | X wrong & A right | McNemar p |
|---|---|---|---|---|---|---|---|
| A: plain MWPM, supplied DEM | 86224 / 200000 | 0.4311 [0.4290, 0.4333] | 0.03811 | 1 (reference) | - | - | - |
| A4: static model-average re-weighting (control) | 85950 / 200000 | 0.4298 [0.4276, 0.4319] | 0.03775 | 0.9904 [0.9841, 0.9967] | 4445 | 4171 | 0.0033 |
| D-HMM: soft weights, HMM posterior, lag 0 | 86418 / 200000 | 0.4321 [0.4299, 0.4343] | 0.03838 | 1.0069 [0.9973, 1.0170] | 9608 | 9802 | 0.17 |
| D-CNN: soft weights, CNN posterior, lag 0 | 86353 / 200000 | 0.4318 [0.4296, 0.4339] | 0.03829 | 1.0046 [0.9966, 1.0122] | 6977 | 7106 | 0.28 |
| D-CNN: soft weights, CNN posterior, lag 2 | 86409 / 200000 | 0.4320 [0.4299, 0.4342] | 0.03836 | 1.0066 [0.9976, 1.0154] | 9097 | 9282 | 0.17 |
| E-CNN: hard flags (posterior > 0.5), lag 0 | 86203 / 200000 | 0.4310 [0.4288, 0.4332] | 0.03809 | 0.9993 [0.9949, 1.0033] | 1897 | 1876 | 0.74 |

### 5.4 Per experiment (eps ratio vs A, paired bootstrap 95 %; * = McNemar p < 0.05)

| experiment | eps A | A4_avg | D_HMM_lag0 | D_CNN_lag0 | D_CNN_lag2 | E_CNN_lag0 |
|---|---|---|---|---|---|---|
| bX d3 c3_5 | 0.0389 | 0.994 [0.974, 1.014] | 1.029 [1.002, 1.059]* | 1.026 [1.001, 1.054]* | 1.003 [0.974, 1.031] | 1.003 [0.991, 1.016] |
| bX d3 c5_3 | 0.0416 | 0.999 [0.996, 1.003] | 1.006 [0.985, 1.026] | 0.981 [0.960, 1.002] | 0.994 [0.971, 1.018] | 0.996 [0.985, 1.007] |
| bX d3 c5_7 | 0.0380 | 1.007 [0.988, 1.028] | 1.029 [1.006, 1.052]* | 1.020 [0.999, 1.042] | 1.041 [1.017, 1.066]* | 1.005 [0.997, 1.013] |
| bX d3 c7_5 | 0.0378 | 1.001 [0.998, 1.003] | 1.018 [0.998, 1.038] | 1.009 [0.992, 1.025] | 1.003 [0.983, 1.023] | 1.003 [0.994, 1.013] |
| bZ d3 c3_5 | 0.0386 | 1.003 [0.997, 1.008] | 1.011 [0.990, 1.034] | 1.013 [0.997, 1.031] | 1.014 [0.994, 1.035] | 1.006 [0.995, 1.018] |
| bZ d3 c5_3 | 0.0390 | 0.965 [0.948, 0.980]* | 1.016 [0.997, 1.035] | 1.001 [0.984, 1.018] | 1.002 [0.983, 1.020] | 0.995 [0.987, 1.003] |
| bZ d3 c5_7 | 0.0378 | 1.000 [1.000, 1.000] | 1.005 [0.991, 1.020] | 1.003 [0.989, 1.018] | 1.004 [0.986, 1.021] | 0.996 [0.990, 1.002] |
| bZ d3 c7_5 | 0.0371 | 0.994 [0.976, 1.013] | 0.996 [0.975, 1.016] | 1.002 [0.984, 1.018] | 1.007 [0.987, 1.025] | 1.000 [0.992, 1.008] |
| bX d5 c5_5 | 0.0439 | 0.982 [0.965, 1.000] | 1.009 [0.976, 1.043] | 1.008 [0.976, 1.042] | 1.017 [0.981, 1.054] | 0.994 [0.974, 1.015] |
| bZ d5 c5_5 | 0.0401 | 0.989 [0.974, 1.004] | 1.003 [0.973, 1.032] | 1.014 [0.984, 1.044] | 0.986 [0.955, 1.015] | 1.011 [0.995, 1.028] |

Reading of the per-experiment table: 50 decoder-vs-A comparisons were made; 5 reach p < 0.05 (4 are *harm* by a soft decoder, 1 is the A4 gain on bZ d3 c5_3). With a Bonferroni threshold of 0.05/50 = 0.001 only the bX d3 c5_7 CNN-lag-2 harm (p = 0.0011, ratio 1.041) survives. There is no experiment, basis, or distance where a soft tracker gives a significant gain.

**d = 3 vs d = 5.** The soft decoders are significantly harmful when pooled at d = 3 and null at d = 5. The oracle gain available under the model is three times larger at d = 5 (9.9 % vs 2.9 %), and the d = 5 experiments have the largest fitted leakage (1.2 %); A4 gains most there (-1.4 %). **X vs Z.** At d = 3 the HMM harm is concentrated in the X basis (ratio 1.021 vs 1.007) and the A4 gain in the Z basis (0.990 vs 1.000); with 200 000 shots per basis these differences are at the edge of resolution and we do not interpret them.

### 5.5 Same decoders on the fitted simulator (expected gain if the model were exactly right)

Pooled d = 3 (160 000 simulated shots):

| decoder | failures / shots | P_fail [Wilson 95%] | eps per round | eps ratio vs A [paired bootstrap 95%] | A wrong & X right | X wrong & A right | McNemar p | f = recovered fraction of oracle gain [95%] |
|---|---|---|---|---|---|---|---|---|
| A: plain MWPM, supplied DEM | 67618 / 160000 | 0.4226 [0.4202, 0.4250] | 0.03596 | 1 (reference) | - | - | - | - |
| A4: static model-average re-weighting (control) | 67685 / 160000 | 0.4230 [0.4206, 0.4255] | 0.03606 | 1.0028 [0.9955, 1.0101] | 4001 | 4068 | 0.46 | -0.10 [-0.39, 0.16] |
| D-HMM: soft weights, HMM posterior, lag 0 | 67818 / 160000 | 0.4239 [0.4214, 0.4263] | 0.03626 | 1.0084 [0.9978, 1.0192] | 7911 | 8111 | 0.12 | -0.29 [-0.77, 0.07] |
| D-CNN: soft weights, CNN posterior, lag 0 | 67652 / 160000 | 0.4228 [0.4204, 0.4252] | 0.03601 | 1.0014 [0.9922, 1.0114] | 6497 | 6531 | 0.77 | -0.05 [-0.44, 0.26] |
| D-CNN: soft weights, CNN posterior, lag 2 | 67614 / 160000 | 0.4226 [0.4202, 0.4250] | 0.03595 | 0.9998 [0.9893, 1.0100] | 8380 | 8376 | 0.98 | 0.01 [-0.38, 0.36] |
| E-CNN: hard flags (posterior > 0.5), lag 0 | 67557 / 160000 | 0.4222 [0.4198, 0.4247] | 0.03587 | 0.9975 [0.9930, 1.0021] | 1517 | 1456 | 0.27 | 0.09 [-0.07, 0.25] |
| B: oracle flags (simulation only) | 66915 / 160000 | 0.4182 [0.4158, 0.4206] | 0.03493 | 0.9715 [0.9640, 0.9789] | 4883 | 4180 | 1.6e-13 | 1.00 [1.00, 1.00] |

Pooled d = 5 (40 000 simulated shots):

| decoder | failures / shots | P_fail [Wilson 95%] | eps per round | eps ratio vs A [paired bootstrap 95%] | A wrong & X right | X wrong & A right | McNemar p | f = recovered fraction of oracle gain [95%] |
|---|---|---|---|---|---|---|---|---|
| A: plain MWPM, supplied DEM | 17274 / 40000 | 0.4319 [0.4270, 0.4367] | 0.03831 | 1 (reference) | - | - | - | - |
| A4: static model-average re-weighting (control) | 17178 / 40000 | 0.4294 [0.4246, 0.4343] | 0.03767 | 0.9833 [0.9667, 0.9995] | 1180 | 1084 | 0.046 | 0.17 [0.01, 0.34] |
| D-HMM: soft weights, HMM posterior, lag 0 | 17256 / 40000 | 0.4314 [0.4266, 0.4363] | 0.03819 | 0.9968 [0.9668, 1.0294] | 3997 | 3979 | 0.85 | 0.03 [-0.35, 0.32] |
| D-CNN: soft weights, CNN posterior, lag 0 | 17304 / 40000 | 0.4326 [0.4278, 0.4375] | 0.03851 | 1.0053 [0.9764, 1.0374] | 3915 | 3945 | 0.74 | -0.05 [-0.43, 0.22] |
| D-CNN: soft weights, CNN posterior, lag 2 | 17401 / 40000 | 0.4350 [0.4302, 0.4399] | 0.03919 | 1.0230 [0.9890, 1.0575] | 4545 | 4672 | 0.19 | -0.23 [-0.69, 0.10] |
| E-CNN: hard flags (posterior > 0.5), lag 0 | 17174 / 40000 | 0.4294 [0.4245, 0.4342] | 0.03764 | 0.9826 [0.9628, 1.0032] | 1796 | 1696 | 0.094 | 0.18 [-0.03, 0.37] |
| B: oracle flags (simulation only) | 16655 / 40000 | 0.4164 [0.4116, 0.4212] | 0.03452 | 0.9010 [0.8750, 0.9287] | 4284 | 3665 | 4.1e-12 | 1.00 [1.00, 1.00] |

The simulator reproduces the hardware pattern: soft weights recover f = 0.0 +/- 0.4 of the oracle gain at both distances, hard flags and A4 recover 0.1-0.2, and the oracle gain itself is small (eps ratio 0.972 at d = 3, 0.901 at d = 5). This matches the earlier synthetic finding that f collapses when the background detection fraction is high and leakage is a small share of the error budget; here that share is 3-10 %, against 82-95 % in the p = 1e-3 SI1000 cells where f = 0.6-0.9 was measured.

## 6. Do the flags mark anything real? (Table 3)

Plausibility check: for every qubit-round the lag-0 CNN flags (posterior > 0.5, using only detectors up to that round), we look at the stabilisers adjacent to that qubit in the *next* round (not seen by the tracker) and ask how often they fire.

| experiment | model leaked qubit-rounds | flagged qubit-rounds, hardware (CNN lag 0 / lag 2 / HMM) | flagged, simulator (CNN lag 0) | CNN lag-0 recall / precision (simulator) | adjacent detection fraction one round AFTER a flag: flagged vs unflagged (hardware) | two rounds after |
|---|---|---|---|---|---|---|
| bX d3 c3_5 | 1.10 % | 0.20 % / 0.32 % / 0.92 % | 0.20 % | 0.13 / 0.75 | 0.413 vs 0.163 (n = 63k flags) | 0.371 vs 0.164 |
| bX d3 c5_3 | 0.44 % | 0.11 % / 0.17 % / 0.38 % | 0.09 % | 0.13 / 0.64 | 0.380 vs 0.159 (n = 33k flags) | 0.331 vs 0.160 |
| bX d3 c5_7 | 0.44 % | 0.08 % / 0.12 % / 0.33 % | 0.09 % | 0.13 / 0.70 | 0.356 vs 0.148 (n = 23k flags) | 0.307 vs 0.148 |
| bX d3 c7_5 | 0.59 % | 0.10 % / 0.15 % / 0.35 % | 0.10 % | 0.10 / 0.60 | 0.380 vs 0.146 (n = 30k flags) | 0.332 vs 0.147 |
| bZ d3 c3_5 | 1.16 % | 0.17 % / 0.27 % / 0.87 % | 0.15 % | 0.09 / 0.73 | 0.423 vs 0.165 (n = 53k flags) | 0.380 vs 0.166 |
| bZ d3 c5_3 | 0.44 % | 0.09 % / 0.13 % / 0.38 % | 0.06 % | 0.09 / 0.65 | 0.397 vs 0.160 (n = 27k flags) | 0.354 vs 0.160 |
| bZ d3 c5_7 | 0.24 % | 0.05 % / 0.08 % / 0.27 % | 0.04 % | 0.10 / 0.67 | 0.355 vs 0.146 (n = 13k flags) | 0.302 vs 0.146 |
| bZ d3 c7_5 | 0.66 % | 0.08 % / 0.12 % / 0.38 % | 0.08 % | 0.08 / 0.66 | 0.392 vs 0.147 (n = 24k flags) | 0.342 vs 0.148 |
| bX d5 c5_5 | 1.16 % | 0.24 % / 0.42 % / 0.57 % | 0.27 % | 0.15 / 0.66 | 0.386 vs 0.171 (n = 228k flags) | 0.344 vs 0.172 |
| bZ d5 c5_5 | 1.20 % | 0.24 % / 0.33 % / 0.56 % | 0.27 % | 0.15 / 0.65 | 0.385 vs 0.171 (n = 228k flags) | 0.341 vs 0.172 |

Two observations. (i) The flag rate on hardware equals the flag rate on the fitted simulator to within 0.03 percentage points in all ten experiments, so the hardware contains about as many leakage-like episodes as the fitted model says. (ii) After a flag, the adjacent detectors fire 0.36-0.42 of the time in the following round and 0.30-0.38 two rounds later, against 0.15-0.17 after an unflagged qubit-round; the model's prediction for a truly leaked qubit is 0.5 (fully randomised outcome), so the observed 0.4 is consistent with the simulator's precision of 0.6-0.75 (a 0.7 mixture of 0.5 and 0.15 gives 0.40). The flags therefore mark persistent, localised anomalies of the right kind and strength. The reason they do not help is not that they are wrong; it is that at recall 0.08-0.15 they catch few episodes, each episode is worth little when background noise dominates the matching weights, and the ~30 % false positives raise weights on edges that were in fact fine. The HMM flags 2-5 times more often than the CNN and is the most harmful decoder, consistent with its lower simulated precision (0.43-0.55).

## 7. Every modelling choice, stated

| choice | what was done | why / effect |
|---|---|---|
| decoder-A DEM | supplied `circuit_detector_error_model.dem` | reproduces the shipped PyMatching predictions; pij DEMs do not |
| base noise for the simulator | device Pauli model `circuit_noisy.stim`, unmodified | no SI1000 fit needed; matches round-1 detection fraction within 0.003 |
| leakage mechanism | C3 phenomenological model unchanged (rho = 1/2 randomisation of adjacent stabilisers, depolarise on return, final flip) | the hypothesis under test; measurement-qubit leakage not modelled (hardware resets measure qubits every round) |
| attribution of the detection-rate rise | 100 % to data-qubit leakage | the paper attributes the rise to leakage; if part of it is something else, p_L is over-estimated and the oracle gain is an upper bound |
| fit of (p_L, tau) | bisection on p_L for tau in {1,...,32}, squared residual over rounds 1-24, 10 000 simulated shots per evaluation | tau unidentified above 8; d = 5 prefers 8, d = 3 patches 8-32 |
| CNN training set | 50 000 simulated shots per (d, basis, lag), equal mixture of the four d = 3 patches | one model per (d, basis, lag) instead of per experiment, see deviations |
| HMM base rates | per-detector detection fraction of the real data | avoids importing the Pauli model's under-prediction into the emission model |
| A4 control | pi_avg = model mean leaked fraction; return probability pi_avg / tau; every leakage-touched edge raised statically | the fair no-per-shot comparator identified in the synthetic study |
| soft-weight constants | c = rho on time-like edges, 2/3 on return edges, rho on final data edge; posteriors < 0.02 ignored | unchanged from the pre-registration |
| statistics | Wilson 95 % on P_fail; eps = 0.5(1 - (1 - 2P)^(1/25)); paired shot bootstrap (2000, seed 42) on eps ratio; McNemar exact binomial | all comparisons paired on identical shots |
| simulated test set | 20 000 shots per experiment, seed = 7000 + hash of name | small; its f intervals are wide (+/- 0.4) |
| circuit adapter | `leakage_sim_real.py`: round boundary = non-final `M`; sweep-controlled `CX` skipped in adjacency; chip (row, col) coordinates mapped to the (d+1)^2 lattice | minimal changes; the injection/XOR machinery is inherited unchanged |

## 8. What the Willow 2025 dataset would need (not downloaded; 5.7 GB; project notes record Zenodo 13273331 as four zips totalling 112 GB)

The 2025 "below threshold" experiments differ in exactly the ways that matter here, so a scope test on them would need:

1. **A leakage-removal-aware model.** Willow applies data-qubit leakage removal (DQLR) every round, so the multi-round leakage this tracker exploits should be largely absent; the expected outcome is a *scope-null* (no rise in detection fraction, fitted p_L x tau near 0, no gain for any leakage decoder). The fit step must therefore allow tau near 1 and report a confidence interval on the leaked fraction, not just a point estimate.
2. **Per-round detection fraction from the data** as the primary diagnostic (Figure 1a style) for d = 3, 5, 7; if it is flat, the rest of the pipeline is a formality.
3. **Decoder A matched to the dataset's own baseline** (their shipped DEM and decoder predictions), and the same shot-level agreement check as Table 1 before anything else.
4. **Compute**: the d = 7 circuits have 48 measure qubits and 25+ rounds; CNN training and per-shot soft decoding scale roughly 2x over d = 5, so about 2 CPU-hours per experiment on this machine or a larger host; a d = 3 subset (if the zip members can be pulled individually with HTTP range requests, as the project notes indicate for zenodo.org) would fit the current budget.
5. **Positive control**: Willow also contains runs *without* DQLR (reported in the paper's supplement); those, if present in the public release, are the proper place to look for a gain.

## 9. Deviations from the plan for this analysis

- CNN trackers were trained **per (distance, basis, lag)** on a mixture of the fitted simulators of the patches, not per experiment (8 trainings instead of 20), to fit the time and memory budget; the HMM is per experiment as specified.
- HMM was run at lag 0 only (the plan listed "D-HMM soft" without a lag); CNN at lag 0 and 2 as specified.
- The simulated test set is 20 000 shots per experiment (the plan did not fix a number); its oracle-fraction intervals are wide.
- The A4 control uses the fitted model's mean leaked fraction (the pre-registration calls it the "average leakage probability"); no other static variants were run.
- The Willow DQLR scope-null test was **not** run (the 5.7 GB download was out of scope at the time); Section 8 lists what it needs.
- Four CNN trainings were interrupted once and re-run from scratch with the same seeds; the per-shot result files were checkpointed, so no decoder result was recomputed twice.

## 10. Files

- `real_data_results.csv` - every (set, experiment or pool, decoder) row: failures, shots, P_fail with Wilson bounds, eps with bounds, eps difference and ratio vs A with paired-bootstrap bounds, McNemar counts and p, f with bounds (simulated set), flag statistics.
- `real_data_figure.png` - Figure 1.
- `sanity_decoderA.csv` - Table 1 source.
- `fit_leakage.json` - fitted (p_L, tau) per experiment with the hardware, Pauli-only and fitted per-round curves.
- `leakage_sim_real.py`, `fit_leakage.py`, `train_cnn_real.py`, `run_real.py`, `analyze_real.py` - the scripts, in run order.
- `real_data_models.tar.gz` - the eight CNN state dicts; `real_data_pershot_results.tar.gz` - per-shot failure arrays and meta JSON for every decoder; `real_data_logs.tar.gz` - run logs.
