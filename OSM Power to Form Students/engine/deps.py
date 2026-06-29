"""
deps.py — 缺套件就裝(冪等)
=================================================================
換地方(在 config.py 填 LAT/LON)會 live 抓那塊 OSM,缺 osmnx 就會報錯。
這支冪等:已裝就跳過,新環境 Run All 自動補齊,不必再去終端手動 pip。
預設大巴窯(離線)其實用不到 osmnx,但裝上不礙事。
"""
import importlib.util
import subprocess
import sys


def _ensure(pkg, mod=None, optional=False):
    """缺就 pip 裝、已裝就跳過。optional=True 時失敗只警告不丟錯。"""
    if importlib.util.find_spec(mod or pkg) is None:
        try:
            print("⏳ 安裝 / installing %s …" % pkg)
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=True)
            print("   ✓ 裝好 / installed", pkg)
        except Exception as e:
            if optional:
                print("  (可選,跳過 / optional, skipped:", pkg, "—", e, ")")
            else:
                raise
    else:
        print("✓ 已裝 / present:", pkg)


def ensure():
    """裝齊整條管線會用到的套件。"""
    _ensure("osmnx")                              # 換地方 live 抓 OSM 必需
    for p in ("contextily", "pyproj"):            # Step 0 衛星底圖用,失敗不影響 Step 1–5
        _ensure(p, optional=True)
    print("依賴就緒 / deps ready —— 換地方(改 config.py 的 LAT/LON)也不會再報缺 osmnx。")
