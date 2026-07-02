"""算子序列图:一个权力体制 = 一串算子,逐步套用、逐步看形态怎么长出来。
  regime_steps_strip(states, ...) — 总览:每步一栏,上排 3D 量体、下排 2D footprint,
                                    全部同 bounds / 同 z 高度,可横向比对。
  regime_step_3d(recs, ...)       — 单步 3D 一张(全部建筑,不抽样),存到指定路径。
  regime_step_2d(recs, ...)       — 单步 2D footprint 一张,存到指定路径。
run.py 用后两个出 regime_steps/<体制>/{步序}_{算子}_3d.png / _2d.png 的逐帧序列。
states = [(op_label, recs), ...];第 0 个约定为 ("current", 现状 recs)。
recs 工作单位同 operators.py:[{geom, h, sh, frozen}]。算是 controller 的事,这里只画。"""
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon
import common
from . import _base

CAM = {"elev": 48, "azim": -60}          # urban 视角:稍微高一点俯瞰;全序列固定机位,逐帧才可比


def _nice_step(span, target=8):
    """xy 网格间距:取 span/target 附近的整数级距(米)。"""
    raw = span / max(target, 1)
    for s in (25, 50, 100, 200, 250, 500, 1000, 2000):
        if raw <= s:
            return s
    return 5000


def _scene_of(states):
    """全部步骤的共同场景:bounds(算子可能放大 footprint,取全序列并集)+ 最高高度。"""
    x0 = y0 = float("inf"); x1 = y1 = float("-inf"); hmax = 1.0
    for _, recs in states:
        for r in recs:
            hmax = max(hmax, float(r["h"]))
            for p in common._polys(r["geom"]):
                b = p.bounds
                x0 = min(x0, b[0]); y0 = min(y0, b[1]); x1 = max(x1, b[2]); y1 = max(y1, b[3])
    return x0, y0, x1, y1, hmax


def _draw_3d(ax, recs, scene, axis=False):
    """一格 3D 量体(角色配色,**全部建筑**)。
    所有面合进一个 Poly3DCollection(逐栋一个 collection 上万栋会拖死 matplotlib)。
    axis=True:显示坐标轴空间 + 地面(xy)网格(单图用);False:纯量体(总览小格用)。"""
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    x0, y0, x1, y1, hmax = scene
    faces, colors = [], []
    for r in recs:
        fs = _base.building_faces(r["geom"], float(r["h"]), x0, y0)
        pts = [c for f in fs for c in f]
        if not pts or not np.isfinite(np.asarray(pts, dtype=float)).all():
            continue                                     # 跳过退化量体
        col = _base.SH_COLOR.get(r["sh"], "#b8b8b8")
        faces.extend(fs)
        colors.extend([col] * len(fs))
    pc = Poly3DCollection(faces, facecolors=colors, edgecolor="white", linewidths=0.05, alpha=0.92)
    try:
        ax.add_collection3d(pc, autolim=False)
    except TypeError:                                    # 旧版 mpl 无 autolim 参数
        ax.add_collection3d(pc)
    xm, ym = x1 - x0, y1 - y0
    zm = hmax * 1.05
    ax.set_xlim(0, xm); ax.set_ylim(0, ym); ax.set_zlim(0, zm)
    if axis:
        # xyz 全部**固定真实比例**(1m 在三轴等长,不做竖向夸张);全序列共用 scene → 逐帧比例一致
        zasp, zoom = zm, 1.0
    else:
        # 总览小格:竖向夸张但封顶(不然矮楼压平看不见);zoom 吃掉 mpl 3D 的默认大留白
        zasp, zoom = min(max(hmax, 1) * 4, max(xm, ym) * 0.9), 1.35
    try:
        ax.set_box_aspect((xm, ym, zasp), zoom=zoom)
    except TypeError:                                    # 旧版 mpl 无 zoom 参数
        ax.set_box_aspect((xm, ym, zasp))
    ax.view_init(**CAM)
    if not axis:
        ax.set_axis_off()
        return
    # 坐标轴空间:白色 pane;xy 地面画**明确网格划分**(z=0,刻度对齐,单位米)
    step = _nice_step(max(xm, ym))
    for gx in np.arange(0, xm + step * 0.01, step):
        ax.plot([gx, gx], [0, ym], [0, 0], color="#c4c4c4", lw=0.6, zorder=-50)
    for gy in np.arange(0, ym + step * 0.01, step):
        ax.plot([0, xm], [gy, gy], [0, 0], color="#c4c4c4", lw=0.6, zorder=-50)
    ax.set_xticks(np.arange(0, xm + step * 0.01, step))
    ax.set_yticks(np.arange(0, ym + step * 0.01, step))
    ax.grid(True)
    ax.set_xlabel("x (m)", fontsize=9, labelpad=10)
    ax.set_ylabel("y (m)", fontsize=9, labelpad=10)
    ax.set_zlabel("高度 (m)", fontsize=9, labelpad=8)
    ax.tick_params(labelsize=7, pad=2)
    for axis3 in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis3.pane.set_facecolor("white")
        axis3.pane.set_edgecolor("#c8c8c8")
        axis3._axinfo["grid"].update(color="#dcdcdc", linewidth=0.4)


def _draw_2d(ax, recs, scene):
    """一格 2D footprint(角色配色),锁定共同 bounds 才能逐帧横比。"""
    x0, y0, x1, y1, _ = scene
    common.plot_footprints(ax, recs, lambda r: _base.SH_COLOR.get(r["sh"], "#b8b8b8"), lw=0.1)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)


def _legend(fig, y=0.02):
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=_base.SH_COLOR[s]) for s in common.STAKEHOLDERS]
    fig.legend(handles, [_base.SH_LABEL[s] for s in common.STAKEHOLDERS], loc="lower center",
               bbox_to_anchor=(0.5, y), ncol=len(common.STAKEHOLDERS), fontsize=9, frameon=False)


def _col_title(i, lab, recs):
    head = "current" if i == 0 else "step %d · %s" % (i, lab)
    return "%s\nn=%d · 平均高 %.1fm" % (head, len(recs), float(np.mean([r["h"] for r in recs])))


def _save(fig, path):
    if path is not None:
        from pathlib import Path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=120, bbox_inches="tight", pad_inches=0.083)


def regime_steps_strip(states, title=None, save_name="regime_steps", show=True):
    """体制的算子序列总览:ncols=步数(含 current),上排 3D、下排 2D,同尺度。"""
    scene = _scene_of(states)
    n = len(states)
    fig = plt.figure(figsize=(3.4 * n, 7.4))
    gs = fig.add_gridspec(2, n, height_ratios=[1.15, 1.0], hspace=0.02, wspace=0.05,
                          left=0.02, right=0.98, top=0.86, bottom=0.09)
    for i, (lab, recs) in enumerate(states):
        ax3 = fig.add_subplot(gs[0, i], projection="3d")
        _draw_3d(ax3, recs, scene)
        ax3.set_title(_col_title(i, lab, recs), fontsize=10)
        ax2 = fig.add_subplot(gs[1, i])
        _draw_2d(ax2, recs, scene)
    _legend(fig)
    if title:
        fig.suptitle(title, fontsize=14, y=0.97)
    _base.autosave(fig, save_name)
    if show:
        plt.show()
    return fig


def regime_step_3d(recs, title=None, scene=None, path=None, show=True):
    """单步 3D 一张(全部建筑)。scene 传全序列共同场景(不传就用本步自身)。path 给了就直接落盘。"""
    scene = scene or _scene_of([("", recs)])
    fig = plt.figure(figsize=(10.2, 7.8))
    ax = fig.add_subplot(111, projection="3d")
    _draw_3d(ax, recs, scene, axis=True)
    _legend(fig, y=0.005)
    if title:
        fig.suptitle(title, fontsize=13, y=0.97)
    fig.subplots_adjust(left=0.0, right=0.96, top=0.93, bottom=0.11)   # 底/右留空,轴标签不被图例压到
    _save(fig, path)
    if show:
        plt.show()
    return fig


def regime_step_2d(recs, title=None, scene=None, path=None, show=True):
    """单步 2D footprint 一张。scene 传全序列共同场景(不传就用本步自身)。path 给了就直接落盘。"""
    scene = scene or _scene_of([("", recs)])
    x0, y0, x1, y1, _ = scene
    asp = (y1 - y0) / max(x1 - x0, 1e-9)
    fig, ax = plt.subplots(figsize=(9.0, max(9.0 * asp, 3.0) + 1.0))
    _draw_2d(ax, recs, scene)
    _legend(fig, y=0.01)
    if title:
        fig.suptitle(title, fontsize=13, y=0.98)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.08)
    _save(fig, path)
    if show:
        plt.show()
    return fig


def _lerp_geom(ga, gb, t):
    """同构几何(算子仿射变形前后:同环数、同顶点数)的顶点线性插值。结构不同回 None。"""
    pa, pb = common._polys(ga), common._polys(gb)
    if len(pa) != len(pb):
        return None
    outs = []
    for A, B in zip(pa, pb):
        ca, cb = list(A.exterior.coords), list(B.exterior.coords)
        if len(ca) != len(cb):
            return None
        outs.append(Polygon([(xa + (xb - xa) * t, ya + (yb - ya) * t)
                             for (xa, ya), (xb, yb) in zip(ca, cb)]))
    return outs[0] if len(outs) == 1 else MultiPolygon(outs)


def morph_recs(a, b, t):
    """a→b 的中间形态(t∈0..1):逐栋几何顶点 + 高度线性插值 = 真 morph。
    栋数改变(split_to_towers/infill)或几何不同构 → 回 None(调用端退回交叉溶解)。"""
    if len(a) != len(b):
        return None
    out = []
    for ra, rb in zip(a, b):
        g = _lerp_geom(ra["geom"], rb["geom"], t)
        if g is None:
            return None
        nr = dict(rb)
        nr["geom"] = g
        nr["h"] = float(ra["h"]) + (float(rb["h"]) - float(ra["h"])) * t
        out.append(nr)
    return out


def steps_gif_morph(states, kind, out_path, scene=None, label="", frame_paths=None,
                    hold_ms=1100, morph_frames=5, morph_ms=100):
    """逐步「渐变过程」gif:步与步之间做**几何 morph**(顶点/高度插值后重新渲染中间帧),
    不是像素淡入淡出;栋数改变的步(split/infill)自动退回交叉溶解。
    states=[(op_label, recs)...];kind='3d'/'2d';frame_paths=已存在的逐步 png(当停留帧)。"""
    from pathlib import Path
    from PIL import Image
    render = regime_step_3d if kind == "3d" else regime_step_2d
    scene = scene or _scene_of(states)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.parent / ("_morph_tmp_%s.png" % kind)

    holds = [Image.open(p).convert("RGB") for p in frame_paths]

    def _render_mid(mid, i):
        t = "%s · step %d · %s" % (label, i + 1, states[i + 1][0])
        render(mid, title=t, scene=scene, path=tmp, show=False)
        plt.close("all")
        im = Image.open(tmp).convert("RGB").copy()
        return im

    # raw:('img', PIL) 或 ('blend', 前后 hold 序号, t)——blend 等全部 pad 完再算
    raw, durs = [], []
    for i in range(len(states) - 1):
        a, b = states[i][1], states[i + 1][1]
        raw.append(("img", holds[i])); durs.append(hold_ms)
        # 视觉无变化的步(如 freeze)不插帧
        if len(a) == len(b) and all(ra["geom"] is rb["geom"] and ra["h"] == rb["h"]
                                    for ra, rb in zip(a, b)):
            continue
        for k in range(1, morph_frames + 1):
            t = k / (morph_frames + 1)
            mid = morph_recs(a, b, t)
            if mid is None:                              # 栋数改变 → 退回交叉溶解
                raw.append(("blend", i, t))
            else:
                raw.append(("img", _render_mid(mid, i)))
            durs.append(morph_ms)
    raw.append(("img", holds[-1])); durs.append(hold_ms * 2)
    if tmp.exists():
        tmp.unlink()

    # 各帧因 bbox_inches='tight' 尺寸略有出入 → 全部居中贴到同一张白底
    imgs = [r[1] for r in raw if r[0] == "img"]
    W = max(im.width for im in imgs)
    H = max(im.height for im in imgs)

    def pad(im):
        cv = Image.new("RGB", (W, H), "white")
        cv.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
        return cv

    holds_p = [pad(im) for im in holds]
    frames = []
    for r in raw:
        if r[0] == "img":
            frames.append(pad(r[1]))
        else:
            _, i, t = r
            frames.append(Image.blend(holds_p[i], holds_p[i + 1], t))
    frames[0].save(out_path, save_all=True, append_images=frames[1:],
                   duration=durs, loop=0, optimize=True)
    return out_path
