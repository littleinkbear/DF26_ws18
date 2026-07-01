"""
render.py 调 Replicate:体块参考图(结构)+ 提示词(表面)生成 AI 渲染影像,存到 out/<slug>/。
API token 从环境变量 REPLICATE_API_TOKEN 读,绝不硬编码;dry_run=True 只打印 payload 不联网。
MODEL_ADAPTERS 兜住不同模型入参:nano-banana {prompt,image_input:[图]} / flux-kontext {prompt,input_image:图}。
"""
import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:                  # 找得到 07 根的 settings.py
    sys.path.insert(0, str(ROOT))
import settings

OUT = ROOT / "out"


def _file(path):
    return open(path, "rb")


# 模型到入参构造
MODEL_ADAPTERS = {
    "google/nano-banana": lambda img, prompt, neg: {"prompt": prompt, "image_input": [_file(img)]},
    "black-forest-labs/flux-kontext": lambda img, prompt, neg: {
        "prompt": prompt, "input_image": _file(img), "output_format": "png"},
}


def _adapt(model, img, prompt, neg):
    for key, fn in MODEL_ADAPTERS.items():
        if model.startswith(key):
            return fn(img, prompt, neg)
    # 未登记模型:通用猜测(prompt+image)
    print("  未登记的模型 %s,用通用入参(prompt+image_input);如报错请在 MODEL_ADAPTERS 加适配。" % model)
    return {"prompt": prompt, "image_input": [_file(img)]}


def has_token():
    return bool(os.environ.get("REPLICATE_API_TOKEN"))


def render(image_path, prompt_dict, slug=None, model=None, dry_run=False, suffix=""):
    """参考图 + 提示词生成渲染图。
    image_path: massing 参考图;prompt_dict: prompt_gen 输出。
    dry_run 或无 token 只打印 payload。返回 PNG 路径(dry_run 返回 None)。"""
    slug = slug or settings.SLUG
    model = model or settings.MODEL
    prompt = prompt_dict["prompt"]; neg = prompt_dict.get("negative", "")
    regime = prompt_dict.get("regime", "out")

    if dry_run or not has_token():
        print("【dry-run%s】model=%s" % ("" if dry_run else "(未设 REPLICATE_API_TOKEN)", model))
        print("  参考图:", Path(image_path).relative_to(ROOT) if str(ROOT) in str(image_path) else image_path)
        print("  prompt:", prompt)
        print("  negative:", neg)
        print("  设好 token 且 dry_run=False 即真渲。export REPLICATE_API_TOKEN=...(见 README)")
        return None

    import replicate     # 仅真跑时才需要
    payload = _adapt(model, image_path, prompt, neg)
    out = replicate.run(model, input=payload)
    # replicate 返回可能是 url 列表或 FileOutput
    data = out[0] if isinstance(out, (list, tuple)) else out
    dst = OUT / slug / ("render_%s%s.png" % (regime, suffix))
    dst.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(data, "read"):
        dst.write_bytes(data.read())
    else:
        import urllib.request
        urllib.request.urlretrieve(str(data), dst)
    print("  渲染图 %s" % dst.relative_to(ROOT))
    return dst


def render_all(massing_paths, prompts, slug=None, model=None, dry_run=False):
    """对一组 {regime: 参考图} + {regime: prompt_dict} 逐个渲。返回 {regime: 输出路径}。"""
    out = {}
    for regime, img in massing_paths.items():
        print("【%s】" % regime)
        out[regime] = render(img, prompts[regime], slug=slug, model=model, dry_run=dry_run)
    return out


if __name__ == "__main__":
    # 自测:dry-run 出 developer_led 的 payload
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import prompt_gen, massing
    slug = sys.argv[1] if len(sys.argv) > 1 else settings.SLUG
    P = prompt_gen.build_all(slug, ["developer_led"])
    m = massing.massing_for_regimes(slug, ["developer_led"])
    render(m["developer_led"], P["developer_led"], slug=slug, dry_run=True)
