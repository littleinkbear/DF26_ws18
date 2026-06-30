"""Step1 图:灰 footprints(还没贴角色)+ 实测高度直方图。
上海版 height_source 全是 measured_ai(AI影像解译-带高度,实测),不再是 OSM 的 levels×3.5 估算——
所以这里直接画实测高度分布,并标出 >100m 的真超高层 token(OSM/新加坡版没有的东西)。"""
import numpy as np
import matplotlib.pyplot as plt
from . import _base


def data_overview(df, show=True):
    """左:真实 footprints 全灰;右:实测高度分布(标平均、p90、>100m 超高层)。"""
    h = df["height_m"].astype(float)
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(15, 7))

    _base.plot_footprints(axL, df, color_for=lambda r: "#9a9a9a")
    axL.set_title("建筑占地(全灰:这步只看楼本身,还没贴角色)", fontsize=12)

    hi = int(h.max())
    bins = range(0, hi + 8, max(3, hi // 80 * 3 or 3))
    axR.hist(h, bins=bins, color="#4a6fa5", label="实测高度 measured_ai")
    n_hi = int((h > 100).sum())
    if n_hi:
        axR.hist(h[h > 100], bins=bins, color="#c0654a", label=">100m 超高层 ×%d" % n_hi)
    axR.axvline(h.mean(), color="#222", ls="--", lw=1.2, label="平均 %.1f m" % h.mean())
    axR.axvline(h.quantile(.9), color="#5a9367", ls=":", lw=1.2, label="p90 %.1f m" % h.quantile(.9))
    axR.set_xlabel("高度 height (m)  ·  最高 %.0f m" % h.max()); axR.set_ylabel("栋数 count")
    axR.set_title("实测高度分布(全为 AI 解译实测,非楼层估算)", fontsize=12)
    axR.legend(loc="upper right", fontsize=9, frameon=False)

    _base.footer(fig)
    fig.tight_layout(); fig.subplots_adjust(bottom=0.18)
    if show:
        plt.show()
    return fig
