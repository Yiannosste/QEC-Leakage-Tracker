> Working note, written during the project and kept for the record. It may use project shorthand and may contain numbers that were later corrected. `results/facts.md` supersedes it wherever they differ.

# Where could C3-style soft leakage tracking give a practical gain, and is there public data to test it?

*Cross-platform survey for project C3, written 20 Oct 2026 for a 4th-year ECE reader. Papers were read as targeted page extracts through alphaXiv (page numbers given), two as full text; data records were checked through the Zenodo REST API. Every quote is under 20 words. Companion files: `platform_survey.csv` (one scored row per platform/mechanism) and `platform_papers.csv` (every paper, how it was verified). No simulations were run.*

---

## 0. Summary in plain words

C3 tracks a **hidden per-qubit state** (a transmon stuck in |2⟩ for several rounds) using only the pattern of stabiliser outcomes, and turns the per-round probability of that state into soft edge weights for MWPM. On Google's devices this is null because the hidden state is removed every cycle (Willow) or is a few per cent of the error budget (Sycamore 2023). The question here is: on which other hardware does a long-lived hidden state (i) exist, (ii) leave a readable syndrome fingerprint, (iii) carry a large share of the logical error, (iv) have **no** cheap hardware herald that already solves it, and (v) come with public raw syndromes?

The answer, after reading 45 papers across six platforms:

1. **IBM fixed-frequency transmons (Nighthawk square lattice, heavy-hex)** satisfy all five conditions and are the only platform that does. There is no data-qubit leakage removal, measure qubits are often not even reset, memories run to 50 to 150 rounds, two independent 2026 papers see a persistent error component that grows with round number and correlates between checks sharing a data qubit, IQ-based leakage post-selection lowers the logical error by 12 to 21 %, and a 200 MB public dataset of d = 3 / d = 5 surface-code syndromes exists (Zenodo 23335425). **Feasibility 5/5.**
2. **Neutral-atom loss (Harvard/QuEra)** has the strongest physics, loss is about half of all errors, the fingerprint is deterministic, and the hidden state lasts for the whole shot, and a 1 GB public raw dataset exists (Zenodo 15685795). But the loss *is* heralded at the end of each shot, and decoders that use that delayed herald already exist and are published with the data. The honest C3 question there is "how much of the heralded gain can syndrome-only inference recover on real data?" (the Nishio 2026 question, never tested on hardware). **Feasibility 4/5.**
3. **Trapped ions (Quantinuum)** have the largest leakage share of any platform (41 % of 1/Λ) and the authors explicitly invite a leakage-aware decoder, but the per-round optical repump shortens episodes to about one round and no raw syndrome data are public. **2/5.**
4. **Cat, dual-rail, GKP, fluxonium, spin, photonic** platforms either herald the hidden state every cycle by construction (that is what an erasure qubit is), or have no multi-round QEC syndrome data, or both. **1 to 2/5.**

---

## 1. The five requirements, restated as tests

| # | requirement | how I scored it |
|---|---|---|
| i | hidden state persists over several rounds | mean episode length in rounds, from the paper's own removal/reset scheme |
| ii | syndrome fingerprint strong enough without hardware heralds | how many stabilisers are randomised, with what probability, every round |
| iii | large share of the logical error | a number from the paper (budget, post-selection gain, or oracle) |
| iv | no cheap herald or removal already solving it | does the published experiment already feed a flag to the decoder, or remove the state each cycle? |
| v | public raw syndrome data | repository, size, format, rounds, shots, verified on Zenodo where possible |

Feasibility 1 to 5 = "a C3-style soft tracker could give a practical gain **and** be checked on real data within a student project".

---

## 2. Scored table (short form; full text of each cell is in `platform_survey.csv`)

| platform / mechanism | (i) lifetime | (ii) fingerprint | (iii) share | (iv) herald / removal | decoder prior art | (v) public data | score |
|---|---|---|---|---|---|---|---|
| **IBM transmons**, leakage, no DQLR, measure qubits not reset | multi-round; correlations persist over many rounds up to 150-round memories (Kan 2026); τ ≈ T1(|2⟩)/round, tens of rounds (estimate) | C3's own model; Kan 2026 sees persistent correlations between checks sharing a data qubit | ≥ 12 to 21 % (IQ post-selection gain, IBM 2026); persistent component doubles ε by round 100 | none in the public data; no DQLR | IQ hard flags on repetition codes (Hanisch); post-selection (IBM 2026); end-to-end GNN (Lange 2026). **No syndrome-inferred soft weights** | **Zenodo 23335425**, 200 MB, d=3/d=5, 10⁵ shots × {5,10,20,30,50} rounds | **5** |
| **Neutral atoms, atom loss** (Harvard/QuEra) | whole shot ("arbitrarily long"); public run = 4 rounds | deterministic: X and Z checks on the lost atom anticommute → "flickering" every round | ≈ 50 % of errors; ≥ 80 % of leakage is loss | **delayed herald** at final readout (loss-resolving imaging), used by the decoder | delayed-erasure MLE, Pauli envelope, ML with loss info (1.73×); syndrome-only: Nishio 2026 (offline), Wang 2026 (GNN) | **Zenodo 15685795**, 997 MB raw 0/1/loss shots + notebook | **4** |
| Neutral atoms, Atom Computing / Microsoft | ≤ 2 cycles (atom measured, reset, replaced) | 50 % readout error + partner Z, already in the DEM per shot | loss channels exceed Pauli errors | imaging every measurement + replacement | per-shot DEM update (done) | none found | 2 |
| Neutral atoms, erasure conversion (Yb, Caltech/Princeton) | μs to 100 μs Rydberg/metastable lifetimes; not visible in current slow cycles | same as loss once converted | 33 to 56 % of gate errors convertible | fluorescence erasure image, fidelity ≈ 0.98 | erasure-aware decoding with hardware flags | on request | 2 |
| **Trapped ions, hyperfine leakage** (Quantinuum) | indefinite without repump; with Helios repump 6.5× after three rounds → ≈ 53 % survival per round, mean episode ≈ 2.1 rounds (inferred) | gates with a leaked ion fail → cascades | **41 % of 1/Λ** | per-round repump + SWAP-LRU every 3 rounds | none; authors invite one | **none public** (d=3: 15 840 shots × 20 rounds) | 2 |
| Trapped ions, ion / chain loss | rare | 2 + 2 stabilisers | negligible at realistic rates | QND gadget 96.5 %, beacons | feed-forward restoration | none | 1 |
| Cat qubits (AWS Ocelot, Alice & Bob) | ≈ 1 cycle (ancilla f→e reset each cycle; bit-flip excursion ≈ 1/κn̄) | 1-D code: 2 neighbours; bit flips heralded by buffer photons (proposal) | erasure info: 1.63 % → 1.47 % per cycle (≈ 10 %) | extra readout pulse every cycle | erasure matching already used | on request | 1 |
| Dual-rail erasure qubits | until next check (every gate/round) | check flags the qubit; missed erasures 9×10⁻⁴ per check | erasures 10 to 40× Pauli | mid-circuit erasure check + reset | weighted UF/MWPM; imperfect checks (Chang 2025) | on request; no memory data | 2 |
| GKP (Yale sBs) | 17.2 cycles for leakage above |f⟩ | streaks of ancilla 'e' outcomes; weak correlation tail | 1.3×10⁻⁴ per cycle (small) | |f⟩ reset each cycle | post-selection only | not stated | 1 |
| Fluxonium / qutrit erasure / Zuchongzhi LRU | 40 to 85 μs erasure lifetimes | hardware herald only | ≈ half of fluxonium gate error | erasure checks; LRU each cycle | post-selection | none | 1 |
| Spin qubits | drift on ms scales; no multi-round QEC | none published; real-time Bayesian drift tracking exists at the physical level | not quantified | nuclear feedback | none | 3-qubit only | 1 |
| Photonics | none (photons consumed) | heralded by no-click | heralded | detector | native erasure decoding |, | 1 |

---

## 3. Platform notes with the evidence

### 3.1 IBM fixed-frequency transmons, the regime C3 was built for, on hardware that still has it

Why it fits. Google removed the multi-round state with DQLR; IBM has not. The PNNL/Fordham/NASA study on an IBM Nighthawk r2 processor (`ibm_phoenix`, d = 3…6, up to 150 rounds, 20 000 shots per duration) states it plainly: the long-lived structure is "compatible with a persistent error component, potentially associated with leakage or environmental drift" (Kan et al. 2026, p. 9); detection probabilities rise during the memory in nearly every check, and correlations persist for many rounds only between checks that share a data qubit (p. 9, Fig. 10f). Of leakage-removal circuits they write: "Our circuits contain none" (Appendix D2). The distance-6 Z-memory error per round "rises from 0.330 % [0.306 %, 0.358 %] to 0.838 %" between rounds 3 to 13 and 61 to 101 (p. 9), the persistent component eventually dominates. IBM's own 2026 heavy-hex paper quantifies a lower bound on the share: IQ-based leakage post-selection gives "a further reduction in logical error per round of 11.8% and 21.0% in Z and X bases" (p. 5). Hanisch et al. report, for IBM repetition codes to 100 rounds, that once a qubit leaks it does not operate as intended, "leading to persistent faults over multiple stabilizer measurements" (p. 6). Older IBM heavy-hex data had leakage of 6.54 × 10⁻³ per measurement (Sundaresan 2023, p. 13).

Lifetime. Not measured in rounds by any of these papers. On fixed-frequency devices there is no tunable-coupler CZ, so the Sycamore transport mechanism that shortened C3's episodes (p_t = 0.3 per gate, `realism_report.md`) should be weaker; the |2⟩ state then decays with roughly T1/2 (hundreds of μs on Nighthawk) against a ≈ 2 μs round, tens of rounds. This is an estimate, marked provisional, and is the first thing the fingerprint analysis should measure.

Herald. None in the public binary records. IBM can return IQ data (`meas_level=1`) and the 2026 paper fits 3-state Gaussian mixtures to it, so a herald *could* be obtained for validation on self-collected data, but the shipped public dataset is bits only, exactly C3's premise.

Decoder prior art. Hanisch: IQ-derived hard flags (edge weight 0), repetition code. IBM 2026: post-selection. Lange 2026: an end-to-end GNN-RNN that gets 1.47 % per round vs 2.79 % for MWPM at d = 3 (Table II), a ×1.9 gap that an explicit leakage tracker should account for part of. No paper feeds a syndrome-inferred leakage posterior into MWPM weights on IBM surface-code data.

Public data. Zenodo 23335425 (`ibm_berlin.zip`, 200.2 MB; verified through the Zenodo API): surface-code memory d = 3 at two placements and d = 5 on IBM Nighthawk r1, "10⁵ shots at each duration t ∈ {5, 10, 20, 30, 50}" (p. 6), stored as Stim b8 detection events, logical flips, calibrated p_ij detector error models, plus the raw IBM Runtime results. One important circuit detail: "measure qubits are measured but never reset between rounds" (p. 6), so a leaked *measure* qubit also persists, a second hidden state C3's data-qubit HMM does not model yet. The Kan 2026 dataset has no data statement; IBM cloud access (Open plan) would allow a d = 3 self-collected run.

### 3.2 Neutral atoms, ideal physics, but the herald is already there at the end of the shot

Harvard/QuEra, repeated surface code (Bluvstein et al. 2025, Nature 649, 39). The error budget: the error per round "reduces toward 0.1% per round on shots with no qubit loss (Fig. 2e), consistent with a p3 scaling and roughly half of our errors being loss" (p. 3), and "our leakage is at least 80% loss" (p. 16). Loss is the cleanest possible C3 state: "doing a gate with a lost atom simply turns off the gate" (p. 16), so the X and Z stabilisers on that atom anticommute and the detectors around it flicker; "the flickering can continue for arbitrarily long times" (p. 16). Detection is delayed: "we detect them at the final qubit measurement, constituting delayed-erasure information" (p. 16). With that information plus a machine-learning decoder they gain "a factor of 1.73(13)x compared to conventional methods" (p. 3). QuEra's theory paper puts the loss share at "more than 40% of the total physical errors in recent experiments" (Liu 2026, p. 1).

Prior art is dense: delayed-erasure MLE/MWPM (Baranes 2026, and its Fig. 2b shows that knowing the loss *time* adds little over knowing only *which* atom), Pauli-envelope decoders (Liu 2026), superchecks, correlated-loss decoders (Perrin 2026), the Cambridge delayed-erasure DEM construction (SSR "at measurement time rather than at the moment of loss", 2609.10079 p. 3). Syndrome-only inference exists in two forms: Nishio 2026 (offline, averages over many shots, lists single-shot online inference as future work) and Wang 2026 (STGNN that locates loss from the flicker). What does not exist is a single-shot HMM → soft-MWPM tracker evaluated against the hardware flag on real shots.

Public data. Zenodo 15685795, `Zenodo.zip` 996.8 MB: "raw atom measurement 0,1,loss results", the decoding notebook (stim 1.14, torch 2.4) and trained ML decoders; verified through the Zenodo API. Caveat: the repeated-QEC runs are 4 rounds (each 4.45 ms), so an episode can be seen for at most 3 to 4 rounds, and the d = 5 set is of order 10⁴ shots.

Atom Computing / Microsoft (toric code, 2606.04079) is the counter-example: "a typical atom participates in two syndrome extraction cycles before being measured, reset, and if necessary, replaced" (p. 3), each detected loss is written into the DEM per shot as "a readout error with a likelihood of 50% on the lost qubit" (p. 15). That is already a per-shot erasure decoder; nothing for C3 to add, and no data statement was found.

### 3.3 Trapped ions, biggest share, shortest episodes, no data

Quantinuum Helios colour code (2610.24077, Oct 2026): a ¹³⁷Ba⁺ qubit can leak into six nearby hyperfine levels and "Leaked population can persist in these levels until a mid-circuit reset returns it to the qubit subspace" (p. 2). The error budget: "If we add the leakage contribution to all channels, it amounts to 41% of 1/Λ" (p. 5). Mitigation is a per-round optical repump, "the suppression is 6.5(1)× after three cycles" (p. 2), i.e. about 15 % of leaked population survives three rounds; if the repump acts geometrically this is ≈ 53 % survival per round and a mean episode of ≈ 2.1 rounds (our inference, not a number from the paper), plus a SWAP-LRU every three rounds. The decoders ignore leakage, and the authors write that since the repump is imperfect and "some fraction of leaked qubits remain leaked, such a decoder can prove useful even while using leakage repump" (Discussion). Statistics are small (Table I: d = 3, 15 840 shots × 20 rounds; d = 7, 3 failures) and no data repository is given. Earlier H2 data: leakage "3.9(2)×10⁻⁴" per 2Q gate against 1.8 × 10⁻³ infidelity (Moses 2023, p. 7), i.e. ≈ 20 % of two-qubit error, with persistence "if left untreated it will saturate the system" (Ryan-Anderson 2021, p. 8); those experiments used leakage-detection gadgets to discard shots, and no syndrome data are public. Ion loss is rare and heralded (Stricker 2020: QND detection efficiency "96.5(4) %", p. 3).

Verdict: physics fits (i) to (iii) only partially (episodes ≈ 1 round after repump), (iv) is half-satisfied (repump is removal, not a herald), (v) fails. If Quantinuum released syndromes, a one-round leakage model (not C3's multi-round HMM) would be the right tool.

### 3.4 Cat, dual-rail and GKP bosonic qubits, heralded by design

AWS Ocelot (Putterman 2025): the ancilla transmon's |f⟩→|e⟩ decay during readout is treated as an erasure and heralded every 2.8 μs cycle by an extra pulse; erasure-aware matching lowers the d = 5 logical phase-flip per cycle from 1.63(4) % to 1.47(6) % (Fig. 3, p. 6). Data "upon reasonable request" (p. 10). A 2026 theory paper argues cat bit flips are themselves erasures because "a strong buffer emission signals the beginning of a bit-flip event" (2607.01375, p. 3), again a hardware signal. No Alice & Bob multi-cat repetition-code experiment appeared in the alphaXiv index for 2024-06 to 2026-10.

Dual-rail (Levine 2024; Chou 2023; de Graaf 2024; IQA 2025): the hidden state |00⟩ is checked every gate or round; "erasure probability p_erasure = 2.19(2) × 10⁻³ per gate while the residual errors are ∼ 40 times lower" (Levine p. 1); mid-circuit checks reach a "missed erasure fraction of (9.0 ± 0.5) × 10⁻⁴" with "an erasure rate of 2.92 ± 0.01% and a Pauli error rate of 0.31 ± 0.01%" per check (de Graaf p. 1). The only C3-shaped niche is the *missed* erasure (false negative), which Chang 2025 already treats in simulation; no multi-round QEC syndrome data exist.

GKP (Sivak 2023): a real multi-cycle hidden state, ancilla leakage above |f⟩ with an exponential tail of "17.2 cycles, corresponding to 85 μs" (p. 31) at "1.3 × 10⁻⁴ per cycle" (p. 5), visible as streaks of 'e' outcomes and a weak "correlation tail" (p. 32). They post-select on it. It is a single-mode code (no matching graph), so C3's edge-weight machinery does not apply; a 1-D HMM would, but the share is ~10⁻⁴ per cycle.

### 3.5 Other superconducting variants, spins, photonics (brief)

Fluxonium and transmon-qutrit erasure demonstrations (2607.27123: "leakage error rate of 0.022(2)%" per gate, p. 5; 2604.08672: 45 μs erasure lifetime) are single-qubit and herald the state by a resonator shift. USTC's d = 7 run (He 2025) removes data-qubit leakage every cycle with a microwave LRU; without it Λ < 1, the strongest statement that unmitigated transmon leakage is above-threshold, but the unmitigated syndromes were not released (not verified). Spin qubits have no multi-round surface-code data (Takeda 2022: three qubits, one round); the closest hidden-state precedent is physical-level: an FPGA "computes the Bayesian estimate of ∆Bz" of the nuclear gradient in real time (Shulman 2014, p. 2). Photonic fusion-based schemes herald loss by a missing click and consume the photon, so no per-qubit state persists (general knowledge; not re-verified this session).

---

## 4. Public raw-data inventory (verified)

| dataset | platform | contents | size / shots / rounds | verified how |
|---|---|---|---|---|
| Zenodo 23335425 `ibm_berlin.zip` | IBM Nighthawk r1 surface code | detection events (Stim b8), logical flips, p_ij DEMs, raw Runtime results; d=3 ×2, d=5, X-stability, ZZ merge | 200.2 MB; 10⁵ shots × t ∈ {5,10,20,30,50} | Zenodo API + Lange 2026 p. 6 |
| Zenodo 15685795 `Zenodo.zip` | Harvard/QuEra atom array | raw 0/1/loss atom measurements, decoding notebook, ML decoders; d=3/5 repeated QEC | 996.8 MB; 4 rounds; d=5 ≈ 9×10³ shots | Zenodo API + Bluvstein 2025 p. 23 |
| Zenodo 19339056 | QuEra theory | processed simulation data for the Pauli-envelope paper | 1.9 MB | Zenodo API |
| Zenodo 13273331, 6804040 | Google Willow / Sycamore | already used by C3 (null) | 112 GB /, | prior sessions |
| Quantinuum, AWS Ocelot, Atom Computing, Alice & Bob, Yale dual-rail, IQA |, | **no public syndrome data** ("upon request" or no statement) |, | pages read |

---

## 5. Ranked recommendation and first experiments

### Rank 1, IBM Nighthawk surface code (Zenodo 23335425)

Why first: it is the only candidate where the hidden state is long-lived, unheralded, a double-digit share of the error, and public, the exact regime C3's simulator was validated in.

First experiment (three steps, no new hardware):

1. **Fingerprint test, model-free** (same tools as `willow_diagnostics`): per-round detection fraction for d = 3 and d = 5 at t = 50 (expect a rise, as Kan 2026 saw on `ibm_phoenix`); time-correlation of detector pairs that share a data qubit at lags 1 to 20 vs pairs that do not (Kan's Fig. 10f on public data); run-length distribution of consecutive firings of the 2 to 4 detectors around each data qubit against a round-shuffled null. This decides whether episodes are multi-round and estimates τ. Fit C3's phenomenological (p_L, τ) to the rise as done for Sycamore in `fit_leakage.json`.
2. **Simulator changes to `leakage_sim.py`** (via `leakage_sim_real.py`'s `LeakyCircuitReal`): (a) IBM circuit, rotated surface code with CZ layers on a square lattice, ≈ 2 μs rounds; (b) **no reset of measure qubits**, detectors compare outcomes two rounds apart, which changes the detector graph and means a leaked measure qubit persists too, add a second HMM class for measure qubits (Varbanov 2020 did this with analog readout; here syndrome-only); (c) transport p_t ≈ 0 (fixed-frequency CZ; treat as a swept parameter 0 to 0.1 because it is not measured); (d) no DQLR; (e) background Pauli rates from the shipped p_ij DEMs so the background detection fraction matches the data (0.14 to 0.17 was the killer on Sycamore; the IBM value must be measured first). Then compute the **oracle ceiling**: MWPM with perfect per-round leakage flags vs MWPM with the shipped p_ij DEM at the fitted (p_L, τ). If the oracle removes < 5 % of ε, stop, same scope-null as Willow.
3. **Real-data decoding**: baselines = MWPM on the shipped p_ij DEM and belief matching; C3 HMM-soft and CNN-soft trackers trained on the matched simulator; pre-registered held-out split by duration (tune on t = 20, test on t = 30, 50), shuffled-round placebo, Holm correction, the `adaptive_protocol.md` rules. The GNN-RNN numbers (1.47 % vs 2.79 % at d = 3) are the published upper reference for "how much a learned decoder recovers".

Oracle ceiling estimate before any run: IBM 2026's 12 to 21 % post-selection gain is a lower bound on the leakage share (it only removes shots flagged with ≥ 90 % confidence at readout); the Kan 2026 doubling of ε between round 10 and round 100 suggests the persistent component is comparable to the Pauli floor in long memories. A tracker recovering C3's typical 0.4 to 0.7 of the oracle would then be worth 5 to 15 % of ε at t = 50, above the ±1.5 % resolution of 10⁵ shots.

Fallback if the public file is insufficient: collect a d = 3 memory on IBM cloud with `meas_level=1` so that an IQ-based 3-state herald exists for validation (as in Hanisch 2024), and compare inferred flags with the herald, the transmon version of Nishio's inference-vs-LDU test.

### Rank 2, Harvard/QuEra atom loss (Zenodo 15685795)

Why second: the hidden state and the fingerprint are textbook, the data are public and come with the authors' own decoder notebook, but the herald exists at the end of each shot and is already used, so the deliverable is a comparison, not a new gain.

First experiment:

1. Load the raw 0/1/loss shots and reproduce the paper's three numbers with the notebook (conventional decoding; loss-aware; 1.73× with ML).
2. **Simulator changes to `leakage_sim.py`**: replace the transmon model (partner depolarisation, transport, return with random Pauli) by the atom-loss model: a lost data qubit has all subsequent CZ gates removed (identity on the partner), never returns, and reads out as "loss" at the end; loss probability per CZ and per move taken from the paper's released error model (arXiv ancillary files). Episode lifetime is infinite, so the HMM has an absorbing state. Only 4 rounds: use the forward filter and a fixed-lag smoother with lag ≤ 2.
3. Four decoders on the same shots: (A) MWPM, no loss information; (B) delayed-erasure MWPM with the final-readout loss flags (Baranes App. C), this is the **hardware-herald reference**; (C) C3 soft tracker with no flags; (D) tracker + flags (the tracker adds the loss *time*). The **oracle ceiling** is the simulator run with perfect per-round loss knowledge; Baranes Fig. 2b predicts (D) ≈ (B), so the scientific result is the fraction (C)/(B), the first hardware test of syndrome-only loss inference against a real herald. Also test the ≥ 80 % claim: shots whose flicker pattern the tracker flags but whose final readout shows no loss are the non-loss leakage.

### Honest "already done / no data" list

- Neutral-atom loss **with** the delayed herald: done (Bluvstein 2025, Baranes 2026, Liu 2026, Perrin 2026, Atom Computing 2026).
- Syndrome-only loss inference as an idea: done in theory (Nishio 2026, Wang 2026); not done on hardware with a soft-weight MWPM, that is the Rank-2 gap.
- Trapped-ion leakage: best physics, no public syndromes; Quantinuum states the gap themselves.
- Cat / dual-rail / fluxonium erasure qubits: heralded by construction; nothing to infer.
- GKP ancilla leakage: real multi-cycle state, wrong code family, tiny share.
- Spin qubits and photonics: no multi-round syndrome data (spins) or no persistent state (photons).

---

## 6. Deviations and limits

1. **Reading depth.** Full text was read for Kan 2026 (2610.23840) and Quantinuum 2026 (2610.24077). All other 2026/2025 papers were read as alphaXiv page extracts selected by five fixed questions (typically 6 to 10 pages per paper); "not in pages read" in `platform_survey.csv` means exactly that, not absence from the paper. Papers marked "prior session" in `platform_papers.csv` were not re-read. Two spin-qubit papers and the photonics claim rest on discovery listings or general knowledge only.
2. **Quote verification.** The quotes used in this report were matched verbatim (after whitespace/ligature normalisation) against the extracted page text; three carry PDF line-break hyphens in the source ("era-sures", "re-set", "per-sist") that are removed here.
3. **IBM leakage lifetime in rounds** is an estimate from T1 and round time, not a measurement; it is the first quantity the Rank-1 experiment must produce.
4. **Public-data searches** used two web searches per platform plus the Zenodo API for the three records named above; absence of a data release for Quantinuum, AWS, Atom Computing and Alice & Bob is based on their papers' data statements (or lack of one) and is provisional.
5. **Alice & Bob repetition-code experiment**: none found in the alphaXiv index for 2024-06 to 2026-10; if one exists outside arXiv it was missed.
6. No simulations or decoding runs were performed (as instructed); all "oracle ceiling" statements are estimates from published numbers.


## Correction (21 Oct 2026)
An audit found that the Quantinuum repump figure was misread as per-round. The paper reports 6.5(1)× suppression after three cycles (residual 0.153). Assuming geometric decay, the per-round survival is ≈ 0.53 and the mean episode ≈ 2.1 rounds, not 1.2. This makes multi-round leakage on Helios somewhat more relevant to C3 than the original text said; the platform still scores low because no syndrome data are public.
