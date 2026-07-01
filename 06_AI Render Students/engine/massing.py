"""
massing.py 体块参考图(AI 渲染的结构 / reference image)。
把 05 某站点某体制的 recs 用固定机位渲成干净体块截图,发给 AI 当参考图锁结构。
color: 'sh' 按权利方 / 'mono' 素模灰白(推荐)。复用 05 plots,不联网。
"""
from pathlib import Path
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import ws05
import settings

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"


def _bounds(recs):
    polys = [p for r in recs for p in ws05.C._polys(r["geom"])]
    minx = min(p.bounds[0] for p in polys); miny = min(p.bounds[1] for p in polys)
    maxx = max(p.bounds[2] for p in polys); maxy = max(p.bounds[3] for p in polys)
    return minx, miny, maxx, maxy


def _ground_texture(minx, miny, maxx, maxy, slug, factor=2.2):
    """抓真实卫星(Esri,复用 05 ground_sat 缓存),返回 (rgb_array, [lx0,ly0,lx1,ly1] 局部范围)。
    局部范围相对 (minx,miny);factor>1 让卫星比 footprint 宽。"""
    from PIL import Image
    cache = OUT / slug / "ground_sat.jpg"
    _, local = ws05.C.ground_sat(minx, miny, maxx, maxy, cache, factor=factor)
    arr = np.asarray(Image.open(cache).convert("RGB"))
    return arr, local


def render_massing(recs, path, color="mono", cam=None, dpi=None, zmax=None, title=None,
                   ground=None, slug=None):
    """把 recs 渲成体块图(固定机位)。color: 'mono' 素模 / 'sh' 按权利方。
    ground='sat' 底部铺真实卫星地面。返回 path。"""
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    cam = cam or settings.CAM
    dpi = dpi or settings.MASSING_DPI
    minx, miny, maxx, maxy = _bounds(recs)
    ox, oy = minx, miny
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection="3d")

    gext = None
    if ground == "sat":
        try:
            arr, gext = _ground_texture(minx, miny, maxx, maxy, slug or settings.SLUG)
            # 下采样贴 z=0 平面;arr[0]=北=上,需上下翻转对齐 y
            step = max(1, max(arr.shape[:2]) // 220)
            tex = arr[::step, ::step] / 255.0
            tex = tex[::-1]                                  # 翻转使行与 y 一致
            ny, nx = tex.shape[:2]
            xs = np.linspace(gext[0], gext[2], nx); ys = np.linspace(gext[1], gext[3], ny)
            X, Y = np.meshgrid(xs, ys); Z = np.zeros_like(X)
            ax.plot_surface(X, Y, Z, rstride=1, cstride=1, facecolors=tex, shade=False,
                            linewidth=0, antialiased=False, zorder=0)
        except Exception as e:
            print("  卫星地面跳过(没网或缺 contextily):", e); gext = None

    for r in recs:
        h = float(r["h"])
        if color == "sh":
            fc = ws05.C.SH_COLOR.get(r["sh"], "#999")
        else:
            fc = "#c9c4bd"      # 素模:统一灰白
        faces = ws05.plots.building_faces(r["geom"], h, ox, oy)
        ax.add_collection3d(Poly3DCollection(faces, facecolor=fc, edgecolor="#6f6a63",
                                             linewidths=0.06, alpha=1.0))
    xmax, ymax = maxx - ox, maxy - oy
    zmax = zmax or max((r["h"] for r in recs), default=1) * 1.05
    # 有卫星地面时 x/y 跟着卫星,否则贴 footprint
    x0, x1, y0, y1 = (gext[0], gext[2], gext[1], gext[3]) if gext else (0, xmax, 0, ymax)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_zlim(0, zmax)
    # 竖向夸张 = 实际高度 × VEXAG,避免矮楼被压平
    VEXAG = 4.0
    ax.set_box_aspect((x1 - x0, y1 - y0, max(zmax * VEXAG, (x1 - x0) * 0.06)))
    ax.view_init(elev=cam["elev"], azim=cam["azim"])
    ax.set_axis_off()
    if title:
        ax.set_title(title, fontsize=12)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return Path(path)


def massing_for_regimes(slug=None, regimes=None, color="mono", ext="jpg", ground="sat"):
    """对各体制出固定机位体块参考图(共用 zmax 可横比)。默认 jpg + 卫星地面。
    ground='sat' 底部铺卫星;ground=None 纯白底。返回 {regime: 图路径}。"""
    slug = slug or settings.SLUG
    regimes = regimes or settings.REGIMES
    rr, regs = ws05.regime_recs(slug, regimes)
    zmax = max(max((r["h"] for r in recs), default=1) for recs in rr.values()) * 1.05
    out = {}
    for name, recs in rr.items():
        p = OUT / slug / ("massing_%s.%s" % (name, ext))
        render_massing(recs, p, color=color, zmax=zmax, ground=ground, slug=slug)
        out[name] = p
        print("  -> %s" % p.relative_to(ROOT))
    return out


if __name__ == "__main__":
    import sys
    slug = sys.argv[1] if len(sys.argv) > 1 else settings.SLUG
    print("== 体块参考图:%s ==" % slug)
    massing_for_regimes(slug)
    print("done")
