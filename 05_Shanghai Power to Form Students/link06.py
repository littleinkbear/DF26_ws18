#!/usr/bin/env python
"""
link06.py — 把 run.py 的最新输出接到 06 网站(独立入口,不重跑 05 流程)
=================================================================
先用 run.py 出图,再跑本档,就把「05 最新一批结果」链上 06 的互动网站:
  1) 调 06/run.py <slug>   → 出/更新 06 的 canvas.html + report.html(两者互链)
  2) 调 06/run.py bridge   → 在 05 out/<slug>/<最新时间戳>/ 写 index.html
     (列出本次的图 + 算子序列渐变动画,底部一键跳 06 canvas / report)

入口:打开 out/<slug>/<最新时间戳>/index.html。

用法:
  python link06.py                 # 接 config.py 里的 SLUG
  python link06.py waitan yuyuan   # 接指定站点(可多个)
  python link06.py --all           # 接所有已缓存街道

等价于 run.py --bridge06 的桥接那一段,但**不重跑** 05 流程。
出错时完整回溯印在下方,并写入 out/error_06.log。
首次需装 06 依赖:pip install -r "06_AI Render Students/engine/requirements.txt"
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "engine"))
from bridge06 import bridge


def main():
    ap = argparse.ArgumentParser(description="把 05 最新输出接到 06 canvas.html / report.html")
    ap.add_argument("slugs", nargs="*", help="站点 slug(留空 = config.SLUG)")
    ap.add_argument("--all", action="store_true", help="接所有已缓存街道")
    args = ap.parse_args()

    if not bridge(slugs=args.slugs or None, run_all=args.all):
        sys.exit(1)


if __name__ == "__main__":
    main()
