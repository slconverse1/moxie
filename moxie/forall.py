"""Property tests: `forall x: T:` generates values of T, runs the body, and shrinks a failing input.

Generators and shrinkers work on the type AST (TName / TTuple), so a declared tuple or enum is built
from its field types. The generator is seeded, so a failure replays with `moxie test --seed N`."""
import math
import random
from .values import (Abort, Char, F32, TupleV, EnumV, ListV, ArrayV, INT_CLASSES)

DEFAULT_CASES = 100
DEFAULT_SEED = 20260101


class NoGen(Exception):
    pass


def _path(t):
    return t.path[-1] if t.__class__.__name__ == "TName" else None


def _args(t):
    return t.groups[0] if t.groups else []


def gen(I, t, rng, size, depth=0):
    cls = t.__class__.__name__
    if cls == "TUnit":
        return TupleV([], None)
    if cls == "TTuple":
        names = [lab for lab, _ in t.items]
        return TupleV([gen(I, ty, rng, size, depth) for _, ty in t.items],
                      names if any(names) else None)
    if cls != "TName":
        raise NoGen("a function or union type")
    n = _path(t)
    if n == "Int":
        return _int(rng, size, -(1 << 63), (1 << 63) - 1)
    if n in INT_CLASSES:
        c = INT_CLASSES[n]
        lo, hi = (-(1 << (c.bits - 1)), (1 << (c.bits - 1)) - 1) if c.signed else (0, (1 << c.bits) - 1)
        return c(_int(rng, size, lo, hi))
    if n == "Bool":
        return rng.random() < 0.5
    if n == "Char":
        return Char(rng.choice("abcxyz019 _-ABZéλ"))
    if n == "String":
        return "".join(rng.choice("abcdefghijklmnopqrstuvwxyz 0123456789éλ")
                       for _ in range(rng.randint(0, size)))
    if n in ("Double", "Float"):
        v = rng.choice([0.0, 1.0, -1.0, 0.5, rng.uniform(-size, size), rng.uniform(-1e6, 1e6)])
        return F32.of(v) if n == "Float" else v
    if n in ("List", "Array") and _args(t):
        k = 0 if depth > 3 else rng.randint(0, size)
        items = [gen(I, _args(t)[0], rng, size, depth + 1) for _ in range(k)]
        return ListV(items, max(len(items), 1)) if n == "List" else ArrayV(items)
    if n in I.tuples and not I.tuples[n].tparams:
        info = I.tuples[n]
        vals = [gen(I, f.type, rng, size, depth) for f in info.fields]
        return TupleV(vals, None if info.positional is not None else [f.name for f in info.fields], n)
    if n in I.enums:
        et = I.enums[n].et
        cs = [et.cases[c] for c in et.order]
        if depth > 3:
            cs = [c for c in cs if not c.ftypes] or cs
        ci = rng.choice(cs)
        vals = [gen(I, ty, rng, size, depth + 1) for ty in ci.ftypes]
        if len(vals) < len(ci.fields):
            raise NoGen(f"enum {n}")
        return EnumV(et, ci.name, vals, list(ci.fields) if ci.fields else None)
    raise NoGen(f"the type {n}")


def _int(rng, size, lo, hi):
    r = rng.random()
    if r < 0.15:
        v = rng.choice([0, 1, -1, 2, lo, hi, lo + 1, hi - 1])
    elif r < 0.75:
        v = rng.randint(-size, size)
    else:
        v = rng.randint(lo, hi)
    return max(lo, min(hi, v))


def shrinks(I, t, v):
    """Yield strictly simpler candidates for v, simplest first."""
    cls = t.__class__.__name__
    if cls == "TTuple":
        for i, (_, ty) in enumerate(t.items):
            for s in shrinks(I, ty, v.vals[i]):
                yield TupleV(v.vals[:i] + [s] + v.vals[i + 1:], v.names, v.tname)
        return
    if cls != "TName":
        return
    n = _path(t)
    if n == "Int" or n in INT_CLASSES:
        c = type(v)
        x = int(v)
        if x == 0:
            return
        sign = 1 if x > 0 else -1
        cands = [0]
        d = x
        while abs(d) > 1:
            d = int(d / 2)
            cands.append(x - d)
        cands += [x - sign] + ([-x] if x < 0 else [])
        seen = set()
        for y in cands:
            if y in seen or abs(y) > abs(x) or y == x:
                continue
            seen.add(y)
            try:
                yield c(y) if c is not int else y
            except Abort:
                pass
        return
    if n == "Bool":
        if v:
            yield False
        return
    if n == "Char":
        if v != "a":
            yield Char("a")
        return
    if n == "String":
        if v:
            yield ""
            yield v[: len(v) // 2]
            yield v[:-1]
            yield v[1:]
        return
    if n in ("Double", "Float"):
        if v != 0.0:
            yield 0.0 if n == "Double" else F32.of(0.0)
            if abs(v) >= 2 and math.isfinite(v):
                yield float(int(v / 2)) if n == "Double" else F32.of(int(v / 2))
        return
    if n in ("List", "Array") and _args(t):
        items = v.items
        mk = (lambda xs: ListV(xs, max(len(xs), 1))) if n == "List" else (lambda xs: ArrayV(xs))
        if items:
            yield mk([])
            yield mk(items[: len(items) // 2])
            for i in range(len(items)):
                yield mk(items[:i] + items[i + 1:])
            for i, x in enumerate(items):
                for s in shrinks(I, _args(t)[0], x):
                    yield mk(items[:i] + [s] + items[i + 1:])
        return
    if n in I.tuples and not I.tuples[n].tparams:
        info = I.tuples[n]
        for i, f in enumerate(info.fields):
            for s in shrinks(I, f.type, v.vals[i]):
                yield TupleV(v.vals[:i] + [s] + v.vals[i + 1:], v.names, v.tname)
        return
    if n in I.enums:
        et = I.enums[n].et
        ci = et.cases[v.case]
        for i, ty in enumerate(ci.ftypes):
            if i < len(v.vals):
                for s in shrinks(I, ty, v.vals[i]):
                    yield EnumV(et, v.case, v.vals[:i] + [s] + v.vals[i + 1:], v.names)
        for cn in et.order:
            if et.cases[cn].index < ci.index and not et.cases[cn].ftypes:
                yield EnumV(et, cn, [], None)
                break
