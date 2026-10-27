# Amendment 1 to the C3 pre-registration (written before the production grids G1–G4 were run)

Reason. Development tests at the centre cell (d = 5, p_L = 2e-3, τ = 8, 2e4 test shots, seed 5) showed that the
per-qubit HMM of decoder D has low precision (0.26–0.34 at θ = 0.5): the shared-stabiliser ambiguity between
neighbouring data qubits and the two-round signature of an ordinary measurement error (which is identical to a
one-round leak) produce false positives, and smoothing makes these false positives more confident, so the HMM
recovered 46–52 % (lag 0) and 29–41 % (lag 2) of the oracle gain. These development numbers are reported in the
final report as such and are not part of the pre-registered grids.

Changes (all fixed here, before any grid run):

1. **Decoder D is split into D-HMM and D-CNN.** D-HMM is the pre-registered per-qubit HMM with two declared
   refinements: (i) the 4-state chain (L_{t−1}, L_t) so that a randomised measurement at round t correctly
   influences the detectors of rounds t and t+1; (ii) two mean-field "explaining-away" iterations in which each
   qubit's emissions are conditioned on its neighbours' current posteriors. D-CNN is a learned tracker:
   a 3-layer causal 3D convolutional network (32 channels, kernel 3×3×3, left-only time padding, final 1×2×2
   convolution mapping the (d+1)² stabiliser lattice to the d² data-qubit lattice; two output channels: leak and
   return logits), trained with binary cross-entropy on simulated trajectories whose labels are the hidden leakage
   state. Fixed-lag ℓ is implemented by shifting the input so the output for round t sees detectors up to t+ℓ.
2. **Training protocol (fixed):** 6e4 training shots generated at the cell's own (p_L, τ) with seed 101 + cell
   index, 8 epochs, Adam 1e-3, batch 256, torch seed 0, one model per lag ℓ ∈ {0, 2}. For the robustness grid G3 the
   CNN trained at the centre cell is applied unchanged to the mismatched data (the "mismatch" for the learned
   tracker is a train/test mismatch; for the HMM it is a parameter mismatch, as pre-registered).
3. **Lags:** D-HMM and D-CNN at ℓ ∈ {0, 2} in G1 (the pre-registered ℓ ∈ {1, 3, 5, ∞} are dropped from G1 for
   compute and run only at the centre cell in G4). f_D* = best of ℓ ∈ {0, 2}, as pre-registered (best lag ≤ 2).
4. **Decoder E** (hard threshold θ = 0.5) is evaluated on the D-CNN posterior at ℓ = 2 and on the D-HMM posterior
   at ℓ = 0.
5. **Soft-weight rule:** edge probability p_e = p_e⁰ ⊕ (c·π) with c = ρ for the time-like edges of adjacent
   stabilisers (π = P(leaked at t)), c = 2/3 for the X and Z data edges at the return round (π = P(return at t)),
   c = ρ for the final data-measurement edge (π = P(leaked at R−1)); posteriors below 0.02 are ignored (speed).
   This refines §3-D of the pre-registration (which only named the Z-stabiliser time-like edges and the X data
   edge); the oracle decoder B uses the same rule with π ∈ {0, 1}.
6. **Verdict rule P1** applies to D-CNN *or* D-HMM (whichever is better per cell is f_D*); the report states which
   tracker achieved it. P2 (robustness, ≥ 0.30 under all six mismatch settings) is evaluated for the same tracker.
7. **Noise model:** SI1000 implemented exactly as in §2 (1q Clifford p/10, data idle during MR 2p) on Stim's
   generated circuit, whose two-qubit gate is CX rather than CZ (declared).

Nothing else in the pre-registration changes. Development-phase results (HMM 46–52 % / 29–41 %, CNN 64 % at
ℓ = 0 and 75 % at ℓ = 2 on the same 2e4 test shots, 4 epochs, 4e4 training shots) are declared here so they cannot
be mistaken for grid results.

# Amendment 2 (written 16 Oct 2026, before any d = 7 primary-grid cell was decoded with a CNN)

Compute: training the CNN per cell at d = 7 costs about 2.5 CPU-hours per cell on this machine (measured by the
latency track: 4.5x the d = 5 epoch time), which would make the nine d = 7 cells of grid G1 take about 16 hours.
Change: at d = 7 the CNN (lag 0 and lag 2) is trained ONCE at the centre cell (p_L = 2e-3, tau = 8; 5e4 training
shots, 6 epochs, as in amendment 1) and applied unchanged to the other eight realistic cells. The HMM remains
matched per cell. Consequence: at d = 7 the D-CNN numbers in the non-centre cells are train/test-mismatched
(the same kind of mismatch that grid G3 measures at d = 5); if anything this biases f_D* downwards, so rule P1
is applied unchanged. Result files of these cells carry the suffix _ctrCNN. Also: d = 7 cells use 1e5 shots
(not 2e5) with the pre-registered extension rule if decoder-A failures < 100.
