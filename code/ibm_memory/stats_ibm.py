"""Apply the frozen primary/secondary rules of ibm_protocol.md to saved per-shot failure arrays."""
import numpy as np, glob, json, sys
from scipy.stats import binomtest
RUNS = [f'memory_d3_q85_T{T}' for T in (5, 10, 20, 30, 50)] + [f'memory_d5_q85_T{T}' for T in (5, 10, 20, 30, 50)]
def eps(P, T): return 0.5 * (1 - (1 - 2 * P) ** (1 / T))
def holm(ps):
    o = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0
    for k, i in enumerate(o): run = max(run, (m - k) * ps[i]); adj[i] = min(1, run)
    return adj
def boot_ratio(fA, fX, T, B=2000, seed=42):
    rng = np.random.default_rng(seed); N = len(fA); r = []
    # multinomial over the 4 joint categories (fast, distributionally identical to shot resampling)
    cats = fA * 2 + fX; cnt = np.bincount(cats, minlength=4); pr = cnt / N
    for _ in range(B):
        c = rng.multinomial(N, pr); pa = (c[2] + c[3]) / N; px = (c[1] + c[3]) / N
        r.append(eps(px, T) / eps(pa, T))
    return np.percentile(r, [2.5, 97.5])
def analyse(variant, alpha):
    sfx = '_defl' if variant == "X'" else ''
    rows = []; pool = dict(XA=[0, 0], XA4=[0, 0], PA=[0, 0])
    for run in RUNS:
        T = int(run.split('_T')[1]); base = f'out/{run}_N100000'
        try:
            A = np.load(f'{base}_A.npy'); X = np.load(f'{base}_Lfull_c0.25{sfx}_X.npy')
            A4 = np.load(f'{base}_Lfull_c0.25{sfx}_A4.npy'); P = np.load(f'{base}_Lfull_c0.25{sfx}_P.npy')
        except FileNotFoundError: continue
        def disc(ref, x): return int(((ref == 1) & (x == 0)).sum()), int(((ref == 0) & (x == 1)).sum())
        r = dict(run=run, T=T, PA=A.mean(), PX=X.mean(), PA4=A4.mean(), PP=P.mean())
        for key, (ref, x) in dict(XA=(A, X), XA4=(A4, X), PA=(A, P)).items():
            b, c = disc(ref, x); r[f'{key}_b'], r[f'{key}_c'] = b, c
            r[f'{key}_p'] = binomtest(b, b + c, 0.5).pvalue if b + c else 1.0
            pool[key][0] += b; pool[key][1] += c
        r['eps_ratio'] = eps(r['PX'], T) / eps(r['PA'], T); r['ci'] = boot_ratio(A, X, T).tolist()
        rows.append(r)
    for key in ('XA', 'XA4', 'PA'):
        adj = holm(np.array([r[f'{key}_p'] for r in rows]))
        for r, a in zip(rows, adj): r[f'{key}_holm'] = float(a)
    res = {}
    for key, (b, c) in pool.items(): res[key] = dict(b=b, c=c, p=float(binomtest(b, b + c, 0.5).pvalue))
    primary = (res['XA']['b'] > res['XA']['c'] and res['XA']['p'] < alpha and
               res['XA4']['b'] > res['XA4']['c'] and res['XA4']['p'] < alpha and
               not (res['PA']['b'] > res['PA']['c'] and res['PA']['p'] < alpha))
    return rows, res, primary
out = {}
for v, alpha in (('X', 0.05), ("X'", 0.025)):
    rows, res, primary = analyse(v, alpha)
    out[v] = dict(rows=rows, pooled=res, primary_met=bool(primary), n_runs=len(rows), alpha=alpha)
    print(f'=== {v}  (runs available: {len(rows)}/10, alpha={alpha})')
    for r in rows:
        print(f"{r['run']:18s} A {r['PA']:.4f} X {r['PX']:.4f} A4 {r['PA4']:.4f} P {r['PP']:.4f} | eps ratio {r['eps_ratio']:.3f} [{r['ci'][0]:.3f},{r['ci'][1]:.3f}] | X vs A b/c {r['XA_b']}/{r['XA_c']} holm {r['XA_holm']:.3g} | X vs A4 {r['XA4_b']}/{r['XA4_c']} | P vs A {r['PA_b']}/{r['PA_c']}")
    print('  pooled:', json.dumps(res), '| PRIMARY MET:', primary)
json.dump(out, open('ibm_stats.json', 'w'), indent=1, default=float)
