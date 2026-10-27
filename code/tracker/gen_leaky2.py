"""gen_leaky2.py - LeakyCircuit interface for circuits WITHOUT ancilla reset (e.g. IBM ibm_miami, Drouet et al.,
arXiv:2607.12118): one M instruction per qubit, noiseless reference measurements at the start, a single data reset,
detectors d_t = m_t XOR m_(t-2), and a separate final data-readout moment.

Marker meaning (what the tracker and the decoder rule use):
  ('m', a, r)    : flip of ancilla a's STATE just before its round-r readout. Without reset the flip persists, so it
                   fires detectors of rounds r and r+1. This is the pattern of a leaked neighbour that scrambles what
                   the ancilla collects. (A pure readout error fires rounds r and r+2; it stays in the background DEM.)
  ('x'|'z', q, r): data error at the start of round r (r = 0: after the data reset).
  ('f', q, R)    : flip of data qubit q's final readout.
Detector 'time' coordinates of these circuits count TICKs, so a proxy replaces them by the round index
(0 .. R-1 for rounds, R for the final data readout), which xa_tracker.py expects. xa_tracker.py is not modified.
"""
from collections import defaultdict
import numpy as np, stim
from leakage_sim import LeakyCircuit, _targets

NOISE = {"DEPOLARIZE1", "DEPOLARIZE2", "X_ERROR", "Y_ERROR", "Z_ERROR", "PAULI_CHANNEL_1", "PAULI_CHANNEL_2"}


def _noisy_m(ins):
    a = ins.gate_args_copy()
    return ins.name == "M" and bool(a) and a[0] > 0


class _CoordProxy:
    """Circuit stand-in: real circuit for sampling/DEM, round-index detector coordinates."""
    def __init__(self, circuit, det_round):
        self._c = circuit; self._co = circuit.get_detector_coordinates(); self._r = det_round
    def get_detector_coordinates(self, *a, **k):
        return {i: [*(self._co[i][:2] if len(self._co[i]) >= 2 else [0, 0]), float(self._r[i])] for i in self._co}
    def __getattr__(self, k): return getattr(self._c, k)


class NoResetLeakyCircuit(LeakyCircuit):
    def __init__(self, circuit: stim.Circuit, rho=0.5):
        self.rho, self._circ = rho, circuit
        flat = circuit.flattened(); self._flat = flat
        # moments (TICK-delimited) that contain noisy measurements
        mom, cur = [], []
        for i, ins in enumerate(flat):
            if ins.name == "TICK": mom.append(cur); cur = []
            else: cur.append(i)
        mom.append(cur)
        meas_moms = [[i for i in m if _noisy_m(flat[i])] for m in mom]
        meas_moms = [m for m in meas_moms if m]
        final = meas_moms[-1]
        q_moms = defaultdict(set)
        for mi, m in enumerate(meas_moms):
            for i in m:
                for t in _targets(flat[i]): q_moms[t].add(mi)
        last = len(meas_moms) - 1
        self.data_qubits = sorted(q for q, ms in q_moms.items() if ms == {last})
        self.meas_qubits = sorted(q for q, ms in q_moms.items() if ms != {last})
        dq = set(self.data_qubits)
        # rounds = measurement moments that read ancillas (the final moment counts if it also reads ancillas)
        self._round_moms = [[i for i in m if not (set(_targets(flat[i])) & dq)] for m in meas_moms]
        self._round_moms = [m for m in self._round_moms if m]; self.rounds = R = len(self._round_moms)
        self._final_idx = {i for i in final if set(_targets(flat[i])) & dq}
        self._round_of = {i: r for r, m in enumerate(self._round_moms) for i in m}
        # detector round = latest round among its measurement records; a final data record -> R
        recs, det_round, k = [], {}, 0
        for i, ins in enumerate(flat):
            if ins.name == "M":
                for t in _targets(ins):
                    recs.append(R if i in self._final_idx else self._round_of.get(i, -1))
            elif ins.name == "DETECTOR":
                rr_ = [recs[len(recs) + t.value] for t in ins.targets_copy() if t.is_measurement_record_target]
                det_round[k] = max(rr_); k += 1
        assert k == circuit.num_detectors
        self.det_round = det_round
        self.base = _CoordProxy(circuit, det_round)
        adj = defaultdict(set)
        for ins in flat:
            if ins.name in ("CX", "CZ"):
                t = _targets(ins)
                for a, b in zip(t[0::2], t[1::2]):
                    for x, y in ((a, b), (b, a)):
                        if x in self.data_qubits and y in self.meas_qubits: adj[x].add(y)
        self.adj = {q: sorted(adj[q]) for q in self.data_qubits}
        self.nq, self.nm = len(self.data_qubits), len(self.meas_qubits)
        self.qidx = {q: i for i, q in enumerate(self.data_qubits)}; self.midx = {m: i for i, m in enumerate(self.meas_qubits)}
        self.dem = circuit.detector_error_model(decompose_errors=True)   # as the authors' helpers/decode.py
        self.num_detectors, self.num_observables = circuit.num_detectors, circuit.num_observables
        self._build_edge_lookup()
        nd, no = self.num_detectors, self.num_observables
        self.pattern = {}
        for tag, (dets, obs) in self.edge_of.items():
            v = np.zeros(nd + no, dtype=bool); v[list(dets)] = True; v[[nd + o for o in obs]] = True
            self.pattern[tag] = v

    def _marker_circuit(self, kind, rr):
        flat, R = self._flat, self.rounds
        mark = stim.Circuit(); tags = {}; k = [0]
        def add(qs, pauli, tagfn):
            for q in qs:
                k[0] += 1; pr = 1e-3 + k[0] * 1e-6
                tags[round(pr, 9)] = tagfn(q); mark.append(pauli, [q], pr)
        reset_done = False; data_marked0 = False; f_done = False
        last_round_idx = {r: max(m) for r, m in enumerate(self._round_moms)}
        for i, ins in enumerate(flat):
            if ins.name in NOISE: continue
            if ins.name == "R": reset_done = True
            if ins.name == "TICK" and reset_done and not data_marked0:
                data_marked0 = True
                if rr == 0 and kind in ("x", "z"):
                    add(self.data_qubits, "X_ERROR" if kind == "x" else "Z_ERROR", lambda q: (kind, q, 0))
            if ins.name == "M":
                if i in self._round_of and kind == "m" and self._round_of[i] == rr:
                    add([t for t in _targets(ins) if t in self.meas_qubits], "X_ERROR", lambda m: ("m", m, rr))
                if i in self._final_idx and kind == "f" and not f_done:
                    f_done = True; add(self.data_qubits, "X_ERROR", lambda q: ("f", q, R))
                if i in self._round_of and kind == "ro" and self._round_of[i] == rr:
                    for t_ in _targets(ins):
                        if t_ in self.meas_qubits:
                            k[0] += 1; pr = 1e-3 + k[0] * 1e-6; tags[round(pr, 9)] = ("ro", t_, rr); mark.append("M", [t_], pr)
                        else: mark.append("M", [t_])
                    continue
                mark.append("M", _targets(ins))
            else:
                mark.append(ins)
            # data marker for round rr >= 1: right after the last readout of round rr-1
            if kind in ("x", "z") and rr >= 1 and i == last_round_idx[rr - 1]:
                add(self.data_qubits, "X_ERROR" if kind == "x" else "Z_ERROR", lambda q: (kind, q, rr))
        return mark, tags

    def with_dem(self, dem):
        from gen_leaky import DEMView, _BaseProxy
        v = DEMView.__new__(DEMView); v._lc = self; v.dem = dem; v.base = _BaseProxy(self.base, dem)
        return v


def _errs(circ):
    out = []
    for ins in circ.detector_error_model(decompose_errors=False).flattened():
        if ins.type != "error": continue
        out.append((round(ins.args_copy()[0], 9), tuple(sorted(t.val for t in ins.targets_copy() if t.is_relative_detector_id())),
                    tuple(sorted(t.val for t in ins.targets_copy() if t.is_logical_observable_id()))))
    return out


def _build_edge_lookup_robust(self):
    """Unique-probability markers as in LeakyCircuit; tags left ambiguous (merged mechanisms) are re-done one
    marker at a time (exact, slower)."""
    self.edge_of = {}; all_tags = set()
    jobs = [("x", r) for r in range(self.rounds)] + [("z", r) for r in range(self.rounds)] + \
           [("m", r) for r in range(self.rounds)] + [("f", self.rounds)] + [("ro", r) for r in range(self.rounds)]
    for kind, rr in jobs:
        mark, tags = self._marker_circuit(kind, rr); all_tags |= set(tags.values())
        errs = _errs(mark); counts = {}
        for pr, d, o in errs: counts[pr] = counts.get(pr, 0) + 1
        for pr, d, o in errs:
            t = tags.get(pr)
            if t is not None and counts[pr] == 1: self.edge_of[t] = (d, o)
        missing = [t for t in tags.values() if t not in self.edge_of]
        if not missing: continue
        # one marker at a time: keep only the instruction for this tag
        for t in missing:
            pr_t = [p for p, tt in tags.items() if tt == t][0]
            single = stim.Circuit()
            for ins in mark:
                if ins.name == "X_ERROR" or ins.name == "Z_ERROR":
                    if round(ins.gate_args_copy()[0], 9) != pr_t: continue
                if ins.name == "M" and ins.gate_args_copy() and round(ins.gate_args_copy()[0], 9) != pr_t:
                    single.append("M", [t.value for t in ins.targets_copy()]); continue
                single.append(ins)
            e = _errs(single)
            if e: self.edge_of[t] = (e[0][1], e[0][2])
    self.silent_markers = all_tags - set(self.edge_of)


NoResetLeakyCircuit._build_edge_lookup = _build_edge_lookup_robust


def predicted_detfrac(circuit):
    """Mean detector firing probability implied by the circuit's own noise model (exact for independent mechanisms)."""
    dem = circuit.detector_error_model(decompose_errors=False, approximate_disjoint_errors=True)
    acc = np.zeros(circuit.num_detectors)   # sum of log|1-2p|
    for ins in dem.flattened():
        if ins.type != "error": continue
        p = ins.args_copy()[0]; ds = [t.val for t in ins.targets_copy() if t.is_relative_detector_id()]
        if ds: acc[ds] += np.log(max(abs(1 - 2 * p), 1e-12))
    return float(np.mean((1 - np.exp(acc)) / 2))


def fit_noise_scale(circuit, dets, lo=0.3, hi=4.0, iters=30):
    """Label-free: one factor s for every noise probability so that the model's mean detection fraction equals the
    observed one (bisection). Returns s."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); import paths
    from gnnrnn.circuits import scale_noise
    target = float(np.mean(dets))
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if predicted_detfrac(scale_noise(circuit, mid)) < target: lo = mid
        else: hi = mid
    return 0.5 * (lo + hi)
