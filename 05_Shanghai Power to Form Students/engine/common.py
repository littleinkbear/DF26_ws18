"""
common.py — 上海:本地多源真实数据 → 离散权利 → (只调高度 / 算子配方) → 新形态(共用契约)
=================================================================
回应最初论文的方法,跑**上海本地多源真实数据**(不是 OSM)。本层负责:
  1 选地   subdistrict(name)              街道多边形(非方形、变大小)
  2 裁切   build_cache / load_buildings   AI实测高度 footprint 裁到街道 + 多源 join
  3 权利   assign_all(级联查表)           一栋 = 一个 stakeholder(EULUC→Function→AOI)
  4 高度   scenario_heights               只调高度(conserve 守恒 / grow 只增)      ← 主册
  （5 算子  operators.py / measure.py      原子算子的配方 → 形态指纹                ← 进阶册）
  通用     extrude_obj / plot_footprints / ground_sat(挤体、绘图、卫星底)

两条取数据的路(见 config.py / 数据集说明.md):
  A. 离线(默认):随包带 3 站缓存 data/<slug>/buildings.parquet,不需联网、不需原始数据集。
  B. 自己建(进阶):config.DATASET_ROOT 指向你下载解压的「上海城市数据集」,build_cache() 从
     5 个 spine 文件(街道边界 × AI建筑-带高度 × EULUC × 带年份Function × 百度AOI)裁切+join 重建缓存。

纯 Python:geopandas + shapely + pandas + pyyaml。零 AI、零语意转换。
诚实:① informal 本数据无信号 → 该类保留但恒为空(不无中生有);② AI 高度对极端超高层(>~340m)可能低估;
      ③ AOI 价格/结构仅作离散 tag、不外发原值;④ EULUC 为地块(面)级、优先于建筑级 Function,
      故居住地块内零星公建会被并入「居民」——简化,非产权考证。danwei(工人新村)用途=居住→算居民,只有形态记得它是单位建的。
"""
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import yaml
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import triangulate
import matplotlib
from matplotlib import font_manager as _fm
# 注意:不在 import 时切后端,好让 notebook inline 显示;当 script 跑才切 Agg。
# 中文字型:**先确认机器上真的有**再选(否则会变成豆腐方块)。Windows/Mac/Linux 都覆盖。
def _set_cjk_font():
    avail = {f.name for f in _fm.fontManager.ttflist}
    for f in ("Microsoft YaHei", "Microsoft JhengHei", "SimHei",          # Windows(学生多用)
              "PingFang SC", "Arial Unicode MS", "Hiragino Sans GB",       # macOS
              "Heiti TC", "STHeiti", "Noto Sans CJK SC", "WenQuanYi Zen Hei"):  # 其余/Linux
        if f in avail:
            matplotlib.rcParams["font.sans-serif"] = [f]
            matplotlib.rcParams["axes.unicode_minus"] = False
            return f
    return None
_set_cjk_font()
import config  # 唯一的总开关:SLUG / DATASET_ROOT / SITES(学生主要改 config.py)

ENGINE = Path(__file__).resolve().parent     # engine/(程式码,学生不用进)
ROOT = ENGINE.parent                          # 包根:data/ out/ config.py *.yaml *.ipynb 都在这
DATA = ROOT / "data"
OUT = ROOT / "out"
LOOKUP_PATH = ROOT / "shanghai_lookup.yaml"
SCEN_PATH = ROOT / "power_scenarios.yaml"
UTM = 32651
FLOOR_H = 3.5

STAKEHOLDERS = ["state", "developer", "resident", "informal", "unknown"]
SH_LABEL = {"state": "政府/公共", "developer": "开发商/资本", "resident": "居民",
            "informal": "非正式(本数据无信号)", "unknown": "未标(无用途join)"}
SH_COLOR = {"state": "#4a6fa5", "developer": "#c0654a", "resident": "#5a9367",
            "informal": "#c2a23c", "unknown": "#b8b8b8"}


# --------------------------------------------------------- 数据集路径(从 config.DATASET_ROOT 实时解析)
def dataset_root():
    """学生下载解压的「上海城市数据集」根目录(config.DATASET_ROOT 实时读;reload(config) 后即更新)。
    未填则回退到项目本地的 data_collection/上海城市数据集(开发者机器才有;学生机一般没有)。"""
    if getattr(config, "DATASET_ROOT", None):
        return Path(config.DATASET_ROOT)
    return ROOT.parent.parent / "data_collection" / "上海城市数据集"   # 开发者本地回退


def dataset_paths():
    """5 个 spine 文件路径(相对 dataset_root)。建缓存时用,见 数据集说明.md。"""
    src = dataset_root()
    return {
        "JD":  src / "03-行政区" / "2其他" / "乡镇街道" / "上海市_乡镇边界.shp",
        "AI":  src / "01-建筑轮廓" / "②AI解析" / "上海市_建筑-AI影像解译-带高度.shp",
        "EU":  src / "09-开源土地利用" / "09-开源土地利用" / "开源建设用地分类" / "Data" / "上海市-开源建设用地.shp",
        "FN":  src / "01-建筑轮廓" / "③其它" / "上海市_建筑-带年份-内测版.shp",
        "AOI": src / "02-POI&AOI" / "2-AOI" / "AOI-baiduapi" / "SHP" / "上海市_AOI.shp",
    }


# --------------------------------------------------------- 3 离散权利(级联查表)
def load_lookup(path=LOOKUP_PATH):
    return yaml.safe_load(open(path, encoding="utf-8"))


def _t(v):
    """正规化 tag 值:nan/none/空 → 「无」。"""
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none", "") else s


def assign_stakeholder(row, lk):
    """级联离散:按 lk['cascade'] 顺序(euluc→function→aoi),第一个来源给出映射即定。
    一栋 = 一个 stakeholder。informal 永不在此被指派(数据无信号),保留作恒空类。"""
    for src in lk["cascade"]:
        if src == "euluc":
            m = lk["euluc"].get(_t(row.get("euluc")))
            if m:
                return m
        elif src == "function":
            m = lk["function"].get(_t(row.get("function")))
            if m and m != "unknown":
                return m
        elif src == "aoi":
            for field in ("aoi_type2", "aoi_type1", "aoi_type"):
                v = _t(row.get(field))
                if v:
                    for kw, sh in lk["aoi_contains"].items():
                        if kw in v:
                            return sh
    return lk.get("default", "unknown")


def assign_all(df, lookup=None):
    """加 'stakeholder' 栏(改 shanghai_lookup.yaml 可变这步)。"""
    lookup = lookup or load_lookup()
    df = df.copy()
    df["stakeholder"] = df.apply(lambda r: assign_stakeholder(r, lookup), axis=1)
    return df


# --------------------------------------------------------- 1+2 选地 + 裁切 + 多源 join(慢,缓存)
def subdistrict(name, JD):
    """按 name 取街道多边形(4326)。返回 (row, polygon)。"""
    jd = gpd.read_file(JD)
    row = jd[jd["name"].fillna("") == name]
    if len(row) == 0:
        row = jd[jd["name"].fillna("").str.contains(name)]
    if len(row) == 0:
        raise ValueError("找不到街道:%s" % name)
    row = row.iloc[[0]].to_crs(4326)
    return row, row.geometry.iloc[0]


def _join(cent, path, bb, cols_map):
    """cent(含 bid 的 representative-point GDF,4326)within path 的面,取 cols_map 列。返回 DataFrame[bid, 目标列...]。"""
    try:
        src = gpd.read_file(path, bbox=bb)
    except Exception:
        return pd.DataFrame({"bid": []})
    have = {k: v for k, v in cols_map.items() if k in src.columns}
    if not have:
        return pd.DataFrame({"bid": []})
    src = src[list(have) + ["geometry"]].rename(columns=have)
    src = src[src.geometry.notna()]
    j = gpd.sjoin(cent[["bid", "geometry"]], src.to_crs(4326), predicate="within", how="left")
    j = j.dropna(subset=list(have.values()), how="all").drop_duplicates("bid")
    return j[["bid"] + list(have.values())]


def build_cache(name=None, slug=None):
    """进阶:从原始「上海城市数据集」裁切 + 多源 join,写 data/<slug>/buildings.parquet(几何 32651)。
    需要 config.DATASET_ROOT 已指向解压后的数据集。返回 GeoDataFrame。详见「01_怎么选数据」notebook。"""
    slug = slug or config.SLUG
    name = name or config.site_name(slug)
    P = dataset_paths()
    if not P["AI"].exists():
        raise FileNotFoundError(
            "找不到数据集文件:%s\n请先在 config.py 把 DATASET_ROOT 指向你解压的「上海城市数据集」根目录。"
            "(没下载也没关系:随包已带 3 站缓存,直接用 load_buildings 即可。见 数据集说明.md)" % P["AI"])

    row, poly = subdistrict(name, P["JD"])
    bb = poly.bounds
    area_km2 = float(row.to_crs(UTM).area.iloc[0] / 1e6)

    ai = gpd.read_file(P["AI"], bbox=bb)
    ai = gpd.clip(ai, poly)
    ai = ai[ai.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()
    ai = ai.rename(columns={"Height": "height_m", "Area": "area_src"})
    ai["height_m"] = pd.to_numeric(ai["height_m"], errors="coerce")
    ai = ai[ai["height_m"] > 0].reset_index(drop=True)
    ai["bid"] = range(len(ai))
    ai = ai.set_crs(4326, allow_override=True)

    cent = ai[["bid", "geometry"]].copy()
    cent["geometry"] = ai.geometry.representative_point()
    cent = gpd.GeoDataFrame(cent, geometry="geometry", crs=4326)

    eu = _join(cent, P["EU"], bb, {"class2": "euluc"})
    fn = _join(cent, P["FN"], bb, {"Function": "function", "Age": "age"})
    aoi = _join(cent, P["AOI"], bb, {"type1": "aoi_type1", "type2": "aoi_type2", "type": "aoi_type",
                                     "结构": "aoi_struct", "价格": "aoi_price", "时间": "aoi_year"})

    out = ai.drop(columns=[c for c in ai.columns if c not in ("bid", "height_m", "area_src", "geometry")])
    for part in (eu, fn, aoi):
        if len(part):
            out = out.merge(part, on="bid", how="left")
    out = gpd.GeoDataFrame(out, geometry="geometry", crs=4326).to_crs(UTM)
    out["area_m2"] = out.geometry.area
    out["height_source"] = "measured_ai"
    out = assign_all(out)

    d = DATA / slug
    d.mkdir(parents=True, exist_ok=True)
    out.to_parquet(d / "buildings.parquet")
    yaml.safe_dump({"name": name, "slug": slug, "area_km2": area_km2, "n": len(out),
                    "bounds_lonlat": list(poly.bounds)},
                   open(d / "site.yaml", "w", encoding="utf-8"), allow_unicode=True)
    print("  ✓ 建缓存 %s(%s):%d 栋 → %s" % (name, slug, len(out), (d / "buildings.parquet").relative_to(ROOT)))
    return out


def has_cache(slug=None):
    slug = slug or config.SLUG
    return (DATA / slug / "buildings.parquet").exists()


def load_buildings(slug=None):
    """读缓存的 per-site buildings(几何 32651);加 'geom' 列。回传 DataFrame。"""
    slug = slug or config.SLUG
    gdf = gpd.read_parquet(DATA / slug / "buildings.parquet")
    df = pd.DataFrame(gdf.drop(columns="geometry"))
    df["geom"] = list(gdf.geometry)
    if "stakeholder" not in df.columns:
        df = assign_all(df)
    return df


def current_buildings(slug=None):
    """整条管线的取数据入口:缓存在就直接读(离线);缓存缺、但 DATASET_ROOT 已设 → 现建再读。"""
    slug = slug or config.SLUG
    if has_cache(slug):
        return load_buildings(slug)
    if getattr(config, "DATASET_ROOT", None):
        build_cache(config.site_name(slug), slug)
        return load_buildings(slug)
    raise FileNotFoundError(
        "没有 %s 的缓存,且未设 config.DATASET_ROOT。\n"
        "→ 随包自带 lujiazui/caoyang/yuyuan 三站缓存,把 SLUG 设成其一即可离线跑;\n"
        "→ 想换别的街道,请下载「上海城市数据集」并设 DATASET_ROOT,见 数据集说明.md。" % slug)


def site_meta(slug=None):
    slug = slug or config.SLUG
    return yaml.safe_load(open(DATA / slug / "site.yaml", encoding="utf-8"))


# --------------------------------------------------------- 4 权力情景(只调高度;与 osm 版同引擎)
def load_scenarios(path=SCEN_PATH):
    return yaml.safe_load(open(path, encoding="utf-8"))["scenarios"]


def apply_scenario(height_m, stakeholder, scenario):
    """grow:只增不减。h' = max(既有, min(h×mult, cap))。"""
    pol = (scenario or {}).get(stakeholder, {})
    h = height_m * max(1.0, float(pol.get("mult", 1.0)))
    if "cap_m" in pol:
        h = min(h, float(pol["cap_m"]))
    return max(h, height_m)


def scenario_heights(df, scenario):
    """conserve(默认):总 GFA 守恒、权力只重分配,new_h = h×w×(ΣGFA/Σ(GFA·w));grow:见 apply_scenario。"""
    mode = (scenario or {}).get("_mode", "conserve")
    if mode == "grow":
        return df.apply(lambda r: apply_scenario(r["height_m"], r["stakeholder"], scenario), axis=1)
    w = df["stakeholder"].map(lambda sh: float((scenario or {}).get(sh, {}).get("mult", 1.0)))
    gfa = df["area_m2"] * df["height_m"]
    T = float(gfa.sum()); S = float((gfa * w).sum())
    if S <= 0:
        return df["height_m"]
    return (df["height_m"] * w * (T / S)).clip(lower=3.0)


# --------------------------------------------------------- recs 桥(进阶册 operators 的工作单位)
def to_recs(df):
    """DataFrame(含 geom/height_m/stakeholder)→ records 列表 [{geom, h, sh, area, frozen}]。
    主册用 DataFrame(只调高度),进阶册 operators.py 用 recs(改几何)——共用同一份载入。"""
    recs = []
    for _, r in df.iterrows():
        recs.append({"geom": r["geom"], "h": float(r["height_m"]),
                     "sh": r["stakeholder"], "area": float(r.get("area_m2", r["geom"].area)),
                     "frozen": False})
    return recs


# --------------------------------------------------------- 通用工具(绘图 / OBJ / 卫星底)
def _polys(geom):
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    return []


def gfa_of(recs):
    return sum(r["geom"].area * r["h"] for r in recs)


def plot_footprints(ax, df_or_recs, color_for, lw=0.2):
    """footprint 著色(批量 PolyCollection,几千~上万栋也秒画)。df_or_recs 可为 DataFrame 或 recs 列表。"""
    from matplotlib.collections import PolyCollection
    rows = (r for _, r in df_or_recs.iterrows()) if hasattr(df_or_recs, "iterrows") else iter(df_or_recs)
    verts, colors = [], []
    for r in rows:
        col = color_for(r)
        for p in _polys(r["geom"]):
            verts.append(list(p.exterior.coords)); colors.append(col)
    if verts:
        ax.add_collection(PolyCollection(verts, facecolors=colors, edgecolors="white", linewidths=lw), autolim=True)
        ax.autoscale_view()
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])


def save_fig(fig, name, out=OUT):
    import matplotlib.pyplot as plt
    out.mkdir(parents=True, exist_ok=True)
    p = out / name
    fig.savefig(p, dpi=120, bbox_inches="tight"); plt.close(fig)
    print("  -> wrote", p.relative_to(ROOT)); return p


def _ring(poly):
    c = list(poly.exterior.coords)
    if len(c) > 1 and c[0] == c[-1]:
        c = c[:-1]
    return c


def _iter_geom_h(df_or_recs, height_col="height_m"):
    """统一迭代 (geom, h):DataFrame 用 height_col;recs 用 'h'。"""
    if hasattr(df_or_recs, "iterrows"):
        for _, r in df_or_recs.iterrows():
            yield r["geom"], float(r[height_col])
    else:
        for r in df_or_recs:
            yield r["geom"], float(r["h"])


def extrude_obj(df_or_recs, height_col="height_m", origin=None):
    """真实 footprint 挤成量体 OBJ(墙 + 三角顶盖)。回传 (obj_str, n_verts, n_faces)。接受 DataFrame 或 recs。"""
    items = list(_iter_geom_h(df_or_recs, height_col))
    polys_all = [p for g, _ in items for p in _polys(g)]
    if origin is None:
        minx = min(p.bounds[0] for p in polys_all); miny = min(p.bounds[1] for p in polys_all)
        origin = (minx, miny)
    ox, oy = origin
    V, F = [], []

    def addv(x, y, z):
        V.append((x - ox, y - oy, z)); return len(V)

    for geom, h in items:
        for poly in _polys(geom):
            ring = _ring(poly)
            n = len(ring)
            if n < 3:
                continue
            base_b = len(V)
            for (x, y) in ring:
                addv(x, y, 0.0)
            base_t = len(V)
            for (x, y) in ring:
                addv(x, y, h)
            for i in range(n):
                j = (i + 1) % n
                b0, b1 = base_b + i + 1, base_b + j + 1
                t0, t1 = base_t + i + 1, base_t + j + 1
                F.append((b0, b1, t1)); F.append((b0, t1, t0))
            for tri in triangulate(poly):
                if not poly.contains(tri.representative_point()):
                    continue
                tc = list(tri.exterior.coords)[:3]
                a = addv(tc[0][0], tc[0][1], h); b = addv(tc[1][0], tc[1][1], h); c = addv(tc[2][0], tc[2][1], h)
                F.append((a, b, c))
    lines = ["# shanghai_power_to_form (DF26_ws18) — real Shanghai footprints extruded (meters, EPSG:32651-local)",
             "# %d items, height=%s" % (len(items), height_col)]
    for (x, y, z) in V:
        lines.append("v %.3f %.3f %.3f" % (x, y, z))
    for (a, b, c) in F:
        lines.append("f %d %d %d" % (a, b, c))
    return "\n".join(lines) + "\n", len(V), len(F)


def ground_sat(minx, miny, maxx, maxy, cache_png, factor=2.0):
    """抓比 patch 宽 factor× 的真实卫星图(Esri)贴 viewer 地面 → 体块坐在真实上海上。
    返回 (data_uri_jpeg, local_extent[lx0,ly0,lx1,ly1]),local 相对 (minx,miny) 与 footprint 同系。"""
    import json as _json, base64, contextily as ctx, pyproj
    from PIL import Image
    cache_png = Path(cache_png); meta_p = cache_png.with_suffix(".json")
    if cache_png.exists() and meta_p.exists():
        return "data:image/jpeg;base64," + base64.b64encode(cache_png.read_bytes()).decode(), _json.load(open(meta_p))
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    hw, hh = (maxx - minx) / 2 * factor, (maxy - miny) / 2 * factor
    to4326 = pyproj.Transformer.from_crs(UTM, 4326, always_xy=True).transform
    cs = [to4326(cx - hw, cy - hh), to4326(cx + hw, cy - hh), to4326(cx - hw, cy + hh), to4326(cx + hw, cy + hh)]
    lons = [p[0] for p in cs]; lats = [p[1] for p in cs]
    span = max(2 * hw, 2 * hh); zoom = 16 if span < 2500 else (15 if span < 6500 else 14)
    img, ext = ctx.bounds2img(min(lons), min(lats), max(lons), max(lats), ll=True,
                              source=ctx.providers.Esri.WorldImagery, zoom=zoom)
    fr = pyproj.Transformer.from_crs(3857, UTM, always_xy=True).transform
    ux0, uy0 = fr(ext[0], ext[2]); ux1, uy1 = fr(ext[1], ext[3])
    local = [ux0 - minx, uy0 - miny, ux1 - minx, uy1 - miny]
    arr = img[:, :, :3] if (getattr(img, "ndim", 0) == 3 and img.shape[2] >= 3) else img
    cache_png.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr).save(cache_png, "JPEG", quality=82)
    _json.dump(local, open(meta_p, "w"))
    return "data:image/jpeg;base64," + base64.b64encode(cache_png.read_bytes()).decode(), local


def site_ground(minx, miny, maxx, maxy, slug=None, factor=2.0):
    slug = slug or config.SLUG
    try:
        return ground_sat(minx, miny, maxx, maxy, OUT / slug / "ground_sat.jpg", factor)
    except Exception as e:
        print("  卫星底失败", slug, e); return None, None


def honest_note(place="上海"):
    return ("本地多源真实数据(AI建筑-实测高度 + EULUC用途 + 带年份Function + 百度AOI)· "
            "「谁的权利」为用途的离散级联查表、非产权考证 · informal 本数据无信号(恒空)· "
            "danwei工人新村按用途算居民(形态记得它是单位建的)· AOI价格/结构仅作离散tag不外发 · %s 教学样本" % place)


if __name__ == "__main__":
    import sys
    slug = sys.argv[1] if len(sys.argv) > 1 else config.SLUG
    df = current_buildings(slug)
    print("== %s (%s) ==" % (config.site_name(slug), slug))
    print("栋数:", len(df), "| 面积km2:", round(site_meta(slug)["area_km2"], 2))
    h = df["height_m"].astype(float)
    print("高度 实测 m: med %.1f / p90 %.1f / max %.1f" % (h.median(), h.quantile(.9), h.max()))
    print("stakeholder:", df.stakeholder.value_counts().to_dict())
    eu = df["euluc"].apply(_t).ne("").mean() if "euluc" in df else 0
    print("EULUC 覆盖 %.0f%% | unknown %.0f%%" % (eu * 100, (df.stakeholder == "unknown").mean() * 100))
    print(honest_note())
