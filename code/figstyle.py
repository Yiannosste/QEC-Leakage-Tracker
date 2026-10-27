"""figstyle.py - the matplotlib settings used by the figure scripts (fig_detect2.py, fig_ibmstab.py).
Mechanics only: a three-step font-size ladder, outward ticks, open frame, frameless legends, 300 dpi."""
META_GREY = "#888888"   # colour of reference lines (zero lines) in all figures


def apply_figure_style(*, frame="open", font=None, sizes=(8, 7, 6), grid=False):
    """Call once before plotting. sizes = (titles/axis labels, legend/annotations, tick labels) in points."""
    import matplotlib as mpl
    base, secondary, tick = sizes
    boxed = frame == "boxed"
    rc = {"font.family": "sans-serif", "font.size": base, "axes.labelsize": base, "axes.titlesize": base,
          "legend.fontsize": secondary, "xtick.labelsize": tick, "ytick.labelsize": tick,
          "axes.linewidth": 0.6, "xtick.direction": "out", "ytick.direction": "out",
          "xtick.major.size": 3, "ytick.major.size": 3, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
          "axes.spines.top": boxed, "axes.spines.right": boxed,
          "axes.spines.left": frame != "none", "axes.spines.bottom": frame != "none",
          "axes.grid": bool(grid), "legend.frameon": False, "figure.dpi": 200, "savefig.dpi": 300,
          "savefig.bbox": "tight", "axes.titleweight": "normal", "axes.titlelocation": "left",
          "axes.labelweight": "normal", "lines.linewidth": 1.2, "patch.linewidth": 0.6,
          "pdf.fonttype": 42, "ps.fonttype": 42}
    if font:
        rc["font.sans-serif"] = [font, "DejaVu Sans"]
    mpl.rcParams.update(rc)
