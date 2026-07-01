"""prints for 05 换地方:按街道取 —— 随包街道目录 / 切站点回报 / 数据集街道名清单 / 建新缓存回报。"""
import config
import common
from ._base import _say


def sites_catalog():
    """随包带缓存的街道目录(改 config.SLUG 即可离线切)。"""
    _say("随包带缓存的街道(改 config.SLUG 即可切):\n")
    for s in config.SITES:
        mark = "有缓存" if (common.DATA / s["slug"] / "buildings.parquet").exists() else "需现建"
        _say("  %-10s %-7s %-12s %s" % (s["slug"], mark, s["name"], s["family"]))
    _say("\n默认主册/报告跑这 3 个代表:", config.REPORT_SITES)


def site_switched(df):
    """切到新站点后的摘要:名称 · 栋数 / 最高 / 中位 · 角色分布。"""
    h = df["height_m"].astype(float)
    _say("现在是:%s(%s)" % (config.site_name(), config.SLUG))
    _say("  %d 栋 · 最高 %.0fm · 中位 %.0fm" % (len(df), h.max(), h.median()))
    _say("  角色:", df.stakeholder.value_counts().to_dict())


def subdistricts():
    """列出数据集里所有乡镇街道名(挑新街道用);没有数据集时给离线建议。"""
    names = common.subdistrict_names()
    if not names:
        _say("未设 DATASET_ROOT(或数据集不在)→ 这步需要数据集。")
        _say("→ 没有数据集也没关系:上面随包 9 个街道足够练全套流程。")
        _say("→ 想要别的街道:下载数据集、在 config.py 设 DATASET_ROOT,见 数据集说明.md。")
        return
    _say("数据集里共 %d 个乡镇街道。含『新村』的(工人新村家族)示例:" % len(names))
    _say("  ", [n for n in names if "新村" in n][:12])
    _say("含『路』的示例:", [n for n in names if n.endswith("路街道")][:8])


def built_switched(slug):
    """建好新街道缓存并切过去后的回报。"""
    _say("建好并切到:", config.site_name(slug))


def no_dataset():
    """没有数据集 → 跳过建缓存的提示。"""
    _say("没有数据集 → 跳过建缓存。先用随包的 9 个街道即可(见第一格)。")
