> Working note, written during the project and kept for the record. It may use project shorthand and may contain numbers that were later corrected. `results/facts.md` supersedes it wherever they differ.

# Prior-art check for C3: syndrome-inferred leakage flags as imperfect erasures for matching

Prepared 2026-10-15 for a 4th-year ECE student (first QEC course). Every paper was verified on the arXiv API (export.arxiv.org); 'peer-reviewed' means arXiv's record carries a DOI/journal reference (plus the earlier verified survey for two older DOIs). 'Fact' = what the paper did; 'Opinion' = my reading. Sub-claims: S1 syndrome-only leakage detection; S2 matching with imperfect flags (recall/precision); S3 flag delay / decoder latency; S4 soft posterior edge weights; S5 inferred flags vs hardware heralds; S6 public leakage models and simulators.

## Plain-language summary

- A 'flag' is a bit (or a probability) that says 'this qubit was leaked in this round'. Hardware can produce it (3-state readout, erasure checks); software can infer it from the pattern of failed parity checks (that is C3).
- Matching decoders use the flag by lowering the weight (the 'cost') of the error edges around the flagged qubit, so the decoder is more willing to blame that qubit.
- The literature already has: (1) the HMM idea for inferring leakage from syndromes [Varbanov 2020]; (2) matching with perfect or hardware flags [Suchara 2015, Riverlane LCD 2025]; (3) decoders that handle a flag that arrives late [Baranes 2026 and others, for atom loss]; (4) imperfect hardware flags [Chang 2025, LCD 2025]. It does NOT have: a per-round leakage posterior turned into soft weights; a recall x precision x lag map for an inferred transmon-leakage flag; a transmon comparison of inferred flags against hardware heralds.

## Papers (one entry each)

### A. Syndrome-only detection of leakage or loss (S1)

#### [2002.07119] Leakage detection for a transmon-based surface code
- **First author / year:** B. M. Varbanov et al., 2020  
- **Status:** peer-reviewed - npj Quantum Information 6, 102 (2020)  
- **DOI:** 10.1038/s41534-020-00330-w  
- **Touches:** S1, S4, S6  
- **How read:** full text (PDF)

**What they did (fact):** Density-matrix simulation of the distance-3 transmon surface code (Surface-17) with a CZ-gate leakage model. Shows that a leaked data qubit makes its neighbouring stabilizers anticommute, so their defect rate rises locally; a leaked ancilla spreads errors to neighbours. Builds one two-state hidden Markov model (HMM) per qubit. Data-qubit HMMs use only the defect history of neighbouring stabilizers; ancilla-qubit HMMs additionally use the analog (soft) readout of that ancilla. Reports an average detection delay of about 1 QEC cycle for data qubits and at most 2 cycles for ancillas, HMM 'optimality' (area under precision-recall curve relative to the oracle) of about 74% for data qubits and 96% for ancillas with analog readout. The HMM posterior is used only for post-selection, discarding about 47% of runs.

**What they did NOT do (fact, with respect to C3):** Did not use the HMM posterior inside a decoder ('we do not consider a leakage-aware decoder in this work'). Did not go beyond d=3 or beyond a density-matrix simulator. Did not study how detection recall, precision or delay change the logical error rate. Did not consider a fixed-lag smoother or decoder commit latency.

#### [1905.12731] Protecting quantum entanglement from leakage and qubit errors via repetitive parity measurements
- **First author / year:** C. C. Bultink et al., 2019  
- **Status:** peer-reviewed - Science Advances 6, eaay3050 (2020)  
- **DOI:** 10.1126/sciadv.aay3050  
- **Touches:** S1  
- **How read:** abstract + discussion section (web)

**What they did (fact):** Experiment on two transmons protected by up to 26 repeated parity measurements. An HMM reading only the parity-outcome record detects when a qubit has leaked; detected leakage is removed by post-selection and Pauli errors by frame updates. Argues HMM cost grows linearly with system size because each HMM only needs local syndromes.

**What they did NOT do (fact, with respect to C3):** No surface code, no decoder re-weighting, no requirement map (recall/precision/delay versus logical error).

#### [2607.29603] Qubit Loss Inference with Stabilizer Codes without Leakage Detection Units
- **First author / year:** Shin Nishio et al., 2026  
- **Status:** preprint - arXiv (Jul 2026, v2 Aug 2026)  
- **DOI:** none (arXiv only)  
- **Touches:** S1, S5  
- **How read:** full text (PDF)

**What they did (fact):** Theory and simulation for qubit LOSS (atoms, ions) without leakage-detection units. Proves a condition for when loss is detectable from syndromes: after removing the lost qubit, some stabilizer checks start to anticommute, so their outcomes become random. Formulates loss inference as 'find the loss pattern that explains the set of random checks' (maximum likelihood, relaxed to minimum set cover with a greedy heuristic, plus a 'signature-recall' score with an analytic threshold 2/3+0.05). Evaluates on the rotated surface code (d=3-9) under trapped-ion and neutral-atom circuit noise. Protocols are compared with an idealised erasure oracle and a noisy hardware LDU; inference beats the noisy LDU at low-to-moderate loss rate (crossover near p_loss ~ 1e-3, LDU better above ~5e-3). Reports recall and precision of the inference (e.g. recall 1.0, precision rising from 0.60 at d=3 to 0.91 at d=9 for one protocol) and how an inference window W trades recall against delay.

**What they did NOT do (fact, with respect to C3):** The classifier is OFFLINE: it averages detector flip rates over an ensemble of repeated shots ('300 trials x 1000 shots'), not a single-shot online tracker; the authors list single-shot online inference as future work. The inferred locations are used to RELOAD atoms, not to re-weight a decoder; combining inference with a decoder is listed as future work. Superconducting leakage is explicitly excluded because a leaked transmon does not satisfy their non-entangling-gate assumption. No soft/posterior weights.

#### [2604.14269] AI-Enabled Decoding of Qubit Loss for Quantum Error-Correcting Codes
- **First author / year:** Yuqing Wang et al., 2026  
- **Status:** preprint - arXiv (Apr 2026, v. May 2026)  
- **DOI:** none (arXiv only)  
- **Touches:** S1, S4, S3  
- **How read:** full text (PDF)

**What they did (fact):** Spatio-temporal graph neural network (STGNN) decoder for atom-array qubit loss with two heads: predict the logical correction and locate lost qubits from the stabilizer 'flicker'. At d=5 it beats MWPM and a delayed-erasure MWPM that receives loss flags from the final round. Locates more than 90% of losses after ten subsequent rounds; losses in the last round are missed more than 85% of the time, which the authors attribute to latency (too few rounds of evidence). Inference time of STGNN vs a modified recurrent AlphaQubit is compared.

**What they did NOT do (fact, with respect to C3):** Atom loss (gate-removal model), not transmon leakage; black-box network, no explicit posterior -> edge-weight rule; no curve of logical error versus flag recall, precision or delay; no comparison with a hardware herald; no simulation on a Pauli+-like transmon model.

#### [2309.13143] ERASER: Towards Adaptive Leakage Suppression for Fault-Tolerant Quantum Computing
- **First author / year:** Suhas Vittal et al., 2023  
- **Status:** peer-reviewed - IEEE/ACM MICRO 2023  
- **DOI:** 10.1145/3613424.3614251  
- **Touches:** S1  
- **How read:** abstract + prior survey notes

**What they did (fact):** Computer-architecture paper. 'Speculates' which qubits have leaked from patterns of failed parity checks and applies leakage-reduction circuits only to them; a '+M' variant adds three-state measurement. Reports logical-error improvements of up to 4.3x and 23x versus always-on LRCs (abstract).

**What they did NOT do (fact, with respect to C3):** The speculation is a hand-made rule used to schedule hardware LRCs, not to change decoder weights. No recall/precision/delay-versus-logical-error curves for a decoder.

#### [2510.25661] Accurate Leakage Speculation for Quantum Error Correction
- **First author / year:** Chaithanya Naik Mude et al., 2025  
- **Status:** peer-reviewed - IEEE/ACM MICRO 2025  
- **DOI:** 10.1145/3725843.3756053  
- **Touches:** S1  
- **How read:** full text (PDF, targeted sections)

**What they did (fact):** 'Gladiator': builds an offline error-propagation graph (calibrated with IBM 7-qubit leakage-injection data) and classifies each syndrome online in nanoseconds as leakage-dominated or not; triggers LRCs only then. Reports 3.11x fewer combined false positives + false negatives than ERASER at d=11, 1.7-3.9x speedups and 16% lower logical error (abstract and Sec. 4). Uses Stim's tableau simulator to simulate leakage.

**What they did NOT do (fact, with respect to C3):** Still a trigger for LRCs; the paper contains no edge re-weighting, no MWPM/PyMatching use of the speculation, and no leakage posterior. Flag delay is discussed only qualitatively ('cost of delaying detection').

### B. Leakage/erasure-aware matching, imperfect flags, soft weights (S2, S4, S5)

#### [1410.8562] Leakage Suppression in the Toric Code
- **First author / year:** Martin Suchara et al., 2014  
- **Status:** peer-reviewed - Quantum Information and Computation 15, 997 (2015); also IEEE ISIT 2015  
- **DOI:** 10.26421/qic15.11-12-8  
- **Touches:** S2, S3, S4  
- **How read:** abstract + HL-decoder paragraph (web); prior survey notes

**What they did (fact):** Monte-Carlo study of leakage in the toric code with a classical leaked-flag model. Introduces the 'Heralded Leakage (HL)' decoder that takes three-outcome measurements (0, 1, L): when an L is seen the decoder only knows the qubit leaked somewhere between its initialisation and that measurement, and it builds a new matching graph whose edge weights near the L event come from a table of conditional error probabilities. Threshold loss from leakage drops from < 4x to about 2x when the decoder has the 3-outcome information (abstract).

**What they did NOT do (fact, with respect to C3):** Flags are perfect (no false negatives/positives) and come from hardware readout; time uncertainty is only within one qubit lifetime; no syndrome-inferred flags; no recall/precision sweep; not a transmon Pauli+ model.

#### [2411.10343] Local Clustering Decoder as a fast and adaptive hardware decoder for the surface code
- **First author / year:** Abbas B. Ziad et al., 2024  
- **Status:** peer-reviewed - Nature Communications 16, 11048 (2025)  
- **DOI:** 10.1038/s41467-025-66773-x  
- **Touches:** S2, S4, S5  
- **How read:** full text (PDF)

**What they did (fact):** Riverlane's Local Clustering Decoder (FPGA Union-Find). An 'adaptivity engine' maps each HERALDED leaked-qubit measurement to a precomputed set of sensitive edges that are 'pregrown' (equivalent to setting their weight to 0). Noise model: SI1000 plus leakage (CZ leakage p_l, relaxation), patch-wiggling LRU so leakage lives at most two rounds. Heralding is imperfect: a false-negative probability equal to the measurement error (5p) is included; false positives are assumed negligible. With leakage dominant (p = p_l = 5e-4), Lambda improves from 2.12 to 3.85 with adaptivity (Fig. 3). Discussion says weighted adaptivity maps and weighted leakage-aware decoding are future work.

**What they did NOT do (fact, with respect to C3):** Herald comes from hardware readout, not from the syndrome. False-negative rate is fixed at 5p, not swept; no recall/precision/delay requirement map. Unweighted (0/1) edges, so no soft posterior weights. Herald arrives at measurement time; no study of herald lag beyond the two-round lifetime model.

#### [2408.00842] Surface Code with Imperfect Erasure Checks
- **First author / year:** Kathleen Chang et al., 2024  
- **Status:** peer-reviewed - PRX Quantum 6, 040355 (2025)  
- **DOI:** 10.1103/d1v7-nctj  
- **Touches:** S2, S3  
- **How read:** full text (PDF, targeted sections)

**What they did (fact):** Surface-code simulations (unrotated code, weighted Union-Find) with IMPERFECT hardware erasure checks for superconducting dual-rail qubits. Imperfections modelled: false negatives (erasure fraction R_e = 0.96-0.98 observed in experiments), imperfect spatial resolution (flag says 'one of the two gate qubits leaked'), and imperfect temporal resolution eta (a flag after a gate came from that gate with probability eta, or from the previous gate with 1-eta; eta = 0.95-0.99 in experiments). Shows how to calibrate the decoder's detector error model for these cases. Threshold stays at least 2x the Pauli-noise threshold; false negatives with a depolarising leaked-partner model degrade the effective distance; a 'tailored' partner-error model keeps effective distance ~2x.

**What they did NOT do (fact, with respect to C3):** Flags are hardware checks (dual-rail), not inferred from syndromes. Temporal uncertainty is only one gate step, not several QEC rounds. No false-positive (precision) sweep reported in the parts read. Not a transmon-leakage (|2>) model with leakage transport.

#### [2208.05461] Erasure qubits: Overcoming the $T_1$ limit in superconducting circuits
- **First author / year:** Aleksander Kubica et al., 2022  
- **Status:** peer-reviewed - Physical Review X 13, 041022 (2023)  
- **DOI:** 10.1103/PhysRevX.13.041022  
- **Touches:** S2  
- **How read:** abstract + earlier novelty note

**What they did (fact):** Proposes superconducting erasure qubits (dual-rail transmons) and simulates the surface code under circuit noise where T1 decay is converted to a detected erasure. Discusses imperfect erasure detection qualitatively: a missed erasure acts as a Pauli error, a false flag as an unnecessary erasure.

**What they did NOT do (fact, with respect to C3):** No quantitative recall/precision/delay map; detection is a hardware check, not inferred. (Imperfect-detection content known from the earlier novelty note and abstract; full text not re-read here.)

#### [2411.16228] Soft information decoding with superconducting qubits
- **First author / year:** Maurice D. Hanisch et al., 2024  
- **Status:** peer-reviewed - APS Open Science 1, 000019 (2026)  
- **DOI:** 10.1103/y9fh-4x6n  
- **Touches:** S4, S5  
- **How read:** abstract + Sec. II.6/III.E (web)

**What they did (fact):** Experiment on IBM transmon devices: repetition codes up to T = 100 rounds decoded with PyMatching using soft (IQ) readout information. Leakage is detected from the IQ plane (a point whose likelihood under both computational-state Gaussians is below 1% is declared 'leaked'); a leaked ANCILLA measurement is declared maximally ambiguous (flip probability 0.5), which sets the weight of the corresponding distance-two time edge to zero. Reports that soft decoding plus this leakage handling improves Lambda over hard decoding.

**What they did NOT do (fact, with respect to C3):** The leakage flag comes from the readout signal, not from the syndrome history; it is a hard flag (weight exactly 0), not a posterior; only ancilla leakage, only repetition codes; no requirement map.

#### [2511.17460] Improved error correction with leakage reduction units built into qubit measurement in a superconducting quantum processor
- **First author / year:** Yuejie Xin et al., 2025  
- **Status:** peer-reviewed - PRX Quantum (2026)  
- **DOI:** 10.1103/y66v-988s  
- **Touches:** S5  
- **How read:** abstract + introduction (web) and prior survey notes

**What they did (fact):** Experiment (Delft): a leakage-reduction unit built into transmon measurement gives three-level readout (3RO) whose |f> outcome heralds a leakage event on a measure qubit at a known round. Detection events plus these hardware leakage flags are fed to a neural-network decoder for a d=3 repetition code and a 7-qubit stability experiment; LRU + 3RO gives the best logical performance without post-selection.

**What they did NOT do (fact, with respect to C3):** Flags are hardware heralds on measure qubits; no syndrome-inferred flags; neural decoder, not matching with explicit weights; no recall/precision/delay study; d=3 only.

#### [2310.05900] Learning to Decode the Surface Code with a Recurrent, Transformer-Based Neural Network
- **First author / year:** Johannes Bausch et al., 2023  
- **Status:** peer-reviewed - Nature 635, 834 (2024)  
- **DOI:** 10.1038/s41586-024-08148-8  
- **Touches:** S4, S5, S6  
- **How read:** appendix sections (web) + prior survey notes

**What they did (fact):** AlphaQubit: recurrent transformer decoder trained on Pauli+ simulations and fine-tuned on Sycamore data. On simulated d<=11 data with leakage, cross-talk and soft I/Q readout, it beats correlated matching. Appendix A.1.9 describes the Pauli+ leakage model used (CZ-dephasing leakage reduced to 2e-4 from 8e-4, heating rate 1/(700 us), DQLR, multi-level reset, passive decay). Appendix B.3 describes 'soft matching' (per-measurement posterior -> instance-specific measurement-error edge probabilities) and states that comparison to a leakage-aware matching decoder that re-weights edges on leakage detections is left to future work.

**What they did NOT do (fact, with respect to C3):** Does not isolate how much of its gain comes from leakage information (no ablation read here); does not build an explicit leakage posterior -> edge weight rule; leakage information enters as readout-derived input features.

#### [2504.03504] Reducing quantum error correction overhead using soft information
- **First author / year:** (Riverlane / Univ. authors; see arXiv 2504.03504) et al., 2025  
- **Status:** peer-reviewed - Quantum Science and Technology (2026)  
- **DOI:** 10.1088/2058-9565/ae4e55  
- **Touches:** S4  
- **How read:** conclusion section (web)

**What they did (fact):** Simulation study (Riverlane-affiliated) of soft-information decoding with a Union-Find/LCD decoder, showing reduced QEC overhead from analog readout. The conclusion explicitly names as an open question how 'probabilistic leakage flags determined during the classification process' could be used to decode superconducting QEC experiments.

**What they did NOT do (fact, with respect to C3):** No leakage decoding is performed; the statement is a direct, dated (2025) acknowledgement that soft leakage flags in a decoder are open.

### C. Flag delay and time-uncertain erasures (S3)

#### [2502.20558] Leveraging Qubit Loss Detection in Fault Tolerant Quantum Algorithms
- **First author / year:** Gefen Baranes et al., 2025  
- **Status:** peer-reviewed - Physical Review X 16, 011002 (2026)  
- **DOI:** 10.1103/ycwc-3myc  
- **Touches:** S3, S4  
- **How read:** full text (PDF, targeted sections)

**What they did (fact):** Introduces the 'delayed-erasure decoder' for qubit loss detected late (e.g. only at the final state-selective readout). For each flagged qubit it adds to the detector error model all the places along the qubit's lifetime where the loss could have happened, each with its probability and syndrome, and decodes with MLE (or MWPM, Appendix C). Key result read: at d=5 with 1% loss per entangling gate, the delayed-erasure decoder with NO information about the loss moment performs comparably to a decoder given the exact loss time (Fig. 2b).

**What they did NOT do (fact, with respect to C3):** Loss model is 'gate removed' (atom arrays), not transmon leakage with partner depolarisation and transport; the flag is a hardware herald, not inferred; the decoder is MLE-centred (MWPM only in an appendix); no false-positive/false-negative sweep of the herald.

#### [2603.04156] Low-Overhead Surface Code with Delayed Atom-Loss Detection via Pauli Envelope
- **First author / year:** Pengyu Liu et al., 2026  
- **Status:** preprint - arXiv (Mar 2026)  
- **DOI:** none (arXiv only)  
- **Touches:** S3, S4  
- **How read:** full text (PDF, targeted sections)

**What they did (fact):** QuEra 'Pauli envelope' framework for delayed atom-loss detection. Bounds the effect of a loss by a low-weight Pauli error set, proves loss-distance guarantees, and proposes an Envelope-MLE decoder (d_loss ~ d) and an Envelope-Matching decoder (d_loss ~ 2d/3, via MWPM). Notably, Envelope-Matching does NOT set affected edge weights to a constant (0); it rescales them by a constant factor, arguing that constant weights become negligible relative to Pauli weights when p_Pauli -> 0. Mentions dual-rail superconducting qubits as a future target and the envelope as a feature for ML decoders.

**What they did NOT do (fact, with respect to C3):** Atom loss with delayed hardware detection; no inferred flags; no recall/precision sweep; the re-weighting factor is a fixed design constant, not a per-event posterior.

#### [2607.29443] Erasure surface code circuit without mid-circuit erasure checks
- **First author / year:** Margaret Pavlovich et al., 2026  
- **Status:** preprint - arXiv (Jul 2026)  
- **DOI:** none (arXiv only)  
- **Touches:** S3, S6  
- **How read:** full text (PDF, targeted sections)

**What they did (fact):** Yale study of erasure-like surface-code performance WITHOUT mid-circuit erasure checks, using only three-state readout at measurement time (plus a 'moonwalking' circuit). Because a qubit leaks at most once between checks, the leakage time is a disjoint (mutually exclusive) distribution, which they show cannot be captured by a single standard detector error model; they build per-pattern DEMs using 'Pauli envelopes'. Ships open-source code (github.com/magzpavz/surface-code-leakage-erasure) built on Stim and a fork of PyMatching, with selectable leaked-qubit effects and erasure-check schedules (every gate, every other slice, once per round, 3-state readout only).

**What they did NOT do (fact, with respect to C3):** Erasure checks and 3-state readouts are assumed perfect (100% fidelity) in the main results; no syndrome-inferred flag; no transmon leakage transport; no recall/precision/delay requirement map.

#### [2603.24237] Correlated Atom Loss as a Resource for Quantum Error Correction
- **First author / year:** Hugo Perrin et al., 2026  
- **Status:** preprint - arXiv (Mar 2026)  
- **DOI:** none (arXiv only)  
- **Touches:** S3  
- **How read:** abstract only

**What they did (fact):** Surface code with teleportation-based loss-detection units under partially correlated atom loss; introduces a decoding strategy that uses loss correlations to convert the delayed-erasure channel into an erasure channel (abstract).

**What they did NOT do (fact, with respect to C3):** Atom loss, hardware detection units, no inferred flags, no requirement map.

### D. Hardware heralds and herald imperfections (S5, S2)

#### [2607.17204] Heralded Leakage Detection with Preserved Computational-State Coherence in a Fixed-Frequency Transmon
- **First author / year:** Takeaki Miyamura et al., 2026  
- **Status:** preprint - arXiv (Jul 2026)  
- **DOI:** none (arXiv only)  
- **Touches:** S5  
- **How read:** abstract + intro (web)

**What they did (fact):** Experimental scheme for heralded leakage detection on a fixed-frequency transmon using only standard dispersive-readout hardware, preserving computational-state coherence; motivated as a flag for the decoder (abstract/intro).

**What they did NOT do (fact, with respect to C3):** No QEC experiment and no decoder; a hardware-herald building block only.

#### [2112.03708] Realizing Repeated Quantum Error Correction in a Distance-Three Surface Code
- **First author / year:** Sebastian Krinner et al., 2021  
- **Status:** peer-reviewed - Nature 605, 669 (2022)  
- **DOI:** 10.1038/s41586-022-04566-8  
- **Touches:** S5  
- **How read:** Appendix C paragraph (web)

**What they did (fact):** ETH d=3 surface code experiment using three-state readout to reject runs with detected leakage in post-processing; rejected fraction about 8% per cycle (Appendix C).

**What they did NOT do (fact, with respect to C3):** Post-selection only; no decoder use of the flag.

#### [2608.21961] Surface-Code Quantum Error Correction for Molecular Tweezer Arrays: Encoding, Layout, and Correlated Noise
- **First author / year:** Niharika Verma et al., 2026  
- **Status:** preprint - arXiv (Aug 2026)  
- **DOI:** none (arXiv only)  
- **Touches:** S2  
- **How read:** abstract + Sec. V paragraph (web)

**What they did (fact):** Surface-code simulation for molecular tweezer arrays; Section V sweeps the fraction f of losses that are NOT heralded (silent losses receive a random Pauli but no zero-weight edge) and shows how the architectures degrade with f.

**What they did NOT do (fact, with respect to C3):** Molecular loss, hardware heralds; recall-only sweep; no precision or delay; no inferred flags.

### E. Public leakage models, parameters and simulators (S6)

#### [2207.06431] Suppressing quantum errors by scaling a surface code logical qubit
- **First author / year:** Rajeev Acharya et al., 2022  
- **Status:** peer-reviewed - Nature 614, 676 (2023)  
- **DOI:** 10.1038/s41586-022-05434-1  
- **Touches:** S6  
- **How read:** supplement paragraphs (web) + prior survey notes

**What they did (fact):** Google d=3/d=5 surface code. Supplement defines the 'Pauli+' simulator and its leakage model: heating |1>->|2>, CZ-gate dephasing leakage |11><->|02> with Kraus amplitude p_t = 8e-4 (median of isolated CZ characterization), and leakage transport from numerically calibrated CZ unitaries (|22><->|13>, |21><->|03>). Pauli+ reproduces detection probabilities and pair correlations better than a Pauli model.

**What they did NOT do (fact, with respect to C3):** Pauli+ source code is not released (not found in this search either); numbers are device-specific medians.

#### [2408.13687] Quantum error correction below the surface code threshold
- **First author / year:** Rajeev Acharya et al., 2024  
- **Status:** peer-reviewed - Nature 638, 920 (2025)  
- **DOI:** 10.1038/s41586-024-08449-y  
- **Touches:** S6  
- **How read:** paper (web) + prior survey notes (full text read in earlier session)

**What they did (fact):** Google d=7 below-threshold experiment with DQLR every cycle. Supplement's Pauli+ model includes heating, CZ leakage, transport |12>->|30>, and imperfect DQLR (P2->1 = 1, P3->2 = 0.5, P3->1 = 0.5 in simulation). Leakage and stray interactions are estimated at 17% of the error budget. Without DQLR, simulated Lambda saturates near 1 at large distance.

**What they did NOT do (fact, with respect to C3):** No leakage-aware decoder; code not public.

#### [2211.04728] Overcoming leakage in scalable quantum error correction
- **First author / year:** Kevin C. Miao et al., 2022  
- **Status:** peer-reviewed - Nature Physics 19, 1780 (2023)  
- **DOI:** 10.1038/s41567-023-02226-w  
- **Touches:** S6  
- **How read:** prior survey notes (full text read in earlier session) + web excerpts

**What they did (fact):** Google DQLR paper. Measured leakage transport in a calibrated CZ: about 18% of |30> population moves to |12> and vice versa, about 61% for |31><->|22>; a spurious phase ~0.65 pi on the partner when the high-frequency qubit is in |2>. Injected |2> on a data qubit decays with a time constant of about 4.4 cycles without removal; DQLR holds data-qubit leakage near 1e-3.

**What they did NOT do (fact, with respect to C3):** Hardware paper; no decoder; model parameters are given as measurements, not as a released simulator.

#### [2102.06131] Removing leakage-induced correlated errors in superconducting quantum error correction
- **First author / year:** M. McEwen et al., 2021  
- **Status:** peer-reviewed - Nature Communications 12, 1761 (2021)  
- **DOI:** 10.1038/s41467-021-21982-y  
- **Touches:** S6  
- **How read:** prior survey notes (full text read in earlier session)

**What they did (fact):** Google multi-level reset in a 21-qubit bit-flip code; shows the detection-event tail after injected leakage and that leakage moves from data to measure qubits via the CZ resonance.

**What they did NOT do (fact, with respect to C3):** No decoder, no leakage flags.

#### [2312.10277] Incoherent Approximation of Leakage in Quantum Error Correction
- **First author / year:** Jeffrey Marshall et al., 2023  
- **Status:** peer-reviewed - Physical Review Applied 23, 054025 (2025)  
- **DOI:** 10.1103/PhysRevApplied.23.054025  
- **Touches:** S6  
- **How read:** abstract + Sec. III + App. F (web)

**What they did (fact):** Marshall & Kafri (NASA/Google): Subspace Twirling Approximation (STA) that makes leakage incoherent so it can be simulated cheaply; shows coherence between computational and leaked subspaces decays exponentially with stabilizer rounds. Appendix F gives a physically motivated parameter set: CZ leakage p = 4e-4, heating timescale 500 us, |2> lifetime 10 us, T1 = 20 us, T_phi = 40 us, 1.1 us per round.

**What they did NOT do (fact, with respect to C3):** A simulation-method paper; no detection, no decoder flags.

#### [2308.08186] Efficient Simulation of Leakage Errors in Quantum Error Correcting Codes Using Tensor Network Methods
- **First author / year:** Hidetaka Manabe et al., 2023  
- **Status:** peer-reviewed - New Journal of Physics (2025)  
- **DOI:** 10.1088/1367-2630/ae1529  
- **Touches:** S6  
- **How read:** abstract + Sec. V.2 (web) + prior survey notes

**What they did (fact):** MPS simulation of leakage (coherent and incoherent) in repetition and thin surface codes; warns that twirled (incoherent) approximations can substantially overestimate the logical error rate relative to coherent leakage.

**What they did NOT do (fact, with respect to C3):** Thin codes only; no detection or decoder flags.

#### [2406.04083] Leakage Mobility in Superconducting Qubits as a Leakage Reduction Unit
- **First author / year:** Joan Camps et al., 2024  
- **Status:** peer-reviewed - Physica Scripta 101, 115107 (2026)  
- **DOI:** 10.1088/1402-4896/ae4dc0  
- **Touches:** S6  
- **How read:** Table I + Sec. (web) + prior survey notes

**What they did (fact):** Riverlane density-matrix study of leakage mobility as an LRU. Table I gives a complete, public transmon leakage parameter set: T1 = T2 = 30 us, CZ 40 ns, measurement 600 ns, reset 500 ns, leakage L1 in {0.1%, 0.5%}, mobility L_m in {0.5%..12.5%}, leakage-conditional phase pi/10; CZ leakage modelled as |11> -> -sqrt(1-4L1)|11> + 2 sqrt(L1)|02>.

**What they did NOT do (fact, with respect to C3):** Small stability patches only; no detection, no flags.

### F. Software (not papers)

- **leakysim (GitHub inmzhang/leaky, PyPI 'leakysim')** (software, no paper): Third-party re-implementation of Google's Pauli+ idea on stim.TableauSimulator; decomposes Kraus operators into 'leaky Pauli channels'. README marks it work-in-progress with breaking changes expected. No paper found.
- **surface-code-leakage-erasure (GitHub magzpavz/ and rjb-14/ mirrors), companion to arXiv 2607.29443** (software with preprint (2607.29443)): Stim + PyMatching-fork package simulating static/walking/moonwalking surface codes with leakage and erasure checks; parameters for leaked-qubit effect (depolarising, tailored, skip-gate) and erasure-check schedule. Requires compiling the PyMatching fork from source.
- **Stim gate documentation (quantumlib/Stim doc/gates.md)** (software documentation): Stim itself has no leakage, but its I_ERROR / II_ERROR instructions accept free-form tags such as I_ERROR[LEAKAGE_NOISE_FOR_AN_ADVANCED_SIMULATOR:0.1], i.e. an official hook for annotating leakage locations in a Stim circuit that an external simulator then interprets. Note that 'sweep-bit injection' (the plan's leakage_sim.py approach) is a different, also legitimate, mechanism.
- **Riverlane Deltakit / QEC Explorer notebook 'Leakage-Aware Decoding with the Local Clustering Decoder'** (software documentation): Public notebook with pre-generated leakage circuits and LCD decoding with/without leakage awareness.

## Sub-claim table

| Sub-claim | Status | Closest ids | One-sentence reasoning |
|---|---|---|---|
| S1: Leakage detection from syndromes only (HMM / neural) in the surface code | **PARTLY DONE** | 2002.07119, 1905.12731, 2607.29603, 2604.14269, 2309.13143, 2510.25661 | The idea 'infer leakage from the defect history with a per-qubit HMM' is Varbanov et al. 2020 (data-qubit HMMs use defects only; ancilla HMMs add analog readout) and was shown experimentally by Bultink et al. 2020; syndrome-only inference of LOSS was formalised in 2026 (Nishio et al., offline multi-shot; Wang et al., GNN). What is not published: a single-shot, online transmon-leakage tracker (filter and fixed-lag smoother) evaluated at d>=5 in a circuit-level (Pauli+-like) model with recall, precision and latency reported as functions of the smoothing lag. C3 can claim the characterisation, not the idea. |
| S2: Leakage/erasure-aware matching with IMPERFECT flags (recall, precision < 1): requirement maps | **PARTLY DONE** | 2408.00842, 2411.10343, 2608.21961, 2208.05461, 1410.8562 | Imperfect HARDWARE flags have been studied: false negatives (Chang et al. 2025 with R_e = 0.96-0.98; LCD with a fixed 5p false-negative rate; molecular arrays with a silent-loss fraction f), and one-gate temporal ambiguity (Chang et al.). No paper sweeps recall AND precision AND delay of a flag for matching under a transmon leakage model, and none does it for a syndrome-inferred flag whose errors are correlated with the syndrome itself (which is the realistic case for C3). The pilot's observation that false positives are cheap for matching is consistent with, but not stated in, these papers. |
| S3: Effect of flag DELAY / decoder latency on the value of leakage or erasure information | **PARTLY DONE (and the pilot's framing needs changing)** | 2502.20558, 2603.04156, 2607.29443, 1410.8562, 2408.00842, 2604.14269 | Delay as 'the flag arrives late and the decoder does not know exactly when the event happened' is well studied for atom loss and 3-state readout: Suchara 2015 spreads the flag over the qubit's lifetime; Baranes et al. 2026 show a delayed-erasure decoder with NO loss-moment information performs about as well as one with the exact time; Liu et al. 2026 and Pavlovich et al. 2026 formalise this with Pauli envelopes and disjoint distributions. Therefore the pilot result 'a one-round delay destroys the gain' holds only for a decoder that mis-attributes the flag to the wrong round; a paper must include a lag-aware baseline (shift or spread the flag over the lag). What remains open is the specific trade-off for an INFERRED flag between smoother lag (better recall/precision) and streaming-decoder commit latency, and whether a fixed-lag smoother can match the hardware herald. |
| S4: Soft / posterior-weighted edge re-weighting from a leakage posterior (not hard flags) | **OPEN** | 2411.16228, 2310.05900, 2603.04156, 2504.03504, 2411.10343, 2107.13589 | All leakage-aware matching found uses HARD flags (edge weight set to 0 or pregrown: Suchara 2015, LCD 2025, Hanisch et al. 2026 from IQ outliers) or a fixed rescaling constant (Liu et al. 2026). Soft weights exist for READOUT uncertainty (Pattison et al. 2021; AlphaQubit's 'soft matching' appendix), and two papers explicitly list the leakage version as future work (AlphaQubit App. B.3; 2504.03504 conclusion 'probabilistic leakage flags'; LCD 'weighted adaptivity maps'). No paper turns a per-qubit per-round leakage POSTERIOR into continuous MWPM edge weights and measures the gain over hard thresholding. |
| S5: Comparison of inferred flags vs hardware heralds (3-state readout, LRU readout, LCD-style heralds) | **PARTLY DONE (done for atom loss, open for transmon leakage)** | 2607.29603, 2411.10343, 2511.17460, 2411.16228, 2607.17204, 2112.03708 | Nishio et al. 2026 compare syndrome inference against a noisy hardware LDU for atom/ion LOSS and find a crossover near p_loss ~ 1e-3 (inference wins below, LDU above) - this is the same question as S5 but for a different error model and an offline classifier. For transmons, hardware heralds exist with known imperfections (3-state readout ~1% false positives per qubit in Krinner 2022; 98.4% removal/99.2% assignment in Xin 2026; LCD's 5p false negatives), but no paper puts an inferred transmon-leakage flag and a hardware herald in the same simulation. |
| S6: Public leakage models and parameters; Stim-compatible leakage simulators 2023-2026 | **DONE (enough public material; official Pauli+ code still not released)** | 2207.06431, 2408.13687, 2211.04728, 2312.10277, 2406.04083, 2607.29443, 2308.08186 | Numbers are public: CZ leakage 8e-4 (Google 2023 supplement) or 2e-4 (AlphaQubit) or 4e-4 (Marshall-Kafri) per CZ; heating 1/(700 us) or 1/(500 us); |2> lifetime ~10 us or decay ~4.4 cycles; transport 18%/61%; DQLR P2->1 = 1, P3->2 = P3->1 = 0.5; L1 in {0.1%,0.5%} and mobility 0.5-12.5% (Camps). Stim-based leakage code exists (leakysim; surface-code-leakage-erasure with a PyMatching fork; Stim's I_ERROR tag hook). Google's own Pauli+ code was not found as a public release. Writing a validated simulator is engineering, not a research claim. |

## Overall verdict

NOT SCOOPED as a whole; SCOOPED ON S1 as an idea (syndrome-only HMM leakage detection is Varbanov 2020 / Bultink 2020, and syndrome-only loss inference is Nishio 2026 / Wang 2026); S3 is heavily pre-empted by delayed-erasure decoders for atom loss (Baranes 2026, Liu 2026, Pavlovich 2026), which also show that the pilot's 'one-round delay kills the gain' is a property of a naive decoder; S4 (posterior -> soft weights) and the joint S2xS3 requirement map for an INFERRED transmon-leakage flag are open; S5 is open for transmons; S6 is a solved resource question.

**What a C3 paper can honestly claim (opinion):**
- The first explicit chain for transmon leakage: syndrome history -> per-qubit per-round leakage posterior (HMM forward filter and fixed-lag smoother, no analog readout) -> continuous MWPM edge weights -> logical error, at d = 3, 5, (7) in a circuit-level leakage model.
- A requirement map of logical error versus tracker recall, precision and lag, with the lag handled by a lag-aware decoder (spread/shift) rather than by wrong-round attribution.
- A head-to-head comparison, in one simulation, of inferred flags against a hardware herald with LCD-style false negatives and 3-state-readout-style false positives, including the crossover leakage rate (analogue of Nishio et al. for transmons).
- An ablation showing how much of the gain comes from (a) soft versus hard flags and (b) smoother versus filter.

**What it must not claim (fact):**
- That HMM leakage detection from syndromes is new (Varbanov 2020).
- That leakage-aware matching is new (Suchara 2015, LCD 2025).
- That delay inherently destroys the value of a flag (contradicted in spirit by Baranes 2026 Fig. 2b and by Suchara 2015's lifetime-window weights).
- That imperfect erasure flags have never been studied (Chang 2025, LCD 2025).

**Scoop risks (opinion):**
- Nishio et al. (Jul 2026) or Wang et al. (Apr 2026) could extend to superconducting leakage quickly; both groups list it as future work.
- The AlphaQubit team has the data and the simulator to do the leakage-aware matching comparison they deferred.
- If the HMM gain over 'ignore flags' is small once a lag-aware decoder and realistic recall are used, the paper's result is a negative map; that is still publishable as a requirement study but weaker.

## Consequence for the pilot result 'D = 1 destroys the gain'

Fact: the pilot attributed a late flag to the wrong round and never told the decoder about the lag. Fact: Suchara et al. 2015 (HL decoder), Baranes et al. 2026 (delayed-erasure decoder, Fig. 2b: no loss-moment information performs about as well as exact time), Liu et al. 2026 and Pavlovich et al. 2026 all handle a late flag by spreading its probability over the possible earlier rounds, and report little loss. Opinion: the paper must therefore report three delay baselines - (i) wrong-round attribution (streaming, lag unknown), (ii) lag-aware shift (lag known exactly), (iii) lag-aware spread over a window - and frame the 'cliff' as a statement about streaming decoders whose rounds are already committed, not about information value.

## Deviations and caveats

- Full text (PDF) was read for 8 papers: 2607.29603, 2002.07119, 2411.10343, 2604.14269, 2408.00842 (targeted sections), 2502.20558 (targeted sections), 2603.04156 (targeted sections), 2607.29443 (targeted sections), plus targeted sections of 2510.25661. All other entries rest on the arXiv abstract, web-visible excerpts and the earlier verified survey notes; numbers from those are from the quoted excerpts only.
- 2208.05461: the 'imperfect erasure detection' content is taken from the earlier novelty note and abstract; the full text was not re-read in this session.
- AlphaQubit leakage ablation (how much of its gain comes from leakage inputs) was not located; only the appendix statements were used.
- 2504.03504: journal status (QST 2026) and DOI were taken from the IOP landing URL seen in search; the arXiv record was not re-queried via the API.
- Discovery used web search; verification used the arXiv API (export.arxiv.org, batched id_list queries). Crossref was not needed because arXiv records carried DOIs/journal refs for all peer-reviewed entries except 1410.8562 (DOI taken from the earlier verified survey) and 2308.08186 (DOI from the earlier verified survey).
- Semantic Scholar / OpenAlex not used. No Google Scholar.
- Date range emphasised 2024-2026; pre-2014 foundational papers (Aliferis-Terhal 2005, Fowler 2013, Ghosh 2013) are covered in the earlier survey artifact and not repeated here.