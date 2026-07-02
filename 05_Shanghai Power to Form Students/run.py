#!/usr/bin/env python
"""
run.py — 05 一键跑完整流程(免开 notebook)
=================================================================
改这 4 份设定(都在本层),再跑本脚本,所有图会按**最新设定**重出一遍:
  config.py             换站点 SLUG / DATASET_ROOT
  shanghai_lookup.yaml  谁算谁的
  power_scenarios.yaml  只调高度的情景
  regimes.yaml          权力体制 = 算子配方

产出 → out/<slug>/<时间戳>/  (图 + city_current.obj + run.log + 设定快照)

用法:
  python run.py                 # 跑 config.py 里的 SLUG
  python run.py waitan yuyuan   # 跑指定站点(可多个)
  python run.py --all           # 跑所有已缓存街道
  python run.py --bridge06      # 跑完再接 06 出 canvas.html / report.html

流程细节都在 engine/(学生不用进)。
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "engine"))
from pipeline import run


def main():
    ap = argparse.ArgumentParser(
        description="按最新 config/YAML 重生成 05 全部图 → out/<slug>/<时间戳>/")
    ap.add_argument("slugs", nargs="*", help="站点 slug(留空 = config.SLUG)")
    ap.add_argument("--all", action="store_true", help="跑所有已缓存街道")
    ap.add_argument("--bridge06", action="store_true", help="跑完再接 06 出 canvas/report")
    args = ap.parse_args()

    results = run(slugs=args.slugs or None, all_sites=args.all, bridge06=args.bridge06)
    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
