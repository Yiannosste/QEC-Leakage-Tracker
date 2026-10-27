"""xa_tracker_r.py - variant R of the ALL tracker for circuits WITHOUT ancilla reset.

In such circuits a readout error of check j at round t-2 fires the detectors of j at rounds t-2 and t. The base tracker
keeps this mechanism in the round-t background with its prior probability p, i.e. it treats the two detection events
as independent. Variant R replaces, per shot, the prior p of every readout mechanism (j, t-2) in the round-t emission
by its probability given the observed detector d_(j,t-2):
    r = p(1-q) / (p(1-q) + (1-p)q)   if d_(j,t-2) = 1,      r = p q / (p q + (1-p)(1-q))   if d_(j,t-2) = 0,
where q is the firing probability of d_(j,t-2) from all OTHER background mechanisms. The emission becomes the mixture
sum_S prod_{j in S} r_j prod_{j not in S} (1 - r_j) G_ex(o XOR mask_S), with G_ex built without these mechanisms.
Everything else (state, mean-field, calibration, decoding rule) is unchanged. Requires lc.edge_of[('ro', m, r)].
"""
import numpy as np
from xa_tracker import XATracker, _conv


class XATrackerR(XATracker):
    def _build(self):
        super()._build()
        lc, R = self.lc, self.R
        # background firing probability of every detector (log-sum over all mechanisms)
        acc = np.zeros(lc.num_detectors)
        for key, p in self.edges.items():
            for D in key: acc[D] += np.log(max(abs(1 - 2 * p), 1e-12))
        self._fire = (1 - np.exp(acc)) / 2
        self.ro = {}
        for q in lc.data_qubits:
            T = self.tab[q]; S = T["S"]; per = {}
            for t, (Ds, w, G) in list(T["steps"].items()):
                pos = {int(D): i for i, D in enumerate(Ds)}; items = []
                for j, m in enumerate(S):
                    tag = ("ro", m, t - 2)
                    if tag not in lc.edge_of: continue
                    key = frozenset(lc.edge_of[tag][0]); p = self.edges.get(key, 0.0)
                    here = [D for D in key if D in pos]; before = [D for D in key if self.det_round[D] == t - 2]
                    if not here or len(before) != 1 or p <= 0: continue
                    mask = sum(1 << pos[D] for D in here); Db = before[0]
                    pf = self._fire[Db]; q_other = (pf - p) / (1 - 2 * p)        # firing prob without this mechanism
                    items.append((mask, p, int(Db), float(np.clip(q_other, 1e-6, 0.5))))
                if not items: continue
                # remove these mechanisms from G (deconvolution of an independent XOR mechanism)
                Gx = G.astype(np.float64)
                for mask, p, Db, qo in items:
                    idx = np.arange(Gx.shape[0]) ^ mask
                    Gx = ((1 - p) * Gx - p * Gx[idx]) / (1 - 2 * p)
                T["steps"][t] = (Ds, w, np.clip(Gx, 1e-12, 1.0).astype(np.float32))
                per[t] = items
            self.ro[q] = per

    def _run_qubit(self, q, dets, herald_q, pi_prev, lag=None, stats=False):
        per = self.ro.get(q, {})
        if not per: return super()._run_qubit(q, dets, herald_q, pi_prev, lag, stats)
        T = self.tab[q]; saved = T["steps"]
        # per-shot emission tables are not expressible as one G; wrap them so obs(t) computes the mixture
        T["steps"] = {t: (_Mix(v, per.get(t), dets) if t in per else v) for t, v in saved.items()}
        try:
            return super()._run_qubit(q, dets, herald_q, pi_prev, lag, stats)
        finally:
            T["steps"] = saved


class _Mix(tuple):
    """Stand-in for (Ds, w, G) whose G[index] returns the per-shot mixture over readout flips at t-2."""
    def __new__(cls, v, items, dets):
        Ds, w, G = v; return super().__new__(cls, (Ds, w, _MixG(G, items, dets)))


class _MixG:
    def __init__(self, G, items, dets):
        self.G, self.items, self.shape = G, items, G.shape
        d = dets
        self.r = []
        for mask, p, Db, qo in items:
            x = d[:, Db].astype(bool)
            r1 = p * (1 - qo) / (p * (1 - qo) + (1 - p) * qo); r0 = p * qo / (p * qo + (1 - p) * (1 - qo))
            self.r.append(np.where(x, r1, r0).astype(np.float32))
    def __getitem__(self, idx):
        idx = np.asarray(idx); out = None; k = len(self.items)
        for sub in range(1 << k):
            wgt = np.ones(len(idx), np.float32); m = 0
            for j in range(k):
                if (sub >> j) & 1: wgt = wgt * self.r[j]; m ^= self.items[j][0]
                else: wgt = wgt * (1 - self.r[j])
            term = self.G[idx ^ m] * wgt.reshape((-1,) + (1,) * (self.G.ndim - 1))
            out = term if out is None else out + term
        return out
