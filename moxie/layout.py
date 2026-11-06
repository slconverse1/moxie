"""Sizes of values and of pool slots in moxie without a collector (Spec section 3, value layout; section 3a).

A scalar has its natural width, a tuple is its fields in order with alignment padding, an enum is a one-byte tag
plus the largest case, `String[n]` is a length word plus n bytes, and `Array[T][n]` is n elements.  The size of a type
that has no fixed layout (a plain `String`, a generic type, a type from another package) is not known.
"""
from .ast import *   # noqa

SCALARS = {"Int": 8, "UInt": 8, "Int8": 1, "UInt8": 1, "Byte": 1, "Int16": 2, "UInt16": 2, "Int32": 4, "UInt32": 4,
           "Int64": 8, "UInt64": 8, "Float": 4, "Double": 8, "Bool": 1, "Char": 4, "Unit": 0}
WORD = 8

# What a pool slot holds apart from the values in it (to be tuned): the runtime's bookkeeping for one resource.
SLOT = {"Atom": 16, "Cancel": 16, "Chan": 64, "Timer": 32, "Future": 32, "Io file": 64, "Io socket": 64, "Listener": 32,
        "Connection": 128}
HANDLE = WORD            # a foreign handle is one word (Spec section 19)


def _round(n, a):
    return (n + a - 1) // a * a if a > 1 else n


def _const(t):
    if t.__class__ is TExpr and t.expr.__class__ is IntLit:
        return t.expr.v
    return None


def layout(t, decls, depth=0):
    """(size, align) of the type `t`, or None when it has no fixed size.  `decls` maps names to tuple and enum declarations."""
    if depth > 20:
        return None
    c = t.__class__
    if c is TTuple:
        return _fields([ft for _, ft in t.items], decls, depth)
    if c is not TName or len(t.path) != 1:
        return None
    name = t.path[0]
    g = t.groups
    if name in SCALARS and not g:
        s = SCALARS[name]
        return s, max(s, 1)
    if name == "Secret" and len(g) == 1 and len(g[0]) == 1 and "Secret" not in decls:
        return layout(g[0][0], decls, depth + 1)      # a Secret is its value with a different name
    if name == "String" and len(g) == 1 and len(g[0]) == 1 and _const(g[0][0]) is not None:
        return WORD + _const(g[0][0]), WORD
    if name in ("Array", "List") and len(g) == 2 and len(g[0]) == 1 and len(g[1]) == 1 and _const(g[1][0]) is not None:
        e = layout(g[0][0], decls, depth + 1)
        if e is None:
            return None
        n = e[0] * _const(g[1][0]) + (WORD if name == "List" else 0)
        return _round(n, WORD), WORD
    d = decls.get(name)
    if d is None or g:
        return None
    if d.__class__ is TupleDecl:
        if d.tparams:
            return None
        return _fields([f.type for f in d.fields], decls, depth)
    if d.__class__ is EnumDecl and not d.tparams:
        best, al = 0, 1
        for cs in d.cases:
            if cs.fields:
                r = _fields([getattr(f, "type", None) or f for f in cs.fields], decls, depth)
                if r is None:
                    return None
                best, al = max(best, r[0]), max(al, r[1])
        return _round(_round(1, al) + best, al), al
    return None


def _fields(types, decls, depth):
    off, al = 0, 1
    for ft in types:
        r = layout(ft, decls, depth + 1)
        if r is None:
            return None
        off = _round(off, r[1]) + r[0]
        al = max(al, r[1])
    return _round(off, al), al


def type_decls(prog):
    return {st.name: st for st in prog.stmts if st.__class__ in (TupleDecl, EnumDecl)}


def slot_bytes(kind, call, decls):
    """(bytes, why) for one creation of `kind` by `call`: bytes is None when the size is not known, and why says what to write."""
    if kind.startswith("handle "):
        return HANDLE, None
    base = SLOT.get(kind)
    if base is None:
        return None, f"no slot size for {kind}"
    groups = call.fn.groups if call.fn.__class__ is GenApp else []
    if kind == "Chan" and call.fn.__class__ is Name and call.fn.name == "signals":
        return base + 8 * 8, None       # eight keywords
    if kind == "Chan" and call.fn.__class__ is Name and call.fn.name == "watch":
        return base + 16 * 272, None    # sixteen changes (a path of up to 255 bytes and a keyword each; to be tuned)
    if kind == "Chan":
        if not groups or len(groups[0]) != 1:
            return None, "a Chan needs its element type, as in Chan[Int][4]()"
        e = layout(groups[0][0], decls)
        if e is None:
            return None, "the element type of a Chan has no fixed size (use a type with a known layout, such as String[n])"
        cap = 0
        if len(groups) > 1:
            cap = _const(groups[1][0]) if len(groups[1]) == 1 else None
            if cap is None:
                return None, "a Chan capacity is not a constant"
        return base + cap * e[0], None
    if kind in ("Atom", "Future"):
        if groups and len(groups[0]) == 1:
            e = layout(groups[0][0], decls)
            if e is None:
                return None, f"the value type of an {kind} has no fixed size"
            return base + e[0], None
        if kind == "Atom" and len(call.args) == 1:
            v = call.args[0].expr
            lit = {IntLit: 8, FloatLit: 8, BoolLit: 1}.get(v.__class__)
            if lit is not None:
                return base + lit, None
        return None, f"write the type of the {kind}, as in {kind}[Int]" + ("(0)" if kind == "Atom" else "()")
    return base, None
