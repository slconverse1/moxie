"""The entry package's Moxie.toml, as far as the reference interpreter uses it: [fibers] and [pools]."""
import os

FIBER_KEYS = {"limit", "memory", "stack"}
POOL_KEYS = {"warn_threshold"}


class ManifestError(Exception):
    pass


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
    out = {"path": m, "fibers": {}, "pools": {}}
    for table, keys in (("fibers", FIBER_KEYS), ("pools", POOL_KEYS)):
        t = data.get(table, {})
        if not isinstance(t, dict):
            raise ManifestError(f"{m}: [{table}] must be a table")
        for k in t:
            if k not in keys:
                raise ManifestError(f"{m}: unknown key '{k}' in [{table}] (known: {', '.join(sorted(keys))})")
        out[table] = dict(t)
    lim = out["fibers"].get("limit")
    if lim is not None and (not isinstance(lim, int) or isinstance(lim, bool) or lim < 1):
        raise ManifestError(f"{m}: [fibers] limit must be a whole number of at least 1")
    return out
