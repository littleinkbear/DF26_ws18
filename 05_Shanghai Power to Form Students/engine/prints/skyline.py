"""prints for 03 城市天際線 —— 站點摘要 / 可選步驟略過 / 可用情景 / OBJ 寫檔回報。"""
import config
import common
from ._base import _say


def headline(df):
    """站點一行摘要:名稱 · 棟數 · 最高。"""
    _say("%s · %d 栋 · 最高 %.0fm" % (config.site_name(), len(df), float(df["height_m"].max())))


def skipped(what, e):
    """某個需聯網/額外套件的步驟失敗時的友善略過(如 step0 卫星)。"""
    _say("跳过%s(没网或缺 contextily):" % what, e)


def scenarios(scen):
    """印可用的權力情景名單(power_scenarios.yaml 的 key)。"""
    _say("可用情景:", list(scen.keys()))


def obj_written(path, nv, nf):
    """common.export_obj() 之後的回報:寫到哪、幾個頂點/面。"""
    _say("OBJ 写到 %s  · verts %d faces %d" % (path.relative_to(common.ROOT), nv, nf))
