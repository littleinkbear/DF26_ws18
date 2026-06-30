"""算子图谱【进阶册】:把「权力算子」与「权力体制」画清楚。
  operator_demo(before, after, title)         — 单个算子的 before/after(教学核心:一个动词改了什么)
  regime_compare(before, after_by_regime)     — 现状 vs 各体制,同高度色阶,横向比形态
  fingerprint_bars(rows)                       — 各体制的形态指纹(瘦长/高度CV/重心集中/栋数)
工作单位是 recs 列表 [{geom,h,sh,frozen}](operators.py 的输出),不是 DataFrame。"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import common
from . import _base

HCMAP = _base.HEIGHT_CMAP


def _hnorm(*rec_lists):
    allh = np.concatenate([[r["h"] for r in rl] for rl in rec_lists]) if rec_lists else np.array([1.0])
    return Normalize(vmin=float(allh.min()), vmax=float(allh.max()))


def _panel(ax, recs, color_for, title):
    common.plot_footprints(ax, recs, color_for, lw=0.1)
    ax.set_title(title, fontsize=11)


def operator_demo(before, after, title="", color="sh", show=True):
    """单个算子的 before/after。color='sh' 按角色 / 'h' 按高度(同色阶)。"""
    fig, (a0, a1) = plt.subplots(1, 2, figsize=(13, 6.4))
    if color == "h":
        norm = _hnorm(before, after)
        cf = lambda r: HCMAP(norm(r["h"]))
    else:
        cf = lambda r: _base.SH_COLOR[r["sh"]]
    _panel(a0, before, cf, "before  ·  n=%d  平均高 %.1fm" % (len(before), np.mean([r["h"] for r in before])))
    _panel(a1, after, cf, "after  ·  n=%d  平均高 %.1fm" % (len(after), np.mean([r["h"] for r in after])))
    if title:
        fig.suptitle(title, fontsize=13, y=1.02)
    if color == "h":
        sm = ScalarMappable(norm=norm, cmap=HCMAP); sm.set_array([])
        fig.colorbar(sm, ax=[a0, a1], fraction=0.018, pad=0.012).set_label("高度 (m)", fontsize=9)
    _base.footer(fig)
    _base.autosave(fig, "operator_demo")
    if show:
        plt.show()
    return fig


def regime_compare(before, after_by_regime, names=None, labels=None, show=True):
    """现状 + 各体制,按**新高度**同色阶著色,一眼看四种权力长出四种形态。"""
    names = names or list(after_by_regime.keys())
    seq = [("current", before)] + [(n, after_by_regime[n]) for n in names]
    norm = _hnorm(*[r for _, r in seq])
    cf = lambda r: HCMAP(norm(r["h"]))
    fig, axes = plt.subplots(1, len(seq), figsize=(4.8 * len(seq), 5.8))
    if len(seq) == 1:
        axes = [axes]
    for ax, (name, recs) in zip(axes, seq):
        lab = (labels or {}).get(name, name)
        _panel(ax, recs, cf, "%s\nn=%d · 平均高 %.1fm" % (lab, len(recs), np.mean([r["h"] for r in recs])))
    sm = ScalarMappable(norm=norm, cmap=HCMAP); sm.set_array([])
    fig.colorbar(sm, ax=axes, fraction=0.014, pad=0.01).set_label("建物高度 (m) — 同色阶可横比", fontsize=10)
    _base.footer(fig)
    _base.autosave(fig, "regime_compare")
    if show:
        plt.show()
    return fig


def fingerprint_bars(rows, labels=None, show=True):
    """rows = measure.compare(...) 的第一个返回值。画 4 个指纹指标的体制对照。"""
    names = list(rows.keys())
    lab = [(labels or {}).get(n, n) for n in names]
    metrics = [("slender", "瘦长比(塔化↑)"), ("h_cv", "高度CV(集权↑)"),
               ("concentration", "重心集中度(集权↑)"), ("n", "栋数(细粒↑)")]
    fig, axs = plt.subplots(2, 2, figsize=(14, 9))
    palette = ["#888888", "#c0654a", "#4a6fa5", "#5a9367", "#c2a23c"]
    x = np.arange(len(names))
    for ax, (key, title) in zip(axs.ravel(), metrics):
        vals = [rows[n][key] for n in names]
        ax.bar(x, vals, color=[palette[i % len(palette)] for i in range(len(names))])
        ax.set_title(title, fontsize=12)
        ax.set_xticks(x); ax.set_xticklabels(lab, rotation=14, fontsize=9)
        for i, v in enumerate(vals):
            ax.text(i, v, ("%.2f" % v) if key != "n" else ("%d" % v),
                    ha="center", va="bottom", fontsize=9)
    fig.suptitle("四种权力 → 四种形态指纹(measure.py 量化)", fontsize=13)
    fig.tight_layout(); fig.subplots_adjust(top=0.92)
    _base.autosave(fig, "fingerprint_bars")
    if show:
        plt.show()
    return fig
