"""
animate.py 渲染间的过渡动画。
(A) param_sweep 单算子强度 0-1 逐帧出体块图 gif,离线可跑(可测核心)。
(B) crossfade 已渲染 AI 图交叉溶解成 gif。
(C) ai_video 相邻两图交给 Replicate 图生视频补间,只给接口。
固定机位:相机不动,只有形态动。
"""
from pathlib import Path
import sys
import warnings; warnings.filterwarnings("ignore")
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import settings
import ws05
import massing

OUT = ROOT / "out"


# (A) 算子强度连续扫
# 可连续参数化算子:强度 t∈[0,1] 映射为算子参数。
SWEEPS = {
    "densify":     lambda recs, t, target: ws05.ops.densify(recs, target=target, far_gain=1.0 + 0.8 * t, cap_m=480),
    "slim":        lambda recs, t, target: ws05.ops.slim(recs, target=target, ratio=1.0 - 0.55 * t),
    "concentrate": lambda recs, t, target: ws05.ops.concentrate(recs, center="state_centroid",
                                                                reach_frac=0.18, state_boost=1.0 + 1.0 * t, cap_m=600),
    "level":       lambda recs, t, target: ws05.ops.level(recs, target=target, toward="median", alpha=t),
}


def param_sweep(slug=None, op="densify", target=("resident", "developer"),
                frames=16, color="mono", gif=True, fps=8):
    """算子强度 0-1 扫 frames 帧,固定机位出体块图,可合成 gif。返回帧路径。"""
    slug = slug or settings.SLUG
    target = list(target)
    recs0, _ = ws05.load_recs(slug)
    base = ws05.ops.freeze(recs0, who=["state"])    # 公共不动,同 05
    sweep = SWEEPS[op]
    # 全程统一 zmax,各帧同尺度
    zmax = max(max((r["h"] for r in sweep(base, t, target)), default=1)
               for t in np.linspace(0, 1, frames)) * 1.05
    d = OUT / slug / ("sweep_%s" % op); d.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, t in enumerate(np.linspace(0, 1, frames)):
        recs = sweep(base, t, target)
        p = d / ("f%03d.png" % i)
        massing.render_massing(recs, p, color=color, zmax=zmax)
        paths.append(p)
    print("  扫了 %d 帧 %s" % (len(paths), d.relative_to(ROOT)))
    if gif:
        g = _gif(paths, OUT / slug / ("sweep_%s.gif" % op), fps=fps)
        print("  gif %s" % (g.relative_to(ROOT) if g else "(缺 imageio,跳过)"))
    return paths


# (B) 渲染图交叉溶解
def crossfade(image_paths, out_gif, steps=10, hold=4, fps=12):
    """若干同尺寸图交叉溶解成 gif。返回 gif 路径或 None。"""
    try:
        import imageio.v2 as imageio
        from PIL import Image
    except ImportError:
        print("  缺 imageio/Pillow,跳过 crossfade"); return None
    imgs = [Image.open(p).convert("RGB") for p in image_paths if Path(p).exists()]
    if len(imgs) < 2:
        print("  少于 2 张可用渲染图,跳过 crossfade"); return None
    w = min(i.width for i in imgs); h = min(i.height for i in imgs)
    imgs = [i.resize((w, h)) for i in imgs]
    frames = []
    for a, b in zip(imgs, imgs[1:] + imgs[:1]):
        for _ in range(hold):
            frames.append(np.asarray(a))
        for s in range(1, steps + 1):
            frames.append(np.asarray(Image.blend(a, b, s / (steps + 1))))
    Path(out_gif).parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(out_gif, frames, fps=fps, loop=0)
    print("  crossfade gif %s" % Path(out_gif).relative_to(ROOT))
    return Path(out_gif)


def _gif(paths, out_gif, fps=8):
    try:
        import imageio.v2 as imageio
    except ImportError:
        return None
    frames = [imageio.imread(p) for p in paths]
    frames = frames + frames[::-1]      # 来回播
    Path(out_gif).parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(out_gif, frames, fps=fps, loop=0)
    return Path(out_gif)


# (C) AI 图生视频
def ai_video_hint(first_png, last_png, model="kwaivgi/kling-v1.6-standard"):
    """相邻两图当首/末帧,交给 Replicate 图生视频补间。只给用法说明,真跑需 token。"""
    print("AI 补间(最顺滑,但中间由 AI 想象,illustrative):")
    print("  在 shell 设 REPLICATE_API_TOKEN,然后:")
    print("    import replicate")
    print("    replicate.run('%s', input={" % model)
    print("        'start_image': open('%s','rb')," % first_png)
    print("        'end_image':   open('%s','rb')," % last_png)
    print("        'prompt': 'fixed camera, the skyline morphs as power redistributes'})")
    print("  备选模型:wan-video/wan-2.2-i2v / runwayml / luma 等(各自入参略不同)。")


if __name__ == "__main__":
    import sys as _s
    slug = _s.argv[1] if len(_s.argv) > 1 else settings.SLUG
    op = _s.argv[2] if len(_s.argv) > 2 else "densify"
    print("== 算子强度扫描动画:%s %s ==" % (slug, op))
    param_sweep(slug, op=op, frames=12)
    print("done")
