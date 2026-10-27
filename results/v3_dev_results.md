# Tracker v3 development results (synthetic only, development seed 7000)

Cells: shots where only the tracker is right / only MWPM is right (exact McNemar p in brackets when < 0.1). "off" = the switch-off test kept no qubit (tracker = MWPM). On reset circuits (N1, L1, H1) variant R is identical to the base tracker.

| scenario | base G0 (= v2) | base G1 | base G2 | base G1+G2 | base G2b | R G0 | R G1 | R G2 | R G1+G2 |
|---|---|---|---|---|---|---|---|---|---|
| N1 reset, no leakage | 192/548 (2e-40) | 66/117 (2e-4) | 128/137 | 41/21 (0.015) | 118/53 (7e-7) | = base | = base | = base | = base |
| N2 no-reset, no leakage | 80/215 (2e-15) | 69/184 (3e-13) | 9/26 (0.006) | 1/7 (0.07) | 2/9 (0.065) | 101/143 (0.009) | 63/86 (0.07) | 51/48 | 14/34 (0.006) |
| N3 no-reset, 1.7× noise, no leakage | 152/400 (1e-26) | 151/379 (1e-23) | off | off | 116/298 (2e-19) | 148/258 (5e-8) | 84/152 (1e-5) | off | off |
| L1 reset, leakage on all qubits | 644/379 | 644/379 | 661/346 | 644/379 | 644/379 | = base | = base | = base | = base |
| H1 reset, 2 long-lived qubits | 248/298 (0.036) | 248/298 | off | 247/297 | 247/297 | = base | = base | = base | = base |
| L2 no-reset, leakage | 191/218 | 191/218 | 169/179 | 169/179 | 184/250 (0.002) | 194/139 (0.003) | 194/139 | 185/162 | 185/162 |
| H3 no-reset, 1.7× noise, 2 long-lived qubits | 170/250 (1e-4) | 170/250 | off | off | 100/117 | 160/223 (0.002) | 160/223 | 44/48 | 44/48 |

Oracle (true flags) for scale: L1 562/140, H1 212/116, L2 193/41, H3 141/105.

**Rule 1 (no harm in N1 to N3)** is passed by: base G1+G2 and R G2.
**Rule 2 (summed gain over L1, H1, L2, H3, as a fraction of MWPM's failures there; A failures 1694, 1320, 588, 1255):**
- base G1+G2: +0.156 − 0.038 − 0.017 + 0 = **+0.10**
- R G2: +0.186 + 0 + 0.039 − 0.003 = **+0.22**

**Selected: v3 = R + G2** (readout explaining away + per-run switch-off test). R + G2b was not evaluated (G2b failed rule 1 with the base tracker).

**Honest notes.**
- In the no-reset scenarios even v3 recovers only a small part of the oracle gain (L2: +23 of a possible +152).
- In H1 and H3 (few long-lived qubits) no variant gains: the oracle gain is small there, and the tracker's flags are not precise enough.
- The switch-off test G2 turns the tracker off under a noise mismatch (N3, H3), even when a real hidden state exists (H3). This is conservative by design.
