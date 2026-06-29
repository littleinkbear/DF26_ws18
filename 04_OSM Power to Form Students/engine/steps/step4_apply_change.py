"""
step4_apply_change.py — 套用权力情景:只调高度 → 看新形态(PAYOFF)
=====================================================================
做什么:
  同一批 1163 栋新加坡 大巴窑(Toa Payoh) 楼、同一批 footprint、同一批离散 stakeholder 标签,
  分别套 current / developer_led / community_led / state_eco 四个权力情景。
  每个情景**只改高度**(footprint 不动、stakeholder 标签不动),产出:
    1) out/step4_change.png   — 4 连幅 footprints,按「新高度」用同一色阶著色
                                 (一眼看出哪一方更有权 → 量体/天际线怎么长)
    2) out/step4_metrics.png  — 各情景的对照长条:总 GFA(×baseline)、平均高、
                                 最高、各 stakeholder 平均高
    3) out/buildings_<scenario>.csv — 每情景逐栋新高度(只高度栏变)
  stdout 印情景对照表。

为什么:
  这是回应论文方法的最简单 forward 版本——「改谁更有权 → 看城市形态」。
  前三步把 OSM 楼离散对应到一个 stakeholder;这步把「权力」具体化成
  「各方各自一套只动高度的政策」,于是同一座城市因权力配置不同而长出不同量体。
  payoff:形态差异不是换了资料、换了 footprint,而**纯粹来自「谁更有权」**。

教什么:
  形态 = footprint × 高度。锁死 footprint、只放开高度这一个自由度,
  就能把「权力 → 形态」这条因果讲得干净可教:看得到的天际线变化
  完全归因于 power_scenarios.yaml 里那几个 mult / cap / floor 数字。
  学生改 YAML = 亲手做反事实。

诚实:tag 稀疏(unknown=106)、高度多为 levels×3.5 估计、「谁的权利」是离散可编辑
      对应而非产权考证——这是教学练习,非真实规划预测。

零 AI:只用 pandas / numpy / matplotlib / shapely / pyyaml(经 common 契约)。
跑法:cd 到本目录,python3 step4_apply_change.py(预设离线读 bundled data)。
"""
import numpy as np
import pandas as pd
import matplotlib

# --- 移到 steps/:把父目录加进 import 路径,确保能找到 common / config / plots ---
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))
__import__('sys').path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[2]))
import common
import plots   # view 层:绘图单一真相源(skyline_panels / metrics / SH_LABEL / save_fig)
from common import (
    FLOOR_H, STAKEHOLDERS, OUT, ROOT,
    current_buildings, load_lookup, assign_all, load_scenarios,
    scenario_heights, honest_note,
)


def get_assigned(verbose=True):
    """载入楼并指派 stakeholder;若无 buildings_assigned.csv 则 assign_all 并存档。"""
    cache = OUT / "buildings_assigned.csv"
    df = current_buildings()                  # 依 config 取那块地;重读拿到 shapely geom 栏
    df = assign_all(df, load_lookup())        # 每栋 → 一个离散 stakeholder(纯查表)
    if not cache.exists():
        # 存可读的对应表(不含 geom 物件,留 wkt 字串即可重建)
        cols = [c for c in df.columns if c != "geom"]
        df[cols].to_csv(cache, index=False)
        if verbose:
            print("  -> wrote", cache.relative_to(ROOT), "(assign_all 结果)")
    elif verbose:
        print("  -> reuse", cache.relative_to(ROOT))
    return df


def main():
    matplotlib.use("Agg")   # headless 存 PNG 不需显示器
    print("=" * 74)
    print("step4 — 同一批楼、同一批 footprint,只因「谁更有权」而高度不同 → 新形态")
    print("=" * 74)

    df = get_assigned()
    scen_all = load_scenarios()
    scen_names = ["current", "developer_led", "community_led", "state_eco"]

    # ---- 1) 对每个情景算逐栋新高度(只高度变),存 CSV ----------------------
    heights = {}                              # name -> Series(逐栋新高度 m)
    for name in scen_names:
        h = scenario_heights(df, scen_all[name])
        heights[name] = h
        out = df.copy()
        out["height_m"] = h.values            # 只改高度栏
        out["scenario"] = name
        cols = [c for c in out.columns if c != "geom"]   # geom 不入 CSV,留 wkt
        path = OUT / f"buildings_{name}.csv"
        out[cols].to_csv(path, index=False)
        print("  -> wrote", path.relative_to(ROOT))

    # baseline GFA 供 ×倍数比对(GFA = 面积 × 楼层数 = area × h / FLOOR_H)
    base_gfa = float((df.area_m2 * heights["current"] / FLOOR_H).sum())

    # ---- 2) 两张图:4 连幅(新高度著色)+ metrics 2×2;与 notebook 同一套 plots ----
    plots.save_fig(plots.skyline_panels(df, heights, names=scen_names, show=False),
                   "step4_change.png")
    plots.save_fig(plots.metrics(df, heights, names=scen_names, show=False),
                   "step4_metrics.png")

    # ---- 3) 供 stdout 的指标(图已由 plots 画好,这里只算数字)----------------
    rows = []
    for name in scen_names:
        h = heights[name]
        gfa = float((df.area_m2 * h / FLOOR_H).sum())
        rows.append({"scenario": name, "gfa_x_base": gfa / base_gfa,
                     "mean_h": float(h.mean()), "max_h": float(h.max())})
    metrics = pd.DataFrame(rows).set_index("scenario")
    by_sh = {}                                # sh -> {scenario: mean_h}
    for sh in STAKEHOLDERS:
        mask = (df["stakeholder"] == sh).values
        if not mask.any():
            continue
        by_sh[sh] = {name: float(heights[name].values[mask].mean()) for name in scen_names}

    # ---- 4) stdout 对照表 --------------------------------------------------
    print("\n情景对照(只高度变;footprint 与 stakeholder 标签不变):")
    print("  %-14s %10s %9s %8s" % ("scenario", "GFA×base", "mean_h", "max_h"))
    for name in scen_names:
        m = metrics.loc[name]
        print("  %-14s %9.2f× %8.1fm %7.0fm"
              % (name, m["gfa_x_base"], m["mean_h"], m["max_h"]))

    print("\n各 stakeholder 平均高 (m) × 情景:")
    head = "  %-26s" % "stakeholder (n)" + "".join("%14s" % n for n in scen_names)
    print(head)
    for sh, d in by_sh.items():
        n = int((df["stakeholder"] == sh).sum())
        label = "%s (%d)" % (plots.SH_LABEL[sh], n)
        print("  %-26s" % label + "".join("%13.1fm" % d[name] for name in scen_names))

    print("\n读法:同一批楼、同一批 footprint、同一批标签——四幅的差异**只**来自")
    print("      power_scenarios.yaml 里各 stakeholder 的 mult/cap/floor。改 YAML = 做反事实。")
    print("\n" + honest_note())

    print("\n写出的档:")
    for f in ["step4_change.png", "step4_metrics.png"] + \
             [f"buildings_{n}.csv" for n in scen_names]:
        print("  out/" + f)


if __name__ == "__main__":
    main()
