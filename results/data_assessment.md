# Which public data can test the leakage tracker? (25 Oct 2026)

**Rule of thumb.** The tracker can only help where a hidden state lives for *several rounds* and nobody removes it. Hardware that removes data-qubit leakage every round (Google DQLR, USTC LRU, Quantinuum repump) leaves little to correct. Hardware without reset (IBM Nighthawk, as used in these datasets) is the right place.

| dataset | chip / group | leakage removal | experiments | circuit published? | shots | used before by C3? | verdict |
|---|---|---|---|---|---|---|---|
| **Zenodo 23335425** (Lange et al., arXiv:2610.03869) | IBM ibm_berlin (Nighthawk r1) | none | d=3 stability (17 runs), d=3/d=5 memory, ZZ merge | stability: yes (exact DEM match); memory: no | 5×10⁴ to 10⁵ per run | memory: yes (null); stability: **positive pre-registered result** | done (stability). Memory needs the authors' circuit (human task) |
| **Zenodo 21336494** (Drouet, McLauchlan, …, Brown, Harper, arXiv:2607.12118) | IBM **ibm_miami** (Nighthawk), other group, other dates | **none** (the paper says ibm_miami has no mid-circuit reset) | stability: fig3 (d=5 patch, depth 2 to 12, 4 096 shots each, 2 strategies), fig10 (depth 2 to 32, X and Z, 2 048 shots each); memory: fig7 (d=5, depth 2 to 32, 4 096 shots, 3 strategies × 4 states), fig8 (d=3, depth 2 to 40), fig2 (d=5, 2 048 shots); **fig4: memory with raw IQ data** (3-state leakage classification) | **yes**: Stim circuits with a calibration-based noise model + raw bitstrings + calibration CSV | ≈ 0.05 to 0.25 M per figure | no | **best replication target**. Different chip, group and day. IQ data allow a direct leakage ground-truth check. Smaller shot counts and shorter depths than ibm_berlin, so lower power |
| Zenodo 13273331 (Google Willow 2025) | Google 105Q/72Q | **DQLR every round** | d=3/5/7 memory, d=29 repetition code | yes | 5×10⁴ per run | yes (null) | **negative control**: pre-register "tracker switches itself off, no gain, no harm" |
| Zenodo 6804040 (Google Sycamore 2023) | Google 72Q | no DQLR, but leakage moves away fast during CZ (short episodes) | d=3/5 memory | yes | 5×10⁴ per run | yes (null with old trackers) | secondary: expected small or no gain (short episodes) |
| arXiv:2610.23840 (IBM Nighthawk r2, up to 150 rounds, reports "long-lived correlations") | IBM | none | d=3 to 6 memory | ? | ? | no | **no data statement found**: ask the authors |
| arXiv:2610.11658 (IBM heavy-hex memory + logic) | IBM Heron | ? | memory, logic | ? | ? | no | no data statement found |
| arXiv:2607.01887 (LUCI on IBM) | IBM | ? | surface code with dropouts |, |, | no | data "upon reasonable request" |
| Zenodo 15685795 (Harvard/QuEra atom loss) | neutral atoms | loss is heralded | 4-round QEC | yes (notebook) | ~10⁴ | no | different physics (heralded loss); not a direct test |

## What this means for the paper
1. **Replication**: ibm_miami (Zenodo 21336494). Different chip and group, no reset, stability *and* memory circuits published.
2. **Mechanism**: the ibm_miami IQ data (fig4) say which qubits really leaked (at least at readout). We can check whether the tracker's flags line up with them. This is the leakage-vs-defect test.
3. **Negative control**: Willow (DQLR). A pre-registered prediction that the tracker turns itself off there turns "nothing to correct" into a useful result: it shows the method does not invent gains.
4. **Adapter work needed for ibm_miami**: their circuits use no-reset syndrome extraction and one measurement instruction per qubit. A measurement-error marker must flip only the recorded bit (X before and after M), and the final data readout is a separate layer. Check on synthetic data before any real shot.

## Power warning
ibm_miami stability depths are short (fig3 ≤ 12 rounds; fig10 ≤ 32) and shots are few (2 048 to 4 096 per circuit). On ibm_berlin the gain was ≈ 0 at T ≤ 10 and −6 % at T = 20. So the fig3 runs are unlikely to show a gain. A fair primary test should pool all stability circuits and state this power limit before reading outcomes.
