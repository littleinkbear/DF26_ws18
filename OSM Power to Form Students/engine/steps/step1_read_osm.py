"""
step1_read_osm.py — 先看 OSM 楼本身,还没贴权力
=================================================================
做什么:
  依 config 载入 OSM 楼(common.current_buildings;预设 bundled 的 1163 栋新加坡 大巴窑(Toa Payoh)),
  画出**真实 footprints**(全灰、不分类),再画高度直方图,
  并报告 tag 覆盖、height 来源占比、总栋数/总面积。

为什么:
  这是 forward pipeline(改权力→看形态)的第 0 步——**先诚实看清原料**。
  在贴任何「谁的权利」之前,要先知道:这批楼长什么形状、有多高、
  资料有多稀疏。权力对应(step2)与情景(step3)都建立在这层原料上,
  所以本步刻意**全灰著色**:还没有 stakeholder,只有 OSM 几何与 tag。

教什么:
  1. OSM 的 tag 很稀疏:1163 栋几乎都只有 building=*,amenity/office/shop
     非空的寥寥可数——这正是后面要「离散查表」而非「语意推断」的原因。
  2. 高度大多是估计值(building:levels×3.5),只有少数是实测 height tag;
     形态研究要对「资料来源」诚实,不要把估计当测量。
  3. footprint 是真实的(UTM 公尺座标、含内环/天井),整条 pipeline
     都保留它不变——权力只调高度。

零 AI:只用 pandas/numpy/matplotlib(经 common)。无语意转换、无神经网。

osmnx live 抓法(可选,本步预设读 bundled,离线可跑;见 README):
    import osmnx as ox
    gdf = ox.features_from_place("Toa Payoh, Singapore", {"building": True})
    gdf = gdf[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])].to_crs(config.UTM)  # ← UTM 由 config 中心点经度自动推导 / auto-derived from config
    # 再抽 building/amenity/office/shop/tourism/name + height/levels → 存 data/buildings.csv

跑:cd .../osm_power_to_form && python3 step1_read_osm.py
"""
import matplotlib
# --- 移到 steps/:把父目录加进 import 路径,确保能找到 common / config / plots ---
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))
__import__('sys').path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[2]))
import config
import common
import plots   # view 层:绘图单一真相源(notebook 与本 step 共用同一张图)


def main():
    matplotlib.use("Agg")   # 当 script headless 跑时:存 PNG 不需要显示器
    # --- 载原料(只 OSM 楼本身;尚未 assign_all,还没贴权力)。依 config 取那块地 ---
    df = common.current_buildings()
    n = len(df)
    total_area = df["area_m2"].sum()

    # --- (1) 灰 footprints + 高度直方图:与 notebook 同一张图(plots.data_overview)---
    fig = plots.data_overview(df, show=False)
    plots.save_fig(fig, "step1_overview.png")

    # --- (2) 文字报告:tag 覆盖 / height 来源 / 规模 ---
    print("\n=== Step 1 报告:OSM 楼本身(还没贴权力)===")
    print("总栋数          : %d" % n)
    print(f"总 footprint 面积: {total_area:,.0f} m²  (平均 {total_area / n:.0f} m²/栋)")
    print("高度            : 平均 %.1f m / 最矮 %.1f m / 最高 %.1f m"
          % (df["height_m"].mean(), df["height_m"].min(), df["height_m"].max()))

    print("\n-- tag 覆盖(非空栋数,看出有多稀疏)--")
    for key in ("building", "amenity", "office", "shop"):
        nonempty = (df[key].map(common._t) != "").sum()
        print("  %-9s 非空 %5d / %d  (%.1f%%)" % (key, nonempty, n, 100 * nonempty / n))
    # building=yes 是「有 building tag 但无细分类」的代表,后面多落 unknown/resident
    n_yes = (df["building"].map(common._t) == "yes").sum()
    print("  其中 building=yes(无细分类): %d (%.1f%%)" % (n_yes, 100 * n_yes / n))

    print("\n-- height_source 占比(测量 vs 估计)--")
    vc = df["height_source"].value_counts()
    for s in ("measured", "levels_x3.5", "default"):
        c = int(vc.get(s, 0))
        print("  %-12s %5d / %d  (%.1f%%)" % (s, c, n, 100 * c / n))

    print("\n写了哪些档:")
    print("  out/step1_overview.png   (左:真实 footprints 全灰;右:高度分布依来源著色)")
    print("\nhonest_note:", common.honest_note())


if __name__ == "__main__":
    main()
