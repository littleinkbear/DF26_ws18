#!/usr/bin/env python
"""06 入口:把 05 的权力形态体块变成 AI 渲染影像与过渡动画。改设定编辑 config.yaml。
用法:run.py [slug] | canvas/report [slug...] | bridge <slug> <dir> | notebooks。
无参数=REPORT_SITES 全部出 canvas+report+index。"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "engine"))         # 让 import 找到 engine

try:                                              # Windows cp950 打印中文会崩,强制 utf-8
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main(argv):
    import settings
    import build_canvas
    import build_report

    # 无参数:全部站点 canvas+report+目录页
    if not argv:
        sites = settings.REPORT_SITES
        for s in sites:
            build_report.build(s)                 # build() 先出 canvas 再 report
        build_report.build_index(sites, None)
        return

    cmd = argv[0]
    rest = argv[1:]

    if cmd == "canvas":
        for s in (rest or settings.REPORT_SITES):
            build_canvas.build(s)
    elif cmd == "report":
        for s in (rest or settings.REPORT_SITES):
            build_report.build(s)
    elif cmd == "context":
        # 重建周边语境体量 data/<slug>/context.parquet(需 05 config.DATASET_ROOT 指向原始数据集)。
        # 宽度取 config.yaml 的 context_margin_m。改完重跑 canvas 生效。
        import ws05
        margin = getattr(settings, "CONTEXT_MARGIN_M", 800)
        for s in (rest or settings.REPORT_SITES):
            ws05.use_site(s)
            ws05.C.build_context(s, margin_m=margin)
    elif cmd == "bridge":
        if len(rest) < 2:
            sys.exit("用法:python run.py bridge <slug> <05的Step_05目录>")
        build_report.build_bridge_index(rest[0], rest[1])
    elif cmd == "notebooks":
        import _build_notebooks
        _build_notebooks.main()
    else:
        # 单个 slug:该站 canvas+report
        build_report.build(cmd)


if __name__ == "__main__":
    main(sys.argv[1:])
