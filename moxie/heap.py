"""moxie/gc heap limit (Spec section 3, `[memory] heap`).

The reference interpreter has no collector of its own: Python frees what nothing refers to.  To enforce the
limit it measures the live values with a model of moxie/gc's layout (a value header of 16 bytes, 8 bytes per
slot, a string's bytes) by walking everything the running program can still reach: the fibers' frames, the
module scopes, and what those hold.  The walk runs every so many calls and loop turns and at each fiber switch,
and when it finds the limit passed it first runs a full Python collection (to drop cycles), measures again, and
only then ends the program with a summary of the heap.  Sizes are the model's, not Python's.
"""
import gc
import sys
import types
from collections import deque

from . import values as V
from .core import Env, ProgramExit

HEADER = 16
SLOT = 8
EVERY = 4000                 # calls and loop turns between measurements, at least

_WALK = None


def walkable():
    """The classes whose instances the walk follows; anything else (syntax trees, the interpreter) is ignored."""
    global _WALK
    if _WALK is None:
        from . import streams, calls
        from . import sched as S
        cs = [c for m in (V, S, streams) for c in vars(m).values() if isinstance(c, type) and c.__module__ == m.__name__]
        cs.append(calls.LazyV)
        skip = {V.Abort, V.BreakEx, V.ContinueEx, V.ReturnEx, V.EnumType, V.CaseInfo, V.TypeV, V.Builtin,
                S.Scheduler, S.Fiber, S.ExtFail, S.EventSink}
        _WALK = frozenset(c for c in cs if c not in skip)
    return _WALK


def model_size(roots, stop=()):
    """(bytes, {kind: bytes}) for what `roots` reach."""
    walk = walkable()
    seen = set(id(s) for s in stop)
    total = 0
    kinds = {}
    todo = list(roots)
    while todo:
        o = todo.pop()
        t = type(o)
        if t in (int, float, bool, type(None)) or isinstance(o, (int, float)):
            continue
        i = id(o)
        if i in seen:
            continue
        seen.add(i)
        add = 0
        if isinstance(o, str):
            add = HEADER + len(o.encode("utf-8", "replace"))
            kind = "String"
        elif t in (list, tuple, deque, set, frozenset):
            add = SLOT * len(o)
            todo.extend(o)
            kind = "List"
        elif t is dict:
            add = 2 * SLOT * len(o)
            todo.extend(o.keys())
            todo.extend(o.values())
            kind = "Dict"
        elif t is Env:
            add = SLOT * len(o.vars)
            todo.extend(o.vars.values())
            todo.extend((o.parent, o.recv, o.usings))
            kind = "scopes"
        elif t is types.GeneratorType:
            fr = o.gi_frame
            if fr is not None:
                todo.extend(fr.f_locals.values())
            if o.gi_yieldfrom is not None:
                todo.append(o.gi_yieldfrom)
            continue
        elif t is types.FunctionType:
            for c in o.__closure__ or ():
                try:
                    todo.append(c.cell_contents)
                except ValueError:
                    pass
            continue
        elif t in walk:
            add = HEADER
            kind = t.__name__.replace("V", "") or t.__name__
            for k in t.__mro__:
                for sl in getattr(k, "__slots__", ()):
                    if hasattr(o, sl):
                        todo.append(getattr(o, sl))
            d = getattr(o, "__dict__", None)
            if d:
                todo.extend(d.values())
        else:
            continue
        total += add
        kinds[kind] = kinds.get(kind, 0) + add
    return total, kinds


def roots_of(I):
    rs = [I.module_env] if getattr(I, "module_env", None) is not None else []
    rs.extend(getattr(I, "packages", {}).values())
    S_ = I.sched
    rs.extend(f.gen for f in S_.fibers if not f.done)
    rs.extend(f.sendval for f in S_.fibers if not f.done)
    fr = sys._getframe(1)
    while fr is not None:
        rs.extend(fr.f_locals.values())
        fr = fr.f_back
    return rs


def measure(I):
    return model_size(roots_of(I), stop=(I.prelude,))


def fmt_bytes(n):
    for unit, k in (("GiB", 1 << 30), ("MiB", 1 << 20), ("KiB", 1 << 10)):
        if n >= k:
            return f"{n / k:.1f} {unit}"
    return f"{n} bytes"


def check(I):
    """Called every so often: end the program when the live heap is over the limit even after a full collection."""
    I.heap_count = 0
    used, kinds = measure(I)
    I.heap_gap = max(EVERY, used // 100)      # a bigger heap is measured less often, so the cost stays a fraction of the run
    if used <= I.heap_limit:
        return
    gc.collect()
    used, kinds = measure(I)
    if used <= I.heap_limit:
        return
    top = sorted(kinds.items(), key=lambda kv: -kv[1])[:4]
    summary = ", ".join(f"{k} {fmt_bytes(v)}" for k, v in top)
    raise ProgramExit(1, f"out of memory: the heap limit is {I.heap_limit:,} bytes ([memory] heap) and "
                         f"{used:,} bytes are live ({summary})")


def tick(I):
    I.heap_count += 1
    if I.heap_count >= I.heap_gap:
        check(I)
