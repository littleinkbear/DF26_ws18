"""
step3_scenarios.py — 把「权力情景」摊开成一张可读的政策表/热图
=================================================================
做什么:
  读 power_scenarios.yaml(common.load_scenarios()),把每个情景的
  「各 stakeholder 高度政策(mult 乘数 / cap_m 上限 / floor_m 下限)」
  画成一张一眼可读的表 + 乘数热图 → out/step3_policies.png;
  并在 stdout 逐情景、逐 stakeholder 印「对你做什么」的白话。

为什么:
  这是整条 pipeline 的「政策旋钮面板」。step1 把楼对应到离散 stakeholder、
  step2 套政策算新高度看形态——而所有反事实都浓缩在这份 YAML 的数字里。
  先把旋钮本身画清楚,读者才知道后面形态的差别「是谁、被调了多少」。

教什么:
  权力变化 = **只调高度**:h' = clip(h × mult, floor_m, cap_m)。
  footprint(真实 OSM 形状)与 stakeholder 标签(谁的权利)都**不变**。
  想做别的反事实?**改 power_scenarios.yaml 就是反事实的另一半**——
  不必碰任何程式:多一个情景、把某 stakeholder 的 mult 调大/加个 cap,
  就是在问「若某方更有权、且只准动高度,城市会长成什么样」。

跑:在本资料夹下 `python3 step3_scenarios.py`(读 bundled YAML,离线)。
"""
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
# --- 移到 steps/:把父目录加进 import 路径,确保能找到 common / config / plots ---
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))
__import__('sys').path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[2]))
import common
import plots   # view 层:SH_LABEL / SH_COLOR / save_fig


# 一个 stakeholder 在某情景没列政策 = 高度照旧(等同 mult=1.0、无 cap/floor)。
def policy_of(scenario, sh):
    """回传该情景对该 stakeholder 的政策 dict(缺项补预设)。"""
    pol = (scenario or {}).get(sh, {})
    return {
        "mult": float(pol.get("mult", 1.0)),
        "cap_m": pol.get("cap_m", None),     # None = 无上限
        "floor_m": pol.get("floor_m", None), # None = 无下限
    }


def policy_text(p):
    """把一个政策 dict 变成白话:对「高度」做了什么。"""
    parts = []
    m = p["mult"]
    if abs(m - 1.0) < 1e-9:
        parts.append("高度照旧(×1.0)")
    elif m > 1.0:
        parts.append("拔高 ×%.2g(+%.0f%%)" % (m, (m - 1) * 100))
    else:
        parts.append("压低 ×%.2g(−%.0f%%)" % (m, (1 - m) * 100))
    if p["floor_m"] is not None:
        parts.append("下限 ≥%gm" % p["floor_m"])
    if p["cap_m"] is not None:
        parts.append("上限 ≤%gm" % p["cap_m"])
    return "、".join(parts)


def cell_text(p):
    """表格储存格:紧凑呈现 mult(/floor/cap)。"""
    s = "×%.2g" % p["mult"]
    if p["floor_m"] is not None:
        s += "\n≥%gm" % p["floor_m"]
    if p["cap_m"] is not None:
        s += "\n≤%gm" % p["cap_m"]
    return s


def main():
    matplotlib.use("Agg")   # headless 存 PNG 不需显示器
    scenarios = common.load_scenarios()
    scen_names = list(scenarios.keys())
    shs = common.STAKEHOLDERS  # 固定顺序:state, developer, resident, informal, unknown

    # ---- 预先算出 政策矩阵(供热图)与 文字矩阵(供表格)----
    mult_mat = np.ones((len(scen_names), len(shs)))
    cell_mat = [["" for _ in shs] for _ in scen_names]
    pols = {}  # (scen, sh) -> policy dict
    for i, sn in enumerate(scen_names):
        for j, sh in enumerate(shs):
            p = policy_of(scenarios[sn], sh)
            pols[(sn, sh)] = p
            mult_mat[i, j] = p["mult"]
            cell_mat[i][j] = cell_text(p)

    # ---- stdout:逐情景逐 stakeholder 白话 ----
    print("=" * 72)
    print("step3 — 权力情景 = 各 stakeholder 的「只调高度」政策")
    print("  公式:h' = clip(h × mult, floor_m, cap_m);footprint 与标签都不变")
    print("=" * 72)
    for sn in scen_names:
        print("\n[情景] %s" % sn)
        if not scenarios[sn]:
            print("  (空政策 = 基线:用 OSM 观测高度,什么都不调)")
        for sh in shs:
            p = pols[(sn, sh)]
            listed = sh in (scenarios[sn] or {})
            tag = "" if listed else "  (未列→预设)"
            print("  - %-9s %-22s : %s%s" % (sh, plots.SH_LABEL[sh], policy_text(p), tag))

    # ---- 图:上=乘数热图(色=拔高/压低),下=完整政策表 ----
    fig = plt.figure(figsize=(11, 7.2))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.15], hspace=0.32)

    col_labels = ["%s\n%s" % (sh, plots.SH_LABEL[sh]) for sh in shs]

    # 上:乘数热图(以 1.0 为中点的发散色;标出 cap/floor 为注记)
    ax0 = fig.add_subplot(gs[0])
    vmax = float(np.nanmax(np.abs(mult_mat - 1.0)))
    vmax = max(vmax, 0.1)
    im = ax0.imshow(mult_mat, cmap="RdBu_r", vmin=1 - vmax, vmax=1 + vmax, aspect="auto")
    ax0.set_xticks(range(len(shs))); ax0.set_xticklabels(col_labels, fontsize=8)
    ax0.set_yticks(range(len(scen_names))); ax0.set_yticklabels(scen_names, fontsize=9)
    ax0.set_title("高度乘数 mult(红=拔高 / 蓝=压低 / 白=照旧;cap=上限, fl=下限)", fontsize=10)
    for i in range(len(scen_names)):
        for j in range(len(shs)):
            p = pols[(scen_names[i], shs[j])]
            txt = "×%.2g" % p["mult"]
            extra = []
            if p["floor_m"] is not None:
                extra.append("fl%g" % p["floor_m"])
            if p["cap_m"] is not None:
                extra.append("cap%g" % p["cap_m"])
            if extra:
                txt += "\n" + " ".join(extra)
            # 颜色越深字用白,反之用黑
            shade = abs(p["mult"] - 1.0) / vmax
            color = "white" if shade > 0.55 else "black"
            ax0.text(j, i, txt, ha="center", va="center", fontsize=7.5, color=color)
    cb = fig.colorbar(im, ax=ax0, fraction=0.025, pad=0.02)
    cb.set_label("mult", fontsize=8)

    # 下:完整政策表(mult + floor + cap),空政景以「照旧」呈现
    ax1 = fig.add_subplot(gs[1]); ax1.axis("off")
    table = ax1.table(
        cellText=cell_mat,
        rowLabels=scen_names,
        colLabels=col_labels,
        cellLoc="center", rowLoc="center", loc="center",
    )
    table.auto_set_font_size(False); table.set_fontsize(8)
    table.scale(1, 2.2)
    # 表头用各 stakeholder 的代表色,储存格依拔高/压低淡染
    for (r, c), cell in table.get_celld().items():
        if r == 0 and c >= 0:               # 栏标题列
            cell.set_facecolor(plots.SH_COLOR[shs[c]]); cell.set_text_props(color="white", fontsize=8)
        elif c == -1:                        # 列标题(情景名)
            cell.set_text_props(fontweight="bold", fontsize=9)
        elif r >= 1 and c >= 0:
            m = pols[(scen_names[r - 1], shs[c])]["mult"]
            if m > 1.0:
                cell.set_facecolor((0.97, 0.90, 0.88))
            elif m < 1.0:
                cell.set_facecolor((0.88, 0.92, 0.96))
            else:
                cell.set_facecolor((0.96, 0.96, 0.96))
    ax1.set_title("政策表:格内 = mult(/下限≥/上限≤);未列的 stakeholder = ×1.0 照旧",
                  fontsize=10, pad=12)

    fig.suptitle("step3 权力情景的「只调高度」政策面板 — 改 power_scenarios.yaml = 反事实的另一半",
                 fontsize=12)
    plots.save_fig(fig, "step3_policies.png")

    print("\n" + common.honest_note())
    print("\n[写了哪些档]")
    print("  out/step3_policies.png  (乘数热图 + 完整政策表)")


if __name__ == "__main__":
    main()
