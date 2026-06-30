"""
plots/_base.py — 繪圖共用核心(view 層 DRY)
=================================================================
這裡只放「畫圖」會重複用到的東西:角色調色盤、footprint 著色、存檔、
高度色階、3D 幾何面、圖例擺放。算資料是 model(common.py)的事,這裡不算。

設計:
  - common.py = model(載資料 / 貼角色 / 算高度 / 擠 OBJ),不碰 matplotlib。
  - plots/    = view(畫),只收「已算好的」df / heights / scenarios。
  - 不在這裡強制 matplotlib 後端 → notebook 用 inline、steps/*.py 在 __main__ 設 Agg。
"""
from datetime import datetime
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np
import common  # model 契約(STAKEHOLDERS / FLOOR_H / _polys / OUT / ROOT / honest_note + 字型设置)

# 中文字型:用 common 的「**先确认存在再选**」逻辑(避免变成豆腐方块)
common._set_cjk_font()


# ---- 自動存圖(view 層唯一存圖出口):每個 plots.* 都把圖落盤,學生不用逐張存 --------------
# 一次 run 開一個 timestamp 夾;所有圖歸在 out/<slug>/Step_<num>/<timestamp>/NN_name.png。
# 預設關閉 → build_report(走自己的 save_fig)不受影響;notebook 在 setup 呼叫 capture() 才開。
_CAPTURE = {"on": False, "num": None, "slug": None, "stamp": None, "seq": 0}


def capture(num, slug=None):
    """開啟自動存圖。num = notebook 前綴(如 '03')。slug 留空 = 存檔當下的 config.SLUG
    (這樣 05 換街道後,圖會跟著存到新 slug 夾)。回傳這次 run 的 timestamp 字串。"""
    _CAPTURE.update(on=True, num=str(num), slug=slug,
                    stamp=datetime.now().strftime("%Y%m%d_%H%M%S"), seq=0)
    return _CAPTURE["stamp"]


def autosave(fig, name):
    """capture() 開了才動作:把 fig 存成 out/<slug>/Step_<num>/<timestamp>/NN_name.png。
    slug 在存檔當下取(config.SLUG 變了也跟著走);seq 自動編號、把同一 run 的圖排序。"""
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
    try:                                  # 順手更新 out/manifest.json,讓 web/index.html 讀到最新
        import manifest
        manifest.bump(slug, _CAPTURE["num"], _CAPTURE["stamp"])
    except Exception as e:
        print("  manifest skip:", e)
    return p

# ---- 角色調色盤(view):从 common 取(单一真相源,简体)-----------------------
SH_COLOR = common.SH_COLOR
SH_LABEL = common.SH_LABEL

HEIGHT_CMAP = plt.get_cmap("viridis")   # 高度色階:低=深紫、高=黃,所有圖共用可橫比


# ---- footprint 著色(step1/2/4 共用):用 common 的批量版(快)-----------------
plot_footprints = common.plot_footprints


def legend_below(ax, handles, labels, ncol=None, fontsize=8):
    """圖例放座標軸下方一排,不蓋資料。"""
    ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, -0.04),
              ncol=ncol or len(labels), fontsize=fontsize, frameon=False)


def height_norm(*height_series):
    """跨多個情景共用的高度 Normalize(同色階才能橫向比對)。"""
    allh = np.concatenate([h.values for h in height_series])
    return Normalize(vmin=float(allh.min()), vmax=float(allh.max()))


def footer(fig, note=None):
    """圖底放誠實說明。"""
    fig.text(0.5, -0.04, note or common.honest_note(), ha="center", fontsize=7, color="#666")


def save_fig(fig, name, dpi=120):
    """存圖到 out/ 並關閉(headless steps 用)。"""
    p = common.OUT / name
    fig.savefig(p, dpi=dpi, bbox_inches="tight"); plt.close(fig)
    print("  -> wrote", p.relative_to(common.ROOT)); return p


# ---- 3D 幾何(step5 的 mpl 與 plotly 前處理共用)---------------------------
def origin_of(df):
    """整批樓的左下角(UTM 公尺座標很大,平移到原點附近好畫)。"""
    ox = min(p.bounds[0] for g in df["geom"] for p in common._polys(g))
    oy = min(p.bounds[1] for g in df["geom"] for p in common._polys(g))
    return ox, oy


def building_faces(geom, h, ox, oy):
    """footprint → 3D 面:四周的牆 + 一個頂蓋(近似:外環當一面)。"""
    faces = []
    for poly in common._polys(geom):
        ring = list(poly.exterior.coords)
        if len(ring) > 1 and ring[0] == ring[-1]:
            ring = ring[:-1]                       # 去掉重複的閉合點
        for i in range(len(ring)):                 # 每條邊長出一面牆
            j = (i + 1) % len(ring)
            x0, y0 = ring[i]; x1, y1 = ring[j]
            faces.append([(x0 - ox, y0 - oy, 0), (x1 - ox, y1 - oy, 0),
                          (x1 - ox, y1 - oy, h), (x0 - ox, y0 - oy, h)])
        faces.append([(x - ox, y - oy, h) for (x, y) in ring])   # 頂蓋
    return faces
