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
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import font_manager
import numpy as np
import common  # model 契約(STAKEHOLDERS / FLOOR_H / _polys / OUT / ROOT / honest_note)

# 中文字型:自動偵測電腦實際裝了的字體,避免變成豆腐方塊。
#   簡體中文優先 → 沒有再用繁體中文 → 都沒有用泛 CJK 字體。
# (舊版只是設 rcParams 不會報錯,等於永遠選第一個、沒真的偵測;這裡用
#  font_manager 查實際裝了哪些 family,挑到才用。)
_FONT_PREF = (
    # ---- 簡體中文優先 ----
    "Microsoft YaHei", "SimHei", "SimSun", "KaiTi", "FangSong",   # Windows 簡中
    "PingFang SC", "Hiragino Sans GB", "STHeiti", "STSong",       # macOS 簡中
    "Source Han Sans SC", "Source Han Sans CN", "Noto Sans CJK SC",  # 思源/Noto 簡中
    "WenQuanYi Zen Hei", "WenQuanYi Micro Hei",                   # Linux 簡中
    "Droid Sans Fallback",
    # ---- 沒有簡體才退繁體中文 ----
    "Microsoft JhengHei", "MingLiU", "PMingLiU",                  # Windows 繁中
    "PingFang TC", "Heiti TC", "Apple LiGothic",                  # macOS 繁中
    "Source Han Sans TC", "Noto Sans CJK TC",                     # 思源/Noto 繁中
    # ---- 最後泛 CJK / Unicode 後援 ----
    "Arial Unicode MS", "PingFang HK",
)


# 用來驗證「這個字體真的畫得出中文」的測試字(簡 + 繁各一個常用字)
_CJK_PROBE = "简體"


def _font_has_cjk(path):
    """讀字體檔的 cmap,確認真的有中文字符(避免挑到只有拉丁字的字體)。"""
    try:
        from matplotlib.ft2font import FT2Font
        face = FT2Font(path)
        cmap = face.get_charmap()           # {unicode_codepoint: glyph_index}
        return all(ord(ch) in cmap for ch in _CJK_PROBE)
    except Exception:
        return False


def _detect_cjk_font():
    """偵測這台電腦能畫中文的字體,回傳 (family名, 是否經偏好序命中)。

    兩段式,確保換任何同學的電腦都能用:
      1) 偏好序命中 → 簡體優先、繁體次之(且驗證檔案真的含中文字符)。
      2) 偏好序全沒中 → 掃描全機字體,挑第一個 cmap 真的含中文的當後援。
    都找不到才回 None(極少見:整台機器無任何中文字型)。
    """
    try:
        fonts = font_manager.fontManager.ttflist
    except Exception:
        return None
    by_name = {}
    for f in fonts:
        by_name.setdefault(f.name, f.fname)   # family -> 任一字體檔路徑
    # 1) 偏好序:簡 → 繁,命中且檔案確實含中文才採用
    for name in _FONT_PREF:
        if name in by_name and _font_has_cjk(by_name[name]):
            return name
    # 2) 偏好序沒中 → 全機掃描,挑任何畫得出中文的字體
    for f in fonts:
        if _font_has_cjk(f.fname):
            return f.name
    return None


_CJK_FONT = _detect_cjk_font()
if _CJK_FONT:
    # 偵測到的字體擺第一,其餘偏好序當後援,DejaVu Sans 殿後(拉丁字不缺字)。
    matplotlib.rcParams["font.sans-serif"] = (
        [_CJK_FONT] + [f for f in _FONT_PREF if f != _CJK_FONT] + ["DejaVu Sans"]
    )
else:
    import warnings
    warnings.warn("未偵測到任何中文字型,圖上中文可能顯示為方塊。"
                  "請安裝任一中文字體(如 Noto Sans CJK / 思源黑體)。")
matplotlib.rcParams["axes.unicode_minus"] = False   # 負號用 ASCII,不靠中文字型

# ---- 角色調色盤(view):color = 著色,label = 中文名 -----------------------
SH_COLOR = {"state": "#4a6fa5", "developer": "#c0654a", "resident": "#5a9367",
            "informal": "#c2a23c", "unknown": "#b8b8b8"}
SH_LABEL = {"state": "政府/公共", "developer": "開發商/資本", "resident": "居民",
            "informal": "在地/非正式", "unknown": "未標(building=yes/無tag)"}

HEIGHT_CMAP = plt.get_cmap("viridis")   # 高度色階:低=深紫、高=黃,所有圖共用可橫比


# ---- footprint 著色(step1/2/4 共用)---------------------------------------
def plot_footprints(ax, df, color_for, lw=0.2):
    """畫真實 OSM footprints,用 color_for(row)->色 著色。"""
    for _, r in df.iterrows():
        col = color_for(r)
        for p in common._polys(r["geom"]):
            xs, ys = p.exterior.xy
            ax.fill(xs, ys, facecolor=col, edgecolor="white", linewidth=lw)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])


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
