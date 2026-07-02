"""
engine/bridge06.py — (可选)把 05 的体块接到 06_AI Render(学生不用进这里)
=================================================================================
链路:05 out/<slug>/<时间戳>/index.html  →  06 canvas.html  ⇄  06 report.html
06 唯一入口 = run.py(设定都在 06 的 config.yaml;程式在 06/engine)。
排错:子进程 stdout/stderr 全部截获;失败时把完整回溯印在下方,并追加写入 out/error_06.log。

对外入口:bridge(slugs=None, run_all=False)。顶层 run.py --bridge06 会调它。
"""
import subprocess
import sys
import os
import traceback
import datetime
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
for _p in (str(ENGINE.parent), str(ENGINE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import config
import common as C

R06 = C.ROOT.parent / "06_AI Render Students"
ERRLOG = C.OUT / "error_06.log"                  # 所有详细错误统一追加到这份日志


def _log_error(title, body):
    """把一段错误(带时间戳与分隔线)追加写入 ERRLOG。"""
    ERRLOG.parent.mkdir(parents=True, exist_ok=True)
    with ERRLOG.open("a", encoding="utf-8") as f:
        f.write("\n" + "=" * 78 + "\n")
        f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {title}\n")
        f.write(body.rstrip() + "\n")


def _run06(*args):
    """跑 06/run.py。成功回 True;失败印出子进程完整 stderr 回溯并写 ERRLOG。"""
    cmd = [sys.executable, "-X", "faulthandler", "run.py", *args]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    r = subprocess.run(cmd, cwd=str(R06), env=env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.stdout.strip():
        print(r.stdout.rstrip())
    if r.returncode == 0:
        if r.stderr.strip():                     # 非致命警告也别吞掉,一并显示
            print("  [stderr]", r.stderr.rstrip())
        return True
    print(f"  ❌ 06 执行失败(exit {r.returncode}):{' '.join(cmd)}")
    print("  ---- 子进程 stderr(完整回溯)----")
    print(r.stderr.rstrip() or "  (stderr 为空)")
    _log_error(f"命令失败 exit={r.returncode}: {' '.join(cmd)}  (cwd={R06})",
               f"--- stdout ---\n{r.stdout}\n--- stderr ---\n{r.stderr}")
    print(f"  📝 详细已写入:{ERRLOG}")
    return False


def _latest_stamp_dir(slug):
    """本站最新一批产物目录。先找 pipeline 布局 out/<slug>/<时间戳>/,
    再回退 notebook 布局 out/<slug>/Step_05/<时间戳>/。找不到回 None。"""
    site = C.OUT / slug
    def _stamps(root):
        return sorted((p for p in root.iterdir() if p.is_dir() and p.name[:1].isdigit()),
                      key=lambda p: p.name) if root.exists() else []
    for root in (site, site / "Step_05"):
        st = _stamps(root)
        if st:
            return st[-1]
    return None


def bridge(slugs=None, run_all=False):
    """把每个站接到 06:出 canvas.html + report.html,并在 05 最新结果目录写「前向链接页」index.html。"""
    if run_all:
        slugs = [p.name for p in C.DATA.iterdir() if (p / "buildings.parquet").exists()]
    else:
        slugs = slugs or [config.SLUG]

    failed = []
    for s in slugs:
        print("== 06 产出:", s, "==")
        try:
            ok = _run06(s)                        # run.py <slug> = 该站 canvas.html + report.html(互链)
            stamp = _latest_stamp_dir(s)          # 05 最新结果目录 → 写 index.html 前向链到 06 canvas / report
            if stamp is not None:
                ok = _run06("bridge", s, str(stamp)) and ok
                print("  ↪ 05 结果页:", (stamp / "index.html").relative_to(C.ROOT))
            cv = R06 / "out" / s / "canvas.html"
            if cv.exists():
                print("  ✅", cv)
            else:
                print("  ⚠ 未生成 canvas.html —— 错误回溯见上方;若是缺依赖:"
                      "pip install -r \"06_AI Render Students/engine/requirements.txt\"")
            if not ok:
                failed.append(s)
        except Exception:
            tb = traceback.format_exc()
            print(f"  ❌ 桥接端异常(site={s}):\n{tb}")
            _log_error(f"桥接端异常 site={s}", tb)
            print(f"  📝 详细已写入:{ERRLOG}")
            failed.append(s)

    if failed:
        print("\n⚠ 失败站点:", ", ".join(failed), "→ 完整错误在", ERRLOG)
    else:
        print("\n入口:打开 05 结果页 <时间戳>/index.html → 一键跳 06 canvas.html / report.html(canvas 与 report 互链)。")
    return not failed
