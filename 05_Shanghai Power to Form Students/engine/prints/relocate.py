"""prints for 05 換地方:按街道取 —— 隨包街道目錄 / 切站點回報 / 數據集街道名清單 / 建新緩存回報。"""
import config
import common
from ._base import _say


def sites_catalog():
    """隨包帶緩存的街道目錄(改 config.SLUG 即可離線切)。"""
    _say("随包带缓存的街道(改 config.SLUG 即可切):\n")
    for s in config.SITES:
        mark = "✓缓存在" if (common.DATA / s["slug"] / "buildings.parquet").exists() else "·需建"
        _say("  %-10s %-7s %-12s %s" % (s["slug"], mark, s["name"], s["family"]))
    _say("\n默认主册/报告跑这 3 个代表:", config.REPORT_SITES)


def site_switched(df):
    """切到新站點後的摘要:名稱 · 棟數 / 最高 / 中位 · 角色分布。"""
    h = df["height_m"].astype(float)
    _say("现在是:%s(%s)" % (config.site_name(), config.SLUG))
    _say("  %d 栋 · 最高 %.0fm · 中位 %.0fm" % (len(df), h.max(), h.median()))
    _say("  角色:", df.stakeholder.value_counts().to_dict())


def subdistricts():
    """列出數據集裡所有乡镇街道名(挑新街道用);沒有數據集時給離線建議。"""
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
    """建好新街道緩存並切過去後的回報。"""
    _say("建好并切到:", config.site_name(slug))


def no_dataset():
    """沒有數據集 → 跳過建緩存的提示。"""
    _say("没有数据集 → 跳过建缓存。先用随包的 9 个街道即可(见第一格)。")
