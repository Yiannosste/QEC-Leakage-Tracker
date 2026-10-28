# How the tracker works

This is the method as I fixed it for all experiments (facts.md F1). Code: `code/tracker/xa_tracker.py`
(tracker), `code/sim/leakage_sim.py` (simulator and the matching decoder with soft weights),
`code/tracker/gen_leaky.py` (adapter for the IBM stability circuit). The weight rule is derived in
`results/derivation_soft_weight.md`.

## The problem

A surface-code experiment gives, per shot, a syndrome: one bit per detector, which compares a stabiliser
outcome with its previous value. When a data qubit leaves the computational space (leaks) it stays leaked for several rounds and scrambles every stabiliser that touches it (in the model: each adjacent check outcome is flipped with probability ρ = 1/2 per round). The matching decoder does not know this. The
tracker's job is to infer, from the syndrome alone, how likely each data qubit is to be leaked in each round,
and to pass that to the decoder.

## Leakage model in simulation

I use Stim's rotated surface-code memory (`surface_code:rotated_memory_z`) with SI1000 noise of strength p.
Each data qubit leaks with probability p_L per round, stays leaked for a geometric time with mean τ rounds,
flips each adjacent stabiliser outcome with probability ρ = 1/2 per round while leaked, gets a Pauli drawn uniformly from X, Y, Z on return, and flips its final readout with probability ρ if it is leaked at the end. On real data I use the same
model as a description of "a long-lived state that scrambles neighbouring checks". Syndromes alone cannot say
whether that state is leakage or a defect.

## State space

One hidden Markov model per data qubit. The hidden state of qubit q at round t holds the leakage bit
L ∈ {0, 1} and one measurement-flip bit for each neighbouring check (both bases, up to four checks). The flip
bits let the model explain away an ordinary measurement error, whose two-round detector pattern looks like a
one-round leak. Transitions: L goes 0→1 with probability p_L (per qubit) and 1→0 with probability p_ret
(global). The flip bits are drawn each round from the given, undecomposed detector error model: the exact circuit model in simulation, the authors' shipped p_ij model on hardware.

## Emission

The observation at round t is the set of detection events of the neighbouring checks. Given the hidden state,
each detector fires with a probability from the detector error model (the background), XOR the flip bit, and, if L = 1, flipped with probability ρ. Forward-backward then gives π(q, t) = P(L = 1 | all detection events
of the shot) and the posterior of a return at t. The "lag 2" variants only see rounds up to t + 2 (online).
The frozen tracker ALL uses the whole record (offline smoothing).

## Coupling between neighbours

Neighbouring data qubits share checks, so one qubit's leakage changes another qubit's emission model. I run
8 damped Jacobi mean-field passes with damping 0.5: in each pass every qubit is re-run with its neighbours'
current posteriors folded into its emission probabilities, and the new posterior is averaged with the old one.

## Label-free calibration

p_L (per qubit) and p_ret (global) are fitted by Baum-Welch on calibration shots that are never decoded.
Start: p_L = 3e-3, p_ret = 0.25. 12 iterations, ρ fixed at 1/2. The E-step uses the same mean-field inference
as decoding. I report the fitted log-likelihood minus the log-likelihood of the same model with p_L → 0 as the
evidence, in nats per shot. In detect2 the learned p_L was 1.1 to 1.4e-3 for a true 1.0e-3, and p_ret 0.15
to 0.18 for a true 0.125. On leak-free data the fit does not go to zero; see facts.md F6. And on leak-free shots sampled from the ibm_berlin shipped model the evidence is still 50 to 60 % of the real value (facts.md F5), so I only read it next to that null, never on its own.

## Decoding rule

Per shot, every matching-graph edge e touched by a possibly leaked qubit gets p_e ← p_e ⊕ c·π, with c = ρ for
the time-like edges of adjacent checks, 2/3 for the X/Z data edges at the return round, and ρ for the final
data-readout edge. π below 0.02 is ignored. Edge weights are log((1 − p_e)/p_e) as usual and PyMatching 2.4
does the matching. Soft weights beat hard flags on the same posterior in 53 of 54 tracker-cell pairs (F2: median gain in f +0.05 to +0.12 for the CNN, +0.15 to +0.32 for the HMM).

Controls: A is plain MWPM. B is the oracle with the true flags (simulation only). A4 is the static control,
where every shot gets the mean posterior over all shots. P is the placebo, where every shot gets another
shot's posteriors (fixed permutation, seed 0).

## Cost

Per qubit and round, forward-backward costs O(N · S²) for N shots and S = 2 · 2^k hidden states with k
neighbouring checks (k ≤ 4, so S ≤ 32), times the 8 + 1 mean-field passes. It is Python/NumPy, vectorised over
shots. Measured: ALL takes about 450 s per 40 000 shots at d = 5 and 25 rounds on 12 CPU cores (F3), and
about 15 min per T = 100 ibm_berlin stability run, calibration plus tracking, on 12 cores (F5). The smoke test
(`scripts/smoke_test.sh`, d = 3, 10 rounds, 1 000 + 500 shots) takes about 15 s on one core.

## What is not in the method

No IQ (analog readout) data, no leakage removal unit, no training labels, no hand tuning. The only per-run adaptation is the Baum-Welch fit of p_L per qubit and p_ret on that run's own calibration shots. Every other setting above was fixed in `protocols/detect2_protocol.md` and reused unchanged on the IBM data.
