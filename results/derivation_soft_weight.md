## Derivation of the soft-weight rule  p_e = p_e0 XOR (c * pi)

**Setting.** A matching-graph edge `e` is a set of one or two detectors (plus possibly the logical observable) that one
physical fault flips. In the leakage-free circuit model the edge flips with probability `p_e0` (from the Stim detector
error model). Leakage adds a *second, independent* way to flip the same edge, but only while a hidden binary state is
on: `L = 1` means "data qubit q is leaked at round r".

**Flip probability given the leakage state.** Write `q_e = P(leakage mechanism flips e | L = 1)`:

| edge class | leakage mechanism in the simulator | q_e |
|---|---|---|
| time-like edge of a stabiliser adjacent to q, round r (detectors (m, r), (m, r+1)) | outcome of m at round r randomised, flipped with probability rho | `rho` (= 1/2 default) |
| X data edge and Z data edge of q at the return round | random Pauli X, Y or Z with probability 1/3 each; X-edge flips for X or Y, Z-edge flips for Y or Z | `2/3` each |
| final data edge of q (leaked during the last data measurement) | data outcome flipped with probability rho | `rho` |

Two independent flips of the same edge combine by exclusive-or: `a XOR b := a + b - 2ab` (the edge is flipped if exactly one of
the two mechanisms fires). So

    P(e flips | L = 1) = p_e0 XOR q_e,        P(e flips | L = 0) = p_e0.

**Marginalising the hidden state.** The tracker gives a posterior `pi = P(L = 1 | syndromes seen so far)`. The decoder does not
know `L`, so it must use the marginal flip probability:

    p_e = (1 - pi) * p_e0 + pi * (p_e0 XOR q_e)
        = p_e0 + pi * q_e - 2 * pi * q_e * p_e0
        = p_e0 XOR (pi * q_e).                                             (1)

Equation (1) is exact for one edge and one hidden state, and it is the rule implemented in `FlagMatcher._set_edge`
(`p_add = c * pi` with `c = q_e`). The matching weight is then the usual `w_e = log((1 - p_e) / p_e)`. For the oracle decoder
`pi` is 0 or 1 and (1) reduces to the two conditional values above.

**Approximations hidden in (1) when it is applied to the whole graph.**
1. *Independence across edges.* A leaked qubit flips the time-like edges of *all* its adjacent stabilisers (two or four
   of them) over *several consecutive rounds*, and a Y return error flips the X and Z data edges together. These are
   correlated multi-edge (hyperedge) events. Equation (1) keeps only the marginal probability of each edge and lets the
   matcher treat them as independent; this is the same approximation MWPM already makes for Y errors in the base model.
2. *Independence across rounds.* `L_r` and `L_{r+1}` are strongly correlated (geometric lifetime tau), so the flips of the
   time-like edges at rounds r and r+1 are correlated. Plugging in `pi_r` and `pi_{r+1}` separately ignores this.
3. *Return probability.* The exact quantity for the return edges is `P(L_{r-1} = 1, L_r = 0)`. The pipeline uses the CNN's
   second output head for this (trained on the true return labels); the HMM and the count tracker use
   `max(0, pi_{r-1} - pi_r)`, which is the exact value only when the posteriors are nested (no new leakage at r).
4. *Double use of the syndrome.* `pi` is computed from the same detection events that the matcher explains. The
   randomised stabiliser outcomes therefore enter twice: once as evidence for `pi`, once as defects to be matched.
   Within the independence approximation this is harmless (the weight is the marginal flip probability), but it
   is one reason why the optimal scale of `c` need not be exactly 1.
5. *Threshold.* Posteriors below 0.02 are left at `p_e0` (speed); the neglected `pi * q_e <= 0.01` is of the same order as
   `p_e0` for time-like edges (~ 5p = 0.005), so the threshold is not negligible in principle, only in effect.
6. *Hyperedges created by leakage are not added.* Mechanisms whose detector set is not already a graph edge (none in
   this simulator: every leakage effect is a single Pauli at a circuit location, so all land on existing edges or
   boundary edges) would need new edges.

**Why scan the scale s.** If the posterior is calibrated and the approximations are benign, the optimum of the scanned
rule `p_e = p_e0 XOR (s * c * pi)` should be at `s = 1`. An optimum at `s > 1` says that the decoder benefits from
*over*-trusting the flags (typically because the independence approximation 1 under-weights the joint event); `s < 1`
says the flags are over-confident or that the double-counting in 4 hurts. The scan therefore measures how far the
pipeline is from the "right" rule and how sensitive the headline fraction `f` is to that choice.
