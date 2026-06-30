"""
manifest.py — out/manifest.json 的讀寫(讓 web/index.html「隨時讀取 out 最新一筆」)
=================================================================
out/manifest.json 是 web 前端的單一資料源。兩處會更新它:
  · plots.autosave 每存一張圖 → manifest.bump(slug, step, ts)   (圖清單 + 時間戳,輕量)
  · build_report 出完報告     → manifest.set_report(slug, n, h_max, unknown%)
  · refresh_index.py          → 全掃 out/ 重建(載入 buildings 算完整統計)
所有路徑都相對 out/(web/index.html 以 ../out/ 前綴取用)。fig 失敗永不影響繪圖(呼叫端 try/except)。
"""
import json
import glob
from datetime import datetime
from pathlib import Path
import common


def _path():
    return common.OUT / "manifest.json"


def _load():
    p = _path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"sites": {}}


def _save(d):
    d["generated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    common.OUT.mkdir(parents=True, exist_ok=True)
    _path().write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def _meta(slug):
    """slug → (name, family, n)。name/family 先查 config.SITES;n 讀 data/<slug>/site.yaml。"""
    import config
    name, family = slug, ""
    for s in config.SITES:
        if s["slug"] == slug:
            name, family = s["name"], s.get("family", "")
            break
    else:
        try:
            name = config.site_name(slug)
        except Exception:
            pass
    n = None
    sy = common.DATA / slug / "site.yaml"
    if sy.exists():
        try:
            import yaml
            n = yaml.safe_load(open(sy, encoding="utf-8")).get("n")
        except Exception:
            pass
    return name, family, n


def _rel(p):
    return str(Path(p).relative_to(common.OUT)).replace("\\", "/")


def bump(slug, step, ts):
    """每存一張圖呼叫:重掃該 timestamp 夾的 png,更新該 slug 的最新圖清單 + 時間。輕量、不載 buildings。"""
    d = _load()
    sites = d.setdefault("sites", {})
    name, family, n = _meta(slug)
    tsdir = common.OUT / slug / ("Step_%s" % step) / ts
    figs = sorted(_rel(f) for f in glob.glob(str(tsdir / "*.png")))
    e = sites.setdefault(slug, {})
    e.update(name=name, family=family, step=str(step), updated=ts, figures=figs)
    if n is not None:
        e["n"] = n
    if (common.OUT / slug / "report.html").exists():
        e["report"] = "%s/report.html" % slug
    _save(d)


def set_report(slug, n, h_max, unknown_pct):
    """build_report 出完報告呼叫:補上完整統計 + 報告連結。"""
    d = _load()
    sites = d.setdefault("sites", {})
    name, family, _ = _meta(slug)
    e = sites.setdefault(slug, {})
    e.update(name=name, family=family, n=int(n),
             h_max=round(float(h_max)), unknown_pct=round(float(unknown_pct)),
             report="%s/report.html" % slug)
    _save(d)
