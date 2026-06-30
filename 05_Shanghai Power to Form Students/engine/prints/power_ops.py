"""prints for 04 進階:權力算子 —— 算子詞彙 / 體制配方 / 形態指紋 / 自訂算子登記確認。
（檔名 power_ops 避免和 engine/operators.py 混淆;函式內才 import operators 模型層。)"""
import config
from ._base import _say


def vocab(recs):
    """站點 + 棟數 + 9 個算子的詞彙表(power 對 form 的『動詞』)。"""
    import operators as ops
    _say("%s · %d 栋。算子词汇:" % (config.site_name(), len(recs)))
    _say("  ", list(ops.OPS.keys()))


def regimes(regs=None):
    """印 regimes.yaml:每種權力體制的形態指紋 + 算子配方(按序串起的動詞)。"""
    import operators as ops
    regs = regs or ops.load_regimes()
    for name, r in regs.items():
        _say("【%s】%s" % (r["label"], r["fingerprint"]))
        _say("   配方:", " → ".join(s["op"] for s in r["steps"]))


def fingerprints(rows, labels=None):
    """印 measure.compare() 的形態指紋表(瘦長 / 高度CV / 重心集中 / 棟數)。"""
    labels = labels or {}
    for n, m in rows.items():
        _say("  %-20s 瘦长 %.2f · 高度CV %.2f · 重心集中 %.2f · 栋数 %d" %
             (labels.get(n, n), m["slender"], m["h_cv"], m["concentration"], m["n"]))


def registered(name):
    """確認自訂算子已登記進 OPS(和內建 9 個平權)。"""
    import operators as ops
    _say("现在 OPS 里多了:", name in ops.OPS)
