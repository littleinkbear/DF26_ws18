"""
OSM Urban Geospatial Analysis for Grasshopper / Rhino  —  LOCAL FILE, META-ONLY
==============================================================================
Reads a LOCAL .osm / .xml file (no API) and outputs JSON METADATA only —
no curves, breps, points, or colours.

Theoretical Framework:
  Land Use Classification : Lynch (1960) + APA LBCS
  Urban Morphology        : Moudon (1997), Conzen (1960)  — footprint area
  Space Syntax            : Hillier & Hanson (1984)        — node-degree proxy
  POI Accessibility       : Hansen (1959)                  — gravity proximity

GH COMPONENT INPUTS  (set via ZUI right-click → Inputs):
  osm_file   : str     path to a local .osm / .xml file (Overpass / JOSM export)
  run        : bool    True = parse & analyse

NO GRASSHOPPER / RHINO API. FLAT OUTPUTS ONLY — every *_xyz is a single-level
list[] with all objects concatenated. Rebuild branches downstream by Partitioning
the flat list with the matching *_bcount as branch sizes (Partition List).

GH COMPONENT OUTPUTS  (every *_xyz: flat list[float], no nesting):
  building_meta    list[str]    JSON metadata per building
  building_xyz     list[float]  flat footprint verts, all buildings: x,y,z,x,y,z,...
  building_bcount  list[int]    floats per building — Partition building_xyz by this
  road_meta        list[str]    JSON metadata per road (incl. Space Syntax score)
  road_xyz         list[float]  flat road polyline verts, all roads concatenated
  road_bcount      list[int]    floats per road
  poi_meta         list[str]    JSON metadata per POI (incl. Hansen score)
  poi_xyz          list[float]  flat single points x,y,z, all POIs concatenated
  poi_bcount       list[int]    floats per POI (always 3)
  landuse_meta     list[str]    JSON metadata per landuse/leisure/natural area
  landuse_xyz      list[float]  flat area verts, all areas concatenated
  landuse_bcount   list[int]    floats per landuse

  *_xyz: flat floats, z=0 base. sum(*_bcount) == len(*_xyz).
  *_bcount[i] = verts(object i) * 3. Divide by 3 for point count.
  Buildings extrude by height_m (in meta) downstream.
"""

import json
import math
import xml.etree.ElementTree as ET

# ══════════════════════════════════════════════════════════════════
# INTERNAL DEFAULTS  (formerly GH inputs)
# ══════════════════════════════════════════════════════════════════
origin_lat = None  # auto = file centre
origin_lon = None  # auto = file centre
floor_h = 3.2      # meters per floor (Taiwan building code)

# ══════════════════════════════════════════════════════════════════
# CLASSIFICATION TABLES
# ══════════════════════════════════════════════════════════════════

AMENITY_TO_CATEGORY = {
    "school": "education",
    "university": "education",
    "college": "education",
    "kindergarten": "education",
    "library": "education",
    "language_school": "education",
    "hospital": "healthcare",
    "clinic": "healthcare",
    "pharmacy": "healthcare",
    "dentist": "healthcare",
    "doctors": "healthcare",
    "nursing_home": "healthcare",
    "restaurant": "food",
    "cafe": "food",
    "fast_food": "food",
    "bar": "food",
    "pub": "food",
    "food_court": "food",
    "ice_cream": "food",
    "biergarten": "food",
    "bus_station": "transport",
    "taxi": "transport",
    "bicycle_parking": "transport",
    "parking": "transport",
    "fuel": "transport",
    "car_wash": "transport",
    "bank": "finance",
    "atm": "finance",
    "bureau_de_change": "finance",
    "police": "public",
    "post_office": "public",
    "fire_station": "public",
    "community_centre": "public",
    "townhall": "public",
    "courthouse": "public",
    "embassy": "public",
    "social_facility": "public",
    "place_of_worship": "religious",
    "theatre": "culture",
    "cinema": "culture",
    "arts_centre": "culture",
    "museum": "culture",
    "nightclub": "culture",
}

_LANDUSE_TAG_MAP = {
    "residential": "residential",
    "commercial": "commercial",
    "retail": "retail",
    "industrial": "industrial",
    "education": "education",
    "institutional": "institutional",
    "park": "park",
    "garden": "park",
    "recreation_ground": "leisure",
    "grass": "park",
    "meadow": "park",
    "forest": "park",
    "wood": "park",
    "sports_centre": "leisure",
    "pitch": "leisure",
    "playground": "leisure",
    "swimming_pool": "leisure",
    "parking": "transport",
    "railway": "transport",
    "basin": "park",
    "cemetery": "institutional",
    "allotments": "leisure",
    "farmland": "unknown",
    "water": "park",
    "wetland": "park",
    "beach": "leisure",
    "scrub": "park",
}

# ══════════════════════════════════════════════════════════════════
# COORDINATE CONVERSION  (WGS84 → local Cartesian, metres)
# ══════════════════════════════════════════════════════════════════

_M_PER_DEG_LAT = 111320.0


def latlon_to_xy(lat, lon, ref_lat, ref_lon):
    """Return (x, y) in metres relative to (ref_lat, ref_lon)."""
    y = (lat - ref_lat) * _M_PER_DEG_LAT
    x = (lon - ref_lon) * _M_PER_DEG_LAT * math.cos(math.radians(ref_lat))
    return (x, y)


# ══════════════════════════════════════════════════════════════════
# LOCAL OSM FILE PARSER  (replaces the Overpass API)
# Parses standard OSM XML (.osm) — JOSM / Overpass / overpass-turbo export.
# ══════════════════════════════════════════════════════════════════


def load_osm_file(path):
    """Read a local OSM XML file → {"elements": [...]} (Overpass-JSON shape)."""
    tree = ET.parse(path)
    root = tree.getroot()
    elements = []
    for el in root:
        if el.tag == "node":
            tags = {t.get("k"): t.get("v") for t in el.findall("tag")}
            elements.append(
                {
                    "type": "node",
                    "id": int(el.get("id")),
                    "lat": float(el.get("lat")),
                    "lon": float(el.get("lon")),
                    "tags": tags,
                }
            )
        elif el.tag == "way":
            tags = {t.get("k"): t.get("v") for t in el.findall("tag")}
            nds = [int(nd.get("ref")) for nd in el.findall("nd")]
            elements.append(
                {
                    "type": "way",
                    "id": int(el.get("id")),
                    "nodes": nds,
                    "tags": tags,
                }
            )
        # relations ignored (matches original pipeline)
    return {"elements": elements}


def file_center_latlon(osm):
    """Mean lat/lon of all nodes — used as default origin if none given."""
    lats, lons = [], []
    for el in osm["elements"]:
        if el["type"] == "node":
            lats.append(el["lat"])
            lons.append(el["lon"])
    if not lats:
        return 0.0, 0.0
    return sum(lats) / len(lats), sum(lons) / len(lons)


# ══════════════════════════════════════════════════════════════════
# BUILDING CLASSIFICATION & HEIGHT
# ══════════════════════════════════════════════════════════════════


def classify_building(tags):
    b = tags.get("building", "yes")
    am = tags.get("amenity", "")
    sh = tags.get("shop", "")
    to = tags.get("tourism", "")
    of = tags.get("office", "")

    residential = {
        "apartments",
        "residential",
        "house",
        "detached",
        "semidetached_house",
        "terrace",
        "dormitory",
        "bungalow",
        "cottage",
        "villa",
        "townhouse",
        "static_caravan",
    }
    commercial = {
        "commercial",
        "hotel",
        "hostel",
        "office",
        "supermarket",
        "kiosk",
        "bank",
    }
    industrial = {
        "industrial",
        "warehouse",
        "factory",
        "manufacture",
        "storage_tank",
        "hangar",
        "shed",
        "digester",
    }
    education = {"school", "university", "college", "kindergarten"}
    healthcare = {"hospital", "clinic", "pharmacy"}
    religious = {
        "church",
        "cathedral",
        "mosque",
        "temple",
        "synagogue",
        "chapel",
        "shrine",
    }
    government = {"government", "civic", "public"}
    transport = {"train_station", "bus_station", "ferry_terminal", "transportation"}

    if b in residential:
        return "residential"
    if b in commercial or of or to in ("hotel", "hostel", "guest_house", "motel"):
        return "commercial"
    if sh:
        return "retail"
    if b in industrial:
        return "industrial"
    if b in education or am in ("school", "university", "college", "library"):
        return "education"
    if b in healthcare or am in ("hospital", "clinic", "doctors"):
        return "healthcare"
    if b in religious or am == "place_of_worship":
        return "religious"
    if b in government or am in ("townhall", "police", "fire_station", "courthouse"):
        return "institutional"
    if b in transport or am in ("bus_station",):
        return "transport"
    if b == "retail" or am == "marketplace":
        return "retail"
    try:
        if int(tags.get("building:levels", tags.get("levels", 0))) > 5:
            return "mixed_use"
    except (ValueError, TypeError):
        pass
    return "unknown"


def estimate_height(tags, floor_h):
    """Height: explicit 'height' > 'building:levels' > 'levels' > type default."""
    for key in ("height", "building:height"):
        if key in tags:
            try:
                return float(str(tags[key]).replace("m", "").strip())
            except (ValueError, TypeError):
                pass
    for key in ("building:levels", "levels"):
        if key in tags:
            try:
                return float(tags[key]) * floor_h
            except (ValueError, TypeError):
                pass
    type_defaults = {
        "house": 6.4,
        "detached": 6.4,
        "bungalow": 3.5,
        "apartments": 15.0,
        "commercial": 9.6,
        "retail": 4.8,
        "industrial": 8.0,
        "warehouse": 7.0,
        "school": 9.6,
        "hospital": 15.0,
        "church": 14.0,
        "shed": 3.0,
    }
    return type_defaults.get(tags.get("building", "yes"), floor_h * 2)


# ══════════════════════════════════════════════════════════════════
# POI / AREA CLASSIFICATION
# ══════════════════════════════════════════════════════════════════


def classify_poi(tags):
    am = tags.get("amenity", "")
    sh = tags.get("shop", "")
    to = tags.get("tourism", "")
    le = tags.get("leisure", "")
    of = tags.get("office", "")
    pt = tags.get("public_transport", "")

    if am in AMENITY_TO_CATEGORY:
        return AMENITY_TO_CATEGORY[am]
    if sh:
        return "shop"
    if to:
        return "tourism"
    if le:
        return "leisure"
    if of:
        return "office"
    if pt:
        return "transport"
    return "other"


def classify_area(tags):
    for key in ("landuse", "leisure", "natural", "amenity"):
        val = tags.get(key, "")
        if val in _LANDUSE_TAG_MAP:
            return _LANDUSE_TAG_MAP[val]
    return "unknown"


# ══════════════════════════════════════════════════════════════════
# GEOMETRY MATH  (plain (x, y) tuples — no Rhino geometry objects)
# ══════════════════════════════════════════════════════════════════


def shoelace_area(xy):
    """2-D polygon area via Shoelace formula on (x, y) tuples."""
    n = len(xy)
    if n < 3:
        return 0.0
    a = 0.0
    for i in range(n):
        j = (i + 1) % n
        a += xy[i][0] * xy[j][1] - xy[j][0] * xy[i][1]
    return abs(a) * 0.5


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def flatten_xy(pts, z=0.0):
    """List of (x, y) -> flat [x, y, z, x, y, z, ...] (rounded), z=0 base."""
    flat = []
    for p in pts:
        flat.extend([round(p[0], 3), round(p[1], 3), z])
    return flat


def flatten_branches(staging):
    """List-of-flat-float-lists -> (flat single-level list, list[int] bcount).

    bcount[i] = floats in object i. sum(bcount) == len(flat). Partition the flat
    list by bcount downstream to rebuild per-object branches.
    """
    flat = []
    bcount = []
    for sub in staging:
        flat.extend(sub)
        bcount.append(len(sub))
    return flat, bcount


# ══════════════════════════════════════════════════════════════════
# SPACE SYNTAX  —  Node-degree integration proxy (Hillier & Hanson 1984)
# ══════════════════════════════════════════════════════════════════


def build_node_degree(road_ways):
    degree = {}
    for nids in road_ways:
        for nid in nids:
            degree[nid] = degree.get(nid, 0) + 1
    return degree


def segment_integration(nids, degree):
    if not nids:
        return 0.0
    return sum(degree.get(n, 1) for n in nids) / len(nids)


# ══════════════════════════════════════════════════════════════════
# HANSEN ACCESSIBILITY SCORING  (Hansen 1959, simplified)
# ══════════════════════════════════════════════════════════════════


def poi_accessibility_scores(poi_xy, threshold_m=200.0):
    scores = []
    for i, pi in enumerate(poi_xy):
        score = 0.0
        for j, pj in enumerate(poi_xy):
            if i == j:
                continue
            d = dist(pi, pj)
            if 0 < d <= threshold_m:
                score += 1.0 / (d * d) * 10000.0
        scores.append(round(score, 3))
    return scores


# ══════════════════════════════════════════════════════════════════
# MAIN PIPELINE  (metadata only)
# ══════════════════════════════════════════════════════════════════

building_meta = []
road_meta = []
poi_meta = []
landuse_meta = []

# xyz outputs — plain nested lists. 1 sublist per object, aligned 1:1 with *_meta.
building_xyz = []
road_xyz = []
poi_xyz = []
landuse_xyz = []

# bcount — floats per object. Partition the flat *_xyz by this to rebuild branches.
building_bcount = []
road_bcount = []
poi_bcount = []
landuse_bcount = []

# Nested staging: per object -> flat [x, y, z, ...]
_building_xyz = []
_road_xyz = []
_poi_xyz = []
_landuse_xyz = []

if run and osm_file:
    try:
        fh = float(floor_h) if (floor_h is not None) else 3.2

        # ── 1. Load local OSM file ────────────────────────────────
        osm = load_osm_file(osm_file)
        print("OSM elements loaded: {}".format(len(osm.get("elements", []))))

        # ── 2. Reference origin (given, else file centre) ─────────
        if origin_lat is not None and origin_lon is not None:
            ref_lat, ref_lon = float(origin_lat), float(origin_lon)
        else:
            ref_lat, ref_lon = file_center_latlon(osm)

        # ── 3. Build node → (x, y) lookup ─────────────────────────
        nodes = {}
        for el in osm["elements"]:
            if el["type"] == "node":
                nodes[el["id"]] = latlon_to_xy(el["lat"], el["lon"], ref_lat, ref_lon)

        # ── 4. POI nodes ──────────────────────────────────────────
        poi_xy = []
        for el in osm["elements"]:
            if el["type"] != "node":
                continue
            tags = el.get("tags", {})
            if not any(
                k in tags
                for k in (
                    "amenity",
                    "shop",
                    "tourism",
                    "leisure",
                    "office",
                    "historic",
                    "public_transport",
                )
            ):
                continue
            xy = nodes.get(el["id"]) or latlon_to_xy(
                el["lat"], el["lon"], ref_lat, ref_lon
            )
            cat = classify_poi(tags)
            poi_xy.append(xy)
            _poi_xyz.append(flatten_xy([xy]))  # single point: x, y, 0
            poi_meta.append(
                json.dumps(
                    {
                        "category": cat,
                        "name": tags.get("name", ""),
                        "amenity": tags.get("amenity", ""),
                        "shop": tags.get("shop", ""),
                        "tourism": tags.get("tourism", ""),
                    },
                    ensure_ascii=False,
                )
            )

        # ── 5. Road topology for Space Syntax ─────────────────────
        road_node_lists = [
            el.get("nodes", [])
            for el in osm["elements"]
            if el["type"] == "way" and "highway" in el.get("tags", {})
        ]
        node_degree = build_node_degree(road_node_lists)
        max_degree = max(node_degree.values()) if node_degree else 1

        # ── 6. Process all Ways ───────────────────────────────────
        skip_hw = {
            "proposed",
            "construction",
            "bus_stop",
            "crossing",
            "give_way",
            "stop",
            "traffic_signals",
            "turning_circle",
        }

        for el in osm["elements"]:
            if el["type"] != "way":
                continue
            tags = el.get("tags", {})
            nids = el.get("nodes", [])
            pts = [nodes[n] for n in nids if n in nodes]

            if len(pts) < 2:
                continue

            # ─ ROADS ─
            if "highway" in tags:
                hw = tags.get("highway", "unclassified")
                if hw in skip_hw:
                    continue
                integ_raw = segment_integration(nids, node_degree)
                integ_norm = round(integ_raw / max_degree, 3) if max_degree > 0 else 0
                _road_xyz.append(flatten_xy(pts))  # polyline verts: x,y,0,...
                road_meta.append(
                    json.dumps(
                        {
                            "highway": hw,
                            "name": tags.get("name", ""),
                            "maxspeed": tags.get("maxspeed", ""),
                            "lanes": tags.get("lanes", ""),
                            "oneway": tags.get("oneway", "no"),
                            "surface": tags.get("surface", ""),
                            "integration": integ_norm,
                            "note": "integration: Space Syntax local connectivity proxy (Hillier 1984)",
                        },
                        ensure_ascii=False,
                    )
                )

            # ─ BUILDINGS ─
            elif "building" in tags:
                if len(pts) < 3:
                    continue
                lu = classify_building(tags)
                height = estimate_height(tags, fh)
                footarea = shoelace_area(pts)
                # Footprint vertices flattened: x,y,z,x,y,z,... (z=0 base)
                _building_xyz.append(flatten_xy(pts))
                building_meta.append(
                    json.dumps(
                        {
                            "land_use": lu,
                            "height_m": round(height, 1),
                            "footprint_m2": round(footarea, 1),
                            "name": tags.get("name", ""),
                            "levels": tags.get(
                                "building:levels", tags.get("levels", "")
                            ),
                            "addr_street": tags.get("addr:street", ""),
                            "addr_housen": tags.get("addr:housenumber", ""),
                            "building_tag": tags.get("building", "yes"),
                        },
                        ensure_ascii=False,
                    )
                )

            # ─ LANDUSE / LEISURE / NATURAL AREAS ─
            elif any(k in tags for k in ("landuse", "leisure", "natural", "amenity")):
                if len(pts) < 3:
                    continue
                lu = classify_area(tags)
                _landuse_xyz.append(flatten_xy(pts))  # polygon verts: x,y,0,...
                raw_tag = (
                    tags.get("landuse")
                    or tags.get("leisure")
                    or tags.get("natural")
                    or tags.get("amenity", "")
                )
                landuse_meta.append(
                    json.dumps(
                        {
                            "category": lu,
                            "osm_tag": raw_tag,
                            "name": tags.get("name", ""),
                            "area_m2": round(shoelace_area(pts), 1),
                        },
                        ensure_ascii=False,
                    )
                )

        # ── 7. Hansen accessibility scores → into poi_meta ────────
        acc_scores = poi_accessibility_scores(poi_xy)
        for i, score in enumerate(acc_scores):
            d = json.loads(poi_meta[i])
            d["accessibility_score"] = score
            d["note"] = "Hansen (1959) gravity proximity score"
            poi_meta[i] = json.dumps(d, ensure_ascii=False)

        # ── 8. xyz outputs — flat single-level list, no nesting ──
        # All objects concatenated: x,y,z,x,y,z,... ; *_bcount = floats per object.
        building_xyz, building_bcount = flatten_branches(_building_xyz)
        road_xyz, road_bcount = flatten_branches(_road_xyz)
        poi_xyz, poi_bcount = flatten_branches(_poi_xyz)
        landuse_xyz, landuse_bcount = flatten_branches(_landuse_xyz)

        print(
            "OK. Buildings: {}  Roads: {}  POIs: {}  Areas: {}".format(
                len(building_meta), len(road_meta), len(poi_meta), len(landuse_meta)
            )
        )

    except Exception as exc:
        import traceback

        print("ERROR: {}\n{}".format(exc, traceback.format_exc()))
else:
    print("Waiting: connect osm_file and set run=True")
