"""The entry package's Moxie.toml, as far as the reference interpreter uses it: [fibers] and [pools]."""
import os

FIBER_KEYS = {"limit", "memory", "stack"}
POOL_KEYS = {"warn_threshold", "header"}
PROGRAM_KEYS = {"memory"}
SIZE_UNITS = {"": 1, "B": 1, "KB": 1000, "MB": 1000 ** 2, "GB": 1000 ** 3, "KIB": 1024, "MIB": 1024 ** 2, "GIB": 1024 ** 3}


class ManifestError(Exception):
    pass


def parse_size(v):
    """A size in bytes from a whole number or a string such as "64KiB" (1024-based) or "64KB" (1000-based); None if malformed."""
    import re
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v if v >= 0 else None
    mt = re.fullmatch(r"\s*(\d+)\s*([A-Za-z]*)\s*", v) if isinstance(v, str) else None
    if not mt or mt.group(2).upper() not in SIZE_UNITS:
        return None
    return int(mt.group(1)) * SIZE_UNITS[mt.group(2).upper()]


def find(path):
    d = os.path.dirname(os.path.abspath(path))
    while True:
        m = os.path.join(d, "Moxie.toml")
        if os.path.isfile(m):
            return m
        up = os.path.dirname(d)
        if up == d:
            return None
        d = up


def load(path):
    """Return {"path":..., "fibers": {...}, "pools": {...}} for the nearest manifest, or {} when there is none."""
    m = find(path) if path else None
    if m is None:
        return {}
    import tomllib
    try:
        with open(m, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ManifestError(f"{m}: {e}")
    out = {"path": m, "fibers": {}, "pools": {}, "program": {}}
    for table, keys in (("fibers", FIBER_KEYS), ("pools", POOL_KEYS), ("program", PROGRAM_KEYS)):
        t = data.get(table, {})
        if not isinstance(t, dict):
            raise ManifestError(f"{m}: [{table}] must be a table")
        for k in t:
            if k not in keys:
                raise ManifestError(f"{m}: unknown key '{k}' in [{table}] (known: {', '.join(sorted(keys))})")
        out[table] = dict(t)
    for table, key in (("fibers", "memory"), ("fibers", "stack"), ("program", "memory")):
        if key in out[table] and parse_size(out[table][key]) is None:
            raise ManifestError(f"{m}: [{table}] {key} must be a size such as \"64KiB\" (1024-based) or \"64KB\" (1000-based)")
    if "header" in out["pools"] and not isinstance(out["pools"]["header"], str):
        raise ManifestError(f"{m}: [pools] header must be a file name")
    lim = out["fibers"].get("limit")
    if lim is not None and (not isinstance(lim, int) or isinstance(lim, bool) or lim < 1):
        raise ManifestError(f"{m}: [fibers] limit must be a whole number of at least 1")
    return out
