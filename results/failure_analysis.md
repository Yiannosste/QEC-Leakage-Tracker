# Why the multi-round leakage tracker is null on real hardware, and what time structure Willow does have

*Project C3 → Willow real-signal track. Written 20 Oct 2026 for a 4th-year ECE reader. Every number below comes either from a paper I read in this session (quoted with section, under 20 words) or from one of our own reports (file named). The companion table `papers_read.csv` lists each paper, how it was verified, and its key numbers. No simulations were run for this document.*

---

## 0. One-paragraph summary

Our tracker looks for a data qubit that stays leaked for several rounds and makes its neighbouring stabilisers fire again and again. That pattern is what the HMM and the causal CNN are trained to detect, and it is what sets the soft matching weights. On the two public Google datasets that pattern is either very weak (Sycamore 2023) or essentially absent (Willow 2025), so the tracker has nothing to find. The papers explain why: on Sycamore 2023 the leakage lifetime was already being shortened by CZ transport into the reset measure qubits, and leakage was only a few per cent of the logical error budget; on Willow the data-qubit leakage removal (DQLR) operation empties the leaked state every cycle, leaving about 10⁻³ leaked population that lives for less than one round. What Willow **does** have, according to Google's own supplement and to an independent re-analysis of the released data, is structure **across shots**: hour-scale calibration drift of a few per cent, transient two-level-system (TLS) episodes that make one or two detectors fire three times more often for tens to hundreds of cycles, and rare bursts. None of the published work has yet turned that across-shot structure into a strictly causal, per-shot decoder on Willow data; the closest papers either estimate static DEMs from the same shots they decode, use drift for post-selection, or demonstrate adaptive weights only in simulation. Section 4 turns this into three hypotheses with explicit confirm/kill tests.

---

## 1. Why the leakage tracker is null, our numbers next to the papers' numbers

### 1.1 What the tracker needs

The tracker is a hidden-state estimator. Its evidence for "qubit q is leaked at round t" is a run of rounds in which the two to four stabilisers touching q keep flipping. In our synthetic study this worked (f = 0.60 to 0.93 of the oracle gain at p = 10⁻³; `realism_report.md` Table 2) because three things were true at once:

1. leaked episodes lasted several rounds (mean 5.8 rounds at the centre cell),
2. leakage was most of the error budget (82 to 95 % of logical errors at p = 10⁻³; `real_data_report.md` §5.5), and
3. the background detection fraction was low (0.04 to 0.05), so a run of flips stood out.

On both devices at least two of these three fail.

### 1.2 Sycamore 2023 (Zenodo 6804040)

| quantity | our measurement (`real_data_report.md`) | paper statement (Google 2023, Nature 614) |
|---|---|---|
| background detection fraction | 0.135 to 0.160 per detector (Table 1) | weight-4 stabilisers 0.180 ± 0.013 in Pauli+ simulation, Sec. III |
| rise of detection fraction over the run | +0.006 to +0.020 absolute, rounds 1 → 24 (Table 2) | "relative rise of 12% for distance-5 and 8% for distance-3 over 25 cycles" (Sec. III); Pauli+ reproduces 7 % |
| leaked data-qubit-rounds | 0.24 to 1.2 % (fitted p_L 2.4×10⁻⁴ to 2.1×10⁻³, τ 8 to 32, τ poorly identified above 8) | rise "attribute[d] to data qubits leaking into non-computational excited states" (Sec. III); CZ leakage p_t = 8×10⁻⁴ per gate (Supp. XIV.A.3) |
| leakage removal on data qubits | none modelled explicitly; episodes drained by transport | transport via "|22⟩ ⇐⇒ |13⟩ and |21⟩ ↔ |03⟩" during CZ (Supp. XIV.A.3); measure qubits reset each round |
| leakage share of logical error | oracle B removes 2.9 % (d = 3) / 9.9 % (d = 5) of ε (§5.5) | leakage is one slice of the 1/Λ budget in Fig. 4a (not read as a number here) |
| tracker result | HMM ε-ratio 1.014 [1.006, 1.021] (worse), CNN lag 0 1.007, lag 2 1.008 at d = 3; null at d = 5; static A4 0.995 / 0.986 (§5.1 to 5.2) |, |
| flag quality on hardware | CNN flags 0.05 to 0.42 % of qubit-rounds; after a flag the adjacent detectors fire 0.36 to 0.42 vs 0.15 to 0.17 otherwise (Table 3); simulated recall 0.08 to 0.15, precision 0.60 to 0.75 |, |

Reading. The flags are *real* (adjacent stabilisers really do fire 2.5× more often after a flag), but (i) the tracker catches only ~10 % of episodes, (ii) each episode is worth little because the background fires at 0.15 anyway, and (iii) the whole leakage mechanism is only 3 to 10 % of ε, so even perfect knowledge would help by 3 to 10 %. Our realism study gives the mechanism behind (i): CZ transport into a measure qubit that is reset every round shortens data-qubit episodes. At transport probability p_t = 0.3 per gate the mean episode drops from 5.85 to 1.40 rounds and f(CNN) falls from 0.72 to 0.50, f(HMM) from 0.51 to 0.09 (`realism_report.md` §4). Miao et al. measured exactly this transport on Sycamore: "around 18% of the population of |30⟩ is transported to |12⟩" and "around 61% for |31⟩ ↔ |22⟩" (Sec. II). So the 2023 device was already in the short-episode regime without any dedicated data-qubit reset.

### 1.3 Willow 2025 (Zenodo 13273331, d = 3 patch q6_7, memory-Z, 30 rounds)

| quantity | our measurement (`willow_scope_report.md`) | paper statement |
|---|---|---|
| detection fraction vs round | 0.0763 in rounds 1 to 28; slope −2.4 ± 1.0 ×10⁻⁵ per round (flat) (§3) | Miao 2022, DQLR: "detection probability immediately stabilizes to around 18% and remains steady" (Sec. IV); Google 2025 Fig. S11 notes the rise only *without* DQLR |
| residual leaked population | p_L ≤ 3×10⁻⁴ for lifetimes τ ≥ 2, i.e. ≤ 0.1 % of data-qubit-rounds (95 %); τ = 1 not bounded by the curve, ≲ 3×10⁻³ from the time-pair statistic (§4) | Miao 2022: data qubits "start each cycle with around 1×10⁻³ leakage population" rising to ~5×10⁻³ "immediately following measurement, before it is removed" (Sec. III); DQLR "contains the leakage dynamics to a single cycle" |
| leakage share of 1/Λ | oracle at the 95 % upper limit (T2) removes 4 to 5 % of ε; at T1 (0.79 % leaked, τ = 1) it would remove 55 %, but the data do not contain T1 (flags 0 to 0.15 % vs 0.79 % expected) (§5) | Google 2025 Table S4 (72Q, perfect DQLR assumed): "CZ leakage … 0.022 (5%)", "Leakage (heating) … 0.005 (1%)" of 1/Λ |
| what DQLR buys |, | Google 2025 Sec. III: DQLR gives "a 35% increase in Λ" at d = 5 while "detection probability decreases by only 12%"; Supp. IV.A.2c: without DQLR the simulated "Λ_{d/d+2} saturates to a value around 1" |
| tracker result | all soft decoders −2 % to +1 %, none significant after Holm correction over 12 tests; same decoders recover 22 to 49 % of the oracle gain on the matched simulator (§5) |, |

Reading. Two separate facts make Willow a scope-null by construction. First, the leakage that survives into the next round is bounded to ≤ 0.1 % of qubit-rounds, so the multi-round signature the tracker was built for does not exist; the residual 10⁻³ leakage Miao et al. report lives *inside* one cycle and is removed before the next stabiliser measurement. A one-round episode randomises its four stabilisers once, which is indistinguishable from an ordinary measurement error, and matching already has an edge for that. Second, even if we could flag every residual leaked qubit-round perfectly, Google's own budget says leakage is ~6 % of 1/Λ and our oracle says ≤ 5 % of ε; with 50 000 shots our ratio resolution is ±1.5 %, so a tracker that recovered a realistic half of that would sit at −2 %, right at the edge of detectability. The "τ = 1 is unbounded" caveat does not rescue the idea: at τ = 1 the tracker's own simulated recovery is only 0.22 to 0.49 of a gain that the device shows no sign of carrying (A4 with the T1 leaked fraction *worsens* the real decoder by 0.7 %, p = 0.0008).

### 1.4 Does any published decoder gain from leakage on these datasets?

No. AlphaQubit (Bausch et al. 2024) decoded the real Sycamore 2023 data with binary detector inputs and an even/odd split; its leakage and soft-readout results are on Pauli+ *simulation*, where the leakage flag is derived from the I/Q readout ("post_2 … the probability of having seen leakage", App. A.1.7), i.e. supplied by the hardware, not inferred from syndromes. On that simulation a binary leaked flag "slightly increases the lead" over correlated matching (Sec. 2.3.2) and the soft version more so, and at d = 7 with 0.1 % leakage the ML decoder's error rises "≈ 30%" while leakage-unaware matching rises "≈ 60% − 80%". So the best published evidence that leakage information helps a decoder is (a) on simulated data and (b) with a readout herald. Nobody has shown a leakage-derived gain on the real 2023 or 2025 syndromes. Our null is therefore consistent with the literature, not in tension with it.

### 1.5 Bottom line for the paper

State the scope as a regime: the tracker is for devices **without** per-cycle data-qubit leakage removal **and** with low leakage mobility (episodes of several rounds), where leakage is a large share of the error budget. Sycamore 2023 fails the second condition (transport) and the third (3 to 10 % share); Willow fails all three. This is not a failure of the method; it is the method's domain boundary, confirmed on hardware.

---

## 2. Inventory of time-structured noise documented for Willow (and the 72-qubit sibling)

Units: a Willow surface-code round takes about 1.1 μs ("each round of syndrome extraction requires 1.1 μs", Arms et al. 2025 Sec. IV.D, inferred from the data). A 30-round shot is ~33 μs of circuit time; the shot repetition period (including reset and readout dead time) is **not given in the papers I read**, so conversions from seconds to shots below use the Google supplement's own equivalence "once per hour, or once every 3 × 10⁶ shots" for the 1000-round repetition code, i.e. ~1.2 ms per 1000-round shot, and are marked approximate for 30-round shots.

| # | phenomenon | timescale | magnitude | source | can a causal per-shot tracker see it? |
|---|---|---|---|---|---|
| T1 | Slow calibration drift (qubit frequency, readout, TLS wandering) | hours; between re-calibrations (every 4 runs in the 15-h test) | Λ = 2.18 ± 0.07 (SD over 16 runs, ~3 %); "logical error rates … right after drift recalibration are not appreciably lower than those just prior" | Google 2025 Sec. III, Fig. 2e | Yes in principle, but the published evidence says it is small: the NN decoder fine-tuned strictly causally on dataset N−1 had "similar accuracy as an even/odd split" (Supp. III.C) |
| T2 | Global noise level drift within a long run | ≥ 6 h across 200 samples of the d = 29 repetition code | "total noise drops approximately 7% over the first three-fifths of the samples before climbing again" | Arms et al. 2025 (arXiv 2512.10814) Sec. IV.D, Fig. 7 | Only if the drift is *relative* between edge types; a uniform rescaling of all edge probabilities barely moves MWPM (our A3 control: f ≤ 0.15 at optimum scale 8, `control_baselines.csv`) |
| T3 | Per-hyperedge rate drift | hours (sample to sample) | "least stable excitation rates may change by a factor of 3-5 for time-like and space-like hyperedges"; most stable ones constant | Arms et al. 2025 Sec. IV.D | Yes, this is the relative drift a windowed DEM could track; magnitude at the d = 3/5/7 surface-code runs is unknown |
| T4 | Transient TLS on one or two detectors | "tens or hundreds of cycles" (≈ 1 to 10 shots of 30 rounds, approx.); "stays high for 1-2 ms" | detection probability up "by over a factor of 3"; causes a high-distance (d > 19) repetition-code failure "about once per hour" | Google 2025 Sec. IV and Supp. V.A, Fig. S7b | Yes, a per-detector two-state HMM over consecutive shots is the natural model (Hypothesis H2) |
| T5 | "TLS-like" within-shot episodes (adjacent detector pair flipping for many rounds) | width "approximately 16 rounds (18 μs)" with a long tail; "approximately 4000 events per sample (1 per 28 ms)" | detector pair nearly constantly flipping | Arms et al. 2025 Sec. IV.E.3, Fig. 13 | Partly: 16 rounds is within one 30-round shot, so this is a *within-shot* hidden state (the leakage tracker's own territory, but on measure/readout rather than data-qubit leakage); whether episodes straddle consecutive shots is untested |
| T6 | High-energy (radiation) bursts | "roughly once per hour, or once every 3 × 10⁶ shots"; decay "around 400-700 μs"; Arms: "approximately 4× more high-energy events" with a looser threshold | many detectors spike simultaneously, "spatially localized to neighborhoods of roughly 30 qubits"; all d = 27 repetition-code failures | Google 2025 Sec. IV, Supp. V.A, Fig. 3d/S7a; Arms 2025 Sec. IV.E.2 | Not in a 50 000-shot surface-code file (expected 0.02 to 0.07 events); only in the repetition-code set |
| T7 | Pre-gap-engineering reference bursts (not Willow) | every ~10 s, 25 to 30 ms decay | 4 → 24 of 26 qubits erroring | McEwen 2022 Sec. II to III | Historical; shows what gap engineering removed |
| T8 | TLS spectral diffusion of T1 | abrupt changes on "15-minute timescales" (Klimov); 1 to 10 MHz over 272 h (Carroll, IBM) | T1 "by up to an order of magnitude" | Klimov 2018; Carroll 2022 | Same timescale as T1/T3; surfaces as per-qubit relative rate drift |
| T9 | Residual leakage | one cycle | 10⁻³ → 5×10⁻³ within a cycle, removed by DQLR | Miao 2022; our bound ≤ 0.1 % multi-round | No multi-round signal (Section 1) |
| T10 | Long-range correlated measurement errors | spatial, across the 105-qubit chip | "correlated measurement errors rather than high-weight Pauli errors" | Arms 2025 abstract, Sec. IV.E.1 | Not temporal per se; if they come in bursts they would show up as T4/T6 |
| T11 | Our own observation (not re-verified here) | blocks of consecutive shots | block-variance ratio of the shot-level detection count 7 to 90× the shuffled null (reported in the task brief) | this project, earlier session | **Provisional** until re-measured in `willow_diagnostics.md`; the inventory above says the most likely drivers are T3/T4 |

Two reading notes. (a) The Google and Arms numbers come from the **72-qubit** processor's repetition code (1000 rounds, 10⁵ shots per sample), not from the 105-qubit surface-code runs we decode; the surface-code files are 50 000 shots each, so the rate of rare events inside one file is low. (b) Everything with a timescale of hours (T1 to T3, T8) is slow compared with a 50 000-shot file: if one file took of order a minute to acquire, hour-scale drift is nearly constant inside it and only the *between-file* structure can be tracked, and Google already showed that between-file causal adaptation of the NN decoder is roughly neutral.

---

## 3. What prior work already did with across-shot structure, and what remains open

| approach | representative work | data | causal? | per-shot weights? | result |
|---|---|---|---|---|---|
| Static prior fitted on a calibration set before the run | Google 2025 Supp. III.B; Sivak et al. 2024 | Sycamore/Willow hardware | yes (calibration set "precedes the rest of the experiment") | no, one prior for all 1 to 250-cycle data | learned prior "10% average improvement of the LER" over SI1000 for MWPM; RL prior −3.3 % vs correlation-based prior at d = 5 |
| Static DEM re-estimated from the decoded shots themselves | Takou et al. 2026 (2606.11496); Remm et al. 2026 | Willow d = 3/5/7, 50k shots | no (in-sample) | no | "typically at the 5% − 10% level" vs SI1000; comparable to RL prior |
| Time series of DEMs to *characterise* drift | Arms et al. 2025 | Willow 72Q repetition code | yes (per 10⁵-shot sample) | no decoding with them | 7 % global drift over hours; ×3 to 5 on least-stable hyperedges; proposed as "online characterization" |
| Drift used for post-selection | Hoyt et al. 2026 (2609.29018) | IBM repetition codes (10⁴-shot windows); Google d = 5 10-round | yes | no (rejects shots) | retained LEP −10.6 % (d = 7), −28.8 % (d = 9) at 15 % rejection |
| Windowed adaptive DEM + adaptive decoding | Bhardwaj et al. PRX Quantum 2026 (2511.09491); Huo & Li 2017; Spitz et al. 2018; Wang et al. DGR 2023 | **simulation only** | yes | per-window | logical error tracks the ground truth; DGR 3.6× under mismatch |
| Learned decoder fine-tuned on hardware, causal split | Google 2025 Supp. III.C (AlphaQubit on the stability set); Lange et al. 2026 (IBM stability expt.) | hardware | yes (dataset N−1 → N) | no (one network per dataset) | "similar accuracy as an even/odd split", i.e. no measurable drift penalty or gain at the dataset scale |
| Hardware-heralded adaptivity | Ziad et al. 2025; Hanisch et al. 2024 | simulation / IBM soft readout | yes | yes, hard (weight 0) | needs a herald the public datasets do not contain |
| Calibration-conditioned decoder | Stein et al. 2026 (FiLM) | IBM repetition code | yes | no (per-calibration) | uses side-information, not syndromes |

**What remains open** (as of the papers found; the alphaXiv and web scans were not exhaustive, see Deviations):

1. No paper decodes Willow (or Sycamore) surface-code data with weights that change **within** a dataset as a causal function of the preceding shots' syndromes and reports a Holm-corrected gain against the shipped RL prior with a shuffled-order placebo. The simulation precedents (Bhardwaj, DGR, Spitz, Huo to Li) make the *method* unoriginal; the hardware test with a placebo would be the new element, or the new null.
2. No paper models the **per-detector transient** (T4) as a hidden state over consecutive shots and re-weights the time-like edges of that detector for the duration of the episode. Arms et al. describe the episodes; Google describes them; nobody decodes with them.
3. The dataset most likely to show a gain is **not** the 105-qubit d = 3/5/7 file (one calibration, 50 000 shots, few rare events) but `google_72Q_surface_code_d3_d5_set2` ("different calibration states of the device … LER … smaller than 3×10⁻³ to … approaching 10⁻²", Table S2) and `set1` (16 consecutive runs over 15 h). A between-dataset causal update there is the hardware analogue of what Bhardwaj et al. simulated. The rep-code d = 29 set is the only place with enough shots to see T6 bursts.

---

## 4. Three falsifiable hypotheses for a causal per-shot hidden-state decoder on Willow

Common design rules for all three (to be frozen in `adaptive_protocol.md` before any held-out run): the decoder sees shots strictly in acquisition order and may use only shots 1…n−1 to set the weights of shot n; the baseline is our own MWPM (and belief matching) on the shipped RL-optimised DEM on identical shots; the **placebo** is the same algorithm run on a random permutation of the shots (this keeps every per-shot statistic but destroys time order, any "gain" that survives the placebo is regularisation, not time structure); statistics are paired (bootstrap on the ε ratio, McNemar) with Holm correction over all pre-registered comparisons; tuning on one dataset, evaluation on others.

### H1, Slow relative drift of edge-type rates is trackable and worth > 1 % of ε

*Claim.* Within a 50 000-shot file, or across the 16 consecutive runs of 72Q set1, the ratios between edge classes (measurement-like vs space-like vs boundary) drift slowly (T2/T3). An exponentially-weighted causal estimate of per-detector detection fractions (or of the pairwise p_ij in a trailing window, as in Spitz / Bhardwaj) that rescales *classes* of edges, not a single global factor, beats the static RL prior.

*Confirming observable.* (i) The block-wise (e.g. 1000-shot) per-detector detection fraction has autocorrelation at lag 1 to 10 blocks significantly above the shuffled null, and the per-class ratios (not just the total) move. (ii) The causal decoder's ε ratio vs the RL-prior baseline is < 1 with Holm-corrected p < 0.05 on held-out files, and the same algorithm on shuffled order gives a ratio consistent with 1.

*Killing control.* Any of: block autocorrelation of the class ratios consistent with the shuffled null; gain in acquisition order equal to gain on shuffled order (then it is just in-sample re-fitting of a static DEM, Takou's 5 to 10 % vs SI1000, ~0 vs RL); gain ≤ 1.5 % (our resolution at 50 000 shots) on every held-out file. Prior expectation from the papers: Λ varies by ~3 % (SD) over 15 h and a strictly causal NN adaptation at the dataset scale was neutral, so the honest prior for H1 is "small or null" at the within-file scale; it is more plausible across set2's deliberately varied calibration states.

### H2, Transient single-detector TLS episodes span consecutive shots and are worth re-weighting

*Claim.* The "one or two detectors suddenly increasing in detection probability by over a factor of 3, settling … tens or hundreds of cycles later" episodes (Google 2025 Sec. IV) extend over several consecutive 30-round shots. A per-detector two-state causal HMM over the shot index (state = normal / hot, emission = that detector's count in the shot) raises the measurement-error (time-like) edge weight of a hot detector for the shots it is hot. Since the 2023 study showed our flags mark real anomalies even when they do not help (adjacent fire rate 0.36 to 0.42 vs 0.15 to 0.17), the question is only whether the episodes are long and common enough.

*Confirming observable.* (i) Model-free: for each detector, the run-length distribution of "above-threshold shots" (e.g. count > 3× its mean) has a tail significantly heavier than the shuffled null, and hot runs cluster in space on 1 to 2 adjacent detectors (not chip-wide, that would be H3). (ii) The decoder gain is concentrated in shots the HMM marks hot (McNemar on hot shots only), and the placebo (shuffled order destroys runs) gives nothing. (iii) In the matched Stim simulation with injected hot-detector episodes of the fitted duration, the same HMM recovers a measurable fraction of the oracle (flag-known) gain.

*Killing control.* Run-length tails equal to the shuffled null for every detector (episodes do not survive the shot boundary, e.g. because the shot repetition period is longer than 1 to 2 ms); or hot-shot fraction × per-episode damage below 1 % of ε (then even the oracle is below resolution, as at Willow T2); or hot-shot gain = 0 while the hot flags are confirmed real by the next-shot adjacent-fire test.

### H3, Chip-scale bursts are detectable per shot and the decoder should give up on them

*Claim.* High-energy events (T6) raise the detection fraction of many detectors at once for 400 to 700 μs, i.e. a handful of consecutive shots. A one-dimensional causal detector on the per-shot total detection count (e.g. CUSUM) flags the burst shots; the decoder either rescales all edges to the burst level or heralds "unreliable". This is Hoyt et al.'s post-selection idea made causal and applied to the whole chip.

*Confirming observable.* Shot-level detection-count outliers (> 5σ above the trailing median) occur in temporally clustered groups significantly more often than in shuffled order, with the Google decay profile; the logical failures in flagged shots exceed the baseline rate by a large factor; removing or re-weighting them lowers ε by at least the flagged-shot failure share.

*Killing control.* Expected count: at "once every 3 × 10⁶ shots" of 1000 rounds, a 50 000-shot, 30-round surface-code file should contain ≈ 0.02 to 0.07 events (Arms's 4× looser count still gives < 0.3). **H3 is therefore pre-killed for the d = 3/5/7 surface-code files** and testable only on the 72Q d = 29 repetition-code set (100 × 10⁵ shots × 1000 rounds), where Google already attributes all d = 27 failures to these events. If, on the surface-code files, outlier shots are not clustered in time, H3 is dead there regardless of model.

### What I would run first

Order by prior probability × testability: H2 on the d = 3 files (nine patches pooled; model-free run-length test first, it costs nothing), then H1 on set2/set1 (between-dataset causal update, the Bhardwaj protocol on hardware), and H3 only on the repetition-code set. If the model-free statistics in `willow_diagnostics.md` show the block-variance excess (T11) is entirely explained by a few hot detectors, H2 is the whole story and H1 is moot.

---

## 5. Deviations and limits of this document

1. **Reading depth.** Full text read for Google 2025 (main + supplement), Google 2023 (main + supplement), Miao 2022, AlphaQubit, Klimov 2018, Carroll 2022, McEwen 2022, McEwen 2024, Huo & Li 2017, Nickerson & Brown 2019. Targeted page extracts only (alphaXiv PDF queries, not the whole paper) for Arms 2025, Takou 2026, Hoyt 2026, Bhardwaj 2026, Wang DGR 2023, Sivak 2024, Morales-Hashemi 2026, Stein 2026, Poster 2026, Blume-Kohout & Young 2025. **Spitz et al. 2018 was not read** (not in the alphaXiv index; arXiv proxy-blocked): its title and venue are taken from the reference lists of Hoyt 2026 and Morales-Hashemi 2026. The arXiv id I first fetched for Spitz (1712.00502) turned out to be Nickerson & Brown; it is kept in the table as relevant adjacent work.
2. **Leakage share in Google 2023 Fig. 4a** was not extracted as a number (figure only); the 2025 Table S4 numbers (5 % + 1 %) are used instead.
3. **Shot repetition period** of the Willow runs is not stated in the papers I read; conversions from "cycles" and "ms" to "shots" in Section 2 and H2/H3 are approximate and flagged.
4. **Literature scan coverage.** Two alphaXiv discovery searches plus two web searches; not an exhaustive arXiv listing. The "what remains open" claims in Section 3 are therefore provisional.
5. **T11 (block-variance 7 to 90×)** is quoted from the task brief and was not re-computed here; it is marked provisional.
6. No simulations and no new decoding were run (as instructed).
