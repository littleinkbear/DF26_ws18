"""
my_operator.py —— 你的算子练习场(复制粘贴模板 + 一个可跑的例子)
=================================================================
配套「算子替换指南.md」。这里放一个**已经能跑**的自定义算子 `taper`,你照着改即可。
用法(在进阶 notebook 里):

    import operators as ops
    import my_operator                      # 导入本文件
    ops.register("taper", my_operator.taper)   # 登记,和内置 9 个算子平权
    # 然后就能写进 regimes.yaml 的 steps:  {op: taper, target: [resident, developer], keep: 0.7}

算子契约(详见 算子替换指南.md):
  recs = [{geom, h, sh, frozen}, ...]  几何单位=米(EPSG:32651);GFA ∝ geom.area × h。
  纯函数:别改原始 recs,先复制再改,返回新列表。
"""
import shapely.affinity as aff   # 算子只需要 shapely;要用 common 的工具时在函数里再 import


def taper(recs, target, keep=0.7, cap_m=300.0):
    """示例算子「收分塔」:把目标楼 footprint 缩到 keep 面积、高度按 1/keep 补偿(单栋 GFA 守恒)→ 更细更高,封顶 cap_m。
    （这其实就是 slim 的一个变体,留作你改写的起点。）"""
    out = [dict(r) for r in recs]                       # ① 复制,别动原始
    f = max(keep, 1e-3) ** 0.5                          #   面积比 → 线性缩放比
    for r in out:
        if r["sh"] in target and not r.get("frozen"):   # ② 只动目标、未冻结
            r["geom"] = aff.scale(r["geom"], xfact=f, yfact=f, origin="centroid")  # ③ 缩 footprint
            r["h"] = min(r["h"] / max(keep, 1e-3), cap_m)                          #    补高度、封顶
    return out


# ---------- 你的算子从这里开始:复制上面的 taper,改名 + 改第 ③ 步 ----------
def my_op(recs, target, amount=1.5):
    """TODO：换成你的形态操作。下面默认只抬高度(加 GFA),你可以改成旋转 / 缩放 / 拆分……"""
    out = [dict(r) for r in recs]
    for r in out:
        if r["sh"] in target and not r.get("frozen"):
            r["h"] = r["h"] * amount
            # r["geom"] = aff.rotate(r["geom"], 20, origin="centroid")   # 例:旋转
    return out


if __name__ == "__main__":
    # 自测:对当前站点跑一下 taper,打印 before/after 的平均高与栋数
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))  # 让独立执行也找得到 config.py
    import config, common as C, operators as ops
    df = C.assign_all(C.current_buildings(config.SLUG))
    recs = C.to_recs(df)
    after = taper(recs, target=["resident", "developer"], keep=0.6)
    import numpy as np
    print("taper 自测 OK | before 平均高 %.1f → after %.1f | 栋数 %d→%d" % (
        np.mean([r["h"] for r in recs]), np.mean([r["h"] for r in after]), len(recs), len(after)))
