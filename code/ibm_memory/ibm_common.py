"""Shared helpers for the IBM ibm_berlin real-data test (C3 project). Data: Zenodo 23335425."""
import stim, pymatching, numpy as np, collections
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
ROOT = paths.IBM_BERLIN   # docs/DATA.md

def load(run):
    p = f'{ROOT}/{run}'
    dem = stim.DetectorErrorModel.from_file(f'{p}/error_model.dem'); n = dem.num_detectors
    det = stim.read_shot_data_file(path=f'{p}/detection_events.b8', format='b8', num_detectors=n)
    obs = stim.read_shot_data_file(path=f'{p}/logical_flips.b8', format='b8', num_detectors=0, num_observables=1)[:, 0]
    return dem, det, obs

def dem_errors(dem):
    out = []
    for inst in dem.flattened():
        if inst.type == 'error':
            ds = tuple(t.val for t in inst.targets_copy() if t.is_relative_detector_id())
            ob = any(t.is_logical_observable_id() for t in inst.targets_copy())
            out.append((inst.args_copy()[0], ds, ob))
    return out

def period(dem):
    c = collections.Counter()
    for p, ds, ob in dem_errors(dem):
        if len(ds) == 2: c[abs(ds[1] - ds[0])] += 1
    return c.most_common(1)[0][0]

def chains(dem):
    """Follow time-like edges (index difference = period) to group detectors into per-check chains."""
    P = period(dem); n = dem.num_detectors
    nxt = {}
    for p, ds, ob in dem_errors(dem):
        if len(ds) == 2 and abs(ds[1] - ds[0]) == P:
            a, b = sorted(ds); nxt[a] = b
    has_prev = set(nxt.values()); out = []
    for i in range(n):
        if i in has_prev: continue
        ch = [i]
        while ch[-1] in nxt: ch.append(nxt[ch[-1]])
        out.append(ch)
    return P, out
