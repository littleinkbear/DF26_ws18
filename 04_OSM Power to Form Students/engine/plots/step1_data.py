"""Step1 圖:灰 footprints(還沒貼角色)+ 高度直方圖(依來源著色)。"""
import matplotlib.pyplot as plt
from . import _base


@_base.safeplot
def data_overview(df, show=True):
    """左:真實 footprints 全灰;右:高度分佈,依 height_source 疊色。"""
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(15, 7))

    _base.plot_footprints(axL, df, color_for=lambda r: "#9a9a9a")
    axL.set_title("建築佔地(全灰:這步只看楼本身,還沒貼角色)", fontsize=12)

    src_color = {"measured": "#4a6fa5", "levels_x3.5": "#5a9367", "default": "#b8b8b8"}
    src_label = {"measured": "measured(實測)", "levels_x3.5": "levels×3.5(樓層估)",
                 "default": "default(預設)"}
    bins = range(0, int(df.height_m.max()) + 6, 3)
    stacks = [df.loc[df.height_source == s, "height_m"] for s in src_color]
    axR.hist(stacks, bins=bins, stacked=True, color=[src_color[s] for s in src_color],
             label=[src_label[s] for s in src_color])
    axR.axvline(df.height_m.mean(), color="#c0654a", ls="--", lw=1.2,
                label="平均 %.1f m" % df.height_m.mean())
    axR.set_yscale("log")          # y 用對數刻度:棟數跨距大,矮樓很多、高樓很少也看得清
    axR.set_xlabel("高度 height (m)"); axR.set_ylabel("棟數 count(log)")
    axR.legend(loc="upper center", bbox_to_anchor=(0.5, -0.10), ncol=4, fontsize=8, frameon=False)

    _base.footer(fig)
    fig.tight_layout(); fig.subplots_adjust(bottom=0.18)
    if show:
        plt.show()
    return fig
