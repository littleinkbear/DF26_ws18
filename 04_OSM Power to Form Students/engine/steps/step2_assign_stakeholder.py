"""
step2_assign_stakeholder.py — 把每栋 OSM 楼离散地对应「这是谁的权利」
==================================================================
做什么:
  读 data/buildings.csv(step1 抓好的 1163 栋 Toa Payoh)→ common.assign_all(df)
  纯 tag 查表得到每栋一个离散 stakeholder ∈ {state, developer, resident,
  informal, unknown} → 用 SH_COLOR 把真实 footprint 著色画出来,并附一条
  「各 stakeholder 栋数 / 面积占比」的小长条 → 存 out/step2_stakeholders.png
  与 out/buildings_assigned.csv(多一栏 stakeholder)。

为什么:
  这是 pipeline 的「权力地图」那一步——forward 练习(改权力→看形态)里,
  必须先有一张「谁算谁的」的离散底图,后面 step3 才能对某个 stakeholder
  「只调高度」做反事实。这一步只负责「贴标签 + 画出来」,不动几何、不改高度。

教什么:
  1. 纯 tag 查表、离散:一栋 = 一个 stakeholder,第一个命中即定(order 优先序)。
     不做语意转换(没有共现/熵/分布/manifold 那套),就是一张可读的对应表。
  2. stakeholder_lookup.yaml 是「反事实的一半」:学生改那张表 = 改「谁算谁的」,
     重跑这一步就得到不同的权力地图(另一半是 step3 改 power_scenarios.yaml 的高度政策)。
  3. 诚实:unknown=106 是 building=yes 或无可辨 tag 的楼,我们不硬猜产权;
     tag 本就稀疏、高度多为 levels×3.5 估计——标签是「离散可编辑对应」非产权考证。

零 AI:只用 pandas / numpy / matplotlib / shapely / pyyaml(透过 common)。
跑法:在 osm_power_to_form/ 目录下 `python3 step2_assign_stakeholder.py`(预设离线读 bundled CSV)。
"""
import numpy as np
import matplotlib

# --- 移到 steps/:把父目录加进 import 路径,确保能找到 common / config / plots ---
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))
__import__('sys').path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[2]))
import common
import plots   # view 层:绘图单一真相源


def main():
    matplotlib.use("Agg")   # headless 存 PNG 不需显示器
    # --- 1) 载入 + 离散贴标(纯 tag 查表,不动几何/高度)。依 config 取那块地 -------
    df = common.current_buildings()
    df = common.assign_all(df)          # 加 'stakeholder' 栏;footprint 与 tag 都不变

    counts = df["stakeholder"].value_counts()
    areas = df.groupby("stakeholder")["area_m2"].sum()
    # 照 common.STAKEHOLDERS 的固定顺序排(缺的补 0),画图与表格才稳定
    order = common.STAKEHOLDERS
    n_by = np.array([int(counts.get(sh, 0)) for sh in order], dtype=float)
    a_by = np.array([float(areas.get(sh, 0.0)) for sh in order], dtype=float)
    n_share = n_by / n_by.sum() if n_by.sum() else n_by
    a_share = a_by / a_by.sum() if a_by.sum() else a_by

    print("step2 — 离散 stakeholder(纯 tag 查表)")
    print("  栋数分布 :", {sh: int(n_by[i]) for i, sh in enumerate(order)})
    print("  面积占比 :",
          {sh: round(float(a_share[i]), 3) for i, sh in enumerate(order)})
    print("  (unknown=%d 为 building=yes/无可辨 tag,不硬猜)" % int(counts.get("unknown", 0)))

    # --- 2) 画图:与 notebook 同一张图(plots.power_map)----------------------------
    fig = plots.power_map(df, show=False)
    plots.save_fig(fig, "step2_stakeholders.png")

    # --- 3) 存带 stakeholder 栏的 CSV(丢掉 shapely geom 物件,留 wkt 字串) ------
    out_csv = common.OUT / "buildings_assigned.csv"
    df.drop(columns=["geom"]).to_csv(out_csv, index=False, encoding="utf-8")
    print("  -> wrote", out_csv.relative_to(common.ROOT))

    print(common.honest_note())


if __name__ == "__main__":
    main()
