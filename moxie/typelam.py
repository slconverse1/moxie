"""Type lambdas (Spec section 9a): `[A] -> Result[String, A]` is a type-level function.

A lambda is applied by substitution (beta reduction), so it never exists at run time.  Passed where a type constructor is
expected, it is the constructor its body names with the lambda's parameters left as holes; a generic alias
(`type alias Fail[A] = Result[A, String]`) is a lambda with a name.  There is no recursion and no matching on types, so
reduction always ends: a lambda's body is written outside itself, and an alias may not mention its own name with other arguments.
"""
from .ast import *   # noqa


class TypeLambdaError(Exception):
    pass


def _names(params):
    return [p.name for p in params]


def subst(t, binds):
    """`t` with each type parameter in `binds` replaced by its type; a bound constructor that is applied (`M[A]`) is reduced."""
    if not binds or t is None:
        return t
    c = t.__class__
    if c is TName:
        if len(t.path) == 1 and t.path[0] in binds:
            b = binds[t.path[0]]
            if not t.groups:
                return b
            args = [subst(x, binds) for x in t.groups[0]]
            r = apply_ctor(b, args)
            return TName(r.path, r.groups + [[subst(x, binds) for x in g] for g in t.groups[1:]], line=t.line) \
                if r.__class__ is TName and len(t.groups) > 1 else r
        return TName(t.path, [[subst(x, binds) for x in g] for g in t.groups], line=t.line) if t.groups else t
    if c is TTuple:
        return TTuple([(lab, subst(ft, binds)) for lab, ft in t.items], line=t.line)
    if c is TFn:
        return TFn([(lab, subst(pt, binds)) for lab, pt in t.params], subst(t.ret, binds), subst(t.recv, binds), line=t.line)
    if c is TUnion:
        return TUnion([subst(m, binds) for m in t.members], line=t.line)
    if c is TStatic:
        return TStatic(subst(t.inner, binds), line=t.line)
    if c is TAny:
        return TAny(subst(t.iface, binds), line=t.line)
    if c is TLambda:
        inner = {k: v for k, v in binds.items() if k not in _names(t.params)}
        return TLambda(t.params, subst(t.body, inner), line=t.line)
    if c is TApp:
        return reduce_app(TApp(subst(t.fn, binds), [[subst(x, binds) for x in g] for g in t.groups], line=t.line))
    return t


def apply_ctor(b, args):
    """The type `b` (a lambda, or a constructor with holes) applied to `args`."""
    if b.__class__ is TApp:
        b = reduce_app(b)
    if b.__class__ is TLambda:
        names = _names(b.params)
        if len(args) != len(names):
            raise TypeLambdaError(f"this type lambda takes {len(names)} type argument{'s' if len(names) != 1 else ''}, but {len(args)} given")
        return subst(b.body, dict(zip(names, args)))
    if b.__class__ is TName:
        if not b.groups:
            return TName(b.path, [list(args)], line=b.line)
        first, rest = list(b.groups[0]), b.groups[1:]
        holes = [i for i, x in enumerate(first) if x.__class__ is THole]
        if len(holes) != len(args):
            raise TypeLambdaError(f"`{b.path[-1]}` here is a constructor of {len(holes)} type argument{'s' if len(holes) != 1 else ''}, but {len(args)} given")
        for i, a in zip(holes, args):
            first[i] = a
        return TName(b.path, [first] + rest, line=b.line)
    raise TypeLambdaError("a type that is not a constructor was applied to type arguments")


def reduce_app(app):
    """`([A] -> T)[Int]` written out: the body with `A` replaced."""
    r = app.fn
    for g in app.groups:
        r = apply_ctor(r, list(g))
    return r


def as_ctor(lam):
    """A lambda passed where a constructor is expected: its body with the parameters left as holes."""
    body = lam.body
    if body.__class__ is TApp:
        body = reduce_app(body)
    holes = {p.name: THole(line=lam.line) for p in lam.params}
    return subst(body, holes)


def alias_lambda(tparams, body, line=0):
    return TLambda(list(tparams), body, line=line)
