"""算子图谱【进阶册】:把「权力算子」与「权力体制」画清楚。
  operator_demo(before, after, title)         — 单个算子的 before/after(教学核心:一个操作改了什么)
  regime_compare(before, after_by_regime)     — 现状 vs 各体制,同高度色阶,横向比形态
  feature_bars(rows)                           — 各体制的形态特征(瘦长/高度CV/重心集中/栋数)
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
    has_cb = (color == "h")
    asp = _base.data_aspect(before)                        # figure 配到内容:panel 填满、无上下留白
    fig, (a0, a1), cax = _base.panel_grid(2, 1, asp, panel_w=5.0, wspace_in=0.22,
                                          title_in=(0.82 if title else 0.42), cbar=has_cb)
    if has_cb:
        norm = _hnorm(before, after)
        cf = lambda r: HCMAP(norm(r["h"]))
    else:
        cf = lambda r: _base.SH_COLOR[r["sh"]]
    _panel(a0, before, cf, "before  ·  n=%d  平均高 %.1fm" % (len(before), np.mean([r["h"] for r in before])))
    _panel(a1, after, cf, "after  ·  n=%d  平均高 %.1fm" % (len(after), np.mean([r["h"] for r in after])))
    for ax in (a0, a1):
        ax.margins(0.01)                                 # 四周数据留白 5%→1%
    if title:
        fig.suptitle(title, fontsize=13, y=0.99, va="top")
    if has_cb:
        sm = ScalarMappable(norm=norm, cmap=HCMAP); sm.set_array([])
        fig.colorbar(sm, cax=cax).set_label("高度 (m)", fontsize=9)   # cax 高度 = subplots 同高
    _base.footer(fig)
    _base.autosave(fig, "operator_demo")
    if show:
        plt.show()
    return fig


def regime_compare(before, after_by_regime, names=None, labels=None,
                   ncols=2, pad=0.1, hpad=0.32, show=True):
    """现状 + 各体制,按**新高度**同色阶著色,一眼看权力长出的形态。
    自动 grid:ncols 列 × ceil(n/ncols) 行(默认 2 列)。
    pad=左右两 panel 空白(wspace),hpad=上下两 row 空白(hspace,需留双行标题)。"""
    names = names or list(after_by_regime.keys())
    seq = [("current", before)] + [(n, after_by_regime[n]) for n in names]
    norm = _hnorm(*[r for _, r in seq])
    cf = lambda r: HCMAP(norm(r["h"]))
    n = len(seq)
    ncols = max(1, min(ncols, n))
    nrows = int(np.ceil(n / ncols))
    asp = _base.data_aspect(before)                # figure 配到内容:每 panel 填满、无上下留白
    fig, axes, cax = _base.panel_grid(ncols, nrows, asp, panel_w=4.8,
                                      title_in=0.5, hspace_in=0.72, cbar=True)
    for ax, (name, recs) in zip(axes, seq):
        lab = (labels or {}).get(name, name)
        _panel(ax, recs, cf, "%s\nn=%d · 平均高 %.1fm" % (lab, len(recs), np.mean([r["h"] for r in recs])))
        ax.margins(0.01)                          # 每 panel 数据留白 5%→1%
    for ax in axes[n:]:                            # 多余格子(n 为奇数时最后一格)隐藏
        ax.set_visible(False)
    sm = ScalarMappable(norm=norm, cmap=HCMAP); sm.set_array([])
    fig.colorbar(sm, cax=cax).set_label(           # cax 高度 = 整片 subplots(跨全部 row)同高
        "建物高度 (m) — 同色阶可横比", fontsize=10)
    _base.footer(fig)
    _base.autosave(fig, "regime_compare")
    if show:
        plt.show()
    return fig


def feature_bars(rows, labels=None, show=True):
    """rows = measure.compare(...) 的第一个返回值。画 4 个特征指标的体制对照。"""
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
    fig.suptitle("四种权力 → 四种形态特征(measure.py 量化)", fontsize=13)
    fig.tight_layout(); fig.subplots_adjust(top=0.92)
    _base.autosave(fig, "feature_bars")
    if show:
        plt.show()
    return fig
