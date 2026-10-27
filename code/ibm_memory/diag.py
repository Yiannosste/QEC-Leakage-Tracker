import sys, json, numpy as np, stim
sys.path.insert(0, sys.path[0]); from ibm_common import *
runs = sys.argv[1:]
res = {}
for run in runs:
    dem, det, obs = load(run); N = len(obs)
    sim = dem.compile_sampler(seed=7).sample(N)[0].astype(np.uint8)
    P, ch = chains(dem)
    L = [c for c in ch if len(c) >= 5]
    def stats(D):
        rates = D.mean(0)
        # run-length histogram of consecutive firings along each chain
        hist = np.zeros(60)
        k3 = []
        for c in L:
            X = D[:, c].astype(np.int8)
            run = np.zeros(N, int)
            for t in range(X.shape[1]):
                run = np.where(X[:, t] == 1, run + 1, 0)
                ended = (run == 0) & (np.roll(run, 0) == 0)
            # count maximal runs
            pad = np.concatenate([np.zeros((N, 1), np.int8), X, np.zeros((N, 1), np.int8)], 1)
            dX = np.diff(pad, axis=1)
            starts = np.argwhere(dX == 1); ends = np.argwhere(dX == -1)
            lens = ends[:, 1] - starts[:, 1]
            h = np.bincount(np.minimum(lens, 59), minlength=60); hist += h
            # 3-round persistence: P(x_t & x_t+1 & x_t+2)
            if X.shape[1] >= 3: k3.append((X[:, :-2] & X[:, 1:-1] & X[:, 2:]).mean())
        return rates, hist, float(np.mean(k3))
    rr, hr, k3r = stats(det); rs, hs, k3s = stats(sim)
    # per-round detection fraction by chain position
    T = max(len(c) for c in L)
    pr = [float(np.mean([det[:, c[t]].mean() for c in L if len(c) > t])) for t in range(T)]
    ps = [float(np.mean([sim[:, c[t]].mean() for c in L if len(c) > t])) for t in range(T)]
    ratio = [(hr[k] + 1) / (hs[k] + 1) for k in range(1, 15)]
    res[run] = dict(period=P, n_chains=len(L), det_frac_real=float(det.mean()), det_frac_dem=float(sim.mean()),
                    per_round_real=pr, per_round_dem=ps, runlen_real=hr[:30].tolist(), runlen_dem=hs[:30].tolist(),
                    runlen_ratio_1to14=ratio, triple_real=k3r, triple_dem=k3s)
    print(f"{run}: P={P} chains={len(L)} det real {det.mean():.4f} dem {sim.mean():.4f} | triple real {k3r:.4f} dem {k3s:.4f} ratio {k3r/k3s:.2f}")
    print('   run-length ratio real/DEM k=1..12:', ' '.join(f'{x:.2f}' for x in ratio[:12]))
    print('   per-round real first/last 3:', [round(x,3) for x in pr[:3]], [round(x,3) for x in pr[-3:]], ' DEM:', [round(x,3) for x in ps[:3]], [round(x,3) for x in ps[-3:]])
json.dump(res, open(f"diag_{runs[0].replace('/','_')}.json", 'w'))
