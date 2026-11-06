"""The checker's types (check.py): what a program's expressions are known to be, and how they relate.

A type is `None` (not known: matches anything), a scalar name (`"Int"`, `"Float"`, `"String"`, `"Bool"`, `"Char"`, `"Unit"`,
`"Decimal"`), or a tuple tagged by its first item:

    ("bounded", lo, hi)        an integer range
    ("named", name)            a declared tuple, enum, or opaque type with no parameters
    ("secret",)                Secret
    ("app", head, args)        a generic type applied to arguments: Box[Int], List[T], Result[A, E]  (args may hold None)
    ("fn", params, ret)        a function type
    ("hid", key, member)       the hidden type of one `any` value: `a.Item` for the parameter a (key "a@line"); fits only itself
    ("tup", items[, labels])   a tuple of types; labels (a tuple of names or None, one per item) when it has field names:
                               (id: Int, name: String).  Labels do not take part in compatible/unify (a tuple is checked by position);
                               they are what a type function matches on.  In a type function's arm a label may be ("pvar", n) or ("param", n)
    ("param", name)            a type parameter of a function being called (bound by unification at the call)
    ("rigid", name)            a type parameter of the function being checked: only itself fits it
    ("lit", n)                 a number as a type (`0`, `1 + Length[Rest]`), for type functions
    ("slit", s)                a string as a type (`"id" -> Int` in a type function)
    ("sz", op, l, r)           arithmetic on type-level numbers (symbolic until both sides are numbers)
    ("pvar", name)             a pattern variable of a type function (`X` in `Array[X][N] -> X`)
    ("tapp", name, args)       a type function applied to arguments that do not yet decide it (symbolic; reduces once they do)
    ("spread", t)              inside ("tup", items): the items of the tuple type t, spliced in once t is known
    ("app", head, args, size)  and size is an int, ("param", n), or ("sz", op, left, right) for `N - 1`
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
        return f"{t[1]}[{', '.join(show(a) for a in t[2])}]" + (f"[{show_size(t[3])}]" if len(t) > 3 and t[3] is not None else "")
    if tag == "fn":
        ps = ", ".join(show(p) for p in t[1])
        return f"({ps}) -> {show(t[2])}"
    if tag == "tup":
        labs = t[2] if len(t) > 2 else (None,) * len(t[1])
        return "(" + ", ".join((f"{show_label(l)}: " if l is not None else "") + show(i) for l, i in zip(labs, t[1])) + ")"
    if tag == "spread":
        return "..." + show(t[1])
    if tag == "lit":
        return str(t[1])
    if tag == "slit":
        return '"' + t[1] + '"'
    if tag == "sz":
        return f"{show(t[2])} {t[1]} {show(t[3])}"
    if tag == "hid":                                       # the member type of one `any` value: a.Item
        return f"{t[1].split('@')[0]}.{t[2]}"
    if tag == "tapp":
        if t[1].startswith("@"):                           # an associated type: C.Item
            return f"{show(t[2][0])}.{t[1][1:]}"
        return f"{t[1]}[{', '.join(show(a) for a in t[2])}]"
    if tag in ("param", "rigid", "pvar"):
        return t[1]
    if tag == "appv":
        return f"{t[1]}[{', '.join(show(a) for a in t[2])}]"
    if tag == "ctor":
        return f"{t[1]}[{', '.join([show(a) for a in t[2]] + ['_'])}]"
    return "?"


def show_label(l):
    return l if isinstance(l, str) else show(l)


def show_size(s):
    if s.__class__ is tuple and s[0] == "sz":
        return f"{show_size(s[2])} {s[1]} {show_size(s[3])}"
    if s.__class__ is tuple:
        return s[1]
    return str(s)


def size_subst(s, binds):
    if s.__class__ is not tuple:
        return s
    if s[0] == "lit":
        return s[1]
    if s[0] in ("param", "pvar"):
        v = binds.get(s[1], s)
        if v.__class__ is tuple and v[0] == "lit":
            return v[1]
        return v if v.__class__ is int or (v.__class__ is tuple and v[0] in ("param", "pvar", "sz")) else None
    if s[0] == "sz":
        a, b = size_subst(s[2], binds), size_subst(s[3], binds)
        if a.__class__ is int and b.__class__ is int:
            return {"+": a + b, "-": a - b, "*": a * b}[s[1]]
        return None if a is None or b is None else ("sz", s[1], a, b)
    return s


def is_wild(t):
    return t is None or (t.__class__ is tuple and t[0] in ("param", "appv", "ctor"))


def compatible(exp, act):
    """Could a value of type `act` be used where `exp` is expected?  Lenient on numbers (the checker's top-level rules own the
    strict integer checks) and on anything unknown."""
    if is_wild(exp) or is_wild(act) or exp == act:
        return True
    if (exp.__class__ is tuple and exp[0] in ("rigid", "tapp", "hid")) or (act.__class__ is tuple and act[0] in ("rigid", "tapp", "hid")):
        return False                      # a type parameter of the function being checked fits only itself
    if isinstance(exp, str) and isinstance(act, str):
        return exp in NUMERIC and act in NUMERIC
    et = exp[0] if exp.__class__ is tuple else None
    at = act[0] if act.__class__ is tuple else None
    if (et == "lit" and act == "Int") or (act.__class__ is tuple and at == "lit" and exp == "Int"):
        return True
    if (et == "slit" and act == "String") or (at == "slit" and exp == "String"):
        return True
    if et == "bounded":
        return act == "Int" or at == "bounded"
    if at == "bounded":
        return exp == "Int" or exp in NUMERIC
    if et == "app" and at == "app":
        if len(exp) > 3 and len(act) > 3 and exp[3].__class__ is int and act[3].__class__ is int and exp[3] != act[3]:
            return False
        return exp[1] == act[1] and len(exp[2]) == len(act[2]) and all(compatible(x, y) for x, y in zip(exp[2], act[2]))
    if et == "fn" and at == "fn":
        if len(exp[1]) != len(act[1]):
            return True      # arities differ legitimately (callbacks, tuple unpacking)
        return all(compatible(x, y) for x, y in zip(exp[1], act[1])) and compatible(exp[2], act[2])
    if (et == "tup" and at in ("named", "app")) or (at == "tup" and et in ("named", "app")):
        return True          # a tuple literal may stand for a declared tuple: its fields are checked where it is built
    if et == "tup" and at == "tup":
        return len(exp[1]) == len(act[1]) and all(compatible(x, y) for x, y in zip(exp[1], act[1]))
    return False


def subst(t, binds):
    """`t` with each ("param", n) replaced by `binds[n]`, or by None (unknown) when `n` has no binding."""
    if t.__class__ is not tuple:
        return t
    tag = t[0]
    if tag in ("param", "pvar"):
        v = binds.get(t[1], t) if _PARTIAL[0] else binds.get(t[1])
        return ("lit", v) if v.__class__ is int and not isinstance(v, bool) else v
    if tag == "sz":
        a, b = subst(t[2], binds), subst(t[3], binds)
        if a.__class__ is tuple and b.__class__ is tuple and a[0] == "lit" and b[0] == "lit":
            return ("lit", {"+": a[1] + b[1], "-": a[1] - b[1], "*": a[1] * b[1]}[t[1]])
        if a.__class__ is tuple and b.__class__ is tuple and a[0] == "slit" and b[0] == "slit" and t[1] == "+":
            return ("slit", a[1] + b[1])
        if a is None or b is None:
            return None
        return ("sz", t[1], a, b)
    if tag == "appv":
        c = binds.get(t[1])
        args = tuple(subst(a, binds) for a in t[2])
        if c.__class__ is tuple and c[0] == "ctor":
            return ("app", c[1], tuple(c[2]) + args)
        return None
    if tag == "app":
        return ("app", t[1], tuple(subst(a, binds) for a in t[2])) + ((size_subst(t[3], binds),) if len(t) > 3 else ())
    if tag == "tapp":
        args = tuple(subst(a, binds) for a in t[2])
        if REDUCER is not None:
            return REDUCER(t[1], args)
        return ("tapp", t[1], args)
    if tag == "fn":
        return ("fn", tuple(subst(p, binds) for p in t[1]), subst(t[2], binds))
    if tag == "tup":
        out, labs = [], []
        tl = t[2] if len(t) > 2 else (None,) * len(t[1])
        for i, lab in zip(t[1], tl):
            if i.__class__ is tuple and i[0] == "spread":
                r = subst(i[1], binds)
                if r.__class__ is tuple and r[0] == "tup":
                    out.extend(r[1])
                    labs.extend(r[2] if len(r) > 2 else (None,) * len(r[1]))
                elif r == "Unit":
                    pass
                elif r is None:
                    return None                    # the rest of the tuple is unknown, so the tuple is
                else:
                    out.append(("spread", r))
                    labs.append(None)
            else:
                out.append(subst(i, binds))
                labs.append(_label_subst(lab, binds))
        return ("tup", tuple(out), tuple(labs)) if any(l is not None for l in labs) else ("tup", tuple(out))
    if tag == "spread":
        return ("spread", subst(t[1], binds))
    return t


_PARTIAL = [False]


def _label_subst(lab, binds):
    """A label that is a variable becomes the name its binding (a string type) gives; one that is not bound yet stays."""
    if lab.__class__ is not tuple:
        return lab
    v = binds.get(lab[1])
    if v.__class__ is tuple and v[0] == "slit":
        return v[1]
    if v is None and not _PARTIAL[0]:
        return None
    return lab


def subst_partial(t, binds):
    """`subst` that leaves the parameters `binds` does not name alone (the pattern variables of a type function's arms)."""
    _PARTIAL[0] = True
    try:
        return subst(t, binds)
    finally:
        _PARTIAL[0] = False


IMPLEMENTS = None        # set by the checker: (type, interface name) -> True / False / None
UNFOLD = None           # set by the checker: a declared tuple type -> the same as a labeled ("tup", ...), or None
REDUCER = None          # set by the checker: (name, args) -> the reduced type, or a symbolic ("tapp", name, args)


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
        elif t[0] == "spread":
            params_in(t[1], out)
        elif t[0] == "tapp":
            for a in t[2]:
                params_in(a, out)
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
        if "conflict" in parts:
            return "conflict"
        la, lb = (a[2] if len(a) > 2 else None), (b[2] if len(b) > 2 else None)
        return ("tup", tuple(parts)) + ((la,) if la is not None and la == lb else ())
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


def match(pat, act, binds, strict=False):
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
    if at in ("param", "appv", "ctor", "tapp") or pt in ("appv", "ctor", "tapp"):
        return True
    if pt == "app":
        if at != "app":
            return False
        if pat[1] == "Seq":
            return act[1] in SEQ_HEADS and len(act[2]) == 1 and match(pat[2][0], act[2][0], binds, strict)
        return pat[1] == act[1] and len(pat[2]) == len(act[2]) and all(match(x, y, binds, strict) for x, y in zip(pat[2], act[2]))
    if pt == "fn":
        if at != "fn":
            return False
        if len(pat[1]) != len(act[1]):
            return False
        return all(match(x, y, binds, strict) for x, y in zip(pat[1], act[1])) and match(pat[2], act[2], binds, strict)
    if pt == "tup":
        return at == "tup" and len(pat[1]) == len(act[1]) and all(match(x, y, binds, strict) for x, y in zip(pat[1], act[1]))
    if strict and isinstance(pat, str) and isinstance(act, str):
        return pat == act
    if strict and isinstance(pat, str) and at == "bounded":
        return pat == "Int"
    return compatible(pat, act)


def _stuck(a):
    """"unk" when a type is not known, "sym" when it is a parameter or an unreduced function (it will be known later), else None."""
    if a is None:
        return "unk"
    if a.__class__ is tuple and a[0] in ("rigid", "param", "tapp", "appv", "ctor", "sz"):
        return "sym"
    return None


def _combine(rs):
    if "no" in rs:
        return "no"
    for r in ("unk", "sym"):
        if r in rs:
            return r
    return "yes"


def tmatch(pat, act, binds):
    """Match the type `act` against the pattern `pat` of a type function.  Pattern variables are ("param", n); None matches anything.
    Returns "yes" (binds filled in), "no", or "unk"/"sym" when `act` is not known well enough to say."""
    if pat is None:
        return "yes"
    if pat.__class__ is tuple and pat[0] == "tup" and not pat[1]:
        pat = "Unit"                                   # the empty tuple type is Unit
    if act.__class__ is tuple and act[0] == "tup" and not act[1]:
        act = "Unit"
    pt = pat[0] if pat.__class__ is tuple else None
    if pt == "bound":                                   # X: Iface  matches any type that implements Iface
        st = _stuck(act)
        if st:
            return st
        ok = IMPLEMENTS(act, pat[2]) if IMPLEMENTS is not None else None
        if ok is None:
            return "unk"
        return tmatch(pat[1], act, binds) if ok else "no"
    if pt == "pvar":
        if pat[1] in binds:
            cur = binds[pat[1]]
            if cur == act:
                return "yes"
            return _stuck(cur) or _stuck(act) or "no"
        binds[pat[1]] = act
        return "yes"
    st = _stuck(act)
    if st:
        return st
    if pt == "tup":
        items = list(pat[1])
        if act == "Unit":
            act = ("tup", ())
        if act.__class__ is tuple and act[0] in ("named", "app") and UNFOLD is not None:
            act = UNFOLD(act) or act                    # a declared tuple is its fields, named
        if act.__class__ is not tuple or act[0] != "tup":
            return "no"
        pl = list(pat[2]) if len(pat) > 2 else [None] * len(items)
        al = list(act[2]) if len(act) > 2 else [None] * len(act[1])
        return _tup_match(items, list(act[1]), binds, pl, al)
    if pt == "app":
        if act.__class__ is not tuple or act[0] != "app" or act[1] != pat[1] or len(act[2]) != len(pat[2]):
            return "no"
        rs = [tmatch(x, y, binds) for x, y in zip(pat[2], act[2])]
        if len(pat) > 3 and pat[3] is not None:
            ps, as_ = pat[3], (act[3] if len(act) > 3 else None)
            if ps.__class__ is tuple and ps[0] == "pvar":
                binds[ps[1]] = as_
            elif as_.__class__ is int and ps != as_:
                rs.append("no")
        return _combine(rs)
    if pt == "appv":
        if act.__class__ is tuple and act[0] == "app" and len(act[2]) >= len(pat[2]):
            keep = len(act[2]) - len(pat[2])
            binds[pat[1]] = ("ctor", act[1], tuple(act[2][:keep]))
            return _combine([tmatch(x, y, binds) for x, y in zip(pat[2], act[2][keep:])])
        return "no"
    if pt == "fn":
        if act.__class__ is not tuple or act[0] != "fn" or len(act[1]) != len(pat[1]):
            return "no"
        return _combine([tmatch(x, y, binds) for x, y in zip(pat[1], act[1])] + [tmatch(pat[2], act[2], binds)])
    if pat.__class__ is tuple and act.__class__ is tuple:
        return "yes" if pat == act else "no"
    if act.__class__ is tuple and act[0] == "bounded":
        act = "Int"
    return "yes" if pat == act else "no"


def _label_match(pl, al, binds):
    """A pattern's label against the item's: None matches anything; a variable binds the name as a string type; a string type
    (a parameter already filled in) must be that name."""
    if pl is None:
        return "yes"
    if al is None:
        return "no"
    if pl.__class__ is tuple:
        if pl[0] == "pvar":
            return tmatch(pl, ("slit", al), binds)
        if pl[0] == "slit":
            return "yes" if pl[1] == al else "no"
        return _stuck(pl) or "no"
    return "yes" if pl == al else "no"


def _tup_match(items, acts, binds, pl, al):
    spread = [i for i, x in enumerate(items) if x.__class__ is tuple and x[0] == "spread"]
    if not spread:
        if len(items) != len(acts):
            return "no"
        return _combine([_combine([_label_match(a, b, binds), tmatch(x, y, binds)]) for a, b, x, y in zip(pl, al, items, acts)])
    k = spread[0]
    before, after = items[:k], items[k + 1:]
    if len(acts) < len(before) + len(after):
        return "no"
    nb, na = len(before), len(after)
    mid = acts[nb:len(acts) - na]
    midl = al[nb:len(acts) - na]
    rs = []
    for lab, alab, x, y in zip(pl[:nb], al[:nb], before, acts[:nb]):
        rs += [_label_match(lab, alab, binds), tmatch(x, y, binds)]
    for lab, alab, x, y in zip(pl[k + 1:], al[len(acts) - na:], after, acts[len(acts) - na:]):
        rs += [_label_match(lab, alab, binds), tmatch(x, y, binds)]
    inner = items[k][1]
    rest = ("tup", tuple(mid), tuple(midl)) if any(l is not None for l in midl) else ("tup", tuple(mid))
    rs.append(tmatch(inner, rest, binds))
    return _combine(rs)


def tree_size(t, memo=None):
    """The number of nodes in a type written out as a tree (a type that holds the same part twice counts it twice); cheap even when
    the parts are shared, so a type that is doubling in size at every step is seen before it is walked."""
    memo = {} if memo is None else memo
    if t.__class__ is not tuple:
        return 1
    k = id(t)
    if k in memo:
        return memo[k]
    n = 1
    for x in t[1:]:
        if x.__class__ is tuple:
            if x and x[0].__class__ is str:
                n += tree_size(x, memo)
            else:
                n += sum(tree_size(y, memo) for y in x)
    memo[k] = n
    return n
