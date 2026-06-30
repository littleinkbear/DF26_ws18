"""
refresh_index.py — 全掃 out/,重建 out/manifest.json(web/index.html 的資料源)。
=================================================================
notebook 存圖時會自動更新 manifest(plots.autosave);build_report 出報告也會更新。
這支是「手動全掃重建」:把 out/ 裡每個站點的最新一筆圖 + 完整統計(載入 buildings 算
最高/unknown%)+ 報告連結,一次寫齊。換句話說:跑完任何輸出後,跑這支就同步好首頁。
    python refresh_index.py
"""
import sys, os, glob
# 本脚本现位于 engine/。HERE=engine（取 common/manifest）；其父=05 根（取 config + out/）。
_HERE = os.path.dirname(os.path.abspath(__file__)); _ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE); sys.path.insert(0, _ROOT)
os.chdir(_ROOT)   # out/ 等相对路径解析到 05 根；任意目录下 `python engine/refresh_index.py` 都可
import warnings; warnings.filterwarnings("ignore")
import config
import common as C
import manifest


def newest_step(slug_dir):
    """該站點最新一筆圖:挑 mtime 最新的 Step_*/<ts> 夾,回傳 (step, ts) 或 None。"""
    best = None
    for ts_dir in glob.glob(os.path.join(slug_dir, "Step_*", "*")):
        if not os.path.isdir(ts_dir):
            continue
        step = os.path.basename(os.path.dirname(ts_dir)).replace("Step_", "")
        ts = os.path.basename(ts_dir)
        m = os.path.getmtime(ts_dir)
        if best is None or m > best[0]:
            best = (m, step, ts)
    return (best[1], best[2]) if best else None


def main():
    out = str(C.OUT)
    mp = os.path.join(out, "manifest.json")
    if os.path.exists(mp):
        os.remove(mp)                            # 全扫重建:先清掉旧的,避免残留已删站点/连结
    slugs = sorted(os.path.basename(p) for p in glob.glob(os.path.join(out, "*")) if os.path.isdir(p))
    if not slugs:
        print("out/ 目前没有任何站点输出。先跑 notebook 或 build_report。")
        manifest._save({"sites": {}})
        return
    done = 0
    for slug in slugs:
        sd = os.path.join(out, slug)
        ns = newest_step(sd)
        if ns:                                   # 有 notebook 存的图 → 记最新一笔 + 图清单
            manifest.bump(slug, ns[0], ns[1])
        # 完整统计(需要 data/<slug> 缓存才载得动 buildings)
        try:
            df = C.assign_all(C.load_buildings(slug))
            h = df["height_m"].astype(float)
            manifest.set_report(slug, len(df), h.max(), (df.stakeholder == "unknown").mean() * 100)
        except Exception:
            pass                                 # 没缓存就只留图清单,不强求统计
        if ns or os.path.exists(os.path.join(sd, "report.html")):
            done += 1
            print("  ✓ %s" % slug)
    print("写了:", os.path.join(out, "manifest.json"), "(%d 站)" % done)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
