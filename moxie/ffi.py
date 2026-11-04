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
        I.pools.acquire("handle " + kind)

    def drop(self, sched=None):
        if self.closed:
            return
        self.closed = True
        self.I.pools.release("handle " + self.kind)
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


def array_elem(t):
    """The scalar element type name of an Array[T] / List[T] of numbers (or Bool), else None."""
    if tname(t) not in ("Array", "List"):
        return None
    g = t.groups[0] if t.groups else None
    n = tname(g[0]) if g else None
    return n if n in SCALARS else None


def is_ptr(t):
    return tname(t) == "Ptr"


def ptr_elem(t):
    g = t.groups[0] if t.groups else None
    return g[0] if g else None


def array_to_c(I, elem, v):
    items = v.items if hasattr(v, "items") else v
    ct = SCALARS[elem]
    conv = (lambda x: float(x)) if elem in ("Float", "Double") else (bool if elem == "Bool" else int)
    return (ct * max(len(items), 1))(*[conv(x) for x in items])


def array_from_c(I, elem, buf, n, old):
    t = TName([elem], None)
    data = [from_c(I, t, buf[i]) for i in range(n)]
    return old.__class__(data, old.cap) if hasattr(old, "cap") else data


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


def is_fn_type(t):
    return t is not None and t.__class__.__name__ == "TFn"


def cb_plan(I, t):
    """How C's callback arguments map to the moxie function's: ("val", type), ("bytes", length ctype), ("ud",).
    An `Array[Byte]` followed by an integer type is C's (pointer, length) pair and arrives as one array;
    `UserData` is C's `void *` user-data pointer and is not passed to the moxie function."""
    plan, ps, i = [], [pt for _nm, pt in t.params], 0
    while i < len(ps):
        pt = ps[i]
        if is_byte_array(pt):
            if i + 1 >= len(ps) or tname(ps[i + 1]) not in SCALARS or tname(ps[i + 1]) in ("Float", "Double", "Bool"):
                raise Abort("in a callback type, an Array[Byte] must be followed by its integer length type")
            plan.append(("bytes", SCALARS[tname(ps[i + 1])]))
            i += 2
            continue
        if array_elem(pt) is not None and not is_byte_array(pt):
            if i + 1 >= len(ps) or tname(ps[i + 1]) not in SCALARS or tname(ps[i + 1]) in ("Float", "Double", "Bool"):
                raise Abort("in a callback type, an Array[T] must be followed by its integer length type")
            plan.append(("array", array_elem(pt), SCALARS[tname(ps[i + 1])]))
            i += 2
            continue
        if is_ptr(pt):
            et = ptr_elem(pt)
            if et is None or ctype_of(I, et) is None:
                raise Abort("Ptr[T] in a callback type needs a T that can cross the foreign boundary")
            plan.append(("ptr", et))
        elif tname(pt) == "UserData":
            plan.append(("ud",))
        else:
            if ctype_of(I, pt) is None:
                raise Abort("a callback parameter cannot cross the foreign boundary")
            plan.append(("val", pt))
        i += 1
    return plan


def cb_ctype(I, t):
    """The C function-pointer type for a moxie function type (callback parameter)."""
    args = []
    for e in cb_plan(I, t):
        if e[0] == "val":
            args.append(ctype_of(I, e[1]))
        elif e[0] in ("bytes", "array"):
            args += [ctypes.c_void_p, e[-1]]
        elif e[0] == "ptr":
            args.append(ctypes.c_void_p)
        else:
            args.append(ctypes.c_void_p)
    rn = tname(t.ret)
    if t.ret is None or rn == "Unit":
        rt = None
    else:
        rt = ctype_of(I, t.ret)
        if rt is None:
            raise Abort("the result of a callback cannot cross the foreign boundary")
    return ctypes.CFUNCTYPE(rt, *args)


def run_sync(I, g):
    """Run a moxie call to completion inside a C callback.  It cannot park: C is waiting for it."""
    if isinstance(g, Done):
        return g.v
    try:
        g.send(None)
    except StopIteration as s:
        return s.value
    raise Abort("a callback called from C must not park (read, write, sleep, select, a query, ...)")


def convert_args(I, plan, cargs):
    vals, k = [], 0
    for e in plan:
        if e[0] == "val":
            vals.append(from_c(I, e[1], cargs[k]))
            k += 1
        elif e[0] == "bytes":
            ptr, n = cargs[k], int(cargs[k + 1])
            raw = ctypes.string_at(ptr, n) if ptr and n else b""
            cls = INT_CLASSES.get("UInt8")
            vals.append(ArrayV([cls(x) if cls else x for x in raw]))
            k += 2
        elif e[0] == "array":
            ptr, n = cargs[k], int(cargs[k + 1])
            ct = SCALARS[e[1]]
            arr = ctypes.cast(ptr, ctypes.POINTER(ct)) if ptr and n else None
            t = TName([e[1]], None)
            vals.append(ArrayV([from_c(I, t, arr[i]) for i in range(n)] if arr else []))
            k += 2
        elif e[0] == "ptr":
            ptr = cargs[k]
            if not ptr:
                raise Abort("C passed a null pointer to a callback that takes Ptr")
            ct = ctype_of(I, e[1])
            vals.append(from_c(I, e[1], ctypes.cast(ptr, ctypes.POINTER(ct))[0]))
            k += 1
        else:
            k += 1
    return vals


class _EvType:
    """The function type of a C-kept callback that is delivered as events: Events[T] means (T...) -> Unit."""
    def __init__(self, t):
        g = t.groups[0][0] if t.groups and t.groups[0] else None
        if g is None:
            raise Abort("Events needs a payload type, such as Events[Int32] or Events[(Int32, Double)]")
        self.single = g.__class__.__name__ != "TTuple"
        self.params = [(None, g)] if self.single else list(g.items)
        self.ret = None


def is_events(t):
    return tname(t) == "Events"


def make_event_thunk(I, ev, sink):
    plan = cb_plan(I, ev)

    def thunk(*cargs):
        try:
            vals = convert_args(I, plan, cargs)
            v = vals[0] if ev.single else TupleV(vals)
            I.sched.post_event(sink, v)
        except BaseException:      # noqa: never let an exception unwind into C
            sink.dropped += 1
        return None
    return thunk


def is_handler(t):
    return tname(t) == "Handler"


def handler_fn_type(t):
    g = t.groups[0][0] if t.groups and t.groups[0] else None
    if g is None or not is_fn_type(g):
        raise Abort("Handler needs a function type, such as Handler[(Int32) -> Int32]")
    return g


def make_handler_thunk(I, ft, fnv):
    """A Python function C keeps and may call from any thread, expecting an answer.  On the scheduler's thread
    the moxie function runs at once (and may not park); on any other thread the call is posted to the scheduler,
    which runs the function in a fiber of its own (it may park) while the calling thread waits for the result."""
    import queue
    import threading
    plan = cb_plan(I, ft)
    rt = ft.ret if ft.ret is not None and tname(ft.ret) != "Unit" else None
    home = threading.get_ident()

    def zero():
        if rt is None:
            return None
        ct = ctype_of(I, rt)
        return ct() if isinstance(ct, type) and issubclass(ct, ctypes.Structure) else (0.0 if ct in (ctypes.c_double, ctypes.c_float) else 0)

    def thunk(*cargs):
        try:
            vals = convert_args(I, plan, cargs)
            if threading.get_ident() == home:
                r = run_sync(I, I.apply(fnv, vals, {}))
            else:
                reply = queue.Queue()
                I.sched.post_call(I, fnv, vals, reply)
                kind, r = reply.get()
                if kind != "ok":
                    return zero()
            return to_c(I, rt, r) if rt is not None else None
        except BaseException as e:      # noqa: re-raised by the next foreign call that returns on the scheduler thread
            if I.__dict__.get("handler_exc") is None:
                I.handler_exc = e
            return zero()
    return thunk


def make_thunk(I, t, fnv, box):
    """A Python function C can call: converts the arguments, runs the moxie function, converts the result."""
    plan = cb_plan(I, t)
    rt = t.ret if t.ret is not None and tname(t.ret) != "Unit" else None

    def thunk(*cargs):
        try:
            vals = convert_args(I, plan, cargs)
            r = run_sync(I, I.apply(fnv, vals, {}))
            return to_c(I, rt, r) if rt is not None else None
        except BaseException as e:      # noqa: carried out of C and re-raised by the caller
            if box.get("exc") is None:
                box["exc"] = e
            if rt is None:
                return None
            ct = ctype_of(I, rt)
            return ct() if isinstance(ct, type) and issubclass(ct, ctypes.Structure) else 0
    return thunk


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
        if is_handler(p.type):
            cargs.append(cb_ctype(I, handler_fn_type(p.type)))
        elif is_events(p.type):
            cargs.append(cb_ctype(I, _EvType(p.type)))
        elif is_fn_type(p.type):
            from .effects import Effects as _E
            if "parks" in (_E.declared(d) or ()):
                raise Abort(f"'{d.name}' takes a callback, so it cannot be declared parks: "
                            "the callback would run on the OS helper thread")
            cargs.append(cb_ctype(I, p.type))
        elif is_byte_array(p.type) or array_elem(p.type) is not None:
            cargs.append(ctypes.c_void_p)
        elif is_userdata(p):
            cargs.append(ctypes.c_void_p)
        elif is_out_handle(I, p):
            cargs.append(ctypes.POINTER(ctypes.c_void_p))
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
    if any(is_out_handle(I, p) for p in d.params or []):
        if not hret:
            raise Abort(f"'{d.name}' has an out-handle parameter, so it must return the handle: Result[H, Error] (C returns an int status, 0 is success) or H (C's result is ignored)")
        cfn.restype = ctypes.c_int if handle_result(I, d.ret)[1] else None
        return ForeignFn(d.name, lib_name, d.params or [], d.ret, cfn, _decl_effects(d), I)
    cfn.restype = (ctypes.c_void_p if hret else ctype_of(I, d.ret)) if d.ret is not None and tname(d.ret) != "Unit" else None
    if d.ret is not None and tname(d.ret) != "Unit" and cfn.restype is None:
        raise Abort(f"the result of '{d.name}' cannot cross the foreign boundary")
    return ForeignFn(d.name, lib_name, d.params or [], d.ret, cfn, _decl_effects(d), I)


def is_userdata(p):
    """`ud: UserData`: a C `void *` user-data argument; the caller does not supply it and C gets NULL."""
    return tname(p.type) == "UserData"


def is_out_handle(I, p):
    """`ref db: Db` where Db is a handle type: a C `Db **` that the call fills in; the caller does not supply it."""
    return p.mod == "ref" and tname(p.type) in getattr(I, "handle_types", {})


def _decl_effects(d):
    from .effects import Effects
    return Effects.declared(d)


def size_of_param(p):
    """If `p` is written `size: UInt = size_of(name)`, the name of the array whose element size it gives."""
    e = p.default
    if e is not None and e.__class__.__name__ == "Call" and e.fn.__class__.__name__ == "Name" and e.fn.name == "size_of" \
            and len(e.args) == 1 and e.args[0].expr.__class__.__name__ == "Name":
        return e.args[0].expr.name
    return None


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
    supplied = [p for p in declared if length_of(p) is None and size_of_param(p) is None and not is_out_handle(I_of(f), p) and not is_userdata(p)]
    if len(pos) > len(supplied):
        raise Abort(f"{f.name} takes {len(supplied)} arguments but {len(pos)} were given", line)
    values = {}
    for p, v in zip(supplied, pos):
        values[p.name] = v
    for k, v in named.items():
        values[k] = v
    keep = []        # buffers must stay alive for the call
    cbbox = {}
    cargs = []
    outs = []        # (param, ctypes object, caller variable)
    ref_by_param = {}
    for key, cname in (refspec or {}).items():
        if isinstance(key, int):
            if key < len(supplied):
                ref_by_param[supplied[key].name] = cname
        else:
            ref_by_param[key] = cname
    outcell = None
    for p in declared:
        if is_userdata(p):
            cargs.append(None)
            continue
        if is_out_handle(I_of(f), p):
            outcell = ctypes.c_void_p()
            cargs.append(ctypes.byref(outcell))
            continue
        sz = size_of_param(p)
        if sz is not None:
            arr = values.get(sz)
            decl = next((q for q in declared if q.name == sz), None)
            el = array_elem(decl.type) if decl is not None else None
            if el is None:
                raise Abort(f"size_of({sz}) in {f.name} needs an array of numbers")
            cargs.append(ctypes.sizeof(SCALARS[el]))
            continue
        n = length_of(p)
        if n is not None:
            arr = values.get(n)
            cargs.append(to_c_scalar_len(p, arr))
            continue
        if p.name not in values:
            raise Abort(f"missing argument '{p.name}' for {f.name}", line)
        v = values[p.name]
        if is_handler(p.type):
            ft = handler_fn_type(p.type)
            if not callable(getattr(v, "__class__", None)) and v is None:
                raise Abort(f"'{p.name}' of {f.name} needs a function", line)
            th = cb_ctype(I_of(f), ft)(make_handler_thunk(I_of(f), ft, v))
            I_of(f).__dict__.setdefault("kept_thunks", []).append(th)     # C may call it at any time: never freed
            I_of(f).sched.listeners += 1
            cargs.append(th)
        elif is_events(p.type):
            from .sched import EventSink
            if not hasattr(v, "chan") or not hasattr(v, "write"):
                raise Abort(f"'{p.name}' of {f.name} keeps a channel write end: pass move tx", line)
            ev = _EvType(p.type)
            sink = EventSink(v, f"{f.name}.{p.name}")
            I_of(f).__dict__.setdefault("event_sinks", []).append(sink)
            th = cb_ctype(I_of(f), ev)(make_event_thunk(I_of(f), ev, sink))
            I_of(f).__dict__.setdefault("kept_thunks", []).append(th)     # C may call it at any time: never freed
            I_of(f).sched.listeners += 1
            cargs.append(th)
        elif is_fn_type(p.type):
            ctype = cb_ctype(I_of(f), p.type)
            th = ctype(make_thunk(I_of(f), p.type, v, cbbox))
            keep.append(th)
            cargs.append(th)
        elif is_byte_array(p.type):
            items = [int(x) for x in (v.items if hasattr(v, "items") else v)]
            buf = (ctypes.c_ubyte * max(len(items), 1))(*items)
            keep.append(buf)
            cargs.append(ctypes.cast(buf, ctypes.c_void_p))
            if p.mod == "ref" and p.name in ref_by_param:
                outs.append((p, buf, ref_by_param[p.name], len(items), v))
        elif array_elem(p.type) is not None:
            el = array_elem(p.type)
            buf = array_to_c(I_of(f), el, v)
            n = len(v.items if hasattr(v, "items") else v)
            keep.append(buf)
            cargs.append(ctypes.cast(buf, ctypes.c_void_p))
            if p.mod == "ref" and p.name in ref_by_param:
                outs.append((p, buf, ref_by_param[p.name], n, v, el))
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
        if len(o) > 5:                       # a writable array of numbers: copy the elements back
            newv = array_from_c(I_of(f), o[5], obj, o[3], o[4])
            scope = cenv.find_scope(cname) if cenv is not None else None
            (scope or cenv).vars[cname] = newv
            continue
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
    if I_of(f).__dict__.get("handler_exc") is not None:
        e, I_of(f).handler_exc = I_of(f).handler_exc, None
        raise e
    if cbbox.get("exc") is not None:       # a callback aborted: C ran on with zeros; now the abort ends the call
        raise cbbox["exc"]
    if outcell is not None:
        hname, wrapped = handle_result(I_of(f), f.ret)
        ptr = outcell.value
        if wrapped:
            status = int(r or 0)
            if status != 0:
                if ptr:                       # e.g. sqlite3_open leaves a handle that must still be closed
                    HandleV(hname, ptr, I_of(f)).drop()
                return Err(make_error(status, f"{f.name} failed with status {status}"))
            if not ptr:
                return Err(make_error(ERR_CODES["MISSING"], f"{f.name} gave no handle"))
            return Ok(HandleV(hname, ptr, I_of(f)))
        if not ptr:
            raise Abort(f"{f.name} gave no handle", line)
        return HandleV(hname, ptr, I_of(f))
    if f.closes:
        for p in declared:
            hv = values.get(p.name)
            if isinstance(hv, HandleV) and hv.kind == f.closes and not hv.closed:
                hv.closed = True
                I_of(f).pools.release("handle " + hv.kind)
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
