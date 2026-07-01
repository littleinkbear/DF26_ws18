# 生成 3 本学生 notebook(简体)并转繁体(opencc s2t)。
# 跑:python run.py notebooks
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent    # 06 根


def md(t): return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}
def code(t): return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                     "source": t.strip("\n").splitlines(keepends=True)}
def notebook(cells): return {"cells": cells, "metadata": {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}


def _preamble():
    return [
        md("""
## 怎么执行
- 点一格,按 **Shift+Enter** 执行;或选单 Run Run All Cells。结果显示在格子下面。
- 代码都在 `engine/`,平时不用打开。本工作坊**依赖 05**(数据/引擎/权力体制),请确保隔壁 `05_Shanghai Power to Form Students/` 在。
"""),
        code("""
# 让 notebook 找到 engine 与 settings(不用改,直接执行)
import sys, os
sys.path.insert(0, os.path.abspath("engine"))
sys.path.insert(0, os.path.abspath("."))
import importlib, settings; importlib.reload(settings)
import ws05, prompt_gen, massing, render, animate
print("就绪 站点 SLUG =", settings.SLUG, " 模型 =", settings.MODEL)
"""),
    ]


# NB1 提示词生成器
def nb_prompt():
    cells = [md("""
# 01 提示词生成器:从「权力」自动出提示词
07 的核心。把 05 算出的「权力 形态」变成一条 AI 渲染提示词,而且**显式拆成两层**:

- **计算层 [computed]** —— 从 05 真实算出的数字(栋数、最高/平均高、形态指纹)。诚实、可追溯,是参考图体块的语言化。
- **论述层 [argued]** —— `config.yaml` 的 `prompts` 段里你写的"这种权力看起来像什么"(材质/氛围)。是**论点不是数据**,标 illustrative。

> 这正是整个工作坊的诚实底线:**结构由权力计算,外观由论述补充**。学生改 `config.yaml` = 改论述层;计算层改不动、也不该改。
""")]
    cells += _preamble()
    cells += [
        md("## 一、看各权力体制自动生成的提示词\n用 05 的 4 种权力体制(+现状),每条都标出 [计算层] 与 [论述层]。"),
        code("""
P = prompt_gen.build_all(settings.SLUG)        # {regime: {prompt,negative,computed,argued,label}}
for r, d in P.items():
    print("【%s】%s" % (d["label"], r))
    print("  [计算层] " + d["computed"])
    print("  [论述层] " + d["argued"])
    print()
"""),
        md("## 二、看一条完整提示词(发给模型的样子)\n注意结尾那句**护栏**:命令模型严格保住参考图的体块/轮廓/天际线——这是诚实性的关键。"),
        code("""
d = P["developer_led"]
print("完整 prompt：\\n", d["prompt"])
print("\\n负面 negative：\\n", d["negative"])
"""),
        md("""
## 三、改论述层 = 改"你主张这种权力长什么样"
打开 `config.yaml`,改 `prompts.regimes.developer_led.look`(例如把"玻璃针塔"改成"混凝土巨构"),
存档、重跑下面这格——**只有论述层会变,计算层照旧**(因为它来自真实数字)。
"""),
        code("""
importlib.reload(prompt_gen)
P = prompt_gen.build_all(settings.SLUG)
d = P["developer_led"]
print("改后 developer_led：")
print("  [计算层](不变) " + d["computed"])
print("  [论述层](你改的) " + d["argued"])
"""),
        md("""
## 诚实边界
- **计算层**来自 05 的真实形态指标(measure.py),是参考图体块的诚实描述。
- **论述层**是"我认为这种权力会长成这样"的可争论假设——是工作坊化约,不是经验断言。
- prompt 用英文(图像模型更稳);中文只在解释。
> 下一本:[`02 体块到影像`] —— 把"参考图体块 + 这条提示词"交给 AI 出图。
"""),
    ]
    return notebook(cells)


# NB2 体块到影像
def nb_render():
    cells = [md("""
# 02 体块到影像:参考图 + 提示词 AI 渲染
管线:**05 的体块截图(结构)** + **01 的提示词(表面)** Replicate 的「1 张参考图 + 文字 图」模型(默认 nano-banana)。

> **结构来自计算(参考图锁住体块),外观来自论述(提示词补材质氛围)。** AI 只许改外观、不许改形态——提示词里有护栏。
""")]
    cells += _preamble()
    cells += [
        md("## 一、出体块参考图(固定机位)+ 配对英文提示词\n对每种权力体制:一张素模体块**参考图 jpg** + 一个**同名 txt**(英文提示词),成对放进 `out/<slug>/`。固定机位,之后动画里动起来的只有形态。"),
        code("""
massing_paths = massing.massing_for_regimes(settings.SLUG, color="mono")   # massing_<regime>.jpg
P = prompt_gen.build_all(settings.SLUG)
txt_paths = prompt_gen.write_prompt_files(settings.SLUG, ref_paths=massing_paths, prompts=P)  # massing_<regime>.txt
print("\\nout/%s/ 里成对的文件:" % settings.SLUG)
for r in massing_paths:
    print("  %-20s %s  +  %s" % (r, massing_paths[r].name, txt_paths[r].name))
"""),
        md("看一张参考图(发给 AI 的「结构底」):"),
        code("""
from IPython.display import Image as IPyImage
IPyImage(filename=str(massing_paths["developer_led"]))
"""),
        md("""
## 二、设好 token(真渲染才需要;不设就 dry-run)
**API token 不写进代码**。在终端(或本 notebook 用 `!`)设一次环境变量:
```
export REPLICATE_API_TOKEN=你的token
```
> 安全:token 是凭证,不要贴进代码/notebook/git。没设 token 时下面会自动 **dry-run**(只打印会发什么,不联网、不花钱)。
"""),
        code("""
print("是否已设 REPLICATE_API_TOKEN：", render.has_token())
P = prompt_gen.build_all(settings.SLUG)
"""),
        md("## 三、出图\n`dry_run=True` 先看 payload(离线);设好 token 后改 `dry_run=False` 真渲(每张约 $0.01–0.05)。"),
        code("""
DRY = not render.has_token()      # 有 token 真渲,否则 dry-run
out = render.render(massing_paths["developer_led"], P["developer_led"],
                    slug=settings.SLUG, dry_run=DRY)
print("输出：", out)
"""),
        md("真渲染后,出全部体制(把 `dry_run` 关掉就逐张渲):"),
        code("""
results = render.render_all(massing_paths, P, slug=settings.SLUG, dry_run=DRY)
print("\\n渲染结果：", {k: (str(v) if v else "dry-run") for k, v in results.items()})
"""),
        md("""
## 想手动挑角度 / 出 ControlNet 条件图?用互动画布
命令行出 `out/<slug>/canvas.html`,浏览器打开:体块坐在**真实卫星**上,拖拽找角度、保存角度,
一键导出 **massing / depth / normal / segmentation / canny** 五种图(作 AI 参考图或 ControlNet 条件图)。
```
python run.py canvas            # 出 3 站
python run.py canvas caoyang    # 单站
```
"""),
        md("""
## 诚实边界
- 渲染图是**illustrative**:体块忠实(参考图约束),但外观是 AI 按论述层想象的——不是这座城真实的样子。
- 模型偶尔会偷偷改天际线;negative + fidelity 护栏只是降低概率,出图要肉眼核对体块有没有被篡改。
> 下一本:[`03 过渡动画`] —— 把不同权力的渲染连成过渡。
"""),
    ]
    return notebook(cells)


# NB3 过渡动画
def nb_anim():
    cells = [md("""
# 03 过渡动画:让权力"连续地"改写城市
三种由诚实到顺滑的过渡(固定机位贯穿——相机不动,只有形态在动):

- **(A) 算子强度扫描**(最诚实):把一个算子的强度从 0 连续加到满,逐帧出体块,每一帧都是**真算子输出**,动画就是"权力之手"在连续施加。离线可跑。
- **(B) 渲染图交叉溶解**:把各权力的 AI 渲染图溶解串场(中间是像素混合)。
- **(C) AI 图生视频补间**:相邻两张当首/末帧,交给 Replicate 视频模型补间(最顺滑,中间由 AI 想象,illustrative)。
""")]
    cells += _preamble()
    cells += [
        md("## (A) 算子强度扫描 —— 离线、最诚实\n把 `slim`(塔化)从 0 加到满,看针塔怎么连续长出来。可换 `densify / concentrate / level`。"),
        code("""
frames = animate.param_sweep(settings.SLUG, op="slim", frames=14, gif=True)
print("帧数：", len(frames))
"""),
        md("放出 gif(来回播):"),
        code("""
from IPython.display import Image as IPyImage
IPyImage(filename=str(animate.OUT / settings.SLUG / "sweep_slim.gif"))
"""),
        md("""
## (B) 渲染图交叉溶解
把 02 渲好的各权力渲染图溶解串场。需先在 02 真渲出图(否则这里没图可溶)。
"""),
        code("""
import glob
renders = sorted(glob.glob(str(animate.OUT / settings.SLUG / "render_*.png")))
if len(renders) >= 2:
    animate.crossfade(renders, animate.OUT / settings.SLUG / "crossfade.gif")
else:
    print("还没有渲染图(先在 02 设 token 真渲)。这里用体块参考图演示溶解：")
    import glob as _g
    ms = sorted(_g.glob(str(animate.OUT / settings.SLUG / "massing_*.jpg")))
    animate.crossfade(ms, animate.OUT / settings.SLUG / "crossfade_massing.gif")
"""),
        md("""
## (C) AI 图生视频补间(说明)
最顺滑,但中间由 AI 想象(可能飘镜头/造楼),标 illustrative。需 token。看用法:
"""),
        code("""
animate.ai_video_hint(
    animate.OUT / settings.SLUG / "render_current.png",
    animate.OUT / settings.SLUG / "render_developer_led.png")
"""),
        md("""
## 小结 & 诚实边界
- **(A)** 每帧是真算子输出,动画忠实表达"权力连续施加",首选当骨架。
- **(B)/(C)** 是观感润色:溶解是像素混合,AI 补间是想象的中间态——都标 illustrative。
- 固定机位是诚实性的关键:相机不动,画面里动的只有形态 = 纯权力信号。
> 想接 05 的算子动画线(`power_to_form/anim_sh`),(A) 的逐帧体块可直接喂同一套合成。
"""),
    ]
    return notebook(cells)


NOTEBOOKS = {
    "01_提示词生成器": nb_prompt,
    "02_体块到影像": nb_render,
    "03_过渡动画": nb_anim,
}


def main():
    from opencc import OpenCC
    cc = OpenCC("s2t")
    for name, fn in NOTEBOOKS.items():
        nb = fn()
        (ROOT / (name + ".ipynb")).write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
        tc_name = cc.convert(name)
        tc = {**nb, "cells": [{**c, "source": [cc.convert(l) for l in c["source"]]} for c in nb["cells"]]}
        (ROOT / (tc_name + ".ipynb")).write_text(json.dumps(tc, ensure_ascii=False, indent=1), encoding="utf-8")
        print("写出:", name, "+", tc_name)


if __name__ == "__main__":
    main()
