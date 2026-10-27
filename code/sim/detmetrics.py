import numpy as np
def det_metrics(pi, L, sub=4_000_000, seed=0):
    p = pi.reshape(-1).astype(np.float64); y = L.reshape(-1).astype(bool)
    if len(p) > sub:
        idx = np.random.default_rng(seed).choice(len(p), sub, replace=False); p, y = p[idx], y[idx]
    o = np.argsort(-p, kind='stable'); ys = y[o]; P = ys.sum(); Nn = len(ys) - P
    tp = np.cumsum(ys); fp = np.cumsum(~ys)
    ap = float((tp[ys] / (np.arange(len(ys))[ys] + 1)).sum() / max(P, 1))
    ranks = np.empty(len(p)); ranks[np.argsort(p, kind='stable')] = np.arange(1, len(p) + 1)
    auc = float((ranks[y].sum() - P * (P + 1) / 2) / max(P * Nn, 1))
    pred = p > 0.5; rec = float((pred & y).sum() / max(P, 1)); prec = float((pred & y).sum() / max(pred.sum(), 1))
    brier = float(((p - y) ** 2).mean()); base = float(y.mean())
    return dict(AP=ap, AUC=auc, recall=rec, precision=prec, brier=brier, base_rate=base)
