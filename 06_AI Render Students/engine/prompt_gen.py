"""
prompt_gen.py 提示词生成器:从权力体制自动出 AI 渲染提示词。
computed 层为 05 算出的数字(诚实);argued 层为 prompts.yaml 写的外观论述(可改)。
纯本地拼字符串,不联网。
"""
import yaml
from pathlib import Path
import ws05            # 05 引擎桥
import settings

ROOT = Path(__file__).resolve().parent.parent


def load_prompts(path=None):
    """论述层提示词。默认读 settings.PROMPTS;传 path 则读该 yaml。"""
    if path is not None:
        return yaml.safe_load(open(path, encoding="utf-8"))
    return settings.PROMPTS


def _fingerprint_words(m):
    """把 05 指标翻成一句计算层英文。"""
    n = m["n"]; hmax = m["h_max"]; hmean = m["h_mean"]; slender = m["slender"]; cv = m["h_cv"]
    bits = ["approximately %d buildings" % n]
    if hmax >= 250:
        bits.append("supertall towers up to ~%d m" % round(hmax))
    elif hmax >= 100:
        bits.append("high-rises up to ~%d m" % round(hmax))
    else:
        bits.append("low- to mid-rise up to ~%d m" % round(hmax))
    bits.append("average height ~%d m" % round(hmean))
    if slender >= 4:
        bits.append("very slender tower profiles")
    elif slender >= 2:
        bits.append("slender profiles")
    if cv >= 1.2:
        bits.append("a single dominant peak (high height contrast)")
    elif cv <= 0.45:
        bits.append("an even, uniform skyline (low height contrast)")
    return ", ".join(bits)


def metrics_for(slug=None, regimes=None):
    """对各体制算 05 形态指纹。返回 {regime: metrics_dict}。"""
    slug = slug or settings.SLUG
    rr, _ = ws05.regime_recs(slug, regimes)
    return {name: ws05.M.diagnose(recs, slug) for name, recs in rr.items()}, rr


def build_prompt(slug, regime, metrics=None, P=None, regs=None):
    """生成某站点某体制的提示词。返回 dict:prompt, negative, computed, argued, label。"""
    P = P or load_prompts()
    if metrics is None:
        rr, _ = ws05.regime_recs(slug, [regime])
        metrics = ws05.M.diagnose(rr[regime], slug)
    regs = regs if regs is not None else ws05.ops.load_regimes(ws05.WS05 / "regimes.yaml")
    label = ws05.regime_label(regs, regime)

    site_ctx = P.get("sites", {}).get(slug) or P.get("sites", {}).get("default", "a city district")
    computed = _fingerprint_words(metrics)                                   # 计算层
    argued = P["regimes"].get(regime, P["regimes"].get("current", {})).get("look", "")  # 论述层
    base = P["base"]

    prompt = (
        "%s of %s. "                       # 视角 站点
        "Structure (from the reference image): %s. "   # 计算层
        "Appearance: %s. "                 # 论述层
        "%s. %s. %s"                       # 风格 保真 画质
        % (base["view"], site_ctx, computed, argued,
           base["render_style"], base["fidelity"], base["quality"])
    )
    return {"regime": regime, "label": label, "prompt": prompt,
            "negative": P.get("negative", ""), "computed": computed, "argued": argued}


def build_all(slug=None, regimes=None):
    """一次出所有体制的提示词。返回 {regime: prompt_dict}。"""
    slug = slug or settings.SLUG
    regimes = regimes or settings.REGIMES
    P = load_prompts()
    mets, _ = metrics_for(slug, regimes)
    regs = ws05.ops.load_regimes(ws05.WS05 / "regimes.yaml")
    return {r: build_prompt(slug, r, metrics=mets[r], P=P, regs=regs) for r in regimes}


def write_prompt_files(slug=None, regimes=None, ref_paths=None, prompts=None):
    """英文提示词写进 out/<slug>/,文件名与参考图同名。
    ref_paths: {regime: 参考图路径};没有则默认 massing_<regime>。返回 {regime: txt路径}。"""
    from pathlib import Path as _P
    slug = slug or settings.SLUG
    prompts = prompts or build_all(slug, regimes)
    d = ROOT / "out" / slug
    d.mkdir(parents=True, exist_ok=True)
    out = {}
    for regime, dct in prompts.items():
        stem = _P(ref_paths[regime]).stem if (ref_paths and regime in ref_paths) else ("massing_%s" % regime)
        txt = d / (stem + ".txt")
        txt.write_text(dct["prompt"].strip() + "\n", encoding="utf-8")
        out[regime] = txt
        print("  -> %s" % txt.relative_to(ROOT))
    return out


if __name__ == "__main__":
    import sys
    slug = sys.argv[1] if len(sys.argv) > 1 else settings.SLUG
    allp = build_all(slug)
    print("== 提示词生成器自测:%s ==\n" % slug)
    for r, d in allp.items():
        print("【%s】%s" % (d["label"], r))
        print("  [计算层] " + d["computed"])
        print("  [论述层] " + d["argued"])
        print("  prompt: " + d["prompt"][:200] + ("…" if len(d["prompt"]) > 200 else ""))
        print()
