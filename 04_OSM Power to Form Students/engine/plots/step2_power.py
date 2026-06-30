"""Step2 圖:角色著色圖 + 各角色棟數/面積佔比長條。df 需已有 'stakeholder' 欄。"""
import numpy as np
import matplotlib.pyplot as plt
import common
from . import _base


@_base.safeplot
def power_map(df, show=True):
    """左:真實 footprint 依角色著色;右:棟數 / 面積佔比小長條。"""
    order = _base.stakeholder_order(df=df)   # 依 yaml + 資料動態取角色(學生加 key 也畫)
    counts = df["stakeholder"].value_counts()
    areas = df.groupby("stakeholder")["area_m2"].sum()
    n_by = np.array([int(counts.get(sh, 0)) for sh in order], float)
    a_by = np.array([float(areas.get(sh, 0.0)) for sh in order], float)
    n_share = n_by / n_by.sum() if n_by.sum() else n_by
    a_share = a_by / a_by.sum() if a_by.sum() else a_by

    fig, (ax_map, ax_bar) = plt.subplots(1, 2, figsize=(15, 8),
                                         gridspec_kw={"width_ratios": [3, 1]})
    _base.plot_footprints(ax_map, df, lambda r: _base.sh_color(r["stakeholder"]))
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=_base.sh_color(sh), edgecolor="white")
               for sh in order]
    labels = ["%s (%s, n=%d)" % (sh, _base.sh_label(sh), int(n_by[i]))
              for i, sh in enumerate(order)]
    _base.legend_below(ax_map, handles, labels, ncol=min(4, len(labels)))   # 一排最多 4 個,超過換行

    y = np.arange(len(order)); bw = 0.38
    colors = [_base.sh_color(sh) for sh in order]
    ax_bar.barh(y + bw / 2, n_share, height=bw, color=colors, edgecolor="white", label="棟數佔比")
    ax_bar.barh(y - bw / 2, a_share, height=bw, color=colors, edgecolor="white",
                alpha=0.5, label="面積佔比")
    ax_bar.set_yticks(y)
    ax_bar.set_yticklabels([_base.sh_label(sh) for sh in order], fontsize=8)
    ax_bar.invert_yaxis(); ax_bar.set_xlabel("佔比 share")
    ax_bar.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=2, fontsize=8, frameon=False)

    _base.footer(fig)
    fig.tight_layout(); fig.subplots_adjust(bottom=0.16)
    if show:
        plt.show()
    return fig
