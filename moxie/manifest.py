"""The entry package's Moxie.toml, as far as the reference interpreter uses it: [fibers], [pools], [program], [memory]."""
import os

FIBER_KEYS = {"limit", "memory", "strings", "temps", "stack"}
POOL_KEYS = {"warn_threshold", "header"}
PROGRAM_KEYS = {"memory", "key_warning", "type_fuel", "eval_fuel"}
NATIVE_KEYS = {"libs", "paths"}
MEMORY_KEYS = {"heap", "slice"}
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
    import difflib
    known_tables = ("name", "entry", "files", "version", "fibers", "pools", "program", "memory", "native", "permissions", "database")
    for k in data:
        if k not in known_tables:
            near = difflib.get_close_matches(k, known_tables, n=1)
            raise ManifestError(f"{m}: unknown key or table '{k}'" + (f" (did you mean '{near[0]}'?)" if near else f" (known: {', '.join(known_tables)})"))
    out = {"path": m, "fibers": {}, "pools": {}, "program": {}, "memory": {}}
    if "native" in data:
        out["native"] = native_table(m, data["native"])
    for table, keys in (("fibers", FIBER_KEYS), ("pools", POOL_KEYS), ("program", PROGRAM_KEYS), ("memory", MEMORY_KEYS)):
        t = data.get(table, {})
        if not isinstance(t, dict):
            raise ManifestError(f"{m}: [{table}] must be a table")
        for k in t:
            if k not in keys:
                near = difflib.get_close_matches(k, sorted(keys), n=1)
                raise ManifestError(f"{m}: unknown key '{k}' in [{table}]" + (f" (did you mean '{near[0]}'?)" if near else "") + f" (known: {', '.join(sorted(keys))})")
        out[table] = dict(t)
    for table, key in (("fibers", "memory"), ("fibers", "strings"), ("fibers", "temps"), ("fibers", "stack"), ("program", "memory"), ("program", "key_warning"), ("memory", "heap")):
        if key in out[table] and parse_size(out[table][key]) is None:
            raise ManifestError(f"{m}: [{table}] {key} must be a size such as \"64KiB\" (1024-based) or \"64KB\" (1000-based)")
    if "type_fuel" in out["program"]:
        tf = out["program"]["type_fuel"]
        if not isinstance(tf, int) or isinstance(tf, bool) or tf < 1:
            raise ManifestError(f"{m}: [program] type_fuel must be a whole number of reductions, 1 or more (the default is 64)")
    if "eval_fuel" in out["program"]:
        ef = out["program"]["eval_fuel"]
        if not isinstance(ef, int) or isinstance(ef, bool) or ef < 1:
            raise ManifestError(f"{m}: [program] eval_fuel must be a whole number of steps, 1 or more (the default is 200000)")
    if "slice" in out["memory"]:
        sl = out["memory"]["slice"]
        mt = __import__("re").fullmatch(r"\s*(\d+)\s*(ns|us|ms|s)?\s*", sl) if isinstance(sl, str) else None
        if not mt and not (isinstance(sl, int) and not isinstance(sl, bool) and sl >= 0):
            raise ManifestError(f"{m}: [memory] slice must be a time such as \"2ms\"")
    if "header" in out["pools"] and not isinstance(out["pools"]["header"], str):
        raise ManifestError(f"{m}: [pools] header must be a file name")
    fb = out["fibers"]
    if "strings" in fb or "temps" in fb:
        sp, tp, mem = parse_size(fb.get("strings")), parse_size(fb.get("temps")), parse_size(fb.get("memory"))
        if mem is not None and sp is not None and tp is not None and sp + tp != mem:
            raise ManifestError(f"{m}: [fibers] strings ({sp}) plus temps ({tp}) is {sp + tp}, but memory says {mem}; "
                                "give memory alone, or strings and temps alone")
        if mem is not None and ((sp is not None and sp > mem) or (tp is not None and tp > mem)):
            raise ManifestError(f"{m}: [fibers] strings or temps is larger than memory ({mem})")
        if mem is None and (sp is None or tp is None):
            raise ManifestError(f"{m}: [fibers] needs both strings and temps (or memory, which they divide)")
    lim = out["fibers"].get("limit")
    if lim is not None and (not isinstance(lim, int) or isinstance(lim, bool) or lim < 1):
        raise ManifestError(f"{m}: [fibers] limit must be a whole number of at least 1")
    return out


def fiber_spaces(fib):
    """(strings, temps) in bytes for one fiber from a [fibers] table, or None when it does not say.
    `memory` is the two together; `strings` and `temps` divide it (one may be left out and is the rest)."""
    mem, sp, tp = parse_size(fib.get("memory")), parse_size(fib.get("strings")), parse_size(fib.get("temps"))
    if sp is not None and tp is not None:
        return sp, tp
    if mem is None:
        return None
    if sp is not None:
        return sp, mem - sp
    if tp is not None:
        return mem - tp, tp
    return None


def native_table(m, t):
    """The validated [native] table of the manifest at `m`: {"libs": [...] or None, "paths": [absolute dirs]}."""
    if not isinstance(t, dict):
        raise ManifestError(f"{m}: [native] must be a table")
    for k in t:
        if k not in NATIVE_KEYS:
            raise ManifestError(f"{m}: unknown key '{k}' in [native] (known: {', '.join(sorted(NATIVE_KEYS))})")
    for k in NATIVE_KEYS & set(t):
        v = t[k]
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            raise ManifestError(f"{m}: [native] {k} must be a list of strings")
    base = os.path.dirname(os.path.abspath(m))
    return {"libs": t.get("libs"), "paths": [os.path.normpath(os.path.join(base, d)) for d in t.get("paths", [])]}


def package_native(pkg_dir):
    """For an imported package directory: (has_manifest, native table or None).  A package without a Moxie.toml
    is a plain file or folder, which the reference interpreter lets declare foreign functions."""
    m = os.path.join(pkg_dir, "Moxie.toml")
    if not os.path.isfile(m):
        return False, None
    import tomllib
    try:
        with open(m, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ManifestError(f"{m}: {e}")
    return True, (native_table(m, data["native"]) if "native" in data else None)
