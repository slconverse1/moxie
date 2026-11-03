"""Foreign functions (Spec section 19a), first version, on Python's ctypes.

Supported across the boundary: fixed-width integers, Int/UInt, Float, Double, Bool,
tuples of those (as C structs, by value), Array[Byte] (a pointer; a following parameter
written `n: T = len(name)` is the length and is filled in by the call), CString, and
`ref` out-parameters of scalars and tuples, and handles (opaque pointers that must be closed).  Not yet: callbacks,
and running a `parks` function on an OS helper thread (it runs inline).
Handles (`handle H closes fn` in a foreign block) are move-only resources: HandleV.
"""
import ctypes
import ctypes.util
import os

from .ast import *   # noqa
from .values import *   # noqa

SCALARS = {
    "Int8": ctypes.c_int8, "Int16": ctypes.c_int16, "Int32": ctypes.c_int32, "Int64": ctypes.c_int64,
    "UInt8": ctypes.c_uint8, "UInt16": ctypes.c_uint16, "UInt32": ctypes.c_uint32, "UInt64": ctypes.c_uint64,
    "Byte": ctypes.c_uint8, "Int": ctypes.c_ssize_t, "UInt": ctypes.c_size_t,
    "Float": ctypes.c_float, "Double": ctypes.c_double, "Bool": ctypes.c_bool,
}


class CStringV(bytes):
    """A NUL-terminated copy of a String, made by cstr(s)."""
    pass


class HandleV:
    """An opaque C pointer owned by moxie code: a move-only resource that is closed exactly once."""
    __slots__ = ("kind", "ptr", "closed", "I")

    def __init__(self, kind, ptr, I):
        self.kind, self.ptr, self.closed, self.I = kind, ptr, False, I
        I.__dict__.setdefault("live_handles", []).append(self)

    def drop(self, sched=None):
        if self.closed:
            return
        self.closed = True
        f = self.I.handle_closers.get(self.kind)
        if f is not None:
            try:
                f.cfn(ctypes.c_void_p(self.ptr))
            except Exception:
                pass

    def __repr__(self):
        return f"<{self.kind} {'closed' if self.closed else hex(self.ptr)}>"


def drop_live_handles(I):
    """At program end: close every handle still open (a leak the checker could not see)."""
    n = 0
    for h in list(I.__dict__.get("live_handles", [])):
        if not h.closed:
            h.drop()
            n += 1
    return n


def handle_result(I, t):
    """If `t` is a handle type H or Result[H, Error], return (H, is_result)."""
    n = tname(t)
    ht = getattr(I, "handle_types", {})
    if n in ht:
        return n, False
    if n == "Result" and t.groups and t.groups[0]:
        h = tname(t.groups[0][0])
        if h in ht:
            return h, True
    return None, False


class ForeignFn:
    __slots__ = ("name", "lib", "params", "ret", "cfn", "effects", "tuples", "I", "closes")

    def __init__(self, name, lib, params, ret, cfn, effects, I):
        self.name, self.lib, self.params, self.ret, self.cfn = name, lib, params, ret, cfn
        self.effects, self.I = effects, I
        self.closes = None


def tname(t):
    return t.path[-1] if t is not None and t.__class__.__name__ == "TName" else None


def is_byte_array(t):
    if tname(t) not in ("Array", "List"):
        return False
    g = t.groups[0] if t.groups else None
    return bool(g) and tname(g[0]) in ("Byte", "UInt8")


def load_library(name, I=None):
    cands = []
    dirs = [d for d in os.environ.get("MOXIE_NATIVE_PATH", "").split(os.pathsep) if d]
    if I is not None and getattr(I, "search_dir", None):
        dirs.insert(0, I.search_dir)
    for d in dirs:
        for fn in ("lib%s.so" % name, "lib%s.dylib" % name, "%s.dll" % name):
            cands.append(os.path.join(d, fn))
    if "/" in name or name.endswith((".so", ".dylib", ".dll")) or ".so." in name:
        cands.append(name)
    found = ctypes.util.find_library(name)
    if found:
        cands.append(found)
    cands += ["lib%s.so" % name, "lib%s.so.1" % name, name]
    last = None
    for c in cands:
        try:
            return ctypes.CDLL(c)
        except OSError as e:
            last = e
    raise Abort(f"cannot load native library '{name}': {last}")


def struct_for(I, t):
    """A ctypes Structure for a declared tuple type."""
    name = tname(t)
    info = I.tuples.get(name)
    if info is None:
        return None
    cache = I.__dict__.setdefault("_ffi_structs", {})
    if name in cache:
        return cache[name]
    fields = []
    for f in info.fields:
        ct = ctype_of(I, f.type)
        if ct is None:
            raise Abort(f"tuple {name} cannot cross the foreign boundary: field '{f.name}' has no C type")
        fields.append((f.name or f"f{len(fields)}", ct))
    S = type(name, (ctypes.Structure,), {"_fields_": fields})
    cache[name] = S
    return S


def ctype_of(I, t):
    n = tname(t)
    if n in SCALARS:
        return SCALARS[n]
    if n == "CString":
        return ctypes.c_char_p
    if n in getattr(I, "handle_types", {}):
        return ctypes.c_void_p
    if n in I.tuples:
        return struct_for(I, t)
    return None


def to_c(I, t, v):
    n = tname(t)
    if n in SCALARS:
        ct = SCALARS[n]
        if n in ("Float", "Double"):
            return float(v)
        if n == "Bool":
            return bool(v)
        return int(v)
    if n in getattr(I, "handle_types", {}):
        if not isinstance(v, HandleV) or v.kind != n:
            raise Abort(f"a {n} handle is needed here")
        if v.closed:
            raise Abort(f"use of a closed {n} handle")
        return v.ptr
    if n == "CString":
        if isinstance(v, CStringV):
            return bytes(v[:-1])
        raise Abort("a CString parameter needs cstr(text)")
    if n in I.tuples:
        S = struct_for(I, t)
        info = I.tuples[n]
        return S(*[to_c(I, f.type, x) for f, x in zip(info.fields, v.vals)])
    raise Abort(f"type {n} cannot cross the foreign boundary")


def from_c(I, t, c):
    n = tname(t)
    if n in SCALARS:
        if n == "Float":
            return F32.of(c)
        if n == "Double":
            return float(c)
        if n == "Bool":
            return bool(c)
        cls = INT_CLASSES.get(n)
        return cls(int(c)) if cls is not None else int(c)
    if n in I.tuples:
        info = I.tuples[n]
        vals = [from_c(I, f.type, getattr(c, f.name or f"f{i}")) for i, f in enumerate(info.fields)]
        names = [f.name for f in info.fields] if info.fields and info.fields[0].name else None
        return TupleV(vals, names, n)
    raise Abort(f"type {n} cannot come back across the foreign boundary")


def make_foreign(I, lib_name, d):
    lib = load_library(lib_name, I)
    try:
        cfn = getattr(lib, d.name)
    except AttributeError:
        raise Abort(f"native library '{lib_name}' has no function '{d.name}'")
    cargs = []
    for p in d.params or []:
        if is_byte_array(p.type):
            cargs.append(ctypes.c_void_p)
        elif p.mod == "ref":
            ct = ctype_of(I, p.type)
            if ct is None:
                raise Abort(f"ref parameter '{p.name}' cannot cross the foreign boundary")
            cargs.append(ctypes.POINTER(ct))
        else:
            ct = ctype_of(I, p.type)
            if ct is None:
                raise Abort(f"parameter '{p.name}' of '{d.name}' cannot cross the foreign boundary")
            cargs.append(ct)
    cfn.argtypes = cargs
    hret, _ = handle_result(I, d.ret)
    cfn.restype = (ctypes.c_void_p if hret else ctype_of(I, d.ret)) if d.ret is not None and tname(d.ret) != "Unit" else None
    if d.ret is not None and tname(d.ret) != "Unit" and cfn.restype is None:
        raise Abort(f"the result of '{d.name}' cannot cross the foreign boundary")
    from .effects import Effects
    dec = Effects.declared(d)
    return ForeignFn(d.name, lib_name, d.params or [], d.ret, cfn, dec, I)


def length_of(p):
    """If `p` is written `n: T = len(name)`, the name of the array it measures."""
    e = p.default
    if e is not None and e.__class__.__name__ == "Call" and e.fn.__class__.__name__ == "Name" and e.fn.name == "len" \
            and len(e.args) == 1 and e.args[0].expr.__class__.__name__ == "Name":
        return e.args[0].expr.name
    return None


def call_foreign(I, f, pos, named, refspec, cenv, line):
    """A generator: a `parks` function runs on an OS helper thread while its fiber waits."""
    named = dict(named or {})
    declared = f.params
    # which declared parameters the caller supplies: all but the length parameters
    supplied = [p for p in declared if length_of(p) is None]
    if len(pos) > len(supplied):
        raise Abort(f"{f.name} takes {len(supplied)} arguments but {len(pos)} were given", line)
    values = {}
    for p, v in zip(supplied, pos):
        values[p.name] = v
    for k, v in named.items():
        values[k] = v
    keep = []        # buffers must stay alive for the call
    cargs = []
    outs = []        # (param, ctypes object, caller variable)
    ref_by_param = {}
    for key, cname in (refspec or {}).items():
        if isinstance(key, int):
            if key < len(supplied):
                ref_by_param[supplied[key].name] = cname
        else:
            ref_by_param[key] = cname
    for p in declared:
        n = length_of(p)
        if n is not None:
            arr = values.get(n)
            cargs.append(to_c_scalar_len(p, arr))
            continue
        if p.name not in values:
            raise Abort(f"missing argument '{p.name}' for {f.name}", line)
        v = values[p.name]
        if is_byte_array(p.type):
            items = [int(x) for x in (v.items if hasattr(v, "items") else v)]
            buf = (ctypes.c_ubyte * max(len(items), 1))(*items)
            keep.append(buf)
            cargs.append(ctypes.cast(buf, ctypes.c_void_p))
            if p.mod == "ref" and p.name in ref_by_param:
                outs.append((p, buf, ref_by_param[p.name], len(items), v))
        elif p.mod == "ref":
            ct = ctype_of(I_of(f), p.type)
            obj = ct(to_c(I_of(f), p.type, v)) if not issubclass(ct, ctypes.Structure) else to_c(I_of(f), p.type, v)
            keep.append(obj)
            cargs.append(ctypes.pointer(obj))
            if p.name in ref_by_param:
                outs.append((p, obj, ref_by_param[p.name]))
        else:
            cargs.append(to_c(I_of(f), p.type, v))
    if f.effects and "parks" in f.effects:
        from .sched import park_thread
        r = yield from park_thread(I, lambda: f.cfn(*cargs))
    else:
        r = f.cfn(*cargs)
    for o in outs:
        p, obj, cname = o[0], o[1], o[2]
        if len(o) > 3:                       # a writable byte buffer: copy the bytes back
            old = o[4]
            cls = INT_CLASSES.get("UInt8")
            data = [cls(obj[i]) if cls else obj[i] for i in range(o[3])]
            newv = old.__class__(data, old.cap) if hasattr(old, "cap") else data
            scope = cenv.find_scope(cname) if cenv is not None else None
            (scope or cenv).vars[cname] = newv
            continue
        val = obj if isinstance(obj, ctypes.Structure) else obj.value
        newv = from_c(I_of(f), p.type, val)
        scope = cenv.find_scope(cname) if cenv is not None else None
        (scope or cenv).vars[cname] = newv
    if f.closes:
        for p in declared:
            hv = values.get(p.name)
            if isinstance(hv, HandleV) and hv.kind == f.closes:
                hv.closed = True
    if f.ret is None or tname(f.ret) == "Unit":
        return UNIT
    hret, wrapped = handle_result(I_of(f), f.ret)
    if hret:
        if not r:
            if wrapped:
                return Err(make_error(ERR_CODES["MISSING"], f"{f.name} returned NULL"))
            raise Abort(f"{f.name} returned NULL, so it cannot return a {hret}; declare it -> Result[{hret}, Error]", line)
        h = HandleV(hret, r, I_of(f))
        return Ok(h) if wrapped else h
    return from_c(I_of(f), f.ret, r)


def to_c_scalar_len(p, arr):
    if arr is None:
        raise Abort("the array for a length parameter was not given")
    return len(arr.items if hasattr(arr, "items") else arr)


def I_of(f):
    return f.I
