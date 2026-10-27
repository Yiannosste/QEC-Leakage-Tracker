"""Load ibm_miami (Zenodo 21336494) shots exactly as the authors' helpers/decode.py does:
bitstring k -> (k + '0'*n_noiseless)[::-1] -> measurements -> stim m2d converter -> detection events, observable."""
import pickle, numpy as np, stim, sys, os
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
ROOT = paths.MIAMI   # docs/DATA.md
sys.path.insert(0, os.path.join(ROOT, 'helpers'))
try:
    from decode import _count_measurements, _qiskit_measure_count   # authors' helpers/decode.py (needs the download)
except ModuleNotFoundError:
    _count_measurements = _qiskit_measure_count = None
_cache = {}
def circuits(fig):
    if fig not in _cache:
        _cache[fig] = (pickle.load(open(f'{ROOT}/inputs/{fig}/circuits.pkl', 'rb')), pickle.load(open(f'{ROOT}/inputs/{fig}/device_results.pkl', 'rb')))
    return _cache[fig]
def case_list(fig):
    C, _ = circuits(fig); return C.get('case_index') or C.get('code_index') or C.get('index')
def bitstrings(fig, i):
    C, R = circuits(fig)
    if isinstance(R, dict):   # fig2-style: dict of strategy -> list
        raise NotImplementedError
    return R[i]
def load(fig, i, want_obs=False):
    C, R = circuits(fig); depth, sc, qk = C['codes'][i][:3]
    n0, n1 = _count_measurements(sc); assert n1 == _qiskit_measure_count(qk)
    bs = R[i]; m = np.array([[c == '1' for c in (k + '0' * n0)[::-1]] for k in bs], dtype=bool)
    det, obs = sc.compile_m2d_converter().convert(measurements=m, separate_observables=True)
    return (sc, det, obs[:, 0]) if want_obs else (sc, det)
