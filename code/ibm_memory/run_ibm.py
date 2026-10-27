"""Run decoders A, X(lag,c), A4, P on one IBM run. Usage: run_ibm.py RUN NSHOTS LAG C [--controls] [--procs K]"""
import sys, os, json, time, numpy as np, multiprocessing as mp
os.environ.setdefault('KMP_AFFINITY', 'disabled')
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
from ibm_common import load, chains
import ibm_tracker as tr
run, N, lag, c = sys.argv[1], int(sys.argv[2]), sys.argv[3], float(sys.argv[4])
lag = 'full' if lag == 'full' else int(lag)
controls = '--controls' in sys.argv; deflate = '--deflate' in sys.argv; procs = int(sys.argv[sys.argv.index('--procs') + 1]) if '--procs' in sys.argv else 6
prm = json.load(open(paths.HMM_PARAMS_OLD)); prm = (prm['a'], prm['b'], prm['q'], prm['s'])
tag = f"{run.replace('/', '_')}_N{N}_L{lag}_c{c}" + ("_defl" if "--deflate" in sys.argv else "")
os.makedirs('out', exist_ok=True)
dem, det, obs = load(run); det, obs = det[:N], obs[:N]
P, ch = chains(dem); r = det.mean(0) if N == len(load(run)[2]) else load(run)[1].mean(0)   # marginal over all shots (no labels)
T = max(len(cc) for cc in ch); R = np.zeros((len(ch), T))
for j, cc in enumerate(ch): R[j, :len(cc)] = r[cc]
tr._init(run, P, ch); tl = tr._G['tl']
PI = np.zeros((N, len(tl)), np.float32)
for lo in range(0, N, 10000):
    X = tr.to_cube(det[lo:lo + 10000], ch, T)
    PI[lo:lo + 10000] = tr.edge_post(tr.posterior(X, R, prm, lag), tl)
    del X
def decode(PIm, name):
    f = f'out/{tag}_{name}.npy'
    if os.path.exists(f): return np.load(f)
    chunks = np.array_split(np.arange(N), procs * 4)
    t = time.time()
    with mp.get_context('fork').Pool(procs) as pool:
        pb = PI.mean(0) if deflate else None
        res = pool.map(tr._decode_chunk, [((ix, PIm[ix], c, 0.02, pb) if deflate else (ix, PIm[ix], c, 0.02)) for ix in chunks])
    pred = np.concatenate(res); fail = (pred != obs).astype(np.uint8); np.save(f, fail)
    print(f'  {name}: P_fail={fail.mean():.4f} ({time.time()-t:.0f}s)', flush=True); return fail
fA = f'out/{run.replace("/", "_")}_N{N}_A.npy'
if not os.path.exists(fA):
    pred = tr._G['m'].decode_batch(det)[:, 0]; np.save(fA, (pred != obs).astype(np.uint8))
A = np.load(fA); print(f'{tag}: A P_fail={A.mean():.4f}; mean edge pi={PI.mean():.3f}; frac>=0.02 {np.mean(PI>=0.02):.3f}', flush=True)
Xf = decode(PI, 'X')
if controls:
    decode(np.broadcast_to(PI.mean(0, keepdims=True), PI.shape), 'A4')
    perm = np.random.default_rng(0).permutation(N); decode(PI[perm], 'P')
