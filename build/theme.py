"""Shared chart theme for research-audits v1. Vector output (SVG), one palette, direct labels."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, INK2, INK3, GRID, PAPER = "#1a1a19", "#5f5e5a", "#8a8984", "#e8e7e3", "#ffffff"
ACCENT, COMPARE, CONTEXT = "#e0612a", "#2a6fc9", "#b4b2a9"          # object of the audit · comparison · context
ACCENT_L, COMPARE_L, CONTEXT_L = "#f6c9b3", "#b9d2f0", "#e2e1dc"
VERDICT = {"supported": "#2a6fc9", "republisher": "#a9c8ee", "partial": "#cfcdc6", "wrong": "#e0612a"}

def apply():
    plt.rcParams.update({
        "font.family": "Inter", "font.size": 9, "svg.fonttype": "none",
        "axes.edgecolor": GRID, "axes.linewidth": 0.8, "axes.labelcolor": INK2, "axes.labelsize": 8,
        "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 11, "axes.titleweight": "medium",
        "axes.titlelocation": "left", "axes.titlecolor": INK, "axes.titlepad": 10,
        "xtick.color": INK3, "ytick.color": INK3, "xtick.labelsize": 8, "ytick.labelsize": 8,
        "xtick.major.size": 0, "ytick.major.size": 0, "legend.frameon": False, "legend.fontsize": 7.5,
        "lines.linewidth": 2.0, "lines.solid_capstyle": "round", "figure.dpi": 100})

def fig(w_mm=174, h_mm=70, **kw):
    apply(); return plt.subplots(figsize=(w_mm / 25.4, h_mm / 25.4), **kw)

def grid_y(ax): ax.grid(axis="y", color=GRID, lw=0.6); ax.set_axisbelow(True)
def grid_x(ax): ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)

def title(ax, takeaway, sub=None):
    ax.set_title(takeaway, loc="left", pad=16 if sub else 8)
    if sub: ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=7.5, color=INK2, va="bottom")

def save(f, path):
    f.savefig(path + ".svg", bbox_inches="tight", pad_inches=0.04)
    f.savefig(path + ".png", dpi=220, bbox_inches="tight", pad_inches=0.04)
    plt.close(f)
