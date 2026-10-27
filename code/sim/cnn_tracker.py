"""cnn_tracker.py - learned leakage tracker: a small causal 3D convolutional network on the detector lattice.

Input  : detector volume (shots, 3, R+1, d+1, d+1): channel 0 = detection event, channels 1-2 = static masks of
         Z-type / X-type stabiliser sites.  For fixed lag ell the time axis is shifted so that the output for round t
         sees detectors up to round t+ell; all time convolutions are causal (left padding only).
Output : (shots, 2, R, d, d): logits of P(L[q, t] = 1) and P(return at t) at the data-qubit positions (2x2 valid conv
         maps the (d+1)^2 stabiliser lattice onto the d^2 data-qubit lattice).
Training: BCE on simulated trajectories (labels = hidden leakage state from leakage_sim).
"""
import os
os.environ.setdefault("KMP_AFFINITY", "disabled")
import numpy as np, torch, torch.nn as nn, time
from leakage_sim import LeakyCircuit


class LatticeMap:
    def __init__(self, lc: LeakyCircuit):
        self.lc = lc; d, R = lc.d, lc.rounds
        self.d, self.R = d, R
        coords = lc.base.get_detector_coordinates()
        nd = lc.num_detectors
        self.det_ix = np.zeros(nd, int); self.det_iy = np.zeros(nd, int); self.det_t = np.zeros(nd, int)
        for i in range(nd):
            x, y, t = coords[i]; self.det_ix[i] = int(x) // 2; self.det_iy[i] = int(y) // 2; self.det_t[i] = int(t)
        assert self.det_ix.max() <= d and self.det_iy.max() <= d and self.det_t.max() == R
        # stabiliser type masks: a site is Z-type if it has a detector at t=0 (memory-Z), X-type otherwise
        self.maskZ = np.zeros((d + 1, d + 1), np.float32); self.maskX = np.zeros((d + 1, d + 1), np.float32)
        sites_t0 = set(zip(self.det_ix[self.det_t == 0], self.det_iy[self.det_t == 0]))
        for ix, iy in set(zip(self.det_ix, self.det_iy)):
            (self.maskZ if (ix, iy) in sites_t0 else self.maskX)[ix, iy] = 1
        qc = lc.base.get_final_qubit_coordinates()
        self.q_ix = np.array([int(qc[q][0]) // 2 for q in lc.data_qubits]); self.q_iy = np.array([int(qc[q][1]) // 2 for q in lc.data_qubits])
        assert self.q_ix.max() < d and self.q_iy.max() < d

    def to_volume(self, dets):
        """dets (N, nd) bool -> (N, 1, R+1, d+1, d+1) uint8 detector volume."""
        N = dets.shape[0]; V = np.zeros((N, 1, self.R + 1, self.d + 1, self.d + 1), np.uint8)
        V[:, 0, self.det_t, self.det_ix, self.det_iy] = dets.astype(np.uint8)
        return V

    def labels(self, L):
        """L (N, nq, R) -> leak (N, R, d, d), ret (N, R, d, d) uint8."""
        N = L.shape[0]; Y = np.zeros((N, 2, self.R, self.d, self.d), np.uint8)
        prev = np.concatenate([np.zeros_like(L[:, :, :1]), L[:, :, :-1]], 2); ret = (prev == 1) & (L == 0)
        Y[:, 0, :, self.q_ix, self.q_iy] = L.transpose(1, 0, 2)  # fancy indexing over qubit axis
        Y[:, 1, :, self.q_ix, self.q_iy] = ret.transpose(1, 0, 2)
        return Y

    def from_grid(self, G):
        """G (N, R, d, d) -> (N, nq, R)."""
        return G[:, :, self.q_ix, self.q_iy].transpose(0, 2, 1)


class CausalConv3d(nn.Module):
    def __init__(self, cin, cout, kt=3, ks=3):
        super().__init__(); self.kt = kt
        self.conv = nn.Conv3d(cin, cout, (kt, ks, ks), padding=(0, ks // 2, ks // 2))
    def forward(self, x):
        x = nn.functional.pad(x, (0, 0, 0, 0, self.kt - 1, 0))
        return self.conv(x)


class LeakNet(nn.Module):
    def __init__(self, ch=32, layers=3, kt=3):
        super().__init__()
        mods = [CausalConv3d(3, ch, kt), nn.ReLU()]
        for _ in range(layers - 1): mods += [CausalConv3d(ch, ch, kt), nn.ReLU()]
        self.body = nn.Sequential(*mods)
        self.head = nn.Conv3d(ch, 2, (1, 2, 2))   # (d+1)^2 -> d^2, per time step
    def forward(self, x):
        return self.head(self.body(x))


class CNNTracker:
    def __init__(self, lc, lag=0, ch=32, layers=3, kt=3, seed=0, threads=4):
        torch.manual_seed(seed); torch.set_num_threads(threads)
        self.lm = LatticeMap(lc); self.lag = lag; self.R = lc.rounds
        self.net = LeakNet(ch, layers, kt)
        self.masks = torch.from_numpy(np.stack([self.lm.maskZ, self.lm.maskX]))  # (2, d+1, d+1)

    def _input(self, V):
        """V (N,1,R+1,d+1,d+1) uint8 -> float tensor (N,3,R,d+1,d+1) shifted by lag (output t sees up to t+lag)."""
        N = V.shape[0]; R = self.R; lag = self.lag
        x = torch.from_numpy(V).float()
        # shift: new[t] = old[t + lag]; pad with zeros beyond the end (final slice R is included when t+lag >= R)
        if lag > 0:
            x = torch.cat([x[:, :, lag:], torch.zeros(N, 1, lag, x.shape[3], x.shape[4])], dim=2)
        x = x[:, :, :R]  # outputs for rounds 0..R-1
        m = self.masks[None, :, None].expand(N, 2, R, -1, -1)
        return torch.cat([x, m], dim=1)

    def fit(self, V, Y, epochs=4, batch=256, lr=1e-3, verbose=True, val=None):
        opt = torch.optim.Adam(self.net.parameters(), lr=lr)
        N = V.shape[0]; idx = np.arange(N); t0 = time.time()
        for ep in range(epochs):
            np.random.shuffle(idx); tot = 0.0; nb = 0
            self.net.train()
            for b in range(0, N, batch):
                sel = idx[b:b + batch]
                x = self._input(V[sel]); y = torch.from_numpy(Y[sel]).float()
                logits = self.net(x)
                loss = nn.functional.binary_cross_entropy_with_logits(logits, y)
                opt.zero_grad(); loss.backward(); opt.step(); tot += loss.item(); nb += 1
            msg = f"epoch {ep + 1}: train BCE {tot / nb:.5f}  ({time.time() - t0:.0f}s)"
            if val is not None:
                Vv, Yv = val; pl = self.predict(Vv)[0]
                yl = Yv[:, 0].astype(bool); pr = pl > 0.5
                tp = (pr & yl).sum(); msg += f"  val recall {tp / max(yl.sum(), 1):.3f} precision {tp / max(pr.sum(), 1):.3f}"
            if verbose: print(msg, flush=True)
        return self

    @torch.no_grad()
    def predict(self, V, batch=1024):
        """Returns leak probs (N, R, d, d) and return probs (N, R, d, d)."""
        self.net.eval(); outs = []
        for b in range(0, V.shape[0], batch):
            outs.append(torch.sigmoid(self.net(self._input(V[b:b + batch]))).numpy())
        P = np.concatenate(outs, 0)
        return P[:, 0], P[:, 1]

    def posteriors(self, dets):
        """dets (N, nd) -> pi_leak (N, nq, R), pi_ret (N, nq, R), pi_final (N, nq) in leakage_sim conventions."""
        V = self.lm.to_volume(dets); pl, pr = self.predict(V)
        pi_leak = self.lm.from_grid(pl); pi_ret = self.lm.from_grid(pr)
        return pi_leak, pi_ret, pi_leak[:, :, -1]

    def save(self, path): torch.save(self.net.state_dict(), path)
    def load(self, path): self.net.load_state_dict(torch.load(path)); return self


if __name__ == "__main__":
    from leakage_sim import FlagMatcher
    from hmm_tracker import flag_metrics
    t0 = time.time()
    lc = LeakyCircuit(5, 25, 1e-3, noise="si1000"); p_L, tau = 2e-3, 8
    lm = LatticeMap(lc)
    dtr, otr, Ltr = lc.sample(40000, p_L, tau, seed=101)
    dte, ote, Lte = lc.sample(20000, p_L, tau, seed=5)  # same test shots as the HMM test
    Vtr, Ytr = lm.to_volume(dtr), lm.labels(Ltr); Vte, Yte = lm.to_volume(dte), lm.labels(Lte)
    print("data ready %.0fs" % (time.time() - t0), Vtr.shape, Ytr.mean(axis=(0, 2, 3, 4)))
    fm = FlagMatcher(lc); e = lambda pred: (pred[:, 0] != ote[:, 0]).mean()
    eA = e(fm.decode_plain(dte)); eB = e(fm.decode_with_posteriors(dte, Lte.astype(float)))
    print("A %.4f B %.4f" % (eA, eB))
    for lag in (0, 2):
        tr = CNNTracker(lc, lag=lag, threads=8).fit(Vtr, Ytr, epochs=4, val=(Vte[:5000], Yte[:5000]))
        pl, pr, pf = tr.posteriors(dte); m = flag_metrics(pl, Lte)
        t1 = time.time(); eD = e(fm.decode_with_posteriors(dte, pl, pr, pf, thresh=0.02)); t2 = time.time()
        eE = e(fm.decode_with_posteriors(dte, (pl > 0.5).astype(float)))
        print("CNN lag %d: recall %.2f prec %.2f delay %.2f | D soft %.4f E hard %.4f | f_D %.0f%% f_E %.0f%% (decode %.0fs)" % (
            lag, m["recall"], m["precision"], m["mean_delay_detected"], eD, eE, 100 * (eA - eD) / (eA - eB), 100 * (eA - eE) / (eA - eB), t2 - t1), flush=True)
        tr.save(f"cnn_centre_lag{lag}.pt")
    print("total %.0fs" % (time.time() - t0))
