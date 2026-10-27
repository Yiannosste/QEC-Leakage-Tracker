"""Aggregate detect2 test grid: apply pre-registered P1/P2 rules, pooled McNemar, secondary summaries."""
import json, glob, os
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
from scipy.stats import binomtest
CELLS = {0:'p0.001_hom',1:'p0.002_hom',2:'p0.003_hom',3:'p0.001_het',4:'p0.002_het',5:'p0.003_het'}
PRIMARY = [1,2,4,5]
R = {i: json.load(open(f'{paths.DET2}/{n}/results.json')) for i,n in CELLS.items() if os.path.exists(f'{paths.DET2}/{n}/results.json')}
out = {'cells_done':[CELLS[i] for i in R], 'per_cell':{}, 'P1':{}, 'P2':{}, 'secondary_pooled':{}}
for i,r in R.items():
    out['per_cell'][CELLS[i]] = {k:{'f':v['f'],'f_ci':v['f_ci'],'AP':v['det']['AP'],'prec':v['det']['precision'],'rec':v['det']['recall'],'pfail':v['pfail']} for k,v in r['trackers'].items()}
    out['per_cell'][CELLS[i]]['_A'] = r['pfail_A']; out['per_cell'][CELLS[i]]['_B'] = r['pfail_B']
prim = [i for i in PRIMARY if i in R]
out['primary_cells_done'] = [CELLS[i] for i in prim]
p1 = {CELLS[i]: {'AP_ALL':R[i]['trackers']['ALL']['det']['AP'], 'AP_old_hmm':R[i]['trackers']['old_hmm']['det']['AP'], 'AP_old_cnn':R[i]['trackers']['old_cnn']['det']['AP']} for i in prim}
out['P1']['cells'] = p1
out['P1']['met'] = all(v['AP_ALL']>v['AP_old_hmm'] and v['AP_ALL']>v['AP_old_cnn'] for v in p1.values()) and len(prim)==4
def pooled(key, cells):
    x = sum(R[i]['mcnemar'][key]['x_right_only'] for i in cells if key in R[i]['mcnemar'])
    y = sum(R[i]['mcnemar'][key]['y_right_only'] for i in cells if key in R[i]['mcnemar'])
    p = binomtest(x, x+y, 0.5).pvalue if x+y else 1.0
    return {'x_right_only':x,'y_right_only':y,'p':p,'n_cells':sum(key in R[i]['mcnemar'] for i in cells)}
for key in ['ALL_vs_old_cnn','ALL_vs_old_hmm']:
    out['P2'][key] = pooled(key, prim)
out['P2']['met_vs_cnn'] = out['P2']['ALL_vs_old_cnn']['x_right_only']>out['P2']['ALL_vs_old_cnn']['y_right_only'] and out['P2']['ALL_vs_old_cnn']['p']<0.05
out['P2']['met_vs_hmm'] = out['P2']['ALL_vs_old_hmm']['x_right_only']>out['P2']['ALL_vs_old_hmm']['y_right_only'] and out['P2']['ALL_vs_old_hmm']['p']<0.05
out['P2']['met'] = len(prim)==4 and out['P2']['met_vs_cnn'] and out['P2']['met_vs_hmm']
keys = sorted({k for i in R for k in R[i]['mcnemar']})
for key in keys:
    out['secondary_pooled'][key+'|primary'] = pooled(key, prim)
    out['secondary_pooled'][key+'|all_cells'] = pooled(key, list(R))
json.dump(out, open(f'{paths.RESULTS_DATA}/det2_aggregate.json','w'), indent=1, default=lambda o: o.item() if hasattr(o,'item') else str(o))
print('cells', out['cells_done']); print('P1', out['P1']['met'], {c:(round(v['AP_ALL'],3),round(v['AP_old_cnn'],3),round(v['AP_old_hmm'],3)) for c,v in p1.items()})
print('P2', out['P2'])
for k,v in out['secondary_pooled'].items(): print(f"{k:32s} {v['x_right_only']:5d} {v['y_right_only']:5d} p={v['p']:.3g} n={v['n_cells']}")
