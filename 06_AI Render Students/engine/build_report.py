"""06 聚合报告:全部产出拼成自含单档 out/<slug>/report.html。
每体制一卡:体块参考图 + AI 渲染图 + 提示词三层 + 形态数字;末尾动画与画布链接。
跑:python run.py  或  python run.py report caoyang"""
import base64
import os
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent           # engine/
ROOT = HERE.parent                                # 06 根
sys.path.insert(0, str(HERE))
import settings          # noqa: E402
import ws05              # noqa: E402
import prompt_gen        # noqa: E402
import massing           # noqa: E402
import animate           # noqa: E402
import build_canvas      # noqa: E402

OUT = ROOT / "out"
MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif"}


# 读磁盘 data URI
def data_uri(p):
    p = Path(p)
    return "data:%s;base64,%s" % (MIME[p.suffix.lower()], base64.b64encode(p.read_bytes()).decode())


def fig(p, cap, cls="", missing=None):
    """一张图做成 figure;缺图给占位。"""
    p = Path(p)
    if not p.exists():
        return '<figure class="%s missing"><div class="ph">%s</div><figcaption>%s</figcaption></figure>' % (
            cls, missing or "(此产出缺失)", cap)
    return '<figure class="%s"><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>' % (
        cls, data_uri(p), cap, cap)


# 确保产出在(缺就补)
def ensure_artifacts(slug, regimes):
    """确保参考图/提示词txt/sweep gif 存在,缺就补;返回 prompts 三层 dict。"""
    d = OUT / slug
    d.mkdir(parents=True, exist_ok=True)
    prompts = prompt_gen.build_all(slug, regimes)                 # prompt 三层
    # 缺一张就整套重出(共用 zmax 才能横比)
    if not all((d / ("massing_%s.jpg" % r)).exists() for r in regimes):
        print("  补体块参考图 massing_*.jpg")
        massing.massing_for_regimes(slug, regimes)
    prompt_gen.write_prompt_files(slug, regimes, prompts=prompts)  # 落 massing_<r>.txt
    # 算子扫描动画(离线);缺才补
    if not (d / "sweep_slim.gif").exists():
        print("  补算子扫描动画 sweep_slim.gif")
        animate.param_sweep(slug, op="slim", frames=12)
    return prompts


# 一张体制卡片
def regime_card(slug, regime, pd, met):
    d = OUT / slug
    label = pd["label"]
    chips = "".join('<span class="chip">%s</span>' % c for c in [
        "%d 栋" % met["n"],
        "最高 ~%d m" % round(met["h_max"]),
        "平均 ~%d m" % round(met["h_mean"]),
        "瘦长比 %.1f" % met["slender"],
    ])
    struct = fig(d / ("massing_%s.jpg" % regime), "结构层 体块参考图(实算)", cls="struct")
    render = fig(d / ("render_%s.png" % regime), "表面层 AI 渲染图", cls="render",
                 missing="dry-run 未渲染<br>(设 REPLICATE_API_TOKEN 后跑 02)")
    return """<section class="card">
  <div class="card-h"><h3>%s</h3><code>%s</code></div>
  <div class="chips">%s</div>
  <div class="imgrow">%s%s</div>
  <div class="prm">
    <div class="lyr"><b>[计算层]</b> <span class="ok">诚实,可追溯</span><p>%s</p></div>
    <div class="lyr"><b>[论述层]</b> <span class="warn">illustrative,可改 config.yaml</span><p>%s</p></div>
    <details><summary>完整 prompt(发给模型)</summary><pre>%s</pre></details>
  </div>
</section>""" % (label, regime, chips, struct, render, pd["computed"], pd["argued"], pd["prompt"])


CSS = """
:root{--accent:#0f5e63;--ink:#1a1f22;--muted:#717b80;--line:#e6e9ea;--bg:#f7f8f7;
 --ok:#2f7d55;--warn:#b06a2c;}
*{box-sizing:border-box;} html{scroll-behavior:smooth;}
body{margin:0;background:var(--bg);color:var(--ink);
 font:16px/1.7 "Helvetica Neue","PingFang SC","Microsoft YaHei",system-ui,sans-serif;}
.wrap{max-width:1080px;margin:0 auto;padding:0 22px 90px;}
.cover{max-width:1080px;margin:0 auto;padding:34px 22px 6px;}
.kick{letter-spacing:.18em;text-transform:uppercase;font-size:11px;color:var(--muted);margin:0 0 8px;}
.cover h1{font-size:27px;line-height:1.3;margin:0 0 8px;font-weight:750;}
.cover p.lead{margin:0 0 14px;color:#3a4347;max-width:830px;font-size:15.5px;}
.banner{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0 6px;}
.banner div{flex:1;min-width:240px;border:1px solid var(--line);border-radius:11px;padding:11px 13px;background:#fff;}
.banner b{display:block;margin-bottom:3px;} .banner .ok{color:var(--ok);} .banner .warn{color:var(--warn);}
.banner p{margin:0;font-size:13px;color:var(--muted);}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin:18px 0;
 box-shadow:0 2px 12px rgba(0,0,0,.05);}
.card-h{display:flex;align-items:baseline;gap:10px;} .card-h h3{margin:0;font-size:19px;}
.card-h code{color:var(--muted);font-size:12.5px;}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:9px 0 12px;}
.chip{font-size:12px;background:#eef3f3;border:1px solid var(--line);border-radius:14px;padding:3px 10px;color:#33474a;}
.imgrow{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
figure{margin:0;} figure img{width:100%;border-radius:9px;display:block;border:1px solid var(--line);}
figcaption{font-size:12px;color:var(--muted);margin-top:5px;}
figure.missing .ph{display:flex;align-items:center;justify-content:center;text-align:center;height:180px;
 border:1px dashed #c8cfd0;border-radius:9px;color:var(--muted);font-size:13px;background:#fafbfb;}
.prm{margin-top:13px;} .lyr{margin:7px 0;} .lyr p{margin:2px 0 0;font-size:14px;}
.lyr .ok{color:var(--ok);font-size:11.5px;} .lyr .warn{color:var(--warn);font-size:11.5px;}
details{margin-top:8px;} summary{cursor:pointer;font-size:13px;color:var(--accent);}
pre{white-space:pre-wrap;background:#f6f8f8;border:1px solid var(--line);border-radius:8px;padding:10px;
 font-size:12.5px;line-height:1.55;margin:7px 0 0;}
h2.sec{font-size:15px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;
 border-top:1px solid var(--line);padding-top:22px;margin:34px 0 4px;}
.gifs{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.cta{display:inline-block;margin-top:8px;background:var(--accent);color:#fff;text-decoration:none;
 border-radius:9px;padding:10px 16px;font-weight:600;}
.foot{font-size:12.5px;color:var(--muted);margin-top:14px;line-height:1.7;}
.foot li{margin:3px 0;}
"""


def build(slug=None):
    slug = slug or settings.SLUG
    regimes = settings.REGIMES
    print("=== report: %s ===" % slug)
    prompts = ensure_artifacts(slug, regimes)
    metrics, _ = prompt_gen.metrics_for(slug, regimes)
    canvas = build_canvas.build(slug)                     # 出 canvas.html
    site = ws05.C.site_meta(slug)
    site_name = site.get("name", slug)

    cards = "".join(regime_card(slug, r, prompts[r], metrics[r]) for r in regimes)
    d = OUT / slug
    gifs = fig(d / "sweep_slim.gif", "算子强度扫描(最诚实,每帧真算子输出)", cls="") \
        + fig(d / "crossfade_massing.gif", "体块/渲染交叉溶解(串场,illustrative)", cls="",
              missing="(缺;跑 03 的 crossfade 生成)")

    html = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>06 %s — AI 渲染报告:权力 形态 影像</title><style>%s</style></head><body>
<div class="cover">
  <p class="kick">06 AI Render — Power Form Image</p>
  <h1>%s AI 渲染报告</h1>
  <p class="lead">同一固定机位下,把每种权力体制的<b>体块(结构,实算)</b>与<b>AI 渲染(表面,论述)</b>并排对照。
  提示词显式拆成 <b>[计算层]</b>(从 05 实算的栋数/高度/形态指纹)与 <b>[论述层]</b>(config.yaml 里主张的外观)。</p>
  <div class="banner">
    <div><b class="ok">结构 = 诚实</b><p>体块由 pipeline 计算,footprint / 高度 / 天际线可追溯。参考图约束 AI 不许加减楼。</p></div>
    <div><b class="warn">表面 = 论述</b><p>材质 / 氛围是 config.yaml 里写的主张,illustrative,非这座城真实的样子。</p></div>
  </div>
</div>
<div class="wrap">
  <h2 class="sec">逐权力体制:结构、表面、提示词</h2>
  %s
  <h2 class="sec">过渡动画</h2>
  <div class="gifs">%s</div>
  <h2 class="sec">互动画布(找角度,导出 ControlNet 条件图)</h2>
  <p>拖拽 orbit 找机位、切权力体制、导出 massing / depth / normal / seg / canny。自含单档,浏览器直接开。</p>
  <a class="cta" href="canvas.html">开互动画布 canvas.html</a>
  <h2 class="sec">诚实边界</h2>
  <ul class="foot">
    <li>渲染图 illustrative:体块忠实(参考图约束 + negative 护栏),外观是 AI 按论述层想象。</li>
    <li>模型偶尔仍偷改天际线,出图肉眼核对体块有没有被篡改。</li>
    <li>动画:算子强度扫描最诚实(每帧真算子);crossfade 是观感润色,中间态混合/想象。</li>
    <li>固定机位贯穿:相机不动,画面里动的只有形态 = 纯权力信号。</li>
  </ul>
</div>
</body></html>""" % (site_name, CSS, site_name, cards, gifs)

    p = d / "report.html"
    p.write_text(html, encoding="utf-8")
    print("写了:", p.relative_to(ROOT), "| %.2f MB" % (p.stat().st_size / 1e6))
    return p


def build_index(sites, pages):
    """出 out/index.html:三站报告 + 画布的目录页。"""
    links = "".join(
        '<li><a href="%s/report.html">%s 报告</a> <a href="%s/canvas.html">互动画布</a></li>' % (s, s, s)
        for s in sites)
    html = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>06 AI 渲染报告目录</title>
<style>body{font:16px/1.8 "PingFang SC","Microsoft YaHei",system-ui;max-width:640px;margin:40px auto;padding:0 20px;color:#1a1f22;}
h1{font-size:22px;} a{color:#0f5e63;} li{margin:8px 0;}</style></head><body>
<h1>06 AI 渲染报告</h1><p>权力 形态 影像。每站一份自含报告 + 互动画布。</p><ul>%s</ul></body></html>""" % links
    p = OUT / "index.html"
    p.write_text(html, encoding="utf-8")
    print("写了:", p.relative_to(ROOT))
    return p


# 05 结果页桥接到 06
def _rel(target, start):
    """start 到 target 的相对 URL(转义,file:// 可点)。"""
    r = os.path.relpath(str(target), str(start)).replace(os.sep, "/")
    return urllib.parse.quote(r)


INDEX05 = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>05 %s 结果 06</title>
<style>body{font:16px/1.7 "PingFang SC","Microsoft YaHei",system-ui;max-width:1000px;margin:34px auto;padding:0 22px;color:#1a1f22;background:#f7f8f7;}
h1{font-size:23px;} .kick{letter-spacing:.16em;text-transform:uppercase;font-size:11px;color:#717b80;}
.cta{display:inline-block;margin:6px 10px 6px 0;background:#0f5e63;color:#fff;text-decoration:none;border-radius:9px;padding:10px 16px;font-weight:600;}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin-top:20px;}
figure{margin:0;background:#fff;border:1px solid #e6e9ea;border-radius:11px;padding:10px;}
figure img{width:100%;border-radius:7px;display:block;} figcaption{font-size:12px;color:#717b80;margin-top:6px;}
.sec{font-size:14px;color:#717b80;text-transform:uppercase;letter-spacing:.06em;margin:28px 0 4px;}</style></head><body>
<p class="kick">05 Power to Form — 本次运行结果</p>
<h1>__SITE__ 05 完整流程结果</h1>
<p>下方是本次 05 跑出的图。往下一步 06 把同一批体块变成互动画布 / AI 渲染报告:</p>
<div>__LINKS__</div>
<div class="sec">本次产出的图(05 Step_05)</div>
<div class="grid">__FIGS__</div>
</body></html>"""


def build_bridge_index(slug, step05_dir, r06=None):
    """在 05 Step_05/<STAMP>/ 写 index.html:列出图 + 前向链到 06 canvas/report。
    step05_dir: 05 图目录(含 *.png)。r06: 06 根(默认 ROOT)。"""
    step05_dir = Path(step05_dir)
    r06 = Path(r06) if r06 else ROOT
    site = ws05.C.site_meta(slug)
    site_name = site.get("name", slug)
    pngs = sorted(step05_dir.glob("*.png"))
    canvas = r06 / "out" / slug / "canvas.html"
    report = r06 / "out" / slug / "report.html"
    links = ""
    if canvas.exists():
        links += '<a class="cta" href="%s">06 互动画布 canvas.html</a>' % _rel(canvas, step05_dir)
    if report.exists():
        links += '<a class="cta" href="%s">06 AI 渲染报告 report.html</a>' % _rel(report, step05_dir)
    if not links:
        links = '<p>(06 产出还没生成:先在 06 跑 build_report.py)</p>'
    figs = "".join('<figure><img src="%s"><figcaption>%s</figcaption></figure>'
                   % (urllib.parse.quote(p.name), p.stem) for p in pngs) or "<p>(此目录暂无 png)</p>"
    html = (INDEX05.replace("__SITE__", str(site_name))
            .replace("__LINKS__", links).replace("__FIGS__", figs))
    p = step05_dir / "index.html"
    p.write_text(html, encoding="utf-8")
    print("写了 05 结果页:", p)
    return p


if __name__ == "__main__":
    try:                                   # 强制 utf-8
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    a = sys.argv[1:]
    if a and a[0] == "--bridge":           # --bridge <slug> <step05_dir>
        build_bridge_index(a[1], a[2])
    elif a:
        build(a[0])
    else:
        sites = settings.REPORT_SITES if hasattr(settings, "REPORT_SITES") else [settings.SLUG]
        pages = [build(s) for s in sites]
        build_index(sites, pages)
