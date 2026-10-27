import json, numpy as np, matplotlib as mpl, matplotlib.pyplot as plt
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import paths
from figstyle import apply_figure_style, META_GREY
D = json.load(open(f'{paths.RESULTS_DATA}/ibmstab_figdata.json'))
apply_figure_style(sizes=(8,7,6))
C = dict(X='#c0392b', Xdec='#c0392b', A4='#5b7fa6', P='#9e9e9e', Xold='#c9a15b')
fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.7), gridspec_kw=dict(wspace=0.5))
ax = axs[0]; Ts = [5, 10, 20, 50, 100]
for key, lab, mk, mfc, dx in [('X_vs_A','new tracker (ALL) vs MWPM','o',None,1.0), ('Xdec_vs_Adec','new tracker vs stronger MWPM','o','white',1.06),
                              ('A4_vs_A','static average (control)','s',None,0.94), ('P_vs_A','wrong-shot placebo','^',None,0.9), ('Xold_vs_A','old IBM tracker','D',None,1.1)]:
    k0 = key.split('_')[0]; y = np.array([D[f'T{t}'][key] for t in Ts]) * 100
    ax.errorbar(np.array(Ts)*dx, y[:,0], yerr=[y[:,0]-y[:,1], y[:,2]-y[:,0]], marker=mk, ms=4, mfc=mfc or C[k0], color=C[k0], lw=2 if k0=='X' else 1, elinewidth=0.8, label=lab, zorder=3 if k0 in ('X','Xdec') else 2)
ax.axhline(0, color=META_GREY, lw=0.6); ax.set_xscale('log'); ax.set_xticks(Ts); ax.set_xticklabels([str(t) for t in Ts]); ax.minorticks_off()
ax.set_xlabel('Rounds T (α = 0)'); ax.set_ylabel('Change in logical failure (%)\n(below 0 = better)')
ax.set_title('Gain grows with run length', loc='left'); ax.margins(0.06)
al = [0, 0.15, 0.3, 0.45, 0.6, 0.8, 1.0]
def runs(T): return [f'T{T}'] + [f'T{T}_alpha{a}' for a in ['0.15','0.3','0.45','0.6','0.8','1.0']]
ax = axs[1]
for T, ls, mk in [(20, '--', 's'), (100, '-', 'o')]:
    y = np.array([D[r]['X_vs_A'] for r in runs(T)]) * 100
    ax.errorbar(al, y[:,0], yerr=[y[:,0]-y[:,1], y[:,2]-y[:,0]], marker=mk, ms=4, color=C['X'], ls=ls, lw=1.6, elinewidth=0.8, label=f'T = {T}')
ax.axhline(0, color=META_GREY, lw=0.6); ax.set_xlabel('Pre-readout rotation α (rad)'); ax.set_ylabel('Change in logical failure (%)')
ax.set_title('No harm at high readout error', loc='left'); ax.legend(frameon=False, loc='lower right'); ax.margins(0.06)
ax = axs[2]
for T, ls, mk in [(20, '--', 's'), (100, '-', 'o')]:
    ax.plot(al, [D[r]['dLL'] for r in runs(T)], marker=mk, ms=4, ls=ls, color='k', lw=1.4, label=f'T = {T}')
ax.axhline(0, color=META_GREY, lw=0.6); ax.set_xlabel('Pre-readout rotation α (rad)'); ax.set_ylabel('Label-free evidence for\nhidden state (nats/shot)')
ax.set_title('Evidence fades with α', loc='left'); ax.legend(frameon=False); ax.margins(0.06)
h, l = axs[0].get_legend_handles_labels(); fig.legend(h, l, loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.2), fontsize=7)
for a_, lt in zip(axs, 'abc'): a_.text(-0.3, 1.08, lt, transform=a_.transAxes, fontsize=9, fontweight='bold', va='bottom')
fig.savefig(f'{paths.FIGURES}/ibmstab_figure.png', dpi=300, bbox_inches='tight')
