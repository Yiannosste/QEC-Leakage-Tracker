# C3 pre-registration: syndrome-inferred leakage flags as imperfect erasures for matching decoders

**Status:** written before any experiment of this phase was run. Nothing below changes after the first production run except by a labelled amendment.

**Claim under test.** In a rotated surface code with transmon-like data-qubit leakage, a minimum-weight matching decoder (PyMatching) gains when the edge probabilities around a leaked qubit are raised using a per-qubit, per-round leakage posterior computed by a two-state hidden Markov model (HMM) from the syndrome history alone (no 3-state readout, no hardware herald). The gain is set by the flag's recall, precision and latency.

**[fact]** = read from a primary source (page given); **[assumption]** = my modelling choice; **[not verified]** = source passage not read.

---

## 1. Leakage model (per shot, classical trajectories driving Pauli injections into a Stim circuit)

Each data qubit `q` carries a hidden state `s_q(t) ∈ {C, L}` (computational / leaked), updated once per QEC round `t` as a Markov chain:

| Symbol | Meaning | Grid | Realistic region | Basis |
|---|---|---|---|---|
| `p_L` | P(C→L) per data qubit per round, applied at round start | {1e-4, 3e-4, 1e-3, 2e-3, 5e-3, 1e-2} | **[5e-4, 5e-3]**; grid points 1e-3, 2e-3, 5e-3 | Google 2025 Table S4: CZ leakage 2.0e-4 per CZ and heating 2.5e-4 per qubit [fact, arXiv 2408.13687v1 p.20]; 4 CZ per data qubit per round gives ≈1.05e-3 (my arithmetic). Miao 2023: operations generate ≈5e-3 leakage population per cycle; data qubits start a cycle near 1e-3 and reach ≈5e-3 after measurement [fact, Nat. Phys. 19, 1780, p.1783, Fig. 3c]; "up to 4e-3 per round, comparable to intrinsic leakage rates in current devices" [fact, p.1784]. Varbanov 2020: L1 = 0.125% per CZ, so N_flux·L1 = 5e-3 per fluxed data qubit per cycle [fact, npj QI 6, 102, p.3, p.11]. The 1e-4 and 1e-2 ends are 5–10× outside the measured range, included to see where the effect vanishes or saturates. |
| `τ` | mean leakage lifetime in rounds; P(L→C) = 1/τ per round (geometric episode length) | {1, 2, 4, 8, 16} | **no-LRU regime: [4, 16]**, grid 4, 8, 16. **LRU regime: {1, 2}**, secondary. | Miao 2023: injected ∣2⟩ on a data qubit decays with exponential constant ≈4.4 cycles with no reset, faster than T1 of ∣2⟩ alone because of transport [fact, p.1781, Fig. 1c]. Varbanov 2020 HMM seepage per cycle Γ(L→C) = N_flux·L2 + 1 − exp(−t_c/(T1/2)), L2 = 2L1 [fact, p.11]; with Table 1 (T1 = 30 µs, t_c = 800 ns) this gives 0.062 per cycle, τ ≈ 16 (my arithmetic). McEwen 2021: T1 ≈ 14 µs, round 955 ns [fact, Nat. Commun. 12, 1761, p.3]; if T1(∣2⟩) ≈ T1/2 this is ≈7 rounds (my inference). With DQLR Google models P(2→1) = 1 per cycle, i.e. τ = 1 [fact, 2408.13687v1 p.18]; τ = 2 stands for an imperfect LRU (their P(3→2) = 0.5) [assumption]. |
| `ρ` | P(outcome of each stabiliser adjacent to a leaked data qubit is randomised) per round, independent across stabilisers and rounds | default **1/2**; sensitivity {0.25, 0.5} | 1/2 | Varbanov 2020: while a data qubit is leaked the defect probability of its neighbouring stabilisers goes to a constant ≈0.5 because the checks become weight-3 anti-commuting operators [fact, p.3, Fig. 3e]. McEwen 2021: injection yields a random readout, detection-event fraction 0.5 [fact, p.4]. ρ < 1/2 is an [assumption] covering partial randomisation (e.g. phase-dependent ancilla leakage). |
| return | on the round of L→C the qubit receives a uniformly random Pauli (I, X, Y, Z each 1/4) | fixed | — | Google's DQLR channel resets ∣2⟩→∣1⟩, so the pre-leakage state is lost [fact, 2408.13687v1 p.17–18]. Full depolarisation is the usual phenomenological convention (Fowler 2013, Suchara 2015, abstract level, [not verified]). [assumption] |
| measure-qubit leakage | **omitted** in the primary model | optional: `p_L^m = p_L`, lifetime 1 round | — | With reset every round, measure-qubit leakage stays ≈3e-4 (MLR) or <1e-4 (DQLR) and lives one round [fact, Miao p.1782, Fig. 3a]; a one-round random outcome is already covered by the SI1000 measurement flip. Declared simplification. |
| transport | **off** in the primary model; optional secondary: leaked data qubit hops to the measure qubit with probability 0.18 per CZ, measure qubit is reset at round end (shortens τ) | {0, 0.18} | — | Miao 2023: ≈18% of ∣30⟩ population is transported to ∣12⟩ per calibrated CZ, 61% for ∣31⟩↔∣22⟩ [fact, p.1781, Fig. 2b]. McEwen 2021: reset on measure qubits raised the data-qubit leakage decay rate 2.4× via transport [fact, p.3]. |

Leakage onset is placed at the start of a round [assumption]; within-round spreading is left to future work, as Miao et al. also note [fact, p.1783].

Simulator validation tests (must pass before production): (V1) `p_L = 0` reproduces plain SI1000 logical error within its 95% interval; (V2) episode lengths are geometric with mean τ (±5%); (V3) detection probability of stabilisers adjacent to a leaked qubit equals ρ⊕p_det0 (±0.02); (V4) at (2e-3, 8) the average detection probability rises over 25 rounds with risetime ≈τ — reported, not tuned, against Google 2023's relative rise of 12% (d = 5) and 8% (d = 3) with ≈5-cycle risetime [fact, Nature 614, 676, p.678].

## 2. Code and background noise

Rotated surface code, Stim generator `surface_code:rotated_memory_z`, d ∈ {3, 5, 7}, **R = 25 rounds** for all d (matches Google 2023 and the P3 pilot; long enough for τ ≤ 16 episodes). Memory-X is run only at the centre cell as a check. Background noise = **SI1000 at p = 1e-3**: CZ two-qubit depolarising p; single-qubit Clifford and idle depolarising p/10; data-qubit idle during measurement/reset ("resonator idle") 2p; reset flip 2p; measurement flip 5p [fact, Gidney–Newman–McEwen, Quantum 5, 605 (2021), arXiv 2108.10457, Table 2 p.5]. Surface-code threshold under SI1000 is 0.3–0.5% [fact, p.6], so p = 1e-3 is 3–5× below threshold. Decoding uses the Z-type detector subgraph for memory-Z. DEM built with `decompose_errors=True`.

## 3. Decoders (all run on the same shots)

- **(A) ignore flags:** PyMatching on the SI1000 DEM. Leakage effects are unmodelled noise.
- **(B) oracle hard flags:** true `s_q(t)` known. For every leaked (q, t): time-like edges of the Z-stabilisers adjacent to q at round t get p = 1/2; the X-type space-like edge of q at the return round gets p = 1/2 ("erasure" weights).
- **(C) oracle soft flags:** same locations, probabilities set to the model values (p = ρ for time-like edges, 1/2 for the return edge). At ρ = 1/2, C ≡ B, so C is run only in the ρ = 0.25 sensitivity.
- **(D) inferred soft flags:** one two-state HMM per data qubit with transition matrix [[1−p_L, p_L], [1/τ, 1−1/τ]] (Varbanov's form [fact, p.11]) and emissions = detector bits of the 2–4 adjacent stabilisers of both types, P(defect∣C) = p_det0 (estimated per detector from a p_L = 0 run), P(defect∣L) = ρ⊕p_det0. Posterior π_q(t∣t+L): **L = 0** forward filter, **L ∈ {1, 2, 3, 5}** fixed-lag smoothers, **L = ∞** full smoother (batch upper bound). Edge probability p_e = p_e^0 ⊕ (π·ρ_e), weight w_e = ln((1−p_e)/p_e).
- **(E) hard-thresholded posterior:** as D but p_e = 1/2 if π > θ, else p_e^0; θ ∈ {0.3, 0.5, 0.7}.

Tracker mismatch (robustness): HMM run with p_L' = p_L × {0.5, 2}, τ' = τ × {0.5, 2}, ρ' ∈ {0.3, 0.7}, and with transport on while the HMM assumes it off.

## 4. Metrics

1. Logical failure probability over 25 rounds `P_fail` with **Wilson 95% interval**; logical error per round ε = ½[1 − (1 − 2P_fail)^{1/R}] with the interval mapped through the same formula.
2. **Λ** = ε_d / ε_{d+2} (Λ_{3/5}, Λ_{5/7}) per decoder, with error propagated from the Wilson intervals.
3. **Oracle gain** G_B = (ε_A − ε_B)/ε_A.
4. **Fraction of oracle gain recovered** f_X = (ε_A − ε_X)/(ε_A − ε_B) for X ∈ {D, E}; 95% interval by **paired shot-level bootstrap** (2000 resamples, seed 42), since all decoders see identical shots. Also report the McNemar discordant counts (A wrong & X right, X wrong & A right).
5. Flag quality per (q, t) against the true `s_q(t)`: ROC AUC, precision–recall AUC, precision and recall at θ = 0.5, **mean detection delay** = mean over episodes of (first t with π > 0.5) − t_onset, plus the fraction of episodes never detected. Reference values: Varbanov's data-qubit HMM had ≈1-cycle average delay and 67% of the optimal PR area [fact, p.6–7].

## 5. Latency protocol

- **Batch:** decode all 25 rounds at once; the tracker may use any lag up to ∞.
- **Streaming:** sliding-window decoding that commits the correction for round t at time t + W, **W ∈ {0, 1, 2, 5}**. The flag for round t is delivered at time t + L (smoother lag plus processing delay), **L ∈ {0, 1, 2, 3, 5}**. A flag arriving after its round is committed is **not** mis-attributed to a later round (the P3 pilot showed misattribution destroys the gain [fact, pilot3_report]); it re-weights only the still-open rounds of the episode, so L > W costs recall on the early rounds of each episode.

Three pre-registered hypotheses, decided at the centre cell (p_L = 2e-3, τ = 8), d = 5 and 7:

- **H-harmful:** for some L > W, ε_D(L, W) > ε_A with the paired bootstrap interval of ε_D − ε_A excluding 0.
- **H-neutral:** for L > W, ε_D(L, W) lies inside the interval of ε_A (late flags are simply useless).
- **H-latency-only:** for every L ≤ 5, ε_D(L, W = L) ≤ ε_D(0, 0) + its half-interval width (the gain is fully recoverable by waiting L rounds). The verdict reports which of the three holds; several may hold in different (L, W) corners and are then reported cell by cell.

## 6. Verdict rules (read off mechanically)

Let the **realistic cells** be the 9 pairs (p_L, τ) ∈ {1e-3, 2e-3, 5e-3} × {4, 8, 16}, the **centre cell** be (2e-3, 8), and f_D* be f_D at the best lag L ≤ 2 in batch mode.

- **P1 (effect):** at both d = 5 and d = 7, the median of f_D* over the 9 realistic cells ≥ **0.50**, and the lower bootstrap bound of f_D* is > 0 in ≥ 7 of 9 cells.
- **P2 (robustness):** at the centre cell, d = 5 and 7, f_D ≥ **0.30** for every one of the six mismatch settings (p_L ×0.5, ×2; τ ×0.5, ×2; ρ' = 0.3, 0.7).
- **P3 (something to recover):** G_B ≥ **0.15** at the centre cell at d = 5 and d = 7, with the interval of ε_A − ε_B excluding 0.
- **P4 (prior art):** the parallel prior-art search finds **no** paper (2014–2026) reporting surface-code logical error versus syndrome-inferred (no herald, no 3-state readout) leakage flags fed to a matching decoder at d ≥ 5 with a delay/latency analysis. Partial results that do *not* close P4: Varbanov 2020 (HMM, d = 3, post-selection), Suchara 2015 (perfect flags), arXiv 2411.10343 (hardware-heralded leakage; from the earlier novelty check, [not re-verified]), Xin 2025 (3-state readout, d = 3, neural decoder), Wang 2026 (GNN, atom loss).

| Verdict | Rule |
|---|---|
| **PAPER-READY** | P1 ∧ P2 ∧ P3 ∧ P4 |
| **KILL** | ¬P4, **or** G_B < 0.15 in ≥ 7 of 9 realistic cells at d = 7, **or** f_D(any lag, batch) < 0.20 in all 9 realistic cells at both d = 5 and d = 7 |
| **NEEDS-MORE** | anything else (for example: P3 ∧ P4 true but median f_D* in [0.20, 0.50); P2 fails at one or two mismatch points only; ≥ 3 realistic cells under-powered after the extension in §7) |

Why these numbers. **0.15 for G_B:** leakage plus stray interactions are ≈17% of Google's 1/Λ budget and DQLR gave a 35% increase in Λ at d = 5 [fact, Nature 638, 920, p.922]; an oracle gain below 15% would be smaller than the hardware alternative. The P3 pilot gave oracle gains of 37–70% for heralded erasures at comparable rates [fact, pilot3_report]. **0.50 recovered:** Varbanov's HMM reached 67% of optimal detection [fact, p.7]; half the oracle gain is the pilot's "half-gain" bar and the minimum that makes a tracker competitive with hardware flags. **0.30 under ×2 mismatch:** a factor 2 in p_L or τ is the realistic calibration uncertainty (device values span 1e-3–5e-3 and 4–16 rounds); we accept losing 40% of the matched effect. **0.20 kill line:** soft-readout decoders report 6.8–10% gains (Ali 2024; Varbanov 2025, abstracts via the survey, [not verified]); a tracker recovering < 20% of the oracle gain would not justify its latency cost.

## 7. Grids, shots and seeds

| Grid | Cells | Decoders | Shots per cell |
|---|---|---|---|
| G1 primary | 9 realistic cells × d ∈ {3, 5, 7}, batch | A, B, D(L = 0, 1, 2, 3, 5, ∞), E(θ = 0.5) | 1e5 (d = 3, 5), 2e5 (d = 7) |
| G2 map | 6 p_L × 5 τ, d = 5 | A, B, D(L = 0, 2) | 5e4 |
| G3 robustness | centre cell, d = 5, 7; six mismatch settings; transport on; ρ = 0.25 (adds C); memory-X | A, B, C, D(L = 0, 2) | 1e5 (d = 5), 2e5 (d = 7) |
| G4 latency | centre cell, d = 5, 7; W × L grid (4 × 5) | A, B, D | 1e5 (d = 5), 2e5 (d = 7) |

Power: with P_fail of order 1e-3–3e-3 at d = 7, 2e5 shots give ≈200–600 decoder-A failures; a 15% relative reduction then gives a paired discordant-count difference of ≈3–4 standard errors (my estimate, scaled from the pilot's 83 vs 7 discordant shots at d = 5 [fact, pilot3_report]). **Stopping rule:** a cell with < 100 decoder-A failures is extended once by ×5 and labelled "extended"; if still < 100 it is labelled under-powered. **Seeds:** simulator seed = 1000 + 100·i_d + 10·i_pL + i_τ (grid indices); HMM/bootstrap seed 42; identical shots for all decoders in a cell. Cost driver: one matching-graph rebuild per shot with any π > 0.01; estimated 10–30 CPU-hours on 16 cores.

## 8. What I could not verify

- The per-operation DQLR removal efficiency and the fitted γ↑/γ↓ leakage rates of McEwen 2021 are in supplements I did not read; only the ratios (40×, 2.4×) and the 4.4-cycle decay are quoted.
- Google 2023's Pauli+ parameter values (its supplement) were not read; only the main-text detection-probability rise is used.
- Units of "Leakage (heating) 2.5e-4" in Google 2025 Table S4 are taken as per qubit per cycle (the table does not state them).
- Fowler 2013, Suchara 2015, Rol 2019, Ali 2024, Varbanov 2025, and arXiv 2411.10343 are cited at abstract level from the earlier survey.
- The HMM delay/optimality figures are from Varbanov's density-matrix d = 3 simulation, not from hardware.

## 9. Known limits accepted in advance

Phenomenological leakage (classical flag, independent randomisation, full depolarisation on return); no ∣3⟩; no within-round spreading; measure-qubit leakage omitted; memory-Z only except one check; p = 1e-3 only; d ≤ 7. Manabe 2025 warns that twirled leakage models can differ from coherent ones (abstract via survey) — a stated caveat, not tested.
