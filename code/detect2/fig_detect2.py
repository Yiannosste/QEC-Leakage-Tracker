import json, numpy as np, matplotlib as mpl, matplotlib.pyplot as plt
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
from figstyle import apply_figure_style, META_GREY
A = json.load(open(f'{paths.RESULTS_DATA}/det2_aggregate.json'))
pc = A['per_cell']
ps = [1, 2, 3]
TR = [('old_hmm','old HMM (archived, lag 0)'), ('old_cnn','old CNN (trained on labels, lag 2)'),
      ('J','J: both bases, no explaining away'), ('XZ','XZ: explaining away, Z checks only'),
      ('ALL','ALL: both bases + explaining away (offline)'), ('ALL_h','ALL + final-readout herald')]
COL = {'old_hmm':'#9e9e9e','old_cnn':'#5b7fa6','J':'#c9a15b','XZ':'#8fb38a','ALL':'#c0392b','ALL_h':'#e8907e'}
LW = {'ALL':2.4}
apply_figure_style(sizes=(8,7,6))
fig = plt.figure(figsize=(7.2, 5.4)); gs = fig.add_gridspec(2, 2, height_ratios=[1, 0.85], hspace=0.55, wspace=0.28)
axs = [fig.add_subplot(gs[0,0]), fig.add_subplot(gs[0,1]), fig.add_subplot(gs[1,1])]
for j,(metric,lab) in enumerate([('AP','Average precision of leakage flags'),('f','Fraction of oracle gain recovered, f')]):
    ax = axs[j]
    for k,name in TR:
        for het,ls,mk in [('hom','-','o'),('het','--','s')]:
            xs=[p for p in ps if f'p0.00{p}_{het}' in pc]; ys=[pc[f'p0.00{p}_{het}'][k][metric] for p in xs]
            ax.plot(np.array(xs)+(0.04 if het=='het' else -0.04), ys, ls=ls, marker=mk, ms=3.5, color=COL[k], lw=LW.get(k,1.2), zorder=3 if k.startswith('ALL') else 2)
            if metric=='f' and het=='hom':
                lo=[pc[f'p0.00{p}_{het}'][k]['f_ci'][0] for p in xs]; hi=[pc[f'p0.00{p}_{het}'][k]['f_ci'][1] for p in xs]
                ax.vlines(np.array(xs)-0.04, lo, hi, color=COL[k], lw=0.8, alpha=0.6)
    ax.set_xticks(ps); ax.set_xticklabels(['1×10⁻³','2×10⁻³','3×10⁻³']); ax.set_xlabel('Pauli noise strength p (SI1000)')
    ax.set_ylabel(lab); ax.margins(0.06)
    if metric=='f': ax.axhline(0, color=META_GREY, lw=0.6, zorder=0)
axs[0].set_title('New tracker flags leakage best', loc='left')
axs[1].set_title('Decoding: tie at low p, ALL ahead at 3×10⁻³', loc='left')
for het,mk in [('hom','o'),('het','s')]:
    xs=[p for p in ps if 'ALL_lag2' in pc.get(f'p0.00{p}_{het}',{})]
    axs[1].plot(np.array(xs)+(0.04 if het=='het' else -0.04), [pc[f'p0.00{p}_{het}']['ALL_lag2']['f'] for p in xs], ls=':', marker=mk, ms=3.5, mfc='white', color=COL['ALL'], lw=1.4, zorder=3)
# panel c: ablations, pooled over primary cells, change in f
ab = [('ALL_h','ALL','+ herald (idea 3)'), ('ALL','XZ','+ X checks (idea 1)'), ('ALL','J','+ explaining away (idea 2)'),
      ('ALL','ALL_true','learned parameters\n(vs true parameters)'), ('ALL','ALL_glob','one global p_L\n→ per-qubit p_L (het)'), ('ALL_lag2','ALL','online, 2-round lag\n(vs full smoothing)')]
ax = axs[2]; prim=['p0.002_hom','p0.003_hom','p0.002_het','p0.003_het']
for y,(a,b,lab) in enumerate(ab):
    d=[pc[c][a]['f']-pc[c][b]['f'] for c in prim if c in pc and a in pc[c] and b in pc[c]]
    ax.scatter(d, [y]*len(d), s=14, color=COL['ALL'] if np.mean(d)>0 else '#5b7fa6', zorder=3, alpha=0.8)
    ax.plot([np.mean(d)]*2, [y-0.3,y+0.3], color='k', lw=1.4)
ax.axvline(0, color=META_GREY, lw=0.6); ax.set_yticks(range(len(ab))); ax.set_yticklabels([x[2] for x in ab]); ax.invert_yaxis()
ax.set_xlabel('Change in f (one dot per cell, p = 2–3×10⁻³)'); ax.set_title('Explaining away matters most; herald adds a little', loc='left'); ax.margins(0.08)
h=[mpl.lines.Line2D([],[],color=COL[k],lw=LW.get(k,1.2),label=l) for k,l in TR]+[mpl.lines.Line2D([],[],color=COL['ALL'],ls=':',marker='o',mfc='white',ms=3,label='ALL, online (2-round lag)'), mpl.lines.Line2D([],[],color='k',ls='-',marker='o',ms=3,label='same p_L on all qubits'),mpl.lines.Line2D([],[],color='k',ls='--',marker='s',ms=3,label='per-qubit p_L (het)')]
axs[2].legend(handles=h, loc='center right', bbox_to_anchor=(-0.75,0.5), frameon=False, fontsize=7)
for a,l,x in zip(axs,'abc',[-0.2,-0.2,-0.62]): a.text(x, 1.08, l, transform=a.transAxes, fontsize=9, fontweight='bold', va='bottom')
fig.savefig(f'{paths.FIGURES}/detect2_figure.png', dpi=300, bbox_inches='tight')
