# Tracker v3: confirmation result (rule 4 of v3_dev_protocol.md). Synthetic only; no ibm_miami outcome read.

Selected in development: **v3 = R + G2** (readout explaining away for no-reset circuits + per-run switch-off test). Re-run on NEW seeds (8000):

| scenario | MWPM P_fail | v3 P_fail | only v3 right / only MWPM right | p | qubits kept |
|---|---|---|---|---|---|
| N1 reset, no leakage | 0.0503 | 0.0520 | 88 / 121 | **0.027** | 1 of 9 |
| N2 no-reset, no leakage | 0.0343 | 0.0333 | 58 / 47 | 0.33 | 1 of 9 |
| N3 no-reset, 1.7× noise, no leakage | 0.0917 | 0.0917 | 0 / 0 | 1 | none |
| L1 reset, leakage on all qubits | 0.0843 | 0.0694 | 655 / 359 | 1e-20 | 5 of 9 |
| H1 reset, 2 long-lived qubits | 0.0657 | 0.0646 | 128 / 106 | 0.17 | 3 of 9 |
| L2 no-reset, leakage | 0.0536 | 0.0498 | 154 / 109 | 0.007 | 3 of 9 |
| H3 no-reset, 1.7× noise, 2 long-lived qubits | 0.1052 | 0.1041 | 58 / 45 | 0.24 | 1 of 9 |

**Verdict: rule 1 fails on N1** (mild harm, +3.4 % failures, p = 0.027). By the rule fixed in advance, **v3 is not used on ibm_miami**. The switch-off test still lets through one qubit with fake leakage in a leak-free reset memory.

## Diagnostic (not part of the selection): the ibm_berlin-type circuit
ibm_berlin stability circuit, T = 50, uniform p = 6e-3, seed 7000:
- N4 (no leakage): MWPM makes **0** failures in 20 000 shots, so there is nothing to harm.
- H4 (2 data qubits with long-lived states, p_L = 3e-3, τ = 40): MWPM 0.0075 → tracker 0.0034 (114 / 34, p = 3e-11) without any guard; 0.0037 with v3 (R + G2; 109 / 35, p = 5e-10).

**What this teaches.** In a stability experiment, logical failures come almost only from long-lived states, so the tracker has a large gain and little room for harm. This matches the ibm_berlin result. In memory experiments, the possible gain from leakage flags is smaller (oracle +4 % to +26 % here), and a few false alarms are enough to cancel it.
