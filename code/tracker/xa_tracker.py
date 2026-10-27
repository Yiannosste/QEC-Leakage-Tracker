"""xa_tracker.py - per-data-qubit leakage tracker with explicit explaining-away of measurement errors.

Ideas combined (switches):
  idea 1  basis='both'  : all neighbouring checks, X- and Z-type, in one joint emission ('z' = Z-type checks only)
  idea 2  explain=True  : the measurement-flip bit f_{m,t} of every neighbouring check is part of the hidden state,
                          so one ordinary measurement error (which fires the same check in rounds t and t+1) is a
                          cheap, fully explained event instead of two independent rare events. Leakage only raises
                          P(f=1) from p_m to p_m XOR 1/2. Neighbouring data qubits that share a check are handled by
                          mean-field passes (explain_passes).  explain=False = joint within-round emission only.
  idea 3  herald        : optional final-readout leakage herald per data qubit, P(h=1|L)=eta, P(h=1|no L)=fh
  idea 4  calibrate()   : label-free Baum-Welch fit of per-qubit p_L, global return rate and rho on syndromes only;
                          the initial state (unleaked before round 0) gives round-dependent priors automatically.

State at round t: s = L_t + 2 * sum_j f_{j,t} 2^j  (explain=True, k neighbouring checks -> 2^(k+1) states)
                  s = L_t                          (explain=False)
Emission at round t depends on (s_{t-1}, s_t) (pair emission): detector outcomes of the neighbouring checks in round t
are  f_{j,t-1} XOR f_{j,t} XOR return flips XOR 'other' base noise, where 'other' is the exact joint distribution of
all remaining DEM mechanisms restricted to these detectors.
"""
import numpy as np
from leakage_sim import _xor_p


def _merged_edges(dem):
    acc = {}
    for ins in dem.flattened():
        if ins.type != "error": continue
        p = ins.args_copy()[0]; comps = []; dets = []
        for t in ins.targets_copy():
            if t.is_separator(): comps.append(frozenset(dets)); dets = []
            elif t.is_relative_detector_id(): dets.append(t.val)
        comps.append(frozenset(dets))
        for key in comps:
            if not key: continue
            q0 = acc.get(key, 0.0); acc[key] = q0 + p - 2 * q0 * p
    return acc


def _conv(pmf, mask, p):
    idx = np.arange(len(pmf)) ^ mask
    return (1 - p) * pmf + p * pmf[idx]


class XATracker:
    def __init__(self, lc, basis="both", explain=True, rho=0.5, p_L=1e-3, p_ret=0.125, herald=None,
                 explain_passes=8, exact_dem=True):
        self.lc, self.R = lc, lc.rounds
        self.basis, self.explain, self.herald, self.passes = basis, explain, herald, explain_passes
        self.sweep, self.damp = "jacobi", 0.5        # frozen on development data (2026-10-25): 8 passes, damping 0.5
        co = lc.base.get_detector_coordinates()
        self.det_round = np.array([int(co[i][2]) for i in range(lc.num_detectors)])
        self.det2m = {}
        for (k, m, r), (dets, o) in lc.edge_of.items():
            if k == "m":
                for D in dets: self.det2m[D] = m
        self.ztype = {m for (k, m, r), (dets, o) in lc.edge_of.items()
                      if k == "m" and any(self.det_round[D] == self.R for D in dets)}
        # exact_dem: undecomposed mechanisms (a Y error stays ONE event that fires X- and Z-checks together)
        self.edges = _merged_edges(lc.base.detector_error_model(decompose_errors=False) if exact_dem else lc.dem)
        self.by_det = {}
        for key in self.edges:
            for D in key: self.by_det.setdefault(D, []).append(key)
        self.set_params(p_L, p_ret, rho)

    # ------------------------------------------------------------------ parameters and tables
    def set_params(self, p_L, p_ret, rho):
        nq = self.lc.nq
        self.p_L = np.broadcast_to(np.asarray(p_L, float), (nq,)).copy()
        self.p_ret, self.rho = float(p_ret), float(rho)
        self._build()

    def _checks(self, q):
        adj = self.lc.adj[q]
        return [m for m in adj if self.basis == "both" or m in self.ztype]

    def _build(self):
        lc, R, rho = self.lc, self.R, self.rho
        self.tab = {}
        for q in lc.data_qubits:
            S = self._checks(q); k = len(S); ns = 2 ** (k + 1) if self.explain else 2
            mine = {D for D in self.det2m if self.det2m[D] in S}
            pat = {}
            for j, m in enumerate(S):
                for r in range(R):
                    if ("m", m, r) in lc.edge_of: pat[("m", j, r)] = frozenset(lc.edge_of[("m", m, r)][0])
            for kind in ("x", "z"):
                for r in range(R):
                    if (kind, q, r) in lc.edge_of: pat[(kind, r)] = frozenset(lc.edge_of[(kind, q, r)][0]) & mine
            if ("f", q, R) in lc.edge_of: pat[("f",)] = frozenset(lc.edge_of[("f", q, R)][0]) & mine
            # base probability of each check's measurement-flip mechanism
            pm = np.zeros((k, R))
            for (kk, *rest), dets in pat.items():
                if kk == "m": pm[rest[0], rest[1]] = self.edges.get(dets, 0.0)
            steps = {}
            for key, dets in pat.items():
                for D in dets:
                    if D in mine: steps.setdefault(int(self.det_round[D]), set()).add(D)
            Lbit = np.arange(ns) & 1
            fbits = (np.arange(ns) >> 1) if self.explain else np.zeros(ns, int)
            per_t = {}
            for t, Dset in steps.items():
                Ds = sorted(Dset); n = len(Ds); pos = {D: i for i, D in enumerate(Ds)}
                def mk(dets): return sum(1 << pos[D] for D in dets if D in pos)
                excl = set()
                if self.explain:
                    for j in range(k):
                        for r in (t - 1, t):
                            if ("m", j, r) in pat: excl.add(pat[("m", j, r)])
                pmf = np.zeros(2 ** n); pmf[0] = 1.0; seen = set()
                for D in Ds:
                    for key in self.by_det.get(D, []):
                        if key in seen or key in excl: continue
                        seen.add(key); msk = mk(key)
                        if msk: pmf = _conv(pmf, msk, self.edges[key])
                xm = mk(pat.get(("x", t), ())); zm = mk(pat.get(("z", t), ()))
                fm = mk(pat.get(("f",), ())) if t == R else 0
                mjp = [mk(pat.get(("m", j, t - 1), ())) for j in range(k)]
                mjc = [mk(pat.get(("m", j, t), ())) for j in range(k)]
                O = 2 ** n
                if t < R:
                    # G[o, s_prev, s_cur] = P(o | s_prev, s_cur)
                    G = np.zeros((O, ns, ns))
                    for sp in range(ns):
                        for sc in range(ns):
                            p = pmf.copy()
                            if self.explain:
                                msk = 0
                                for j in range(k):
                                    if (fbits[sp] >> j) & 1: msk ^= mjp[j]
                                    if (fbits[sc] >> j) & 1: msk ^= mjc[j]
                                p = p[np.arange(O) ^ msk]
                            else:
                                for j in range(k):
                                    if Lbit[sp] and mjp[j]: p = _conv(p, mjp[j], rho)
                                    if Lbit[sc] and mjc[j]: p = _conv(p, mjc[j], rho)
                            if Lbit[sp] and not Lbit[sc] and (xm or zm):   # depolarised on return: X, Y or Z
                                p = (p[np.arange(O) ^ xm] + p[np.arange(O) ^ (xm ^ zm)] + p[np.arange(O) ^ zm]) / 3
                            G[:, sp, sc] = p
                else:
                    # final data readout: depends on s_{R-1} only -> G[o, s]
                    G = np.zeros((O, ns))
                    for s in range(ns):
                        p = pmf.copy()
                        if self.explain:
                            msk = 0
                            for j in range(k):
                                if (fbits[s] >> j) & 1: msk ^= mjp[j]
                            p = p[np.arange(O) ^ msk]
                        else:
                            for j in range(k):
                                if Lbit[s] and mjp[j]: p = _conv(p, mjp[j], rho)
                        if Lbit[s] and fm: p = _conv(p, fm, rho)
                        G[:, s] = p
                per_t[t] = (np.array(Ds), (1 << np.arange(n)).astype(np.int64), np.clip(G, 1e-12, 1.0).astype(np.float32))
            # neighbours sharing each check (for mean-field)
            nbr = [[lc.qidx[q2] for q2 in lc.data_qubits if q2 != q and m in lc.adj[q2]] for m in S]
            self.tab[q] = dict(S=S, k=k, ns=ns, Lbit=Lbit, fbits=fbits, pm=pm, steps=per_t, nbr=nbr)

    # ------------------------------------------------------------------ inference
    def _F(self, q, t, pi_prev, N):
        """F[n, s] = P(f-bits of s | L of s) at round t (mean-field over neighbours' leakage)."""
        T = self.tab[q]; k, ns, Lbit, fbits = T["k"], T["ns"], T["Lbit"], T["fbits"]
        if not self.explain: return np.ones((N, ns))
        a = 1 - 2 * self.rho
        F = np.ones((N, ns), np.float32)
        for j in range(k):
            u = np.ones(N)
            if pi_prev is not None:
                for i2 in T["nbr"][j]: u = u * (1 - 2 * self.rho * pi_prev[:, i2, t])
            pf0 = _xor_p(T["pm"][j, t], (1 - u) / 2); pf1 = _xor_p(T["pm"][j, t], (1 - a * u) / 2)
            pfS = np.where(Lbit[None, :] == 1, pf1[:, None], pf0[:, None])
            bit = ((fbits >> j) & 1)[None, :] == 1
            F *= np.where(bit, pfS, 1 - pfS).astype(np.float32)
        return F

    def _run_qubit(self, q, dets, herald_q, pi_prev, lag=None, stats=False):
        lc, R = self.lc, self.R; T = self.tab[q]; ns, Lbit = T["ns"], T["Lbit"]; N = dets.shape[0]
        i = lc.qidx[q]; pL, pr = self.p_L[i], self.p_ret
        PL = np.array([[1 - pL, pL], [pr, 1 - pr]])
        PLs = PL[Lbit[:, None], Lbit[None, :]].astype(np.float32)       # ns x ns
        def obs(t):
            Ds, w, G = T["steps"][t]; return G[dets[:, Ds].astype(np.int64) @ w]
        def W(t):  # (N, ns, ns): P(s_t | s_{t-1}) P(o_t | s_{t-1}, s_t)
            F = self._F(q, t, pi_prev, N)
            E = obs(t) if t in T["steps"] else 1.0
            return PLs[None] * F[:, None, :] * E
        # final factor on s_{R-1}
        fin = obs(R) if R in T["steps"] else np.ones((N, ns))
        if herald_q is not None:
            eta, fh = self.herald
            h = herald_q.astype(bool)[:, None]
            fin = fin * np.where(Lbit[None, :] == 1, np.where(h, eta, 1 - eta), np.where(h, fh, 1 - fh))
        # forward (alpha_t excludes the final factor), log-scaled
        alpha = np.zeros((R, N, ns), np.float32); ll = np.zeros(N)
        a0 = np.array([1 - pL, pL])[Lbit][None, :] * self._F(q, 0, pi_prev, N)
        if 0 in T["steps"]:
            Ds, w, G = T["steps"][0]
            # round-0 detectors only see f_{.,0}: use s_prev = state with f=0, L=0
            a0 = a0 * G[dets[:, Ds].astype(np.int64) @ w][:, 0, :]
        z = a0.sum(1); alpha[0] = a0 / z[:, None]; ll += np.log(z)
        Ws = [None] * R
        for t in range(1, R):
            Wt = W(t); Ws[t] = Wt
            a = np.matmul(alpha[t - 1][:, None, :], Wt)[:, 0, :]
            z = a.sum(1); alpha[t] = a / z[:, None]; ll += np.log(z)
        zf = (alpha[R - 1] * fin).sum(1); ll += np.log(zf)
        # backward
        post = np.zeros((R, N, ns)); ret = np.zeros((N, R)); n01 = np.zeros(N); n10 = np.zeros(N); d1 = np.zeros(N)
        if lag is None:
            beta = fin / fin.sum(1, keepdims=True)
            g = alpha[R - 1] * beta; post[R - 1] = g / g.sum(1, keepdims=True)
            for t in range(R - 1, 0, -1):
                Wt = Ws[t]
                xi = alpha[t - 1][:, :, None] * Wt * beta[:, None, :]
                xi /= xi.sum((1, 2), keepdims=True)
                Lp, Lc = Lbit[:, None], Lbit[None, :]
                ret[:, t] = (xi * ((Lp == 1) & (Lc == 0))).sum((1, 2))
                if stats:
                    n01 += (xi * ((Lp == 0) & (Lc == 1))).sum((1, 2)); n10 += ret[:, t]
                    d1 += (xi * (Lp == 1)).sum((1, 2))
                beta = np.matmul(Wt, beta[:, :, None])[:, :, 0]; beta /= beta.sum(1, keepdims=True)
                g = alpha[t - 1] * beta; post[t - 1] = g / g.sum(1, keepdims=True)
        else:
            for t in range(R):
                tend = min(R - 1, t + lag)
                beta = fin / fin.sum(1, keepdims=True) if tend == R - 1 else np.ones((N, ns))
                for u in range(tend, t, -1):
                    beta = np.matmul(Ws[u], beta[:, :, None])[:, :, 0]; beta /= beta.sum(1, keepdims=True)
                g = alpha[t] * beta; post[t] = g / g.sum(1, keepdims=True)
            pl = post[:, :, Lbit == 1].sum(2).T
            ret = np.concatenate([np.zeros((N, 1)), np.clip(pl[:, :-1] - pl[:, 1:], 0, 1)], 1)
        pi = post[:, :, Lbit == 1].sum(2).T                              # (N, R)
        out = dict(pi=pi, ret=ret, ll=ll)
        if stats:
            out.update(n01=n01 + pi[:, 0], n10=n10, occ0=(1 - pi[:, :R - 1]).sum(1) + 1.0, occ1=pi[:, :R - 1].sum(1))
        return out

    def posteriors(self, dets, herald=None, lag=None, passes=None, chunk=2000, sweep=None, damp=None):
        """sweep='jacobi' (all qubits from the previous pass) or 'gs' (Gauss-Seidel: each qubit uses its neighbours'
        newest estimates, visited in a fixed order). damp in [0,1): pi <- damp*pi_old + (1-damp)*pi_new."""
        lc, R = self.lc, self.R; N = dets.shape[0]
        passes = self.passes if passes is None else passes
        sweep = getattr(self, "sweep", "jacobi") if sweep is None else sweep
        damp = getattr(self, "damp", 0.0) if damp is None else damp
        P = np.zeros((N, lc.nq, R), np.float32); Rt = np.zeros_like(P)
        for lo in range(0, N, chunk):
            sl = slice(lo, min(N, lo + chunk)); n = sl.stop - sl.start
            est = None; curr = np.zeros((n, lc.nq, R))
            for it in range((passes if self.explain else 0) + 1):
                new = np.zeros((n, lc.nq, R)) if (est is None or sweep == "jacobi") else est.copy()
                src = est
                for q in lc.data_qubits:
                    i = lc.qidx[q]
                    o = self._run_qubit(q, dets[sl], None if herald is None else herald[sl, i],
                                        src if sweep == "jacobi" else (new if est is not None else None), lag)
                    pi = o["pi"] if (est is None or damp == 0) else damp * est[:, i] + (1 - damp) * o["pi"]
                    new[:, i] = pi; curr[:, i] = o["ret"]
                est = new
            P[sl], Rt[sl] = est, curr
        return P, Rt, P[:, :, -1].copy()

    def loglik_and_stats(self, dets, herald=None, chunk=2000, passes=0):
        """Baum-Welch sufficient statistics. passes > 0: neighbours' leakage is explained by mean-field first."""
        lc, R = self.lc, self.R; N = dets.shape[0]
        acc = dict(ll=0.0, n01=np.zeros(lc.nq), occ0=np.zeros(lc.nq), n10=0.0, occ1=0.0)
        for lo in range(0, N, chunk):
            sl = slice(lo, min(N, lo + chunk)); prev = None
            if passes and self.explain:   # neighbours' leakage estimated with the same damped inference as decoding
                prev = self.posteriors(dets[sl], None if herald is None else herald[sl], passes=passes)[0].astype(np.float64)
            for q in lc.data_qubits:
                i = lc.qidx[q]
                o = self._run_qubit(q, dets[sl], None if herald is None else herald[sl, i], prev, stats=True)
                acc["ll"] += o["ll"].sum(); acc["n01"][i] += o["n01"].sum(); acc["occ0"][i] += o["occ0"].sum()
                acc["n10"] += o["n10"].sum(); acc["occ1"] += o["occ1"].sum()
        return acc

    def calibrate(self, dets, herald=None, per_qubit=True, iters=8, rho_grid=(0.5,), init=(3e-3, 0.25), verbose=False):
        """Label-free Baum-Welch on syndromes (and herald if given). Returns the fitted parameters."""
        best = None
        for rho in rho_grid:
            self.set_params(init[0], init[1], rho)
            for it in range(iters):
                acc = self.loglik_and_stats(dets, herald)
                pL = acc["n01"] / acc["occ0"] if per_qubit else np.full(self.lc.nq, acc["n01"].sum() / acc["occ0"].sum())
                pr = acc["n10"] / max(acc["occ1"], 1e-9)
                pL = np.clip(pL, 1e-6, 0.2); pr = float(np.clip(pr, 1e-3, 1.0))
                if verbose: print(f"  rho {rho} it {it}: ll/shot {acc['ll'] / len(dets):.4f} mean pL {pL.mean():.2e} p_ret {pr:.3f}", flush=True)
                self.set_params(pL, pr, rho)
            ll = self.loglik_and_stats(dets, herald)["ll"]
            if best is None or ll > best[0]: best = (ll, self.p_L.copy(), self.p_ret, rho)
        self.set_params(best[1], best[2], best[3])
        return dict(p_L=best[1].tolist(), p_ret=best[2], rho=best[3], ll_per_shot=best[0] / len(dets))
