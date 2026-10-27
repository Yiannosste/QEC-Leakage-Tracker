"""gen_leaky.py - the LeakyCircuit interface (data qubits, adjacency, marker-based edge lookup, leakage
injection, FlagMatcher compatibility) for ANY Stim circuit that measures its ancillas with M (+ separate R) each
round and reads the data qubits in a final M layer (e.g. the IBM ibm_berlin stability circuit of Lange et al.).

Nothing in xa_tracker.py is changed. For real data, `with_dem(dem)` returns a view whose background noise
(used by the tracker and by the matcher) is a given detector error model, e.g. the shipped calibrated p_ij DEM.
"""
from collections import defaultdict
import numpy as np, stim
from leakage_sim import LeakyCircuit, _targets

NOISE = {"DEPOLARIZE1", "DEPOLARIZE2", "X_ERROR", "Y_ERROR", "Z_ERROR", "PAULI_CHANNEL_1", "PAULI_CHANNEL_2"}


class GenLeakyCircuit(LeakyCircuit):
    def __init__(self, circuit: stim.Circuit, rho=0.5):
        self.rho, self.base = rho, circuit
        flat = circuit.flattened()
        ms = [i for i, ins in enumerate(flat) if ins.name == "M"]
        self.meas_qubits = _targets(flat[ms[0]])
        final = set(_targets(flat[ms[-1]]))
        self.data_qubits = sorted(final - set(self.meas_qubits))
        # rounds = M layers that measure the ancillas
        self._round_m = [i for i in ms if set(self.meas_qubits) <= set(_targets(flat[i]))]
        self.rounds = len(self._round_m)
        assert ms[-1] == self._round_m[-1], "final data readout must share the last round's M layer"
        adj = defaultdict(set)
        for ins in flat:
            if ins.name in ("CX", "CZ"):
                t = _targets(ins)
                for a, b in zip(t[0::2], t[1::2]):
                    for x, y in ((a, b), (b, a)):
                        if x in self.data_qubits and y in self.meas_qubits: adj[x].add(y)
        self.adj = {q: sorted(adj[q]) for q in self.data_qubits}
        self.nq, self.nm = len(self.data_qubits), len(self.meas_qubits)
        self.qidx = {q: i for i, q in enumerate(self.data_qubits)}
        self.midx = {m: i for i, m in enumerate(self.meas_qubits)}
        self._flat = flat; self._final_m = ms[-1]
        self.dem = circuit.detector_error_model(decompose_errors=True)
        self.num_detectors, self.num_observables = circuit.num_detectors, circuit.num_observables
        self._build_edge_lookup()
        nd, no = self.num_detectors, self.num_observables
        self.pattern = {}
        for tag, (dets, obs) in self.edge_of.items():
            v = np.zeros(nd + no, dtype=bool); v[list(dets)] = True; v[[nd + o for o in obs]] = True
            self.pattern[tag] = v

    def _marker_circuit(self, kind, rr):
        """Noise-free circuit with unique-probability single-Pauli markers of one kind at one round.
        ('x'|'z', q, r): data error at the start of round r (r = 0: after the initial reset; r >= 1: right after the
        ancilla M of round r-1).  ('m', m, r): flip of ancilla m's round-r outcome.  ('f', q, R): flip of q's final
        readout."""
        flat, R = self._flat, self.rounds
        mark = stim.Circuit(); tags = {}; k = [0]
        def add(qs, pauli, tagfn):
            for q in qs:
                k[0] += 1; pr = 1e-3 + k[0] * 1e-6
                tags[round(pr, 9)] = tagfn(q); mark.append(pauli, [q], pr)
        r = 0; started = False
        for i, ins in enumerate(flat):
            if ins.name in NOISE: continue
            if not started and ins.name in ("R", "RX"):
                mark.append(ins.name, _targets(ins)); continue
            if not started and ins.name == "TICK":
                started = True
                if rr == 0 and kind in ("x", "z"):
                    add(self.data_qubits, "X_ERROR" if kind == "x" else "Z_ERROR", lambda q: (kind, q, 0))
                mark.append(ins); continue
            if ins.name == "M":
                is_round = i in self._round_m
                if is_round and kind == "m" and r == rr:
                    add(self.meas_qubits, "X_ERROR", lambda m: ("m", m, rr))
                if i == self._final_m and kind == "f":
                    add(self.data_qubits, "X_ERROR", lambda q: ("f", q, R))
                mark.append("M", _targets(ins))          # strip the measurement-flip argument
                if is_round:
                    r += 1
                    if r < R and r == rr and kind in ("x", "z"):
                        add(self.data_qubits, "X_ERROR" if kind == "x" else "Z_ERROR", lambda q: (kind, q, rr))
                continue
            mark.append(ins)
        return mark, tags

    def with_dem(self, dem: stim.DetectorErrorModel):
        """View whose background noise is `dem` (same detector structure); used for real hardware shots."""
        return DEMView(self, dem)


class _BaseProxy:
    def __init__(self, circuit, dem): self._c, self._d = circuit, dem
    def get_detector_coordinates(self, *a, **k): return self._c.get_detector_coordinates(*a, **k)
    def detector_error_model(self, decompose_errors=False, **k): return self._d


class DEMView:
    """Delegates everything to the GenLeakyCircuit but replaces the noise model by a shipped DEM."""
    def __init__(self, lc, dem):
        self._lc = lc; self.dem = dem; self.base = _BaseProxy(lc.base, dem)
        assert dem.num_detectors == lc.num_detectors, (dem.num_detectors, lc.num_detectors)
    def __getattr__(self, k): return getattr(self._lc, k)
