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


def study_rect(minx, miny, maxx, maxy, frac):
    """研究范围 = 街区范围中心的矩形(每边 × frac)。返回世界坐标 (sx0,sy0,sx1,sy1)。"""
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    hw, hh = (maxx - minx) * frac / 2, (maxy - miny) * frac / 2
    return cx - hw, cy - hh, cx + hw, cy + hh


def _ground_texture(sx0, sy0, sx1, sy1, slug, factor=1.0):
    """抓全场景(study + 周边环)范围的真实卫星(Esri),返回 (rgb_array, [lx0,ly0,lx1,ly1])。
    local 相对 (sx0,sy0)。缓存 ground_scene.jpg(覆盖全环,与旧 study-only ground_study.jpg 区分,避免读到旧的小图)。"""
    from PIL import Image
    cache = OUT / slug / "ground_scene.jpg"
    _, local = ws05.C.ground_sat(sx0, sy0, sx1, sy1, cache, factor=factor)
    arr = np.asarray(Image.open(cache).convert("RGB"))
    return arr, local


def render_massing(recs, path, color="mono", cam=None, dpi=None, zmax=None, title=None,
                   ground=None, slug=None, context_recs=None):
    """把 study recs 渲成体块图(固定机位)。color: 'mono' 素模 / 'sh' 按权利方。
    study(整个街区)= 实心;context(周边环)= 透明语境。ground='sat' 铺覆盖**全场景(study+周边环)**的真实卫星底。
    红线 = study 街区多边形边界(整个 study 都实心)。返回 path。"""
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    cam = cam or settings.CAM
    dpi = dpi or settings.MASSING_DPI
    slug = slug or settings.SLUG
    context_recs = context_recs or []
    tagged = [(r, True) for r in recs] + [(r, False) for r in context_recs]   # True=study 实心 / False=周边透明
    allrecs = [t[0] for t in tagged]
    minx, miny, maxx, maxy = _bounds(allrecs)                # 全场景(含周边环)= 视野 + 卫星覆盖
    ox, oy = minx, miny
    fig = plt.figure(figsize=(9, 7))
    # computed_zorder=False:mplot3d 不再按质心自动排层(否则宽卫星面会盖住楼)——改由手动 zorder 定顺序
    ax = fig.add_subplot(111, projection="3d", computed_zorder=False)

    if ground == "sat":
        try:
            arr, local = _ground_texture(minx, miny, maxx, maxy, slug, factor=settings.SAT_FACTOR)   # 覆盖全环(倍率见 config.yaml sat_factor)
            # 下采样贴 z=0 平面;arr[0]=北=上,需上下翻转对齐 y
            step = max(1, max(arr.shape[:2]) // 300)
            tex = arr[::step, ::step] / 255.0
            tex = tex[::-1]                                  # 翻转使行与 y 一致
            ny, nx = tex.shape[:2]
            gx0, gy0 = local[0], local[1]                    # local 已相对 (minx,miny)=(ox,oy)
            gx1, gy1 = local[2], local[3]
            xs = np.linspace(gx0, gx1, nx); ys = np.linspace(gy0, gy1, ny)
            X, Y = np.meshgrid(xs, ys); Z = np.zeros_like(X)
            ax.plot_surface(X, Y, Z, rstride=1, cstride=1, facecolors=tex, shade=False,
                            linewidth=0, antialiased=False, zorder=0)   # 最底层
        except Exception as e:
            print("  卫星地面跳过(没网或缺 contextily):", e)

    # 画家算法:按视线水平深度远→近排序,赋递增 zorder(computed_zorder=False 下自管遮挡)
    az = np.radians(cam["azim"])
    ca, sa = np.cos(az), np.sin(az)
    def _depth(r):
        c = r["geom"].centroid
        return c.x * ca + c.y * sa
    order = sorted(range(len(tagged)), key=lambda i: _depth(tagged[i][0]))

    for zi, i in enumerate(order):
        r, is_study = tagged[i]; h = float(r["h"])
        if (not is_study) and zmax:
            h = min(h, zmax)      # 周边高度封顶到 study z-box:低层街区被高周边淹没时不溢出画面
        if color == "sh" and is_study:
            fc = ws05.C.SH_COLOR.get(r["sh"], "#999")
        else:
            fc = "#c9c4bd"      # 素模 / 周边:统一灰白
        alpha = 1.0 if is_study else 0.22                     # study 实心 / 周边透明
        ec = "#6f6a63" if is_study else "#a8a29a"
        faces = ws05.plots.building_faces(r["geom"], h, ox, oy)
        ax.add_collection3d(Poly3DCollection(faces, facecolor=fc, edgecolor=ec,
                                             linewidths=0.06, alpha=alpha, zorder=2 + zi))
    # 红色 study 街区多边形边界(整个 study 实心),z=0,画最上;拿不到多边形则回退用 study bbox
    rings = ws05.C.study_poly_rings(slug)
    if rings:
        for ring in rings:
            ax.plot([p[0] - ox for p in ring], [p[1] - oy for p in ring], zs=0, zdir="z",
                    color="#e02424", linewidth=2.0, zorder=10 ** 6)
    else:
        smnx, smny, smxx, smxy = _bounds(recs)
        ax.plot([smnx - ox, smxx - ox, smxx - ox, smnx - ox, smnx - ox],
                [smny - oy, smny - oy, smxy - oy, smxy - oy, smny - oy], zs=0, zdir="z",
                color="#e02424", linewidth=2.0, zorder=10 ** 6)

    xmax, ymax = maxx - ox, maxy - oy
    zmax = zmax or max((r["h"] for r in allrecs), default=1) * 1.05
    # 视野 = 全场景(study + 周边环 + 卫星)
    ax.set_xlim(0, xmax); ax.set_ylim(0, ymax); ax.set_zlim(0, zmax)
    # 竖向夸张 = 实际高度 × VEXAG,避免矮楼被压平
    VEXAG = 4.0
    ax.set_box_aspect((xmax, ymax, max(zmax * VEXAG, xmax * 0.06)))
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
    context_recs = ws05.load_context_recs(slug)                # 周边语境(透明,跨体制不变),没有则 []
    zmax = max(max((r["h"] for r in recs), default=1) for recs in rr.values()) * 1.05
    out = {}
    for name, recs in rr.items():
        p = OUT / slug / ("massing_%s.%s" % (name, ext))
        render_massing(recs, p, color=color, zmax=zmax, ground=ground, slug=slug, context_recs=context_recs)
        out[name] = p
        print("  -> %s" % p.relative_to(ROOT))
    return out


if __name__ == "__main__":
    import sys
    slug = sys.argv[1] if len(sys.argv) > 1 else settings.SLUG
    print("== 体块参考图:%s ==" % slug)
    massing_for_regimes(slug)
    print("done")
