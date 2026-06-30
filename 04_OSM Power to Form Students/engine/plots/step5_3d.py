"""Step5 圖:真實 footprint 擠成 3D 量體。
  city_3d(sub)        — matplotlib,程式碼定角度(elev/azim)。
  city_3d_plotly(sub) — plotly,瀏覽器裡滑鼠拖動旋轉(回傳 fig,自行 .show()/.write_html())。
sub 需有 'stakeholder' 與高度欄(預設 'height_m';可傳 height_col 指定情景高度)。"""
import numpy as np
import matplotlib.pyplot as plt
import common
from . import _base


def _drawable(sub, height_col):
    """濾掉畫不出來的列:高度非有限(NaN/Inf)或 footprint 空/缺。
    任意 OSM 資料(線上抓的城市、手改的 CSV)都可能出現,留著會讓 mpl
    autoscale 噴 'Axis limits cannot be NaN or Inf'。"""
    h = np.isfinite(sub[height_col].astype(float))
    geom_ok = sub["geom"].apply(lambda g: g is not None and not getattr(g, "is_empty", True)
                                and any(True for _ in common._polys(g)))
    keep = h & geom_ok
    dropped = int((~keep).sum())
    if dropped:
        print("  city_3d:跳過 %d 棟(高度非有限或 footprint 空)" % dropped)
    return sub[keep]


def city_3d(sub, height_col="height_m", elev=30, azim=-60, show=True):
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    sub = _drawable(sub, height_col)
    if len(sub) == 0:
        raise ValueError("city_3d:沒有可畫的建築(高度全非有限或 footprint 全空)")
    ox, oy = _base.origin_of(sub)

    fig = plt.figure(figsize=(11, 7.5))
    ax = fig.add_subplot(111, projection="3d")
    for _, r in sub.iterrows():
        faces = _base.building_faces(r["geom"], float(r[height_col]), ox, oy)
        if not faces:
            continue
        ax.add_collection3d(Poly3DCollection(faces, facecolor=_base.SH_COLOR[r["stakeholder"]],
                                             edgecolor="white", linewidths=0.1, alpha=0.92))
    xmax = max(p.bounds[2] for g in sub["geom"] for p in common._polys(g)) - ox
    ymax = max(p.bounds[3] for g in sub["geom"] for p in common._polys(g)) - oy
    hmax = float(sub[height_col].max())
    ax.set_xlim(0, xmax); ax.set_ylim(0, ymax); ax.set_zlim(0, hmax * 1.1)
    ax.set_box_aspect((xmax, ymax, max(hmax, 1) * 4))   # z 拉高,量體才明顯
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)"); ax.set_zlabel("高度 (m)")
    ax.view_init(elev=elev, azim=azim)

    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=_base.SH_COLOR[s]) for s in common.STAKEHOLDERS]
    ax.legend(handles, [_base.SH_LABEL[s] for s in common.STAKEHOLDERS], loc="upper center",
              bbox_to_anchor=(0.5, -0.06), ncol=len(common.STAKEHOLDERS), fontsize=8, frameon=False)
    fig.tight_layout()
    if show:
        plt.show()
    return fig


def city_3d_plotly(sub, height_col="height_m"):
    import plotly.graph_objects as go
    from shapely.ops import triangulate
    ox, oy = _base.origin_of(sub)

    traces = []
    for sh in common.STAKEHOLDERS:
        rows = sub[sub["stakeholder"] == sh]
        if len(rows) == 0:
            continue
        X, Y, Z, I, J, K = [], [], [], [], [], []
        for _, r in rows.iterrows():
            h = float(r[height_col])
            for poly in common._polys(r["geom"]):
                ring = list(poly.exterior.coords)
                if len(ring) > 1 and ring[0] == ring[-1]:
                    ring = ring[:-1]
                n = len(ring)
                if n < 3:
                    continue
                base = len(X)
                for (x, y) in ring:                 # 底環
                    X.append(x - ox); Y.append(y - oy); Z.append(0.0)
                for (x, y) in ring:                 # 頂環
                    X.append(x - ox); Y.append(y - oy); Z.append(h)
                for i in range(n):                  # 牆:每邊兩個三角形
                    j = (i + 1) % n
                    b0, b1 = base + i, base + j
                    t0, t1 = base + n + i, base + n + j
                    I += [b0, b0]; J += [b1, t1]; K += [t1, t0]
                for tri in triangulate(poly):       # 頂蓋:三角化(濾掉落在外面的)
                    if not poly.contains(tri.representative_point()):
                        continue
                    tc = list(tri.exterior.coords)[:3]
                    a = len(X)
                    for (x, y) in tc:
                        X.append(x - ox); Y.append(y - oy); Z.append(h)
                    I.append(a); J.append(a + 1); K.append(a + 2)
        if X:
            traces.append(go.Mesh3d(x=X, y=Y, z=Z, i=I, j=J, k=K,
                                    color=_base.SH_COLOR[sh], opacity=1.0,
                                    name=_base.SH_LABEL[sh], showlegend=True, flatshading=True))

    fig = go.Figure(data=traces)
    fig.update_layout(
        scene=dict(xaxis_title="x (m)", yaxis_title="y (m)", zaxis_title="高度 (m)",
                   aspectmode="manual", aspectratio=dict(x=1.6, y=1.6, z=0.9)),
        legend=dict(orientation="h", yanchor="top", y=0, xanchor="center", x=0.5),
        margin=dict(l=0, r=0, t=0, b=0))
    return fig
