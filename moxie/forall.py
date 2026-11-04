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


def _user(I, n, name):
    """A closure the mixer wrote in `impl Generatable for n` (static `generate`, method `shrink`)."""
    for table in (I.statics.get(n), I.impls.get(n)):
        if table and name in table and table[name]:
            return table[name][0]
    return None


def gen(I, t, rng, size, depth=0):
    """A generator function: it returns a value of type t (user impls run moxie code)."""
    if depth > 24:
        raise NoGen("a type that nests too deeply (a recursive Generatable needs a depth limit)")
    cls = t.__class__.__name__
    if cls == "TUnit":
        return TupleV([], None)
    if cls == "TTuple":
        vals = []
        for _, ty in t.items:
            vals.append((yield from gen(I, ty, rng, size, depth)))
        names = [lab for lab, _ in t.items]
        return TupleV(vals, names if any(names) else None)
    if cls != "TName":
        raise NoGen("a function or union type")
    n = _path(t)
    cl = _user(I, n, "generate")
    if cl is not None:
        from .prelude import GenR
        v = yield from I.apply(cl, [GenR(rng, size, depth + 1)])
        return v
    if n == "Int":
        return _int(rng, size, -(1 << 63), (1 << 63) - 1)
    if n in INT_CLASSES:
        c = INT_CLASSES[n]
        lo, hi = (-(1 << (c.bits - 1)), (1 << (c.bits - 1)) - 1) if c.signed else (0, (1 << c.bits) - 1)
        return c(_int(rng, size, lo, hi))
    if n == "Bool":
        return rng.random() < 0.5
    if n == "Char":
        return Char(rng.choice("abcxyz019 _-ABZ\u00e9\u03bb"))
    if n == "String":
        return "".join(rng.choice("abcdefghijklmnopqrstuvwxyz 0123456789\u00e9\u03bb")
                       for _ in range(rng.randint(0, size)))
    if n in ("Double", "Float"):
        v = rng.choice([0.0, 1.0, -1.0, 0.5, rng.uniform(-size, size), rng.uniform(-1e6, 1e6)])
        return F32.of(v) if n == "Float" else v
    if n in ("List", "Array") and _args(t):
        k = 0 if depth > 3 else rng.randint(0, size)
        items = []
        for _ in range(k):
            items.append((yield from gen(I, _args(t)[0], rng, size, depth + 1)))
        return ListV(items, max(len(items), 1)) if n == "List" else ArrayV(items)
    if n in I.tuples and not I.tuples[n].tparams:
        info = I.tuples[n]
        for _try in range(50):
            vals = []
            for f in info.fields:
                vals.append((yield from gen(I, f.type, rng, size, depth)))
            try:
                # built through the constructor, so an invariant rejects an invalid draw
                return (yield from I.construct_tuple(info, vals, {}, [], 0))
            except Abort as a:
                if not a.msg.startswith("invariant of"):
                    raise
        raise NoGen(f"a valid {n}: 50 draws all broke its invariant (write impl Generatable for {n})")
    if n in I.enums:
        et = I.enums[n].et
        cs = [et.cases[c] for c in et.order]
        if depth > 3:
            cs = [c for c in cs if not c.ftypes] or cs
        ci = rng.choice(cs)
        vals = []
        for ty in ci.ftypes:
            vals.append((yield from gen(I, ty, rng, size, depth + 1)))
        if len(vals) < len(ci.fields):
            raise NoGen(f"enum {n}")
        return EnumV(et, ci.name, vals, list(ci.fields) if ci.fields else None)
    raise NoGen(f"the type {n} (write impl Generatable for {n})")


def _int(rng, size, lo, hi):
    r = rng.random()
    if r < 0.15:
        v = rng.choice([0, 1, -1, 2, lo, hi, lo + 1, hi - 1])
    elif r < 0.75:
        v = rng.randint(-size, size)
    else:
        v = rng.randint(lo, hi)
    return max(lo, min(hi, v))


def shrink_list(I, t, v):
    """A generator function returning strictly simpler candidates for v, simplest first."""
    out = []
    cls = t.__class__.__name__
    if cls == "TTuple":
        for i, (_, ty) in enumerate(t.items):
            for x in (yield from shrink_list(I, ty, v.vals[i])):
                out.append(TupleV(v.vals[:i] + [x] + v.vals[i + 1:], v.names, v.tname))
        return out
    if cls != "TName":
        return out
    n = _path(t)
    ms = I.methods_of(v, "shrink") if _user(I, n, "shrink") is not None else None
    if ms:
        r = yield from I.apply_method(ms[0], v, [])
        return list(getattr(r, "items", []))
    if n == "Int" or n in INT_CLASSES:
        c = type(v)
        x = int(v)
        if x == 0:
            return out
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
                out.append(c(y) if c is not int else y)
            except Abort:
                pass
        return out
    if n == "Bool":
        if v:
            out.append(False)
        return out
    if n == "Char":
        if v != "a":
            out.append(Char("a"))
        return out
    if n == "String":
        if v:
            out += ["", v[: len(v) // 2], v[:-1], v[1:]]
        return out
    if n in ("Double", "Float"):
        if v != 0.0:
            out.append(0.0 if n == "Double" else F32.of(0.0))
            if abs(v) >= 2 and math.isfinite(v):
                out.append(float(int(v / 2)) if n == "Double" else F32.of(int(v / 2)))
        return out
    if n in ("List", "Array") and _args(t):
        items = v.items
        mk = (lambda xs: ListV(xs, max(len(xs), 1))) if n == "List" else (lambda xs: ArrayV(xs))
        if items:
            out.append(mk([]))
            out.append(mk(items[: len(items) // 2]))
            for i in range(len(items)):
                out.append(mk(items[:i] + items[i + 1:]))
            for i, x in enumerate(items):
                for y in (yield from shrink_list(I, _args(t)[0], x)):
                    out.append(mk(items[:i] + [y] + items[i + 1:]))
        return out
    if n in I.tuples and not I.tuples[n].tparams:
        info = I.tuples[n]
        for i, f in enumerate(info.fields):
            for y in (yield from shrink_list(I, f.type, v.vals[i])):
                out.append(TupleV(v.vals[:i] + [y] + v.vals[i + 1:], v.names, v.tname))
        return out
    if n in I.enums:
        et = I.enums[n].et
        ci = et.cases[v.case]
        for i, ty in enumerate(ci.ftypes):
            if i < len(v.vals):
                for y in (yield from shrink_list(I, ty, v.vals[i])):
                    out.append(EnumV(et, v.case, v.vals[:i] + [y] + v.vals[i + 1:], v.names))
        for cn in et.order:
            if et.cases[cn].index < ci.index and not et.cases[cn].ftypes:
                out.append(EnumV(et, cn, [], None))
                break
    return out
