"""prints for 01 數據:怎麼選、怎麼拼 —— 看一眼數據集狀態 / 拼好的表 / 多源覆蓋率。"""
import config
import common
from ._base import _say


def spine_paths():
    """看 5 個 spine 檔的路徑、以及你機器上有沒有(沒有 = 還沒下數據集,用隨包緩存即可)。"""
    for k, p in common.dataset_paths().items():
        _say("%-4s %s  ->  %s" % (k, "有" if p.exists() else "无", p))
    _say("\nDATASET_ROOT =", config.DATASET_ROOT, " (None = 用随包缓存,离线)")


def prepared(df, source):
    """common.build_or_load() 之後的回報。source='cache' 時提醒是走隨包緩存。"""
    if source == "cache":
        _say("未设 DATASET_ROOT(或数据集不在)→ 用随包缓存。想自己建:见 数据集说明.md")
    _say("拼好了:%d 栋  ·  %s" % (len(df), config.site_name()))


def coverage(df):
    """看一眼多源覆蓋率(euluc/function)+ 前 8 棟的多源欄。"""
    show = [c for c in ["height_m", "euluc", "function", "aoi_type2", "aoi_type1"] if c in df.columns]
    _say("覆盖率:")
    for c in ["euluc", "function"]:
        if c in df.columns:
            _say("  %-9s %.0f%%" % (c, df[c].apply(common._t).ne("").mean() * 100))
    _say("\n样例(前 8 栋的多源列):")
    _say(df[show].head(8).to_string())
