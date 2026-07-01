"""
report.py — backend core logic moved out of build_report.py (pure relocation).
Holds: constants + opencc traditionalization + data/stats + figures + geometry/export.
build_report.py keeps HTML templates (CSS/VIEWER/HTML), fig_block, operator_section,
build_report, build_index and the __main__ entrypoint, importing the names below.
"""
import base64, json, warnings; warnings.filterwarnings("ignore")
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import config
import common as C
import operators as ops
import measure as M
import plots

ROOT = C.ROOT ; OUT = C.OUT


ACCENT = "#0f5e63"
SH_ORDER = ["state", "developer", "resident", "informal", "unknown"]
SHOW = ["current", "developer_led", "community_led", "state_eco"]


try:
    from opencc import OpenCC
    _CC = OpenCC("s2t")
    _t = _CC.convert
except Exception:
    _CC = None
    def _t(s):
        return s


def _zh_hant(html):
    """把报告 HTML 的中文转繁体(opencc s2t,保留领域术语 算子);嵌入的 three/orbit 已是 ASCII,不受影响。"""
    return _t(html) if _CC else html


_LABELS_DONE = [False]


def traditionalize_engine_labels():
    """报告交付物为繁体:把 engine 标签 + matplotlib 图内文字(标题/轴名)转繁,使图也是繁体。
    只在本报告进程生效;notebook 不 import 本文件,仍维持简体,不受影响。"""
    if _LABELS_DONE[0] or not _CC:
        return
    for k, v in list(C.SH_LABEL.items()):
        C.SH_LABEL[k] = _t(v)
    _orig = C.honest_note
    C.honest_note = lambda place="上海": _t(_orig(place))
    # 全局 monkeypatch:图内所有 set_title / suptitle / 轴名 自动转繁(零逐处改动)
    import matplotlib.axes as _ax, matplotlib.figure as _fg

    def _wrap(orig):
        def f(self, text, *a, **k):
            return orig(self, _t(text) if isinstance(text, str) else text, *a, **k)
        return f
    _ax.Axes.set_title = _wrap(_ax.Axes.set_title)
    _ax.Axes.set_xlabel = _wrap(_ax.Axes.set_xlabel)
    _ax.Axes.set_ylabel = _wrap(_ax.Axes.set_ylabel)
    _fg.Figure.suptitle = _wrap(_fg.Figure.suptitle)
    _LABELS_DONE[0] = True


# ----------------------------------------------------------------- 数据 + 指标
def load(slug):
    df = C.load_buildings(slug)
    scen = C.load_scenarios()
    H = {k: (C.scenario_heights(df, scen[k]) if k != "current" else df["height_m"]) for k in scen}
    return df, scen, H


def compute_stats(slug, df, scen, H):
    n = len(df)
    dist = df["stakeholder"].value_counts().to_dict()
    gfa0 = float((df["area_m2"] * df["height_m"]).sum())
    rows = {}
    for k in scen:
        g = float((df["area_m2"] * H[k]).sum())
        rows[k] = {"ratio": g / gfa0, "mean": float(H[k].mean()), "max": float(H[k].max())}
    sh_h = {k: {sh: (float(H[k][df["stakeholder"] == sh].mean()) if (df["stakeholder"] == sh).any() else 0.0)
                for sh in SH_ORDER} for k in scen}
    eu = float(df["euluc"].apply(C._t).ne("").mean()) if "euluc" in df else 0.0
    fn = float(df["function"].apply(C._t).ne("").mean()) if "function" in df else 0.0
    aoi_cols = [c for c in ("aoi_type1", "aoi_type2", "aoi_type") if c in df]
    ao = float(df[aoi_cols].apply(lambda col: col.apply(C._t).ne("")).any(axis=1).mean()) if aoi_cols else 0.0
    h = df["height_m"].astype(float)
    meta = C.site_meta(slug)
    obj = C.extrude_obj(df)
    return {"n": n, "dist": dist, "rows": rows, "sh_h": sh_h, "scen": list(scen.keys()),
            "cov": {"euluc": eu, "function": fn, "aoi": ao},
            "h_med": float(h.median()), "h_p90": float(h.quantile(.9)), "h_max": float(h.max()),
            "n_gt100": int((h > 100).sum()), "area_km2": meta["area_km2"],
            "name": meta["name"], "bounds": meta["bounds_lonlat"], "obj": obj}


# ----------------------------------------------------------------- 图
def color_of(r):
    return C.SH_COLOR[r["stakeholder"]]


def fig_step1(slug, df, s):
    fig, ax = plt.subplots(figsize=(9, 8))
    C.plot_footprints(ax, df, lambda r: "#9aa3a6", lw=0.12)
    ax.set_title("%s — %d 栋真实 footprint(AI解析-带高度,尚未贴权力)\n实测高度 中位 %.0f / p90 %.0f / 最高 %.0f m,%d 栋 >100m" % (
        s["name"], s["n"], s["h_med"], s["h_p90"], s["h_max"], s["n_gt100"]), fontsize=11)
    C.save_fig(fig, "step1_buildings.png", OUT / slug)


def fig_step2(slug, df, s):
    fig, axs = plt.subplots(1, 2, figsize=(15, 7), gridspec_kw={"width_ratios": [1.55, 1]})
    C.plot_footprints(axs[0], df, color_of, lw=0.12)
    axs[0].set_title("离散级联查表(EULUC→Function→AOI):一栋 = 一个 stakeholder", fontsize=11)
    present = [sh for sh in SH_ORDER if s["dist"].get(sh, 0)]
    cnt = [s["dist"].get(sh, 0) for sh in present]
    gfa = [float((df.loc[df.stakeholder == sh, "area_m2"] * df.loc[df.stakeholder == sh, "height_m"]).sum()) for sh in present]
    y = np.arange(len(present)); bw = 0.38
    axs[1].barh(y + bw / 2, cnt, bw, color=[C.SH_COLOR[sh] for sh in present], label="栋数")
    g2 = [g / max(gfa) * max(cnt) for g in gfa]
    axs[1].barh(y - bw / 2, g2, bw, color=[C.SH_COLOR[sh] for sh in present], alpha=.45, label="GFA(缩放)")
    axs[1].set_yticks(y); axs[1].set_yticklabels([C.SH_LABEL[sh].split("(")[0] for sh in present])
    for i, c in enumerate(cnt):
        axs[1].text(c, y[i] + bw / 2, " %d" % c, va="center", fontsize=9)
    axs[1].set_title("栋数 / GFA 占比", fontsize=11); axs[1].legend(fontsize=8, loc="lower right")
    axs[1].spines[["top", "right"]].set_visible(False)
    C.save_fig(fig, "step2_stakeholders.png", OUT / slug)


def fig_step3(slug, df, scen, H, s):
    present = [sh for sh in SH_ORDER if s["dist"].get(sh, 0)]
    M = np.ones((len(scen), len(present)))
    for i, k in enumerate(scen):
        for j, sh in enumerate(present):
            m = df["stakeholder"] == sh
            if m.any():
                M[i, j] = float((H[k][m]).mean() / (df.loc[m, "height_m"]).mean())
    fig, ax = plt.subplots(figsize=(1.4 * len(present) + 3, 0.7 * len(scen) + 2.2))
    vmax = max(1.6, np.nanmax(M)); import matplotlib.colors as mc
    norm = mc.TwoSlopeNorm(vmin=min(0.5, np.nanmin(M)), vcenter=1.0, vmax=vmax)
    im = ax.imshow(M, cmap="RdBu_r", norm=norm, aspect="auto")
    ax.set_xticks(range(len(present))); ax.set_xticklabels([C.SH_LABEL[sh].split("(")[0] for sh in present], fontsize=9)
    ax.set_yticks(range(len(scen))); ax.set_yticklabels(list(scen.keys()), fontsize=9)
    for i in range(len(scen)):
        for j in range(len(present)):
            ax.text(j, i, "×%.2f" % M[i, j], ha="center", va="center", fontsize=8.5,
                    color="white" if abs(M[i, j] - 1) > 0.35 else "#333")
    ax.set_title("高度政策:各情景下各 stakeholder 的平均高 ÷ 基线(红=拔高/蓝=压低)", fontsize=10.5)
    fig.colorbar(im, ax=ax, fraction=.046, pad=.04)
    C.save_fig(fig, "step3_policies.png", OUT / slug)


def fig_step4(slug, scen, s):
    ks = list(scen.keys())
    fig, axs = plt.subplots(1, 3, figsize=(16, 4.6))
    axs[0].bar(ks, [s["rows"][k]["ratio"] for k in ks], color=ACCENT)
    axs[0].axhline(1, ls="--", c="#999", lw=1); axs[0].set_title("总 GFA(×基线)", fontsize=11)
    axs[1].bar(ks, [s["rows"][k]["mean"] for k in ks], color="#7bbf86")
    axs[1].set_title("平均高 (m)", fontsize=11)
    axs[2].bar(ks, [s["rows"][k]["max"] for k in ks], color="#c0654a")
    axs[2].set_title("最高 (m)", fontsize=11)
    for ax in axs:
        ax.tick_params(axis="x", rotation=30, labelsize=8); ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("各情景指标对照(conserve 的总 GFA 恒为 ×1.00 = 守恒)", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, .94))
    C.save_fig(fig, "step4_metrics.png", OUT / slug)


def fig_scenarios_3d(slug, df, scen, H, s):
    import matplotlib.colors as mc, matplotlib.cm as cm
    minx = min(p.bounds[0] for g in df.geom for p in C._polys(g))
    miny = min(p.bounds[1] for g in df.geom for p in C._polys(g))
    show = [k for k in SHOW if k in scen]
    # 一次算几何 + 持份者色(与高度无关)
    xs, ys, dx, dy, shc = [], [], [], [], []
    for _, r in df.iterrows():
        b = r["geom"].bounds
        xs.append(b[0] - minx); ys.append(b[1] - miny)
        dx.append(max(b[2] - b[0], 3)); dy.append(max(b[3] - b[1], 3))
        shc.append(C.SH_COLOR[r["stakeholder"]])
    xs, ys, dx, dy = map(np.array, (xs, ys, dx, dy))
    HV = {k: H[k].values for k in show}
    cur = HV["current"]
    zmax = max(float(HV[k].max()) for k in show) * 1.05
    alld = np.concatenate([HV[k] - cur for k in show if k != "current"])
    vlim = max(8.0, float(np.percentile(np.abs(alld), 95)))
    norm = mc.TwoSlopeNorm(vmin=-vlim, vcenter=0, vmax=vlim); cmap = cm.RdBu_r
    n = len(show)

    def panel(ax, dz, cols, title):
        ax.bar3d(xs, ys, np.zeros(len(xs)), dx, dy, np.clip(dz, 3, None), color=cols, shade=True, edgecolor="none")
        ax.view_init(elev=34, azim=-58); ax.set_zlim(0, zmax); ax.set_box_aspect((1, 1, 0.5))
        ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([]); ax.grid(False)
        ax.set_title(title, fontsize=10.5)
        for pane in (ax.xaxis, ax.yaxis, ax.zaxis):
            pane.pane.set_visible(False)

    fig = plt.figure(figsize=(5 * n, 10.4))
    for i, name in enumerate(show):
        panel(fig.add_subplot(2, n, i + 1, projection="3d"), HV[name], shc,
              "%s\n最高 %.0f m · 平均 %.1f m" % (name, HV[name].max(), HV[name].mean()))
        dh = HV[name] - cur
        nch = int((np.abs(dh) > 3).sum())
        ttl = "基线(无变化)" if name == "current" else "vs 现状:%d 栋变 >3m" % nch
        panel(fig.add_subplot(2, n, n + i + 1, projection="3d"), HV[name], [cmap(norm(v)) for v in dh], ttl)

    h1 = [Patch(fc=C.SH_COLOR[sh], label=C.SH_LABEL[sh].split("(")[0]) for sh in C.STAKEHOLDERS]
    fig.add_artist(fig.legend(handles=h1, loc="center left", bbox_to_anchor=(0.005, 0.74), fontsize=9, frameon=False, title="上排:持份者"))
    h2 = [Patch(fc=cmap(norm(vlim)), label="拔高(+)"), Patch(fc=cmap(norm(0)), label="≈不变"), Patch(fc=cmap(norm(-vlim)), label="压低(−)")]
    fig.legend(handles=h2, loc="center left", bbox_to_anchor=(0.005, 0.26), fontsize=9, frameon=False, title="下排:vs 现状(±%.0fm)" % vlim)
    fig.suptitle("%s — 权力重分配 → 天际线此消彼长(总 GFA 守恒;同视角)\n上=量体(持份者色)· 下=相对现状的高度变化(红拔高/蓝压低)" % s["name"], fontsize=13, fontweight="bold")
    fig.subplots_adjust(left=.06, right=.99, top=.9, bottom=.03, wspace=.02, hspace=.1)
    C.save_fig(fig, "scenarios_3d.png", OUT / slug)


def fig_satellite(slug, df, s):
    import contextily as ctx
    import pyproj
    from shapely.ops import transform as shp_transform
    w, sth, e, n = s["bounds"]
    zoom = 16 if s["area_km2"] < 3.2 else 15
    img, ext = ctx.bounds2img(w, sth, e, n, ll=True, source=ctx.providers.Esri.WorldImagery, zoom=zoom)
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.imshow(img, extent=ext); ax.axis("off")
    ax.set_title("上海 %s — 真实卫星影像 Esri World Imagery" % s["name"], fontsize=12)
    fig.text(.5, .02, C.honest_note(s["name"]), ha="center", fontsize=7, style="italic", color=".4")
    C.save_fig(fig, "satellite.png", OUT / slug)

    to3857 = pyproj.Transformer.from_crs(C.UTM, 3857, always_xy=True).transform
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.imshow(img, extent=ext, alpha=.92)
    for _, r in df.iterrows():
        g = shp_transform(to3857, r["geom"])
        for p in C._polys(g):
            xs, ys = p.exterior.xy
            ax.fill(xs, ys, facecolor=C.SH_COLOR[r["stakeholder"]], alpha=.6, edgecolor="white", linewidth=.12)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.axis("off")
    ax.set_title("真实卫星 + 本地多源 footprint(依离散权利着色)= 真实地方 vs 我们的读法", fontsize=11.5)
    handles = [Patch(fc=C.SH_COLOR[sh], label=C.SH_LABEL[sh].split("(")[0]) for sh in C.STAKEHOLDERS]
    ax.legend(handles=handles, loc="lower right", fontsize=8, framealpha=.9)
    fig.text(.5, .02, C.honest_note(s["name"]), ha="center", fontsize=7, style="italic", color=".4")
    C.save_fig(fig, "satellite_overlay.png", OUT / slug)


def export_obj(slug, df, scen, H, s):
    d = OUT / slug
    for k in ("current", "developer_led"):
        if k in scen:
            dfk = df.copy(); dfk["height_m"] = H[k].values
            obj, nv, nf = C.extrude_obj(dfk)
            (d / ("city_%s.obj" % k)).write_text(obj, encoding="utf-8")
    cols = ["stakeholder", "height_m", "area_m2", "euluc", "function"]
    exp = df[[c for c in cols if c in df]].copy()
    exp.to_csv(d / "buildings_export.csv", index=False, encoding="utf-8")


# ----------------------------------------------------------------- 3D 几何 JSON
def build_geometry(df, scen, H, sat=None, sext=None):
    minx = min(p.bounds[0] for g in df.geom for p in C._polys(g))
    miny = min(p.bounds[1] for g in df.geom for p in C._polys(g))
    recs = []
    for i, (_, r) in enumerate(df.iterrows()):
        for poly in C._polys(r.geom):
            ps = poly.simplify(1.0)
            xy = [[round(x - minx, 1), round(y - miny, 1)] for x, y in list(ps.exterior.coords)[:-1]]
            if len(xy) >= 3:
                recs.append({"p": xy, "sh": r["stakeholder"],
                             "h": {k: round(float(H[k].iloc[i]), 1) for k in scen}})
    d = {"scenarios": list(scen.keys()), "colors": C.SH_COLOR, "labels": C.SH_LABEL, "recs": recs}
    if sat:
        d["sat"] = sat; d["satExtent"] = sext
    return json.dumps(d, separators=(",", ":"))


def _footprint_bounds(df):
    polys = [p for g in df.geom for p in C._polys(g)]
    return (min(p.bounds[0] for p in polys), min(p.bounds[1] for p in polys),
            max(p.bounds[2] for p in polys), max(p.bounds[3] for p in polys))


def fig_operators(slug, df, s):
    """进阶:9 算子 × 4 权力体制 → 形态指纹。渲染 regimes.png + fingerprints.png,返回指纹表数据。"""
    recs = C.to_recs(df)
    regs = ops.load_regimes()
    after = {n: ops.apply_regime(recs, regs[n]) for n in regs}
    labels = {n: _t(regs[n]["label"]) for n in regs}      # 图内体制名转繁
    C.save_fig(plots.regime_compare(recs, after, labels=labels, show=False), "regimes.png", OUT / slug)
    rows, _ = M.compare(recs, after, slug)
    C.save_fig(plots.fingerprint_bars(rows, labels={"current": _t("现状"), **labels}, show=False), "fingerprints.png", OUT / slug)
    return rows, regs, labels
