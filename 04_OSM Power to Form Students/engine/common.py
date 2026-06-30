"""
common.py — OSM → 离散 stakeholder → 只调高度 → 新形态(共用契约)
=================================================================
回应最初论文的方法,**最简单版**:
  拿 OSM 楼 → 直接用 tag 离散地对应「每栋是谁的权利」(不做语意转换,纯查表)
  → 改「权力情景」(各 stakeholder 一套只动高度的政策)→ 看新城市形态。

资料:data/buildings.csv(1163 栋,新加坡 大巴窑(Toa Payoh),osmnx 抓)。栏位:
  building, amenity, office, shop, tourism, name : OSM 原始 tag(字串,空=无)
  height_m        : 解析后高度(m);来源 height tag → building:levels×3.5 → 预设
  height_source   : measured / levels_x3.5 / default
  area_m2         : footprint 面积(m²,UTM)
  wkt             : footprint 几何(WKT,UTM 公尺座标)

纯 Python:pandas + shapely(+ pyyaml)。零 AI、零语意转换。
诚实:tag 稀疏(很多 building=yes / 无 tag → unknown);高度多为 levels×3.5 估计;
      「谁的权利」是从 tag 的**离散、可编辑**对应,不是真实产权考证——这是教学练习(forward:改权力→看形态)。
"""
from pathlib import Path
import csv as _csv
import math
import numpy as np
import pandas as pd
import yaml
import config  # 唯一的总开关:PLACE / BBOX / UTM(学生只改 config.py)
from shapely import wkt as shapely_wkt
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import triangulate
# 注意:common.py 是 model 層,**不碰 matplotlib**。所有繪圖在 engine/plots/。

ENGINE = Path(__file__).resolve().parent   # engine/(程式碼,学生不用进)
ROOT = ENGINE.parent                        # 项目根目录:data/ out/ config.py *.yaml *.ipynb 都在这
DATA = ROOT / "data" / "buildings.csv"

# 输出不覆写:每次跑(每个 Python 程序 / kernel)产出进 out/{时间戳} 自己的资料夹。
#   - notebook Run All:同一个 kernel 共用同一个时间戳资料夹 → 一次跑的图/OBJ/CSV 聚在一起。
#   - 终端各 step 各跑一次:各自一个时间戳资料夹,彼此不覆写、也不覆写上一次的结果。
# 想回看旧结果就开旧时间戳资料夹;OUT_ROOT 是所有批次的总目录。
import datetime as _dt
RUN_STAMP = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")   # 本次执行的时间戳(程序启动时定一次)
OUT_ROOT = ROOT / "out"                                     # 所有批次的总目录
OUT = OUT_ROOT / RUN_STAMP                                  # 本次执行专属输出夹(各档写这里,不覆写)
OUT.mkdir(parents=True, exist_ok=True)
LOOKUP_PATH = ROOT / "stakeholder_lookup.yaml"
SCEN_PATH = ROOT / "power_scenarios.yaml"

STAKEHOLDERS = ["state", "developer", "resident", "informal", "unknown"]
# 角色的中文名 / 著色屬於 view 層,移到 engine/plots/_base.py(SH_LABEL / SH_COLOR)。
FLOOR_H = 3.5


def load_buildings(path=DATA):
    """载入 OSM 楼 + 解析 WKT 几何(加 'geom' 栏)。"""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df["height_m"] = pd.to_numeric(df["height_m"], errors="coerce").fillna(FLOOR_H * 3)
    df["area_m2"] = pd.to_numeric(df["area_m2"], errors="coerce").fillna(0.0)
    df["geom"] = df["wkt"].apply(shapely_wkt.loads)
    return df


# 大巴窑(Toa Payoh)预设 bbox=(W,S,E,N) lon/lat:对应 bundled 的 data/buildings.csv。
# 只要 BBOX≈这个值,就用 bundled 资料(离线、不需 osmnx);换地方才即时抓 OSM。
DEFAULT_BBOX = (103.838, 1.327, 103.862, 1.348)


def fetch_osm_buildings(bbox, utm, place="custom"):
    """换地方:即时抓某 bbox 的 OSM 建筑,输出成 bundled 同样 schema 的 CSV,回传 Path。
    bbox=(W,S,E,N) lon/lat;utm = 目标 UTM EPSG(让面积/座标以米计)。
    已抓过(同 bbox slug)就直接重用 = 快取,不重复抓。
    需要 osmnx(pip install osmnx)+ 联网;否则丢清楚的错误讯息。"""
    slug = bbox_slug(bbox)
    out_csv = ROOT / "data" / ("buildings_%s.csv" % slug)
    if out_csv.exists():
        print("  ↻ 重用快取 / reuse cached:", out_csv.relative_to(ROOT))
        return out_csv

    try:
        import osmnx as ox
    except ImportError:
        raise ImportError("换地方需要 osmnx:pip install osmnx(并联网)")
    from shapely.geometry import box

    w, s, e, n = (float(v) for v in bbox)
    poly = box(w, s, e, n)   # box(minx=W, miny=S, maxx=E, maxy=N)
    print("  ⏳ 抓 OSM 建筑 / fetching OSM buildings for %s …(需联网)" % place)
    gdf = ox.features_from_polygon(poly, {"building": True})   # features_from_polygon = 版本稳定

    # 只留多边形 footprint(滤掉 building=* 的点/线)→ 投影到目标 UTM(米)
    gdf = gdf[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()
    gdf = gdf.to_crs(utm)

    def _col(name):
        """从 gdf 取某栏(有就取、缺就空字串),清掉 nan。"""
        if name in gdf.columns:
            return gdf[name].apply(lambda v: "" if pd.isna(v) else str(v)).tolist()
        return [""] * len(gdf)

    def _height(row_h, row_lv):
        """height tag(数字)→ measured;elif building:levels → levels×3.5;else 预设 3 层。"""
        h = str(row_h).strip()
        if h and h.lower() not in ("nan", "none"):
            try:
                return float(str(h).split()[0].replace("m", "").strip()), "measured"
            except (ValueError, IndexError):
                pass
        lv = str(row_lv).strip()
        if lv and lv.lower() not in ("nan", "none"):
            try:
                return float(str(lv).split(";")[0].strip()) * FLOOR_H, "levels_x3.5"
            except ValueError:
                pass
        return FLOOR_H * 3, "default"

    raw_h = _col("height")
    raw_lv = _col("building:levels")
    rows = []
    geoms = list(gdf.geometry)
    cols = {k: _col(k) for k in ("building", "amenity", "office", "shop", "tourism", "name")}
    for i, g in enumerate(geoms):
        hm, hsrc = _height(raw_h[i], raw_lv[i])
        rows.append({
            "building": cols["building"][i], "amenity": cols["amenity"][i],
            "office": cols["office"][i], "shop": cols["shop"][i],
            "tourism": cols["tourism"][i], "name": cols["name"][i],
            "height_m": hm, "height_source": hsrc,
            "area_m2": round(float(g.area), 1), "wkt": g.wkt,
        })
    out = pd.DataFrame(rows, columns=["building", "amenity", "office", "shop", "tourism",
                                      "name", "height_m", "height_source", "area_m2", "wkt"])
    out.to_csv(out_csv, index=False)
    print("  ✓ 抓到 %d 栋 / fetched %d buildings → %s" % (len(out), len(out), out_csv.relative_to(ROOT)))
    return out_csv


def get_buildings(bbox, utm, place=None):
    """整条管线的单一入口:预设(≈大巴窑 bbox)用 bundled CSV(离线、不需 osmnx);
    换地方(bbox 不同)就即时抓 OSM 那一块再读进来。回传已解析几何的 DataFrame。"""
    tol = 1e-4
    if all(abs(float(a) - float(b)) <= tol for a, b in zip(bbox, DEFAULT_BBOX)):
        return load_buildings()   # bundled 大巴窑,离线
    return load_buildings(fetch_osm_buildings(bbox, utm, place or "custom"))


def current_buildings():
    """整条管线的『按 config 取资料』入口:**呼叫时**才读 config
    (所以在 notebook 里 importlib.reload(config) 后重跑就会跟著换地方)。
    config.BUNDLED=True(预设:LAT/LON 留空)→ 离线读 bundled 大巴窑;
    否则(填了中心点 LAT/LON)→ 即时抓 config.BBOX 那块 OSM 并快取成每个 bbox 一份 CSV
    (重复呼叫直接重用快取、很便宜)。回传已解析几何的 DataFrame。"""
    return load_buildings() if config.BUNDLED else get_buildings(config.BBOX, config.UTM, config.PLACE)


def use_yaml(lookup=None, scenarios=None):
    """切換要用哪組 YAML(assign_all / plots / scenario_heights 全部跟著)。
    lookup / scenarios:檔名(相對本專案根目錄)或絕對路徑;None=該項保持不變。
    回傳目前生效的 (LOOKUP_PATH, SCEN_PATH)。找不到檔就丟清楚錯誤,不會默默用錯檔。
    用法(notebook):common.use_yaml('stakeholder_lookup-2.yaml', 'power_scenarios-2.yaml')。"""
    global LOOKUP_PATH, SCEN_PATH

    def _resolve(x, what):
        p = Path(x)
        if not p.is_absolute():
            p = ROOT / p
        if not p.exists():
            raise FileNotFoundError("找不到 %s:%s(檔名相對 %s)" % (what, p, ROOT))
        return p

    if lookup is not None:
        LOOKUP_PATH = _resolve(lookup, "stakeholder lookup yaml")
    if scenarios is not None:
        SCEN_PATH = _resolve(scenarios, "power scenarios yaml")
    return LOOKUP_PATH, SCEN_PATH


def load_lookup(path=None):
    # path=None → 讀目前生效的 LOOKUP_PATH(可被 use_yaml 切換);傳 path 則讀指定檔。
    return yaml.safe_load(open(path or LOOKUP_PATH, encoding="utf-8"))


def _t(v):
    """正规化 tag 值:nan/none/空 一律当「无」(防 CSV 的 'nan' 字串误判)。"""
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none", "") else s


def assign_stakeholder(row, lookup):
    """tag → stakeholder(离散、依 lookup 的优先序)。第一个命中即定;都不中 → default。
    通用规则:rule 里每个 key 都当成一个 tag 栏名,值是允许的清单(list);
    `any_<栏名>: true` = 该栏只要非空就命中(如 any_shop / any_office / any_library)。
    → 学生在 yaml 自由加 stakeholder、改规则 key(只要对应到资料里有的栏)都照吃,不写死四个栏。"""
    rules = lookup.get("rules", {}) or {}
    order = lookup.get("order") or list(rules.keys())
    for sh in order:
        r = rules.get(sh, {}) or {}
        for key, want in r.items():
            if str(key).startswith("any_"):
                col = str(key)[4:]                       # any_shop → 看 'shop' 栏非空即算
                if want and _t(row.get(col, "")):
                    return sh
                continue
            val = _t(row.get(key, ""))                   # key 当 tag 栏名
            if val and isinstance(want, (list, tuple, set)) and val in want:
                return sh
    return lookup.get("default", "unknown")


def assign_all(df, lookup=None):
    """回传新栏 'stakeholder'。"""
    lookup = lookup or load_lookup()
    df = df.copy()
    df["stakeholder"] = df.apply(lambda r: assign_stakeholder(r, lookup), axis=1)
    return df


def load_scenarios(path=None):
    # path=None → 讀目前生效的 SCEN_PATH(可被 use_yaml 切換)。
    data = yaml.safe_load(open(path or SCEN_PATH, encoding="utf-8")) or {}
    scen = data.get("scenarios")
    if scen is None:
        raise KeyError("YAML 缺少最外層 'scenarios:' 區塊:%s" % (path or SCEN_PATH))
    return scen


def apply_scenario(height_m, stakeholder, scenario):
    """**只增不减**:既有 = 政府与私人早已协商沉淀的事实,不拆、不缩。
    情景 = 各方的「增建」政策:mult≥1 在既有高度上加盖(垂直加密 / 都更);
    cap_m(可选)= 新增高度的上限,但**仍不会低于既有**。
    h' = max(既有高度, min(h × mult, cap_m))。footprint / 标签不变;**GFA 只增不减**。
    (资本家增建、都更新增 = 合理;拆矮既有 = 不现实,故被禁止。)"""
    pol = (scenario or {}).get(stakeholder, {})
    h = height_m * max(1.0, float(pol.get("mult", 1.0)))   # mult<1 视为「不增」(不准缩既有)
    if "cap_m" in pol:
        h = min(h, float(pol["cap_m"]))
    return max(h, height_m)   # 铁律:永不低于既有


def scenario_heights(df, scenario):
    """回传套用某情景后的逐栋新高度 Series(只高度变,footprint/标签不变)。
    两种模式(scenario['_mode'],预设 conserve):
      conserve(总量守恒、重分配):总 GFA 不变,权力只**重分配**既有总量——
        某方多拿、某方少拿,加总不变。每方权重 = 其 mult(可<1=让出、>1=多拿);
        new_h_i = h_i × w_i × (ΣGFA / Σ(GFA·w)),保证 Σ新GFA = Σ旧GFA(资本家 w 稍>1 即多分一点)。
      grow(只增、都更新增):既有为地板,只增不减,总 GFA 上升(见 apply_scenario)。"""
    mode = (scenario or {}).get("_mode", "conserve")
    if mode == "grow":
        return df.apply(lambda r: apply_scenario(r["height_m"], r["stakeholder"], scenario), axis=1)
    w = df["stakeholder"].map(lambda sh: float((scenario or {}).get(sh, {}).get("mult", 1.0)))
    gfa = df["area_m2"] * df["height_m"]
    T = float(gfa.sum()); S = float((gfa * w).sum())
    if S <= 0:
        return df["height_m"]
    return (df["height_m"] * w * (T / S)).clip(lower=3.0)


# ----------------------------------------------------------------- 几何工具
def _polys(geom):
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    return []


def bbox_slug(bbox):
    """把 bbox=(W,S,E,N) 转成档名片段,让不同研究范围的输出互不覆写。
    例:(103.838,1.327,103.862,1.348) -> 'bbox_103.8380_1.3270_103.8620_1.3480'。"""
    w, s, e, n = (float(v) for v in bbox)
    return "bbox_%.4f_%.4f_%.4f_%.4f" % (w, s, e, n)


# ----------------------------------------------------------------- OBJ 挤体(真实 footprint)
def _ring(poly):
    c = list(poly.exterior.coords)
    if len(c) > 1 and c[0] == c[-1]:
        c = c[:-1]
    return c


def extrude_obj(df, height_col="height_m", origin=None):
    """把真实 footprint 挤成量体 OBJ(墙 + 三角化顶盖)。回传 (obj_str, n_verts, n_faces)。
    origin: (x0,y0) 平移到原点附近(预设用资料 bbox 左下);单位公尺。"""
    if origin is None:
        minx = min(p.bounds[0] for g in df["geom"] for p in _polys(g))
        miny = min(p.bounds[1] for g in df["geom"] for p in _polys(g))
        origin = (minx, miny)
    ox, oy = origin
    V, F = [], []

    def addv(x, y, z):
        V.append((x - ox, y - oy, z)); return len(V)  # OBJ 1-indexed

    for _, r in df.iterrows():
        h = float(r[height_col])
        for poly in _polys(r["geom"]):
            ring = _ring(poly)
            n = len(ring)
            if n < 3:
                continue
            base_b = len(V)
            for (x, y) in ring:
                addv(x, y, 0.0)            # 底环 (base_b+1 .. base_b+n)
            base_t = len(V)
            for (x, y) in ring:
                addv(x, y, h)             # 顶环 (base_t+1 .. base_t+n)
            for i in range(n):            # 墙:每边 2 三角
                j = (i + 1) % n
                b0, b1 = base_b + i + 1, base_b + j + 1
                t0, t1 = base_t + i + 1, base_t + j + 1
                F.append((b0, b1, t1)); F.append((b0, t1, t0))
            for tri in triangulate(poly):  # 顶盖:三角化、滤掉落在多边形外的(非凸)
                if not poly.contains(tri.representative_point()):
                    continue
                tc = list(tri.exterior.coords)[:3]
                a = addv(tc[0][0], tc[0][1], h); b = addv(tc[1][0], tc[1][1], h); c = addv(tc[2][0], tc[2][1], h)
                F.append((a, b, c))
    lines = ["# osm_power_to_form — real OSM footprints extruded (zero-dep, meters)",
             "# %d buildings, height col=%s" % (len(df), height_col)]
    for (x, y, z) in V:
        lines.append("v %.3f %.3f %.3f" % (x, y, z))
    for (a, b, c) in F:
        lines.append("f %d %d %d" % (a, b, c))
    return "\n".join(lines) + "\n", len(V), len(F)


def honest_note():
    return ("OSM tag 稀疏(building=yes/无tag→unknown)· 高度多为 levels×3.5 估计 · "
            "「谁的权利」为 tag 的离散可编辑对应、非产权考证 · 新加坡 大巴窑(Toa Payoh) 教学样本")


if __name__ == "__main__":
    df = load_buildings()
    print("buildings:", len(df), "| height_source:", df.height_source.value_counts().to_dict())
    df = assign_all(df)
    print("stakeholder:", df.stakeholder.value_counts().to_dict())
    scen = load_scenarios()
    print("scenarios:", list(scen.keys()))
    base_gfa = (df.area_m2 * df.height_m / FLOOR_H).sum()
    for name in scen:
        h2 = scenario_heights(df, scen[name])
        gfa = (df.area_m2 * h2 / FLOOR_H).sum()
        print("  %-14s 总GFA %.2e (×%.2f baseline) 平均高 %.1fm" % (name, gfa, gfa / base_gfa, h2.mean()))
    obj, nv, nf = extrude_obj(df.head(50))
    print("OBJ(前50栋):verts", nv, "faces", nf)
    print(honest_note())
