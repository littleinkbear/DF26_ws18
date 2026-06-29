"""
geo.py — 換地方的座標小工具(教學預覽用)
=================================================================
這些公式與 config.py 完全一致(同源,不重複維護):中心點 LAT/LON + 半徑
→ BBOX=(W,S,E,N) 與 UTM EPSG。換地方前可先 preview 看範圍,確認再去改 config.py。
"""
import math


def utm_epsg(lon, lat):
    """該點的 UTM EPSG:北半球 326xx、南半球 327xx。"""
    zone = int((lon + 180) // 6) + 1
    return (32600 if lat >= 0 else 32700) + zone


def bbox_utm(lat, lon, radius_m=1200):
    """中心點 (lat, lon) + 半徑(米)→ (BBOX=(W,S,E,N), UTM EPSG)。"""
    dlat = radius_m / 111320.0
    dlon = radius_m / (111320.0 * math.cos(math.radians(lat)))
    bbox = (lon - dlon, lat - dlat, lon + dlon, lat + dlat)
    return bbox, utm_epsg(lon, lat)


def preview(lat, lon, radius_m=1200, place="(未命名)"):
    """印出 config.py 會自動算出的同樣 BBOX/UTM;回傳 (bbox, utm)。"""
    bbox, utm = bbox_utm(lat, lon, radius_m)
    print("預覽(config.py 會自動算出同樣的值)/ preview:")
    print("  PLACE              =", place, "  ← 填進 config.py 的 PLACE")
    print("  LAT, LON, RADIUS_M =", lat, lon, radius_m, "  ← 填進 config.py 這三個值")
    print("  → BBOX =", tuple(round(v, 6) for v in bbox))
    print("  → UTM  =", utm)
    return bbox, utm
