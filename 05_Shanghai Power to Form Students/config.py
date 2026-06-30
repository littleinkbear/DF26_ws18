# config.py —— 学生主要改这里:换站点 / 接自己下载的「上海城市数据集」
# ===========================================================================
# 1) 换站点:把 SLUG 改成下面 SITES 里的某个 slug,存档后在 notebook 重跑「准备」格。
# 2)（可选,进阶）自己建缓存:下载并解压「上海城市数据集」后,把 DATASET_ROOT 指过去,
#    跑「01_怎么选数据」notebook 的建缓存格,就能从原始多源数据**亲手重建** data/<slug>/。
#    不填 DATASET_ROOT 也完全没问题:随包已带 3 站缓存,离线即可跑全部主流程。详见 数据集说明.md。
from pathlib import Path

SLUG = "lujiazui"     # ✏️ 当前站点:改成 SITES 里任一 slug。换地方的完整玩法见「05_换地方-按街道取」notebook。

DATASET_ROOT = None   # ✏️（可选）你解压的「上海城市数据集」根目录(字符串路径),例:
                      #     DATASET_ROOT = "/Users/you/Downloads/上海城市数据集"
                      #   留 None = 用随包缓存(离线)。填了、且数据集在,才会从原始数据建新街道的缓存。

# 随包带缓存的街道(name=乡镇街道层精确名,slug=输出标识,family=形态家族)。改这张表 = 换地方。
# 研究单位是**街道**(乡镇街道多边形),非方框——这是和 04(中心点+半径)的根本不同。详见「05_换地方」notebook。
SITES = [
    # —— 3 个形态家族的代表街道(主册/报告默认跑这 3 个)——
    {"slug": "lujiazui", "name": "陆家嘴街道",     "family": "资本/超高层"},
    {"slug": "caoyang",  "name": "曹杨新村街道",   "family": "单位/工人新村"},
    {"slug": "yuyuan",   "name": "豫园街道",       "family": "居民/里弄石库门"},
    # —— 也随包带缓存,改 SLUG 即可离线切换;想要这 9 个之外的,用数据集按街道名现建 ——
    {"slug": "waitan",    "name": "外滩街道",       "family": "资本/金融遗产"},
    {"slug": "nanjingxi", "name": "南京西路街道",   "family": "资本/商业"},
    {"slug": "kongjiang", "name": "控江路街道",     "family": "单位/工人新村"},
    {"slug": "pengpu",    "name": "彭浦新村街道",   "family": "单位/工人新村"},
    {"slug": "laoximen",  "name": "老西门街道",     "family": "居民/里弄石库门"},
    {"slug": "dapuqiao",  "name": "打浦桥街道",     "family": "居民/里弄+田子坊"},
]

# build_report.py 默认出这 3 站的报告(其余街道可单独 `python3 build_report.py <slug>`)。
REPORT_SITES = ["lujiazui", "caoyang", "yuyuan"]

# ===== 以下自动推导,通常不用改 =====
UTM = 32651   # 上海 UTM 51N(几何度量 / 挤体用米)


def site_name(slug=None):
    """slug → 街道精确名。先查 SITES;查不到再回退读 data/<slug>/site.yaml(让换地方建的新街道也能取名)。"""
    slug = slug or SLUG
    for s in SITES:
        if s["slug"] == slug:
            return s["name"]
    try:
        import yaml
        from pathlib import Path
        return yaml.safe_load(open(Path(__file__).resolve().parent / "data" / slug / "site.yaml", encoding="utf-8"))["name"]
    except Exception:
        raise ValueError("未知 slug:%s(不在 SITES,也没有 data/%s/ 缓存)。见「05_换地方」notebook。" % (slug, slug))
