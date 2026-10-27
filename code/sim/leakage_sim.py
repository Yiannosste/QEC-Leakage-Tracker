"""leakage_sim.py - multi-round data-qubit leakage on top of Stim's rotated surface code (SYNTHETIC).

Model (per shot, hidden Markov state per data qubit q and round r):
  L[q, r] in {0, 1}.  Healthy -> leaked with probability p_L per round; leaked -> healthy with probability
  1/tau per round (geometric lifetime, mean tau rounds).  Optionally an LRU acts each round with efficiency
  eta_lru (leaked -> healthy with prob eta_lru in addition to the natural return).
  While leaked at round r, every stabiliser measurement adjacent to q in round r is randomised: its outcome
  is flipped with probability rho (default 1/2 = fully random outcome).
  On return at round r (L[q,r-1]=1, L[q,r]=0) the qubit is depolarised (random X, Y or Z with prob 1/3 each).
  If leaked during the final data measurement, that data outcome is flipped with probability rho.
  Measure-qubit leakage is assumed removed by multi-level reset every round (not modelled).

The hidden-state effects are Pauli injections (X/Z on a data qubit at a round start, X on a measure qubit
before its measurement, X on a data qubit before the final measurement).  For a stabiliser circuit every such
injection flips a fixed set of detectors/observables (found once from single-marker detector error models), so
the leaky sample = Stim's noisy detector sample XOR the injected patterns - exact and fast.  The oracle flag is
the hidden state itself.

Decoder side: leakage_edges() returns, for every (q, r), the detector-error-model edges that the leakage
mechanisms correspond to (time-like edges of adjacent stabilisers, X/Z data edges at the return round, final
data flip), so a matching decoder can re-weight them per shot (FlagMatcher).
"""
import numpy as np, stim, pymatching
from collections import defaultdict


def make_base_circuit(d, rounds, p, noise="si1000"):
    """noise = 'uniform' | 'si1000like' (Stim generator defaults with meas 5p, reset 2p, data idle p/10) |
    'si1000' (Gidney-Newman-McEwen 2021, Table 2: 2q gate p, 1q Clifford p/10, idle p/10, data idle during
    measurement/reset 2p, reset flip 2p, measurement flip 5p; here the 2q gate is the generator's CX)."""
    if noise == "uniform":
        return stim.Circuit.generated("surface_code:rotated_memory_z", distance=d, rounds=rounds,
            after_clifford_depolarization=p, before_round_data_depolarization=p,
            before_measure_flip_probability=p, after_reset_flip_probability=p)
    gen = stim.Circuit.generated("surface_code:rotated_memory_z", distance=d, rounds=rounds,
        after_clifford_depolarization=p, before_round_data_depolarization=p / 10,
        before_measure_flip_probability=5 * p, after_reset_flip_probability=2 * p)
    if noise == "si1000like":
        return gen
    assert noise == "si1000"
    flat = gen.flattened()
    data = _targets([ins for ins in flat if ins.name == "M"][-1])
    out = stim.Circuit()
    for ins in flat:
        if ins.name == "DEPOLARIZE1" and abs(ins.gate_args_copy()[0] - p) < 1e-15:
            out.append("DEPOLARIZE1", _targets(ins), p / 10)        # single-qubit Clifford: p/10
        elif ins.name == "MR":
            out.append("DEPOLARIZE1", data, 2 * p)                 # data-qubit idle during measurement+reset: 2p
            out.append(ins)
        else:
            out.append(ins)
    return out


def _targets(ins):
    return [t.value for t in ins.targets_copy()]


class LeakyCircuit:
    """Builds the sweep-instrumented circuit and the marker DEM for a (d, rounds, p) surface code memory."""

    def __init__(self, d, rounds, p, noise="si1000", rho=0.5):
        self.d, self.rounds, self.p, self.noise, self.rho = d, rounds, p, noise, rho
        base = make_base_circuit(d, rounds, p, noise)
        self.base = base
        flat = base.flattened()
        # ---- identify qubits and adjacency ----
        mr_layers = [i for i, ins in enumerate(flat) if ins.name == "MR"]
        final_m = [i for i, ins in enumerate(flat) if ins.name == "M"][-1]
        self.meas_qubits = _targets(flat[mr_layers[0]])
        self.data_qubits = _targets(flat[final_m])
        assert len(mr_layers) == rounds, (len(mr_layers), rounds)
        adj = defaultdict(set)
        for ins in flat:
            if ins.name in ("CX", "CZ"):
                t = _targets(ins)
                for a, b in zip(t[0::2], t[1::2]):
                    for x, y in ((a, b), (b, a)):
                        if x in self.data_qubits and y in self.meas_qubits:
                            adj[x].add(y)
        self.adj = {q: sorted(adj[q]) for q in self.data_qubits}
        self.nq, self.nm = len(self.data_qubits), len(self.meas_qubits)
        self.qidx = {q: i for i, q in enumerate(self.data_qubits)}
        self.midx = {m: i for i, m in enumerate(self.meas_qubits)}
        self._flat = flat
        self._final_m = [i for i, ins in enumerate(flat) if ins.name == "M"][-1]
        self.dem = base.detector_error_model(decompose_errors=True)
        self.num_detectors, self.num_observables = base.num_detectors, base.num_observables
        self.det_sampler = None
        self._build_edge_lookup()
        # pattern vectors (detectors + observables) for every injection tag
        nd, no = self.num_detectors, self.num_observables
        self.pattern = {}
        for tag, (dets, obs) in self.edge_of.items():
            v = np.zeros(nd + no, dtype=bool); v[list(dets)] = True; v[[nd + o for o in obs]] = True
            self.pattern[tag] = v

    # ------------------------------------------------------------------ marker DEMs -> edge lookup
    def _marker_circuit(self, kind, rr):
        """Noise-free base circuit with unique-probability single-Pauli markers of one kind at one round."""
        flat, final_m, R = self._flat, self._final_m, self.rounds
        mark = stim.Circuit(); tags = {}
        k = [0]
        def add(qs, pauli, tagfn):
            for q in qs:
                k[0] += 1; pr = 1e-3 + k[0] * 1e-6
                tags[round(pr, 9)] = tagfn(q)
                mark.append(pauli, [q], pr)
        r = 0; started = False
        for i, ins in enumerate(flat):
            if ins.name in ("DEPOLARIZE1", "DEPOLARIZE2", "X_ERROR", "Z_ERROR"):
                continue
            if not started and ins.name == "R":
                mark.append(ins); continue
            if not started and ins.name == "TICK":
                started = True
                if rr == 0 and kind in ("x", "z"):
                    add(self.data_qubits, "X_ERROR" if kind == "x" else "Z_ERROR", lambda q: (kind, q, 0))
                mark.append(ins); continue
            if ins.name == "MR":
                if kind == "m" and r == rr:
                    add(self.meas_qubits, "X_ERROR", lambda m: ("m", m, rr))
                mark.append(ins); r += 1
                if r < R and r == rr and kind in ("x", "z"):
                    add(self.data_qubits, "X_ERROR" if kind == "x" else "Z_ERROR", lambda q: (kind, q, rr))
                continue
            if i == final_m and kind == "f":
                add(self.data_qubits, "X_ERROR", lambda q: ("f", q, R))
            mark.append(ins)
        return mark, tags

    def _build_edge_lookup(self):
        self.edge_of = {}; self.silent_markers = set(); all_tags = set()
        jobs = [("x", rr) for rr in range(self.rounds)] + [("z", rr) for rr in range(self.rounds)] + \
               [("m", rr) for rr in range(self.rounds)] + [("f", self.rounds)]
        for kind, rr in jobs:
            mark, tags = self._marker_circuit(kind, rr)
            all_tags |= set(tags.values())
            dem = mark.detector_error_model(decompose_errors=False).flattened()
            errs = []
            for ins in dem:
                if ins.type != "error": continue
                pr = round(ins.args_copy()[0], 9)
                dets = tuple(sorted(t.val for t in ins.targets_copy() if t.is_relative_detector_id()))
                obs = tuple(sorted(t.val for t in ins.targets_copy() if t.is_logical_observable_id()))
                errs.append((pr, dets, obs))
            unmatched = []
            for pr, dets, obs in errs:
                tag = tags.get(pr)
                if tag is not None: self.edge_of[tag] = (dets, obs)
                else: unmatched.append((pr, dets, obs))
            # merged markers (degenerate errors with identical detector sets): resolve among still-missing tags
            missing = [(p, t) for p, t in tags.items() if t not in self.edge_of]
            for pr, dets, obs in unmatched:
                found = None
                for i in range(len(missing)):
                    for j in range(i + 1, len(missing)):
                        if abs(_xor_p(missing[i][0], missing[j][0]) - pr) < 2e-9: found = [i, j]; break
                        for k in range(j + 1, len(missing)):
                            if abs(_xor_p(_xor_p(missing[i][0], missing[j][0]), missing[k][0]) - pr) < 2e-9: found = [i, j, k]; break
                        if found: break
                    if found: break
                if found is None:
                    raise RuntimeError(f"unresolved merged markers in {kind},{rr}: p={pr} dets={dets}")
                for i in found: self.edge_of[missing[i][1]] = (dets, obs)
                missing = [m for n, m in enumerate(missing) if n not in found]
        self.silent_markers = all_tags - set(self.edge_of)

    # ------------------------------------------------------------------ sampling
    def sample_hidden(self, shots, p_L, tau, eta_lru=0.0, rng=None):
        """Hidden leakage state L[shot, q, r] (uint8)."""
        rng = np.random.default_rng(rng)
        R, nq = self.rounds, self.nq
        L = np.zeros((shots, nq, R), dtype=np.uint8)
        state = np.zeros((shots, nq), dtype=bool)
        p_ret = 1.0 - (1.0 - 1.0 / tau) * (1.0 - eta_lru) if tau > 0 else 1.0
        for r in range(R):
            u = rng.random((shots, nq))
            enter = (~state) & (u < p_L)
            leave = state & (u < p_ret)
            state = (state | enter) & ~leave
            L[:, :, r] = state
        return L

    def sample(self, shots, p_L, tau, eta_lru=0.0, rho=None, seed=0):
        """Returns dets (shots x num_detectors, bool), obs (shots x num_obs, bool), L (hidden state, uint8).
        Base circuit noise is sampled by Stim; leakage effects are Pauli injections whose detector/observable
        flip patterns are XORed in (exact for stabiliser circuits)."""
        rho = self.rho if rho is None else rho
        rng = np.random.default_rng(seed)
        R, nq, nm, nd = self.rounds, self.nq, self.nm, self.num_detectors
        L = self.sample_hidden(shots, p_L, tau, eta_lru, rng)
        ds = self.base.compile_detector_sampler(seed=int(rng.integers(2**31)))
        dets, obs = ds.sample(shots, separate_observables=True)
        tot = np.concatenate([dets, obs], axis=1)
        def inject(tag, sel):
            v = self.pattern.get(tag)
            if v is not None and sel.any():
                tot[sel] ^= v
        # 1) randomised adjacent stabiliser outcomes while leaked
        for q in self.data_qubits:
            i = self.qidx[q]
            leaked = L[:, i, :].astype(bool)
            for m in self.adj[q]:
                coins = rng.random((shots, R)) < rho
                flips = leaked & coins
                for r in range(R):
                    inject(("m", m, r), flips[:, r])
        # 2) depolarise on return (random X, Y or Z)
        prev = np.concatenate([np.zeros((shots, nq, 1), dtype=np.uint8), L[:, :, :-1]], axis=2)
        ret = (prev == 1) & (L == 0)
        pauli = rng.integers(0, 3, size=ret.shape)
        fx = ret & (pauli != 2); fz = ret & (pauli != 0)
        for q in self.data_qubits:
            i = self.qidx[q]
            for r in range(R):
                inject(("x", q, r), fx[:, i, r]); inject(("z", q, r), fz[:, i, r])
        # 3) final data measurement flipped if leaked at the last round
        lastleak = L[:, :, R - 1].astype(bool) & (rng.random((shots, nq)) < rho)
        for q in self.data_qubits:
            inject(("f", q, R), lastleak[:, self.qidx[q]])
        return tot[:, :nd], tot[:, nd:], L

    # ------------------------------------------------------------------ edges touched by leakage at (q, r)
    def leak_edges(self, q, r):
        """Edges whose probability rises while q is leaked in round r: time-like edges of adjacent stabilisers."""
        out = []
        for m in self.adj[q]:
            tag = ("m", m, r)
            if tag in self.edge_of:
                out.append(self.edge_of[tag])
        return out

    def return_edges(self, q, r):
        """Edges for the X and Z data error on q at the start of round r (depolarisation on return)."""
        out = []
        for k in ("x", "z"):
            tag = (k, q, r)
            if tag in self.edge_of:
                out.append(self.edge_of[tag])
        return out

    def final_edge(self, q):
        tag = ("f", q, self.rounds)
        return [self.edge_of[tag]] if tag in self.edge_of else []


def _xor_p(a, b):
    return a + b - 2 * a * b


class FlagMatcher:
    """PyMatching decoder whose edge weights can be raised per shot from leakage flags / posteriors."""

    def __init__(self, lc: LeakyCircuit):
        self.lc = lc
        self.matching = pymatching.Matching.from_detector_error_model(lc.dem)
        # base edge table from the matching graph
        self.base = {}
        for u, v, data in self.matching.edges():
            key = (u, v) if v is not None else (u, None)
            self.base[frozenset([u, v]) if v is not None else frozenset([u, "B"])] = (
                u, v, float(data["weight"]), set(data["fault_ids"]), float(data.get("error_probability", np.nan)))
        self.nd = lc.num_detectors

    def _key(self, dets):
        if len(dets) == 1:
            return frozenset([dets[0], "B"])
        return frozenset(dets)

    def _set_edge(self, dets, obs, p_add):
        key = self._key(dets)
        if key in self.base:
            u, v, w, fids, p0 = self.base[key]
            p0 = p0 if np.isfinite(p0) else 1 / (1 + np.exp(w))
            fids_use = fids
        else:  # edge not in the base graph (should be rare) -> create it
            u = dets[0]; v = dets[1] if len(dets) == 2 else None
            p0 = 0.0; fids_use = set(obs)
        p_new = min(_xor_p(p0, p_add), 0.5 - 1e-6)
        w_new = float(np.log((1 - p_new) / p_new))
        if len(dets) == 2:
            self.matching.add_edge(dets[0], dets[1], fault_ids=fids_use, weight=w_new, merge_strategy="replace")
        else:
            self.matching.add_boundary_edge(dets[0], fault_ids=fids_use, weight=w_new, merge_strategy="replace")
        return key

    def _restore(self, keys):
        for key in keys:
            if key in self.base:
                u, v, w, fids, p0 = self.base[key]
                if v is None:
                    self.matching.add_boundary_edge(u, fault_ids=fids, weight=w, merge_strategy="replace")
                else:
                    self.matching.add_edge(u, v, fault_ids=fids, weight=w, merge_strategy="replace")
            else:  # edge we created: make it effectively absent
                nodes = [n for n in key if n != "B"]
                if len(nodes) == 2:
                    self.matching.add_edge(nodes[0], nodes[1], weight=50.0, merge_strategy="replace")
                else:
                    self.matching.add_boundary_edge(nodes[0], weight=50.0, merge_strategy="replace")

    def decode_with_posteriors(self, dets, pi_leak, pi_ret=None, pi_final=None, rho=None, thresh=0.0):
        """dets: shots x nd bool. pi_leak[shot, q, r] = P(leaked at round r); pi_ret[shot, q, r] = P(return at r)
        (if None, derived as pi_leak[r-1]*(1-pi_leak[r]) ... approximated by max(0, pi_leak[r-1]-pi_leak[r]));
        pi_final[shot, q] = P(leaked at last round) (defaults to pi_leak[:, :, -1]). Entries below `thresh` are ignored.
        Returns predicted observable flips (shots x 1)."""
        lc = self.lc; rho = lc.rho if rho is None else rho
        shots = dets.shape[0]
        if pi_ret is None:
            prev = np.concatenate([np.zeros_like(pi_leak[:, :, :1]), pi_leak[:, :, :-1]], axis=2)
            pi_ret = np.clip(prev - pi_leak, 0, 1)
        if pi_final is None:
            pi_final = pi_leak[:, :, -1]
        pred = np.zeros((shots, lc.num_observables), dtype=np.uint8)
        for s in range(shots):
            touched = []
            qs, rs = np.nonzero(pi_leak[s] > thresh)
            for i, r in zip(qs, rs):
                q = lc.data_qubits[i]
                for dets_e, obs_e in lc.leak_edges(q, r):
                    touched.append(self._set_edge(dets_e, obs_e, rho * pi_leak[s, i, r]))
            qs, rs = np.nonzero(pi_ret[s] > thresh)
            for i, r in zip(qs, rs):
                q = lc.data_qubits[i]
                for dets_e, obs_e in lc.return_edges(q, r):
                    touched.append(self._set_edge(dets_e, obs_e, (2 / 3) * pi_ret[s, i, r]))
            for i in np.nonzero(pi_final[s] > thresh)[0]:
                q = lc.data_qubits[i]
                for dets_e, obs_e in lc.final_edge(q):
                    touched.append(self._set_edge(dets_e, obs_e, rho * pi_final[s, i]))
            pred[s] = self.matching.decode(dets[s])
            if touched:
                self._restore(set(touched))
        return pred

    def decode_plain(self, dets):
        return self.matching.decode_batch(dets)


def wilson(k, n, z=1.96):
    p = k / n; den = 1 + z * z / n; cen = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return cen - half, cen + half


def per_round(p_log, r):
    p_log = np.clip(p_log, 1e-12, 0.5 - 1e-12)
    return 0.5 * (1 - (1 - 2 * p_log) ** (1 / r))


if __name__ == "__main__":
    import time
    t0 = time.time()
    lc = LeakyCircuit(3, 5, 1e-3)
    print("qubits", lc.nq, lc.nm, "edges found", len(lc.edge_of),
          "silent", len(lc.silent_markers))
    dets, obs, L = lc.sample(20000, p_L=0.0, tau=5, seed=1)
    base = lc.base.compile_detector_sampler(seed=1).sample(20000, separate_observables=True)
    print("p_L=0 detection fraction: leaky %.5f  plain %.5f" % (dets.mean(), base[0].mean()))
    fm = FlagMatcher(lc)
    dets, obs, L = lc.sample(20000, p_L=5e-3, tau=5, seed=2)
    print("p_L=5e-3: leaked fraction of (q,r) %.4f, detection fraction %.4f" % (L.mean(), dets.mean()))
    pred0 = fm.decode_plain(dets)
    t1 = time.time(); pred1 = fm.decode_with_posteriors(dets, L.astype(float)); t2 = time.time()
    e0 = (pred0[:, 0] != obs[:, 0]).mean(); e1 = (pred1[:, 0] != obs[:, 0]).mean()
    print("LER ignore flags %.4f, oracle flags %.4f  (%.1f s for %d shots)" % (e0, e1, t2 - t1, len(dets)))
    print("total %.1f s" % (time.time() - t0))
