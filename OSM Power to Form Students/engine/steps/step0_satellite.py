"""
step0_satellite.py — 先看真实的地方:卫星 + figure-ground(整条管线的起点)
=================================================================
抓研究范围的真实卫星影像(Esri World Imagery,contextily),把 OSM footprint 依
stakeholder 著色——让人先看「真实长这样」,再看后面的抽象。三张分开、皆共框对齐:
产出(档名内含 bbox,换地方重跑不会互相覆写):
  out/satellite_<bbox>.png          纯卫星(真实地方)——图上不放任何文字
  out/figureground_<bbox>.png       纯 figure-ground(footprint 依 stakeholder 著色)——只放颜色图例
  out/satellite_overlay_<bbox>.png  卫星 + figure-ground 两层叠在一起——只放颜色图例
纯 Python:contextily(Esri 影像)+ shapely/pyproj 重投影 + matplotlib。零 AI。
诚实:卫星为 Esri World Imagery 公开底图(年份依其更新);footprint/权利为 OSM 离散读法。
"""
import warnings; warnings.filterwarnings("ignore")
# 注意:不在 import 时切 matplotlib 后端,好让 notebook 以 import 方式呼叫时仍维持 inline 显示。
# 当作 script 跑(__main__)才切 Agg(见 main())。
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import contextily as ctx
import pyproj
from shapely.ops import transform as shp_transform
# --- 移到 steps/:把父目录加进 import 路径,确保能找到 common / config ---
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))
__import__('sys').path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[2]))
import config  # 唯一的总开关:PLACE / BBOX / UTM(只改 config.py,本 step 自动跟著)
import common
import plots   # view 层:著色/图例/存档(SH_COLOR / SH_LABEL / save_fig)


def fetch_satellite(bbox=None, zoom=16):
    if bbox is None:
        bbox = config.BBOX
    w, s, e, n = bbox
    img, ext = ctx.bounds2img(w, s, e, n, ll=True, source=ctx.providers.Esri.WorldImagery, zoom=zoom)
    return img, ext


def _draw_footprints(ax, df, utm=None, alpha=.62):
    if utm is None:
        utm = config.UTM
    """把 footprint(UTM→3857)依 stakeholder 著色画到 ax 上(三张图共用同一画法 → 完美对齐)。"""
    to3857 = pyproj.Transformer.from_crs(utm, 3857, always_xy=True).transform
    for _, r in df.iterrows():
        g = shp_transform(to3857, r["geom"])
        for p in common._polys(g):
            xs, ys = p.exterior.xy
            ax.fill(xs, ys, facecolor=plots.SH_COLOR[r["stakeholder"]], alpha=alpha,
                    edgecolor="white", linewidth=.15)


def _color_legend(ax):
    """只放颜色图例(stakeholder 色块 + 文字),放在图面「下方」一排,不遮住图。"""
    handles = [Patch(fc=plots.SH_COLOR[sh], label=plots.SH_LABEL[sh].split("(")[0])
               for sh in common.STAKEHOLDERS]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02),
              ncol=len(handles), fontsize=8, frameon=False)


def fig_satellite(img, ext):
    """第一张:纯卫星,图上不放任何文字。"""
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.imshow(img, extent=ext)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.axis("off")
    return fig


def fig_figureground(df, ext, utm=None):
    """第二张:纯 figure-ground(footprint 依 stakeholder 著色,白底),只放颜色图例。"""
    if utm is None:
        utm = config.UTM
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.set_facecolor("white")
    _draw_footprints(ax, df, utm=utm, alpha=1.0)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.set_aspect("equal"); ax.axis("off")
    _color_legend(ax)
    return fig


def fig_overlay(img, ext, df, utm=None):
    """第三张:卫星 + figure-ground 两层叠在一起,只放颜色图例。"""
    if utm is None:
        utm = config.UTM
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.imshow(img, extent=ext, alpha=.92)
    _draw_footprints(ax, df, utm=utm, alpha=.62)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.axis("off")
    _color_legend(ax)
    return fig


def run(bbox=None, utm=None, df=None, zoom=16):
    """抓卫星 + 画 figure-ground,存三张 bbox 命名的 PNG(换地方重跑不覆写)。
    bbox/utm/df 预设读 config(只改 config.py,本 step 自动跟著)。
    回传 [纯卫星, figure-ground, 叠图] 路径。"""
    if bbox is None:
        bbox = config.BBOX
    if utm is None:
        utm = config.UTM
    img, ext = fetch_satellite(bbox, zoom=zoom)
    if df is None:
        df = common.current_buildings()       # 依 config 取那块楼(离线 bundled 或即时抓 OSM)
    if "stakeholder" not in df.columns:
        df = common.assign_all(df)            # 还没贴权力 → 补贴一次(figure-ground 才有颜色)
    # UTM 校验(reproject 一个质心回 4326,应落在 bbox 内)
    chk = pyproj.Transformer.from_crs(utm, 4326, always_xy=True).transform(*list(df.geom.iloc[0].centroid.coords)[0])
    print("UTM 校验:第一栋质心 → lon/lat %.3f,%.3f(应落在 %.3f–%.3f, %.3f–%.3f 内)" %
          (chk[0], chk[1], bbox[0], bbox[2], bbox[1], bbox[3]))
    slug = common.bbox_slug(bbox)
    p1 = plots.save_fig(fig_satellite(img, ext), "satellite_%s.png" % slug)
    p2 = plots.save_fig(fig_figureground(df, ext, utm=utm), "figureground_%s.png" % slug)
    p3 = plots.save_fig(fig_overlay(img, ext, df, utm=utm), "satellite_overlay_%s.png" % slug)
    return [p1, p2, p3]


def main():
    matplotlib.use("Agg")   # 当 script headless 跑时:存 PNG 不需要显示器
    run()                   # 读 config.BBOX/UTM(换地方只改 config.py)
    print(common.honest_note())


if __name__ == "__main__":
    main()
