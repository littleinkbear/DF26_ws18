"""
step5_export_rhino.py — 真实 footprint 挤成量体 → OBJ + GH 用 CSV
==================================================================
做什么:
  把 OSM 的**真实 footprint**(每栋的实际多边形,UTM 公尺)用 common.extrude_obj()
  挤成 3D 量体:每条边长出两个三角形当「墙」,再把多边形三角化当「顶盖」。
  汇出 current(观测基线)与一个权力情景(预设 developer_led)的 OBJ:
    out/city_current.obj、out/city_<scenario>.obj
  另存 Grasshopper / Rhino 用的逐栋表 out/buildings_export.csv:
    centroid_x, centroid_y, area_m2, height_m(current), height_<scenario>, stakeholder
  (可用 --all-scenarios 一次汇出全部情景的 OBJ。)

为什么:
  这是「forward:改权力 → 看形态」最后一哩——把离散 stakeholder + 只调高度的结果
  变成可在 Rhino/GH 打开、可量、可比的 3D 城市量体。footprint 与标签全程不变,
  变的只有高度,所以两个 OBJ 叠起来能直接看出「谁被准许长高/压低」的形态差。

教什么:
  真实 footprint 挤体 = 墙(侧面)+ 三角顶盖(封顶);量体差异 100% 来自高度政策,
  不是形状魔术。CSV 的 centroid+height 也够在 GH 里用 box/extrude 重建同一座城。

零 AI:只用 common(pandas/numpy/shapely)。python3 跑,于本目录,输出进 out/。
"""
import sys
import csv
# --- 移到 steps/:把父目录加进 import 路径,确保能找到 common / config ---
import pathlib as _pathlib
sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))
__import__('sys').path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[2]))
import common


def export_obj(df, height_col, name):
    """用真实 footprint 挤体,写出一个 OBJ;回传 (path, n_verts, n_faces)。"""
    obj_str, nv, nf = common.extrude_obj(df, height_col=height_col)
    path = common.OUT / name
    path.write_text(obj_str, encoding="utf-8")
    print("  -> wrote %s  | verts %d  faces %d" % (path.relative_to(common.ROOT), nv, nf))
    return path, nv, nf


def export_gh_csv(df, scen_name, scen_heights, name="buildings_export.csv"):
    """逐栋表给 GH/Rhino:centroid + area + current 高 + 情景高 + stakeholder。"""
    path = common.OUT / name
    col_scen = "height_%s" % scen_name
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["centroid_x", "centroid_y", "area_m2", "height_m", col_scen, "stakeholder"])
        for (_, r), h2 in zip(df.iterrows(), scen_heights):
            c = r["geom"].centroid
            w.writerow(["%.3f" % c.x, "%.3f" % c.y, "%.3f" % float(r["area_m2"]),
                        "%.3f" % float(r["height_m"]), "%.3f" % float(h2), r["stakeholder"]])
    print("  -> wrote %s  | %d rows (centroid+area+%s+%s+stakeholder)"
          % (path.relative_to(common.ROOT), len(df), "height_m", col_scen))
    return path


def main():
    all_scen = "--all-scenarios" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    scen_name = args[0] if args else "developer_led"

    df = common.current_buildings()            # 依 config 取那块地
    if "stakeholder" not in df.columns:        # 若还没指派 → 先查表指派(离散、纯 tag)
        df = common.assign_all(df)
    scenarios = common.load_scenarios()
    if scen_name not in scenarios:
        print("unknown scenario %r; available: %s" % (scen_name, list(scenarios.keys())))
        sys.exit(1)

    print("buildings: %d | stakeholder: %s" % (len(df), df.stakeholder.value_counts().to_dict()))

    # current 高度就是 df.height_m;情景高度透过 scenario_heights(只动高度)
    print("\n[OBJ] 真实 footprint 挤成量体(墙 + 三角顶盖):")
    export_obj(df, "height_m", "city_current.obj")

    scen_heights = common.scenario_heights(df, scenarios[scen_name])
    df_scen = df.copy()
    df_scen["height_%s" % scen_name] = scen_heights
    export_obj(df_scen, "height_%s" % scen_name, "city_%s.obj" % scen_name)
    print("  current 平均高 %.1fm  →  %s 平均高 %.1fm（footprint 不变,只动高度）"
          % (df.height_m.mean(), scen_name, scen_heights.mean()))

    if all_scen:
        print("\n[OBJ] --all-scenarios:其余情景:")
        for nm, pol in scenarios.items():
            if nm in ("current", scen_name):
                continue
            h = common.scenario_heights(df, pol)
            d = df.copy(); d["height_%s" % nm] = h
            export_obj(d, "height_%s" % nm, "city_%s.obj" % nm)

    # GH/Rhino 用逐栋表(对应预设/指定的那个情景)
    print("\n[CSV] Grasshopper / Rhino 逐栋表:")
    export_gh_csv(df, scen_name, scen_heights)

    print("\nRhino: File>Import out/city_*.obj;GH: 读 buildings_export.csv")
    print("honest_note:", common.honest_note())


if __name__ == "__main__":
    main()
