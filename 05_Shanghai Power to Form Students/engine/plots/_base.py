"""
plots/_base.py — 绘图共用核心(view 层 DRY)
=================================================================
这里只放「画图」会重复用到的东西:角色调色盘、footprint 著色、存档、
高度色阶、3D 几何面、图例摆放。算资料是 model(common.py)的事,这里不算。

设计:
  - common.py = model(载资料 / 贴角色 / 算高度 / 挤 OBJ),不碰 matplotlib。
  - plots/    = view(画),只收「已算好的」df / heights / scenarios。
  - 不在这里强制 matplotlib 后端 → notebook 用 inline、steps/*.py 在 __main__ 设 Agg。
"""
from datetime import datetime
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np
import common  # model 契约(STAKEHOLDERS / FLOOR_H / _polys / OUT / ROOT / honest_note + 字型设置)

# 中文字型:用 common 的「**先确认存在再选**」逻辑(避免变成豆腐方块)
common._set_cjk_font()


# ---- 自动存图(view 层唯一存图出口):每个 plots.* 都把图落盘,学生不用逐张存 --------------
# 一次 run 开一个 timestamp 夹;所有图归在 out/<slug>/Step_<num>/<timestamp>/NN_name.png。
# 预设关闭 → build_report(走自己的 save_fig)不受影响;notebook 在 setup 呼叫 capture() 才开。
_CAPTURE = {"on": False, "num": None, "slug": None, "stamp": None, "seq": 0}


def capture(num, slug=None):
    """开启自动存图。num = notebook 前缀(如 '03')。slug 留空 = 存档当下的 config.SLUG
    (这样 05 换街道后,图会跟著存到新 slug 夹)。回传这次 run 的 timestamp 字串。"""
    _CAPTURE.update(on=True, num=str(num), slug=slug,
                    stamp=datetime.now().strftime("%Y%m%d_%H%M%S"), seq=0)
    return _CAPTURE["stamp"]


def autosave(fig, name):
    """capture() 开了才动作:把 fig 存成 out/<slug>/Step_<num>/<timestamp>/NN_name.png。
    slug 在存档当下取(config.SLUG 变了也跟著走);seq 自动编号、把同一 run 的图排序。"""
    if not _CAPTURE["on"] or fig is None:
        return None
    import config
    slug = _CAPTURE["slug"] or config.SLUG
    d = common.OUT / slug / ("Step_%s" % _CAPTURE["num"]) / _CAPTURE["stamp"]
    d.mkdir(parents=True, exist_ok=True)
    _CAPTURE["seq"] += 1
    p = d / ("%02d_%s.png" % (_CAPTURE["seq"], name))
    fig.savefig(p, dpi=120, bbox_inches="tight")
    print("  -> saved", p.relative_to(common.ROOT))
    try:                                  # 顺手更新 out/manifest.json,让 web/index.html 读到最新
        import manifest
        manifest.bump(slug, _CAPTURE["num"], _CAPTURE["stamp"])
    except Exception as e:
        print("  manifest skip:", e)
    return p

# ---- 角色调色盘(view):从 common 取(单一真相源,简体)-----------------------
SH_COLOR = common.SH_COLOR
SH_LABEL = common.SH_LABEL

HEIGHT_CMAP = plt.get_cmap("viridis")   # 高度色阶:低=深紫、高=黄,所有图共用可横比


# ---- footprint 著色(step1/2/4 共用):用 common 的批量版(快)-----------------
plot_footprints = common.plot_footprints


def legend_below(ax, handles, labels, ncol=None, fontsize=8):
    """图例放座标轴下方一排,不盖资料。"""
    ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, -0.04),
              ncol=ncol or len(labels), fontsize=fontsize, frameon=False)


def height_norm(*height_series):
    """跨多个情景共用的高度 Normalize(同色阶才能横向比对)。"""
    allh = np.concatenate([h.values for h in height_series])
    return Normalize(vmin=float(allh.min()), vmax=float(allh.max()))


def footer(fig, note=None):
    """图底放诚实说明。"""
    fig.text(0.5, -0.04, note or common.honest_note(), ha="center", fontsize=7, color="#666")


def save_fig(fig, name, dpi=120):
    """存图到 out/ 并关闭(headless steps 用)。"""
    p = common.OUT / name
    fig.savefig(p, dpi=dpi, bbox_inches="tight"); plt.close(fig)
    print("  -> wrote", p.relative_to(common.ROOT)); return p


# ---- 3D 几何(step5 的 mpl 与 plotly 前处理共用)---------------------------
def origin_of(df):
    """整批楼的左下角(UTM 公尺座标很大,平移到原点附近好画)。"""
    ox = min(p.bounds[0] for g in df["geom"] for p in common._polys(g))
    oy = min(p.bounds[1] for g in df["geom"] for p in common._polys(g))
    return ox, oy


def building_faces(geom, h, ox, oy):
    """footprint → 3D 面:四周的墙 + 一个顶盖(近似:外环当一面)。"""
    faces = []
    for poly in common._polys(geom):
        ring = list(poly.exterior.coords)
        if len(ring) > 1 and ring[0] == ring[-1]:
            ring = ring[:-1]                       # 去掉重复的闭合点
        for i in range(len(ring)):                 # 每条边长出一面墙
            j = (i + 1) % len(ring)
            x0, y0 = ring[i]; x1, y1 = ring[j]
            faces.append([(x0 - ox, y0 - oy, 0), (x1 - ox, y1 - oy, 0),
                          (x1 - ox, y1 - oy, h), (x0 - ox, y0 - oy, h)])
        faces.append([(x - ox, y - oy, h) for (x, y) in ring])   # 顶盖
    return faces
