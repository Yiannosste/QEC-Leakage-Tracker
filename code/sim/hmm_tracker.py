"""hmm_tracker.py - per-data-qubit hidden Markov tracker of leakage from detection events only.

Hidden state per qubit q and round r: s_r = (L_{r-1}, L_r) in {00, 01, 10, 11} (4 states), so that emissions that
depend on two consecutive leakage states (a randomised measurement at round r flips detectors at r and r+1) are exact.
Transitions: L: 0->1 with p_L, 1->0 with p_ret.
Emissions at round r: the detectors with time coordinate r that the simulator's injection patterns touch for this
qubit; each such detector fires with probability  q_D (base rate)  XOR-combined with rho for every active influence
(L_r via the randomised measurement at r, L_{r-1} via the randomised measurement at r-1, 2/3 for the return
depolarisation at r, rho for the final data flip).  Detectors are treated as conditionally independent (approximation).

Outputs: filtered P(L_r = 1 | o_{<=r}) (lag 0) or fixed-lag smoothed P(L_r = 1 | o_{<= r+lag}); P(return at r); P(L_{R-1}).
"""
import numpy as np
from leakage_sim import LeakyCircuit, _xor_p


class LeakageHMM:
    def __init__(self, lc: LeakyCircuit, p_L, tau, eta_lru=0.0, rho=None, base_rates=None, calib_shots=20000, seed=123):
        self.lc = lc; self.rho = lc.rho if rho is None else rho
        self.p_L = p_L
        self.p_ret = 1.0 - (1.0 - 1.0 / tau) * (1.0 - eta_lru) if tau > 0 else 1.0
        R, nd = lc.rounds, lc.num_detectors
        self.R = R
        coords = lc.base.get_detector_coordinates()
        self.det_round = np.array([int(coords[i][2]) for i in range(nd)])
        if base_rates is None:
            dets, _ = lc.base.compile_detector_sampler(seed=seed).sample(calib_shots, separate_observables=True)
            base_rates = np.clip(dets.mean(0), 1e-4, 0.5)
        self.base_rates = base_rates
        # transition matrix over s = (L_prev, L_now) -> s' = (L_now, L_next)
        pL, pr = p_L, self.p_ret
        T = np.zeros((4, 4))
        # state index: 0=(0,0) 1=(0,1) 2=(1,0) 3=(1,1); s' first bit must equal s second bit
        for s in range(4):
            lnow = s & 1
            for s2 in range(4):
                if (s2 >> 1) != lnow: continue
                lnext = s2 & 1
                T[s, s2] = (pL if lnext else 1 - pL) if lnow == 0 else (1 - pr if lnext else pr)
        self.T = T
        # per-qubit emission tables: for each round r, list of (detector ids, influence matrix [4 states x nD])
        self.emis = {}
        for q in lc.data_qubits:
            self.emis[q] = self._build_emissions(q)

    def _base_edges(self):
        """Base DEM mechanisms as (p, dets) with decomposed components merged (cached)."""
        if hasattr(self, "_edges"): return self._edges
        acc = {}
        for ins in self.lc.dem.flattened():
            if ins.type != "error": continue
            p = ins.args_copy()[0]; comps = []; dets = []
            for t in ins.targets_copy():
                if t.is_separator(): comps.append(tuple(sorted(dets))); dets = []
                elif t.is_relative_detector_id(): dets.append(t.val)
            comps.append(tuple(sorted(dets)))
            for key in comps:
                if not key: continue
                q0 = acc.get(key, 0.0); acc[key] = q0 + p - 2 * q0 * p
        self._edges = [(p, d) for d, p in acc.items()]
        self._edges_by_det = {}
        for k, (p, d) in enumerate(self._edges):
            for D in d: self._edges_by_det.setdefault(D, []).append(k)
        return self._edges

    @staticmethod
    def _convolve(pmf, mask, p):
        """XOR-convolve a PMF over 2^n outcomes with an independent flip of `mask` occurring with prob p."""
        idx = np.arange(len(pmf)) ^ mask
        return (1 - p) * pmf + p * pmf[idx]

    def _build_emissions(self, q):
        """For each observation step t: detector ids Ds (time coordinate t, touched by q's influences) and a
        4 x 2^len(Ds) table of log P(outcome | state), with the base-noise joint PMF computed exactly from the
        DEM edges restricted to Ds, and leakage influences XOR-convolved on top."""
        lc, R, rho = self.lc, self.R, self.rho
        edges = self._base_edges()
        infl = {}  # detector -> list of (kind, round, prob, pattern-tag)
        pats = {}
        for r in range(R):
            for m in lc.adj[q]:
                tag = ("m", m, r)
                if tag in lc.edge_of:
                    pats[tag] = ("L", r, rho)
            for k in ("x", "z"):
                tag = (k, q, r)
                if tag in lc.edge_of: pats[tag] = ("RET", r, 2 / 3)
        tag = ("f", q, R)
        if tag in lc.edge_of: pats[tag] = ("L", R - 1, rho)
        steps = {}
        for tag in pats:
            for D in lc.edge_of[tag][0]:
                steps.setdefault(int(self.det_round[D]), set()).add(D)
        tables = {}
        for t, Dset in steps.items():
            Ds = sorted(Dset); n = len(Ds); pos = {D: j for j, D in enumerate(Ds)}
            # base joint PMF over the n detectors
            pmf = np.zeros(2 ** n); pmf[0] = 1.0
            seen = set()
            for D in Ds:
                for k in self._edges_by_det.get(D, []):
                    if k in seen: continue
                    seen.add(k); p, d = edges[k]
                    mask = sum(1 << pos[x] for x in d if x in pos)
                    if mask: pmf = self._convolve(pmf, mask, p)
            table = np.zeros((4, 2 ** n))
            for s in range(4):
                lprev, lnow = (s >> 1) & 1, s & 1
                pm = pmf.copy()
                for tag, (kind, r, c) in pats.items():
                    mask = sum(1 << pos[x] for x in lc.edge_of[tag][0] if x in pos)
                    if not mask: continue
                    active = False
                    if t < R:
                        if kind == "L" and ((r == t and lnow) or (r == t - 1 and lprev)): active = True
                        if kind == "RET" and r == t and lprev and not lnow: active = True
                    else:
                        if kind == "L" and r == R - 1 and lnow: active = True
                        if kind == "RET" and r == R - 1 and lprev and not lnow: active = True
                    if active: pm = self._convolve(pm, mask, c)
                table[s] = pm
            tables[t] = (np.array(Ds), np.log(np.clip(table, 1e-12, 1.0)), (1 << np.arange(n)))
        return tables

    def _loglik(self, dets_q_t, table, weights):
        idx = dets_q_t.astype(np.int64) @ weights
        return table[:, idx].T

    def _build_shot_emissions(self, q):
        """Per-step specs for shot-dependent emissions (independent-detector form):
        for step t: Ds, own[s][j] = list of extra flip probs active in state s for detector j (static),
        nbr[j] = list of (neighbour qubit index, round, prob) whose leakage posterior also randomises detector j."""
        lc, R, rho = self.lc, self.R, self.rho
        pats = {}
        for r in range(R):
            for m in lc.adj[q]:
                if ("m", m, r) in lc.edge_of: pats[("m", m, r)] = ("L", r, rho, m)
            for k in ("x", "z"):
                if (k, q, r) in lc.edge_of: pats[(k, q, r)] = ("RET", r, 2 / 3, None)
        if ("f", q, R) in lc.edge_of: pats[("f", q, R)] = ("L", R - 1, rho, None)
        steps = {}
        for tag in pats:
            for D in lc.edge_of[tag][0]: steps.setdefault(int(self.det_round[D]), set()).add(D)
        out = {}
        for t, Dset in steps.items():
            Ds = sorted(Dset); n = len(Ds); pos = {D: j for j, D in enumerate(Ds)}
            own = np.zeros((4, n)); own[:] = self.base_rates[Ds][None, :]
            nbr = [[] for _ in range(n)]
            for tag, (kind, r, c, m) in pats.items():
                for D in lc.edge_of[tag][0]:
                    if D not in pos: continue
                    j = pos[D]
                    for s in range(4):
                        lprev, lnow = (s >> 1) & 1, s & 1
                        active = False
                        if t < R:
                            if kind == "L" and ((r == t and lnow) or (r == t - 1 and lprev)): active = True
                            if kind == "RET" and r == t and lprev and not lnow: active = True
                        else:
                            if kind == "L" and r == R - 1 and lnow: active = True
                            if kind == "RET" and r == R - 1 and lprev and not lnow: active = True
                        if active: own[s, j] = _xor_p(own[s, j], c)
                    if m is not None:  # other data qubits adjacent to m leaked at round r also randomise this detector
                        for q2 in lc.data_qubits:
                            if q2 != q and m in lc.adj[q2]:
                                nbr[j].append((lc.qidx[q2], r, c))
            out[t] = (np.array(Ds), own, nbr)
        return out

    def posteriors(self, dets, lag=0, explain_away=0):
        """dets: shots x nd bool. lag = fixed smoothing lag (0 = causal filter; >= R = full smoothing).
        explain_away = number of mean-field iterations in which each qubit's emissions are conditioned on the
        other qubits' current leakage posteriors (0 = independent per-qubit HMMs)."""
        pi_leak, pi_ret, pi_final = self._posteriors_once(dets, lag, None)
        for _ in range(explain_away):
            pi_leak, pi_ret, pi_final = self._posteriors_once(dets, lag, pi_leak)
        return pi_leak, pi_ret, pi_final

    def _posteriors_once(self, dets, lag, pi_prev):
        lc, R, T = self.lc, self.R, self.T
        shots = dets.shape[0]
        if not hasattr(self, "shot_emis"):
            self.shot_emis = {q: self._build_shot_emissions(q) for q in lc.data_qubits}
        pi_leak = np.zeros((shots, lc.nq, R)); pi_ret = np.zeros_like(pi_leak); pi_final = np.zeros((shots, lc.nq))
        init = np.array([1.0, 0.0, 0.0, 0.0])
        for q in lc.data_qubits:
            i = lc.qidx[q]
            LL = np.zeros((R + 1, shots, 4))
            for t in range(R + 1):
                if pi_prev is None:
                    if t in self.emis[q]:
                        Ds, P, w = self.emis[q][t]; LL[t] = self._loglik(dets[:, Ds], P, w)
                else:
                    if t in self.shot_emis[q]:
                        Ds, own, nbr = self.shot_emis[q][t]
                        n = len(Ds)
                        extra = np.zeros((shots, n))
                        for j in range(n):
                            for (i2, r, c) in nbr[j]:
                                extra[:, j] = _xor_p(extra[:, j], c * pi_prev[:, i2, r])
                        p = _xor_p(own[None, :, :], extra[:, None, :])          # shots x 4 x n
                        p = np.clip(p, 1e-6, 1 - 1e-6)
                        x = dets[:, Ds].astype(float)[:, None, :]
                        LL[t] = (x * np.log(p) + (1 - x) * np.log(1 - p)).sum(2)
            alpha = np.zeros((R, shots, 4))
            a = init[None, :] * np.exp(LL[0]); a = a / a.sum(1, keepdims=True); alpha[0] = a
            for t in range(1, R):
                a = (alpha[t - 1] @ T) * np.exp(LL[t])
                if t == R - 1: a = a * np.exp(LL[R])
                a = a / np.maximum(a.sum(1, keepdims=True), 1e-300); alpha[t] = a
            post = np.zeros_like(alpha)
            for t in range(R):
                tend = min(R - 1, t + lag)
                beta = np.ones((shots, 4))
                for u in range(tend, t, -1):
                    e = np.exp(LL[u]) * (np.exp(LL[R]) if u == R - 1 else 1.0)
                    beta = (beta * e) @ T.T
                    beta = beta / np.maximum(beta.sum(1, keepdims=True), 1e-300)
                g = alpha[t] * beta
                post[t] = g / np.maximum(g.sum(1, keepdims=True), 1e-300)
            pi_leak[:, i, :] = (post[:, :, 1] + post[:, :, 3]).T
            pi_ret[:, i, :] = post[:, :, 2].T
            pi_final[:, i] = post[R - 1, :, 1] + post[R - 1, :, 3]
        return pi_leak, pi_ret, pi_final


def flag_metrics(pi_leak, L, thresh=0.5):
    """Recall, precision at a threshold, plus mean detection delay (rounds from true onset to first posterior > thresh
    within the episode) for the hard-thresholded posterior."""
    pred = pi_leak > thresh; true = L.astype(bool)
    tp = (pred & true).sum(); fp = (pred & ~true).sum(); fn = (~pred & true).sum()
    recall = tp / max(tp + fn, 1); precision = tp / max(tp + fp, 1)
    # delay: for each episode onset
    shots, nq, R = L.shape
    delays = []
    prev = np.concatenate([np.zeros((shots, nq, 1), dtype=bool), true[:, :, :-1]], axis=2)
    onset = true & ~prev
    s_idx, q_idx, r_idx = np.nonzero(onset)
    for s, q, r0 in zip(s_idx, q_idx, r_idx):
        r = r0; det = None
        while r < R and true[s, q, r]:
            if pred[s, q, r]: det = r - r0; break
            r += 1
        delays.append(det if det is not None else np.nan)
    delays = np.array(delays, dtype=float)
    return dict(recall=recall, precision=precision, n_episodes=len(delays),
                frac_episodes_detected=np.mean(~np.isnan(delays)) if len(delays) else np.nan,
                mean_delay_detected=np.nanmean(delays) if np.any(~np.isnan(delays)) else np.nan)


if __name__ == "__main__":
    import time
    from leakage_sim import FlagMatcher
    t0 = time.time()
    lc = LeakyCircuit(3, 10, 1e-3)
    p_L, tau = 3e-3, 5
    dets, obs, L = lc.sample(20000, p_L, tau, seed=5)
    hmm = LeakageHMM(lc, p_L, tau)
    fm = FlagMatcher(lc)
    e_ign = (fm.decode_plain(dets)[:, 0] != obs[:, 0]).mean()
    e_orc = (fm.decode_with_posteriors(dets, L.astype(float))[:, 0] != obs[:, 0]).mean()
    print("ignore %.4f oracle %.4f" % (e_ign, e_orc))
    for lag, ea in ((0, 0), (0, 2), (2, 0), (2, 2), (10, 2)):
        pl, pr, pf = hmm.posteriors(dets, lag=lag, explain_away=ea)
        m = flag_metrics(pl, L)
        e_soft = (fm.decode_with_posteriors(dets, pl, pr, pf, thresh=0.02)[:, 0] != obs[:, 0]).mean()
        e_hard = (fm.decode_with_posteriors(dets, (pl > 0.5).astype(float))[:, 0] != obs[:, 0]).mean()
        print("lag %2d ea %d: recall %.2f precision %.2f delay %.2f | soft %.4f hard %.4f | recovered %.0f%%" % (
            lag, ea, m["recall"], m["precision"], m["mean_delay_detected"], e_soft, e_hard, 100 * (e_ign - e_soft) / (e_ign - e_orc)))
    print("%.1f s" % (time.time() - t0))
