"""Step4 圖:套情景只調高度的新形態。
  skyline_panels(df, heights) — N 連幅 footprints,同色階(可橫比)。
  metrics(df, heights)       — 2×2:總 GFA / 平均高 / 最高 / 各角色平均高。
heights = {情景名: 逐棟新高度 Series}(由 common.scenario_heights 算好傳入)。"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
import common
from . import _base


def skyline_panels(df, heights, names=None, show=True):
    names = names or list(heights.keys())
    norm = _base.height_norm(*[heights[n] for n in names])

    fig, axes = plt.subplots(1, len(names), figsize=(5.5 * len(names), 6.2))
    if len(names) == 1:
        axes = [axes]
    for ax, name in zip(axes, names):
        h = heights[name]
        hmap = dict(zip(df.index, h.values))
        _base.plot_footprints(ax, df, color_for=lambda r: _base.HEIGHT_CMAP(norm(hmap[r.name])))
        ax.set_title("%s\n平均高 %.1f m · 最高 %.0f m" % (name, h.mean(), h.max()), fontsize=11)
    sm = ScalarMappable(norm=norm, cmap=_base.HEIGHT_CMAP); sm.set_array([])
    fig.colorbar(sm, ax=axes, fraction=0.018, pad=0.012).set_label(
        "建物高度 (m) — 同一色階,可橫向比對", fontsize=10)
    _base.footer(fig)
    if show:
        plt.show()
    return fig


def metrics(df, heights, names=None, show=True):
    names = names or list(heights.keys())
    base_gfa = float((df.area_m2 * heights[names[0]] / common.FLOOR_H).sum())
    gfa_x, mean_h, max_h = [], [], []
    for name in names:
        h = heights[name]
        gfa_x.append(float((df.area_m2 * h / common.FLOOR_H).sum()) / base_gfa)
        mean_h.append(float(h.mean())); max_h.append(float(h.max()))

    by_sh = {}
    for sh in common.STAKEHOLDERS:
        mask = (df["stakeholder"] == sh).values
        if not mask.any():
            continue
        by_sh[sh] = {name: float(heights[name].values[mask].mean()) for name in names}

    fig, axs = plt.subplots(2, 2, figsize=(15, 10))
    x = np.arange(len(names))
    palette = ["#888888", "#c0654a", "#5a9367", "#4a6fa5"]
    cols = [palette[i % len(palette)] for i in range(len(names))]

    axs[0, 0].bar(x, gfa_x, color=cols); axs[0, 0].axhline(1.0, ls="--", lw=1, color="k")
    axs[0, 0].set_title("總 GFA ×base")
    for i, v in enumerate(gfa_x):
        axs[0, 0].text(i, v, "×%.2f" % v, ha="center", va="bottom", fontsize=10)
    axs[0, 1].bar(x, mean_h, color=cols); axs[0, 1].set_title("平均高 (m)")
    for i, v in enumerate(mean_h):
        axs[0, 1].text(i, v, "%.1f" % v, ha="center", va="bottom", fontsize=10)
    axs[1, 0].bar(x, max_h, color=cols); axs[1, 0].set_title("最高 (m)")
    for i, v in enumerate(max_h):
        axs[1, 0].text(i, v, "%.0f" % v, ha="center", va="bottom", fontsize=10)
    for ax in (axs[0, 0], axs[0, 1], axs[1, 0]):
        ax.set_xticks(x); ax.set_xticklabels(names, rotation=12)

    n_sh = len(by_sh); w = 0.8 / max(n_sh, 1)
    for k, (sh, d) in enumerate(by_sh.items()):
        axs[1, 1].bar(x + (k - (n_sh - 1) / 2) * w, [d[n] for n in names], width=w,
                      color=_base.SH_COLOR[sh], label=_base.SH_LABEL[sh])
    axs[1, 1].set_title("各 stakeholder 平均高 (m)")
    axs[1, 1].set_xticks(x); axs[1, 1].set_xticklabels(names, rotation=12)
    axs[1, 1].legend(loc="upper center", bbox_to_anchor=(0.5, -0.12),
                     ncol=max(n_sh, 1), fontsize=8, frameon=False)

    fig.tight_layout(); fig.subplots_adjust(bottom=0.12)
    if show:
        plt.show()
    return fig
