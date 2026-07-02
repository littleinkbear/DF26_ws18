"""
engine/pipeline.py — 05 完整流程的「后端引擎」(学生不用进这里)
=================================================================================
顶层入口 run.py 只调 pipeline.run(...);真正把整条流程跑一遍的逻辑全在这里。
读「当下」的 4 份设定(都在顶层、学生自由改),按最新设定把完整流程的图全部重生成:
  config.py             换站点 SLUG / DATASET_ROOT
  shanghai_lookup.yaml  谁算谁的(角色级联查表;新增角色名也可以,会自动配色)
  power_scenarios.yaml  只调高度的情景(新增/删除/改名情景,图会自动跟着变)
  regimes.yaml          权力体制 = 算子配方(新增 op、改 op 顺序、改参数都自动生效)

自定义算子:写在 engine/my_operator.py(顶层函数),会**自动登记**,
regimes.yaml 里就能直接用 { op: 你的函数名, ... }。

产出:
  out/<slug>/<时间戳>/01_data_overview.png ... NN_*.png + city_current.obj
  out/<slug>/<时间戳>/NN_steps_<体制>.png  每个体制的算子序列总览(每步一栏:上 3D 下 2D)
  out/<slug>/<时间戳>/regime_steps/<体制>/<步序>_<算子>_3d.png 与 _2d.png
                                          逐步单图(全部建筑;00_current=基线)
  out/<slug>/<时间戳>/regime_steps/<体制>/anim_3d.gif 与 anim_2d.gif
                                          逐步渐变过程动画(交叉溶解)
  out/<slug>/<时间戳>/run.log             本次全部文字输出
  out/<slug>/<时间戳>/error.log           出错时的完整回溯(没错就不生成)
  out/<slug>/<时间戳>/_config_snapshot/   本次用的 4 份设定快照(以后好回查)

对外只暴露一个函数:run(slugs=None, all_sites=False, bridge06=False) → dict{slug: ok}。
"""
import sys
import shutil
import inspect
import traceback
from datetime import datetime
from pathlib import Path

# --- 让「独立后端」也找得到设定与引擎代码(config/*.yaml 在顶层,引擎代码在 engine/)---
ENGINE = Path(__file__).resolve().parent
PKG_ROOT = ENGINE.parent
for _p in (str(PKG_ROOT), str(ENGINE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:                                         # Windows 终端 cp950 打中文会崩,强制 utf-8
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import matplotlib
matplotlib.use("Agg")                        # 无界面出图(必须在 pyplot 之前)
import matplotlib.pyplot as plt

import config
import common as C
import operators as ops
import measure as M
import plots
import prints
import plots._base as _pb

CONFIG_FILES = ["config.py", "shanghai_lookup.yaml", "power_scenarios.yaml", "regimes.yaml"]
# 新角色自动配色(shanghai_lookup.yaml 里映射到内置 5 类以外的名字时轮流取用)
EXTRA_COLORS = ["#8e6bb5", "#4aa3a3", "#b5527a", "#7a8c3a", "#c98a3d", "#5b7fbf"]

_STATE = {"outdir": None, "seq": 0, "errors": []}


# --------------------------------------------------------------- 存图/日志底座
def _autosave(fig, name):
    """顶掉 plots._base.autosave:图全部存到 out/<slug>/<时间戳>/NN_name.png(不再走 Step_05)。"""
    if fig is None or _STATE["outdir"] is None:
        return None
    d = _STATE["outdir"]
    d.mkdir(parents=True, exist_ok=True)
    _STATE["seq"] += 1
    p = d / ("%02d_%s.png" % (_STATE["seq"], name))
    fig.savefig(p, dpi=120, bbox_inches="tight", pad_inches=0.083)
    print("  -> saved", p.relative_to(C.ROOT))
    return p


_pb.autosave = _autosave                     # 各 step 模块都以 _base.autosave 调用,改这里即全局生效


class _Tee:
    """stdout 同时写终端 + run.log。"""
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            try:
                st.write(s)
            except Exception:
                pass

    def flush(self):
        for st in self.streams:
            try:
                st.flush()
            except Exception:
                pass


def _log_error(stage, tb):
    """完整回溯追加写到 out/<slug>/<时间戳>/error.log,并记入本次失败清单。"""
    p = _STATE["outdir"] / "error.log"
    with p.open("a", encoding="utf-8") as f:
        f.write("\n" + "=" * 78 + "\n")
        f.write("[%s] 阶段失败:%s\n%s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), stage, tb.rstrip()))
    _STATE["errors"].append(stage)
    print("  ❌ %s 失败,完整回溯:\n%s" % (stage, tb))
    print("  📝 已写入", p)


def _guard(stage, fn, *a, **kw):
    """跑一个阶段:失败不中断整站,回溯进 error.log;每阶段后关掉所有 figure 释放内存。"""
    try:
        return fn(*a, **kw)
    except Exception:
        _log_error(stage, traceback.format_exc())
        return None
    finally:
        plt.close("all")


# --------------------------------------------------------------- 设定的三个「自动读取」
def register_custom_ops():
    """engine/my_operator.py 的顶层函数全部自动登记进 ops.OPS(regimes.yaml 可直接引用)。"""
    try:
        import my_operator
    except ImportError:
        return []
    added = []
    for nm, fn in vars(my_operator).items():
        if inspect.isfunction(fn) and fn.__module__ == "my_operator" and not nm.startswith("_"):
            ops.register(nm, fn)
            added.append(nm)
    if added:
        print("已自动登记自定义算子:", ", ".join(added), "(来自 engine/my_operator.py)")
    return added


def extend_palette(df):
    """shanghai_lookup.yaml 映射出内置 5 类以外的新角色时,自动补进调色盘/图例(否则画图 KeyError)。"""
    extra = [sh for sh in df["stakeholder"].unique() if sh not in C.SH_COLOR]
    for i, sh in enumerate(sorted(extra)):
        C.STAKEHOLDERS.append(sh)
        C.SH_COLOR[sh] = EXTRA_COLORS[i % len(EXTRA_COLORS)]
        C.SH_LABEL[sh] = sh
    if extra:
        print("检测到新角色(自动配色):", ", ".join(sorted(extra)))


# --------------------------------------------------------------- 各阶段(对应 notebook A~D)
def stage_data(slug):
    """A 数据→映射:载数据、按最新 lookup 重贴角色、画 data_overview + power_map。回传 df。"""
    df, source = C.build_or_load(slug)
    prints.prepared(df, source)
    prints.coverage(df)
    df = C.assign_all(df)                    # 用**当下的** shanghai_lookup.yaml 重贴(缓存里的旧角色作废)
    extend_palette(df)
    prints.stakeholders(df)
    plots.data_overview(df, show=False)
    plots.power_map(df, show=False)
    return df


def stage_skyline(df):
    """B 只调高度:情景全部从 power_scenarios.yaml 动态读(新增/改名自动跟上)。回传 heights。"""
    try:
        plots.satellite_figureground(df, show=False)      # 需联网,失败自动跳过
    except Exception as e:
        prints.skipped("卫星", e)
    scen = C.load_scenarios()
    prints.scenarios(scen)
    plots.policy_heatmap(scen, show=False)
    names = list(scen.keys())
    if "current" in names:                                # current 固定排第一(metrics 以第一个当基线)
        names.insert(0, names.pop(names.index("current")))
    else:
        names.insert(0, "current")
    heights = {n: (df["height_m"] if n == "current" else C.scenario_heights(df, scen[n]))
               for n in names}
    plots.skyline_panels(df, heights, names=names, show=False)
    plots.metrics(df, heights, names=names, show=False)
    return heights


def stage_operators(df, slug):
    """C 权力算子:各体制横比 + 形态特征量化(单算子 demo 已并入阶段 E 的逐步序列)。"""
    recs = C.to_recs(df)
    prints.op_list(recs)
    regs = ops.load_regimes()
    prints.regimes(regs)

    after, labels = {}, {}
    for n, recipe in regs.items():                        # 每个体制单独套配方,坏一个不拖全部
        res = _guard("体制:%s" % n, ops.apply_regime, recs, recipe)
        if res is not None:
            after[n] = res
            labels[n] = recipe.get("label", n)
    if after:
        plots.regime_compare(recs, after, labels=labels, show=False)
        rows, _ = M.compare(recs, after, slug)
        lab_all = {"current": "现状", **labels}
        plots.feature_bars(rows, labels=lab_all, show=False)
        prints.features(rows, lab_all)
    return after


def stage_regime_steps(df, slug):
    """E 体制算子序列:每个体制按 steps 顺序**逐步**套算子。
    每体制一张总览(每步一栏:上排 3D、下排 2D footprint,同尺度可横比),
    并逐步各出 3D / 2D 两张单图(全部建筑、不抽样)
    → regime_steps/<体制>/{步序}_{算子}_3d.png 与 _2d.png(00_current=基线)。"""
    recs = C.to_recs(df)
    regs = ops.load_regimes()

    for name, recipe in regs.items():                     # 每个体制独立 guard,坏一个不拖全部
        def _one(name=name, recipe=recipe):
            states = [("current", recs)]
            cur = recs
            for step in recipe.get("steps", []):
                op = step["op"]
                if op not in ops.OPS:
                    raise KeyError("算子「%s」未登记(regimes.yaml 的 %s):请写进 engine/my_operator.py"
                                   "(会自动登记)或 engine/operators.py 的 OPS。" % (op, name))
                kw = {k: v for k, v in step.items() if k != "op"}
                cur = ops.OPS[op](cur, **kw)              # 累积套用:state_i = op_i(state_{i-1})
                states.append((op, cur))
            label = recipe.get("label", name)
            plots.regime_steps_strip(states, title="%s(%s)· 算子序列" % (label, name),
                                     save_name="steps_%s" % name, show=False)
            plt.close("all")
            scene = plots.regime_steps._scene_of(states)  # 全序列共同 bounds/z,逐帧同尺度
            d = _STATE["outdir"] / "regime_steps" / name
            frames = {"3d": [], "2d": []}
            for i, (op, st) in enumerate(states):
                t = "%s · step %d · %s" % (label, i, op)
                for kind, fn in (("3d", plots.regime_step_3d), ("2d", plots.regime_step_2d)):
                    p = d / ("%02d_%s_%s.png" % (i, op, kind))
                    fn(st, title=t, scene=scene, path=p, show=False)
                    plt.close("all")
                    frames[kind].append(p)
                    print("  -> saved", p.relative_to(C.ROOT))
            for kind, ps in frames.items():               # 逐帧串成渐变过程 gif(几何 morph)
                g = plots.steps_gif_morph(states, kind, d / ("anim_%s.gif" % kind),
                                          scene=scene, label=label, frame_paths=ps)
                if g is not None:
                    print("  -> saved", g.relative_to(C.ROOT))
        _guard("体制序列:%s" % name, _one)


def stage_obj(df, slug):
    """D OBJ:现状挤成 OBJ 落到本次时间戳夹(3D png 已并入阶段 E 的逐步序列)。"""
    objp, nv, nf = C.export_obj(df, slug)
    prints.obj_written(objp, nv, nf)
    dst = _STATE["outdir"] / objp.name
    shutil.copyfile(objp, dst)
    print("OBJ 也复制到:", dst.relative_to(C.ROOT))


# --------------------------------------------------------------- 单站主流程
def run_site(slug):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = C.OUT / slug / stamp
    outdir.mkdir(parents=True, exist_ok=True)
    _STATE.update(outdir=outdir, seq=0, errors=[])
    config.SLUG = slug                                    # 引擎各处默认参数跟着走(同 notebook 阶段E做法)

    old_stdout = sys.stdout
    logf = (outdir / "run.log").open("w", encoding="utf-8")
    sys.stdout = _Tee(old_stdout, logf)
    try:
        print("=" * 78)
        print("站点 %s(%s) · 时间戳 %s" % (slug, config.site_name(slug), stamp))
        print("输出:", outdir.relative_to(C.ROOT))
        snap = outdir / "_config_snapshot"                # 本次设定快照:以后回查这批图是哪套设定出的
        snap.mkdir(exist_ok=True)
        for f in CONFIG_FILES:
            if (C.ROOT / f).exists():
                shutil.copyfile(C.ROOT / f, snap / f)
        print("设定快照:", ", ".join(CONFIG_FILES), "→", snap.relative_to(C.ROOT))
        print("-" * 78)

        df = _guard("A 数据→映射", stage_data, slug)
        if df is None:
            print("⚠ 数据阶段失败,本站中止(回溯见 error.log)。")
            return False
        _guard("B 天际线", stage_skyline, df)
        _guard("C 权力算子", stage_operators, df, slug)
        _guard("D OBJ", stage_obj, df, slug)
        _guard("E 体制算子序列", stage_regime_steps, df, slug)

        print("-" * 78)
        if _STATE["errors"]:
            print("⚠ 完成(有 %d 个阶段失败):%s" % (len(_STATE["errors"]), ", ".join(_STATE["errors"])))
            print("  完整回溯 →", (outdir / "error.log").relative_to(C.ROOT))
        else:
            print("✅ 全部完成:", outdir.relative_to(C.ROOT))
        return not _STATE["errors"]
    finally:
        sys.stdout = old_stdout
        logf.close()


# --------------------------------------------------------------- 对外唯一入口
def run(slugs=None, all_sites=False, bridge06=False):
    """跑完整流程 A~D。
      slugs      站点 slug 列表;留空 = config.SLUG。
      all_sites  True = 跑所有已缓存街道(data/<slug>/buildings.parquet)。
      bridge06   True = 跑完再接 06_AI Render 出 canvas.html / report.html(见 engine/bridge06.py)。
    回传 {slug: ok}。"""
    if all_sites:
        slugs = sorted(p.name for p in C.DATA.iterdir() if (p / "buildings.parquet").exists())
    else:
        slugs = slugs or [config.SLUG]

    prints.ready()
    register_custom_ops()
    results = {}
    for s in slugs:
        results[s] = run_site(s)

    print("\n" + "=" * 78)
    for s, ok in results.items():
        print(("✅" if ok else "⚠ ") + " " + s)

    if bridge06:
        import bridge06 as B06
        B06.bridge(list(results.keys()))

    return results
