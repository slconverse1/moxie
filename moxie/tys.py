"""The checker's types (check.py): what a program's expressions are known to be, and how they relate.

A type is `None` (not known: matches anything), a scalar name (`"Int"`, `"Float"`, `"String"`, `"Bool"`, `"Char"`, `"Unit"`,
`"Decimal"`), or a tuple tagged by its first item:

    ("bounded", lo, hi)        an integer range
    ("named", name)            a declared tuple, enum, or opaque type with no parameters
    ("secret",)                Secret
    ("app", head, args)        a generic type applied to arguments: Box[Int], List[T], Result[A, E]  (args may hold None)
    ("fn", params, ret)        a function type
    ("tup", items)             a tuple of types
    ("param", name)            a type parameter of the function being checked
    ("appv", name, args)       a type parameter applied to arguments: `F[A]` where `F[_]` is a constructor parameter
    ("ctor", head, fixed)      what such a parameter is bound to: `head` with `fixed` as its leading arguments (`Result[String, _]`)

Nothing here reports errors: the checker asks `compatible` and `unify` and words the message itself.  Unknown (`None`) and
parameters are wildcards in `compatible`, so a type the checker cannot work out never produces a false error.
"""

NUMERIC = {"Int", "Float", "Decimal"}


def show(t):
    if t is None:
        return "?"
    if isinstance(t, str):
        return {"Float": "Double"}.get(t, t)
    tag = t[0]
    if tag == "named":
        return t[1]
    if tag == "bounded":
        return f"Int[{t[1]}..={t[2]}]"
    if tag == "secret":
        return "Secret"
    if tag == "app":
        return f"{t[1]}[{', '.join(show(a) for a in t[2])}]" + (f"[{t[3]}]" if len(t) > 3 else "")
    if tag == "fn":
        ps = ", ".join(show(p) for p in t[1])
        return f"({ps}) -> {show(t[2])}"
    if tag == "tup":
        return "(" + ", ".join(show(i) for i in t[1]) + ")"
    if tag == "param":
        return t[1]
    if tag == "appv":
        return f"{t[1]}[{', '.join(show(a) for a in t[2])}]"
    if tag == "ctor":
        return f"{t[1]}[{', '.join([show(a) for a in t[2]] + ['_'])}]"
    return "?"


def is_wild(t):
    return t is None or (t.__class__ is tuple and t[0] in ("param", "appv", "ctor"))


def compatible(exp, act):
    """Could a value of type `act` be used where `exp` is expected?  Lenient on numbers (the checker's top-level rules own the
    strict integer checks) and on anything unknown."""
    if is_wild(exp) or is_wild(act) or exp == act:
        return True
    if isinstance(exp, str) and isinstance(act, str):
        return exp in NUMERIC and act in NUMERIC
    et = exp[0] if exp.__class__ is tuple else None
    at = act[0] if act.__class__ is tuple else None
    if et == "bounded":
        return act == "Int" or at == "bounded"
    if at == "bounded":
        return exp == "Int" or exp in NUMERIC
    if et == "app" and at == "app":
        if len(exp) > 3 and len(act) > 3 and exp[3] != act[3]:
            return False
        return exp[1] == act[1] and len(exp[2]) == len(act[2]) and all(compatible(x, y) for x, y in zip(exp[2], act[2]))
    if et == "fn" and at == "fn":
        if len(exp[1]) != len(act[1]):
            return True      # arities differ legitimately (callbacks, tuple unpacking)
        return all(compatible(x, y) for x, y in zip(exp[1], act[1])) and compatible(exp[2], act[2])
    if et == "tup" and at == "tup":
        return len(exp[1]) == len(act[1]) and all(compatible(x, y) for x, y in zip(exp[1], act[1]))
    return False


def subst(t, binds):
    """`t` with each ("param", n) replaced by `binds[n]`, or by None (unknown) when `n` has no binding."""
    if t.__class__ is not tuple:
        return t
    tag = t[0]
    if tag == "param":
        return binds.get(t[1])
    if tag == "appv":
        c = binds.get(t[1])
        args = tuple(subst(a, binds) for a in t[2])
        if c.__class__ is tuple and c[0] == "ctor":
            return ("app", c[1], tuple(c[2]) + args)
        return None
    if tag == "app":
        return ("app", t[1], tuple(subst(a, binds) for a in t[2])) + t[3:]
    if tag == "fn":
        return ("fn", tuple(subst(p, binds) for p in t[1]), subst(t[2], binds))
    if tag == "tup":
        return ("tup", tuple(subst(i, binds) for i in t[1]))
    return t


def params_in(t, out=None):
    out = set() if out is None else out
    if t.__class__ is tuple:
        if t[0] == "param":
            out.add(t[1])
        elif t[0] == "appv":
            out.add(t[1])
            for a in t[2]:
                params_in(a, out)
        elif t[0] == "app":
            for a in t[2]:
                params_in(a, out)
        elif t[0] == "fn":
            for p in t[1]:
                params_in(p, out)
            params_in(t[2], out)
        elif t[0] == "tup":
            for i in t[1]:
                params_in(i, out)
    return out


def join(a, b):
    """The one type two values for the same parameter share, or the string "conflict"; unknown gives way."""
    if a is None:
        return b
    if b is None or a == b:
        return a
    if isinstance(a, str) and isinstance(b, str) and a in NUMERIC and b in NUMERIC:
        rank = {"Int": 0, "Float": 1, "Decimal": 2}
        return a if rank[a] >= rank[b] else b      # 1 and 2.5 for one T: the wider number
    ab = ("Int" if a.__class__ is tuple and a[0] == "bounded" else a)
    bb = ("Int" if b.__class__ is tuple and b[0] == "bounded" else b)
    if ab == bb and not (ab.__class__ is tuple and ab[0] in ("app", "fn", "tup", "param")):
        return ab
    if a.__class__ is tuple and b.__class__ is tuple and a[0] == b[0] == "app" and a[1] == b[1] and len(a[2]) == len(b[2]):
        parts = [join(x, y) for x, y in zip(a[2], b[2])]
        return "conflict" if "conflict" in parts else ("app", a[1], tuple(parts)) + (a[3:] if a[3:] == b[3:] else ())
    if a.__class__ is tuple and b.__class__ is tuple and a[0] == b[0] == "tup" and len(a[1]) == len(b[1]):
        parts = [join(x, y) for x, y in zip(a[1], b[1])]
        return "conflict" if "conflict" in parts else ("tup", tuple(parts))
    if a.__class__ is tuple and b.__class__ is tuple and a[0] == b[0] == "fn" and len(a[1]) == len(b[1]):
        parts = [join(x, y) for x, y in zip(a[1], b[1])] + [join(a[2], b[2])]
        return "conflict" if "conflict" in parts else ("fn", tuple(parts[:-1]), parts[-1])
    return "conflict"


def unify(pat, act, binds):
    """Bind the parameters in `pat` from the type `act`.  Returns None when it fits, else a pair (expected, found) naming the
    clash.  A parameter bound twice must agree (`join`)."""
    if pat is None or act is None:
        return None
    if pat.__class__ is tuple and pat[0] == "param":
        if act.__class__ is tuple and act[0] == "param":
            return None
        cur = binds.get(pat[1])
        j = join(cur, act)
        if j == "conflict":
            return (cur, act)
        binds[pat[1]] = j
        return None
    if pat.__class__ is not tuple or act.__class__ is not tuple:
        return None
    if pat[0] == "appv":
        n = len(pat[2])
        if act[0] == "app" and len(act[2]) >= n:
            keep = len(act[2]) - n
            c = ("ctor", act[1], tuple(act[2][:keep]))
            cur = binds.get(pat[1])
            if cur is not None and cur != c:
                return (cur, c)
            binds[pat[1]] = c
            for x, y in zip(pat[2], act[2][keep:]):
                r = unify(x, y, binds)
                if r:
                    return r
        elif act[0] == "appv" and act[1] == pat[1] and len(act[2]) == n:
            for x, y in zip(pat[2], act[2]):
                r = unify(x, y, binds)
                if r:
                    return r
        return None
    if pat[0] == act[0] == "app" and (pat[1] == act[1] or (pat[1] == "Seq" and act[1] in SEQ_HEADS)) and len(pat[2]) == len(act[2]):
        for x, y in zip(pat[2], act[2]):
            r = unify(x, y, binds)
            if r:
                return r
    elif pat[0] == act[0] == "fn" and len(pat[1]) == len(act[1]):
        for x, y in zip(pat[1], act[1]):
            r = unify(x, y, binds)
            if r:
                return r
        return unify(pat[2], act[2], binds)
    elif pat[0] == act[0] == "tup" and len(pat[1]) == len(act[1]):
        for x, y in zip(pat[1], act[1]):
            r = unify(x, y, binds)
            if r:
                return r
    return None


SEQ_HEADS = {"List", "Array", "Set", "Ring", "Stream"}


def match(pat, act, binds):
    """Strict version of `unify` for choosing an overload: False when `act` cannot be what `pat` describes.  Unknown matches.
    `Seq[T]` in a pattern is any source of T."""
    if pat is None or act is None:
        return True
    pt = pat[0] if pat.__class__ is tuple else None
    at = act[0] if act.__class__ is tuple else None
    if pt == "param":
        if at == "param":
            return True
        j = join(binds.get(pat[1]), act)
        if j == "conflict":
            return False
        binds[pat[1]] = j
        return True
    if at in ("param", "appv", "ctor") or pt in ("appv", "ctor"):
        return True
    if pt == "app":
        if at != "app":
            return False
        if pat[1] == "Seq":
            return act[1] in SEQ_HEADS and len(act[2]) == 1 and match(pat[2][0], act[2][0], binds)
        return pat[1] == act[1] and len(pat[2]) == len(act[2]) and all(match(x, y, binds) for x, y in zip(pat[2], act[2]))
    if pt == "fn":
        if at != "fn":
            return False
        if len(pat[1]) != len(act[1]):
            return False
        return all(match(x, y, binds) for x, y in zip(pat[1], act[1])) and match(pat[2], act[2], binds)
    if pt == "tup":
        return at == "tup" and len(pat[1]) == len(act[1]) and all(match(x, y, binds) for x, y in zip(pat[1], act[1]))
    return compatible(pat, act)
