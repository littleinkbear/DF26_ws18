"""接入隔壁 05 的引擎(不重复数据/算子/形态逻辑)。
把 05 根(config.py)和 05/engine 加进 sys.path,设好 05 的 config.SLUG,暴露给 07。
07 总开关命名 settings.py 而非 config.py,避免和 05 的 config 撞名。"""
import sys
from pathlib import Path
import importlib
# 确保能找到 07 的 settings.py
_07ROOT = Path(__file__).resolve().parent.parent
if str(_07ROOT) not in sys.path:
    sys.path.insert(0, str(_07ROOT))
import settings   # 07 总开关

WS05 = Path(settings.WS05).resolve()
_ENGINE = WS05 / "engine"
for p in (str(WS05), str(_ENGINE)):     # 根+engine 都要在路径上
    if p not in sys.path:
        sys.path.insert(0, p)

import config as ws05_config            # 05 的 config.py
import common as C                       # 05 引擎:缓存/角色/高度/recs/OBJ
import operators as ops                  # 05 引擎:9 算子+配方
import measure as M                      # 05 引擎:形态指纹
import plots                             # 05 引擎:绘图


def use_site(slug=None):
    """切到某站点(设好 05 的 config.SLUG)。返回 slug。"""
    slug = slug or settings.SLUG
    ws05_config.SLUG = slug
    importlib.reload  # noqa 占位:config 模块级状态
    return slug


def load_recs(slug=None):
    """读某站点楼宇 recs 列表 [{geom,h,sh,frozen}]。"""
    slug = use_site(slug)
    df = C.assign_all(C.current_buildings(slug))
    return C.to_recs(df), df


def resolve_regimes(regimes=None):
    """把「要跑哪些体制」对齐 05 regimes.yaml 的**实际** key,返回 (names, regs)。
    - 清单默认取 06 config.yaml 的 regimes;写 regimes: all 则自动跟随 05 的全部体制。
    - 清单里 05 找不到的名字:跳过并警告(学生改了 05 regimes.yaml 没同步 06 时,不再 KeyError)。
    - 若 current 以外一个都对不上:自动改用 05 regimes.yaml 的全部体制,报告照样能出。"""
    regs = ops.load_regimes(WS05 / "regimes.yaml")
    wanted = settings.REGIMES if regimes is None else regimes
    if isinstance(wanted, str):                       # regimes: all
        wanted = ["current"] + list(regs)
    keep = [n for n in wanted if n == "current" or n in regs]
    missing = [n for n in wanted if n != "current" and n not in regs]
    if missing:
        print("  ⚠ 06 config.yaml 的 regimes 里,这些在 05 regimes.yaml 找不到,已跳过:%s" % ", ".join(missing))
        print("    05 目前可用体制:%s(改 06 config.yaml 对齐,或直接写 regimes: all 自动跟随 05)" % ", ".join(regs))
    if not [n for n in keep if n != "current"]:       # 全对不上 → 跟随 05 现有全部体制
        keep = ["current"] + list(regs)
        print("  ↪ 自动改用 05 regimes.yaml 的全部体制:%s" % ", ".join(keep))
    return keep, regs


def regime_recs(slug=None, regimes=None):
    """对某站点施加各权力体制,得 {regime: recs}(current=现状基线)。体制名先经 resolve_regimes 对齐。"""
    names, regs = resolve_regimes(regimes)
    recs, _ = load_recs(slug)
    out = {}
    for name in names:
        out[name] = recs if name == "current" else ops.apply_regime(recs, regs[name])
    return out, regs


def load_context_recs(slug=None):
    """读某站点周边语境 recs（透明语境层，供 canny/depth/massing 的 ControlNet 语境）。
    无 context.parquet 则回 []。frozen=True、in_study=0、sh='context'（不参与算子/形态度量）。"""
    slug = use_site(slug)
    df = C.load_context(slug)
    if df is None or len(df) == 0:
        return []
    recs = []
    for _, r in df.iterrows():
        recs.append({"geom": r["geom"], "h": float(r["height_m"]), "sh": "context",
                     "area": float(r.get("area_m2", r["geom"].area)), "frozen": True, "in_study": 0})
    return recs


def slug_bbox(slug=None):
    """SLUG 街区 bbox(UTM 32651):study 多边形优先,其次现状 footprint。
    稳定参考——不随权力体制的 scale/split 等几何变形漂移,供卫星底锚定中心用。
    返回 (minx, miny, maxx, maxy)。"""
    slug = use_site(slug)
    rings = C.study_poly_rings(slug)
    if rings:
        xs = [x for ring in rings for x, y in ring]
        ys = [y for ring in rings for x, y in ring]
        return min(xs), min(ys), max(xs), max(ys)
    # 回退:现状 footprint(不受体制影响)
    polys = [p for g in list(C.current_buildings(slug)["geom"]) for p in C._polys(g)]
    return (min(p.bounds[0] for p in polys), min(p.bounds[1] for p in polys),
            max(p.bounds[2] for p in polys), max(p.bounds[3] for p in polys))


def regime_label(regs, name):
    return "现状" if name == "current" else regs.get(name, {}).get("label", name)
