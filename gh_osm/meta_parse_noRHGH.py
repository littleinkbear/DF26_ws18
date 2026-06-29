"""
Metadata Parser for Grasshopper / Rhino  —  generic JSON-meta reader
====================================================================
Parses ANY list of JSON metadata strings (building_meta / road_meta /
poi_meta / landuse_meta — or any JSON dict string) and unpacks keys &
values. Optional key filter. No geometry.

GH COMPONENT INPUTS  (set via ZUI right-click → Inputs):
  metadata    list[str]   JSON dict strings, 1 per object (the *_meta output)
  filter_key  list[str]   keys to keep (str or list). Empty/None = all keys.

NO GRASSHOPPER API. All outputs are plain Python lists (nested for keys/values).
Rebuild the DataTree yourself downstream with native GH components, using
branch_count to set branch sizes (e.g. Partition List).

FLAT OUTPUTS ONLY. keys/values are single-level list[] (all objects concatenated).
Use branch_count to regroup downstream (Partition List with branch_count as size).

GH COMPONENT OUTPUTS  (all flat list[], no nesting):
  all_keys      list[str]   union of every key seen, across all objects (sorted)
  keys          list[str]   flat: every object's filtered keys, concatenated
  values        list        flat: every object's filtered values, concatenated
  branch_count  list[int]   items per object — Partition keys/values by this to regroup

  sum(branch_count) == len(keys) == len(values).
  branch_count[i] = item count of object i. Missing filter_key skipped per object.
"""

import json

# ══════════════════════════════════════════════════════════════════
# GH INPUT STUBS
# ══════════════════════════════════════════════════════════════════
if "metadata" not in dir():
    metadata = None  # noqa: E701
if "filter_key" not in dir():
    filter_key = None  # noqa: E701


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════


def as_list(x):
    """Normalize None / scalar / iterable -> plain list."""
    if x is None:
        return []
    if isinstance(x, str):
        return [x]
    try:
        return list(x)
    except TypeError:
        return [x]


def parse_meta(item):
    """JSON string (or dict) -> dict. Non-dict / bad JSON -> {}."""
    if isinstance(item, dict):
        return item
    if not isinstance(item, str):
        return {}
    try:
        d = json.loads(item)
        return d if isinstance(d, dict) else {}
    except (ValueError, TypeError):
        return {}


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

dicts = [parse_meta(it) for it in as_list(metadata)]
filt = [str(k) for k in as_list(filter_key)]

# all_keys: union across every object, order = first-seen then sorted.
_seen = set()
for d in dicts:
    for k in d.keys():
        _seen.add(k)
all_keys = sorted(_seen)

# Flat outputs: concatenate every object's keys/values into single-level lists.
# branch_count records each object's length so you can regroup downstream.
keys = []
values = []
branch_count = []
for d in dicts:
    if filt:
        # keep filter order; skip keys absent on this object
        sel = [k for k in filt if k in d]
    else:
        sel = list(d.keys())
    keys.extend(sel)
    values.extend(d[k] for k in sel)
    branch_count.append(len(sel))

print(
    "Parsed {} objects | {} unique keys | filter: {}".format(
        len(dicts), len(all_keys), filt if filt else "(none)"
    )
)
