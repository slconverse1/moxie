"""Units of measure: dimension arithmetic.  A dimension is a sorted tuple of (base unit, exponent) pairs; the empty tuple is a plain number.
Units exist only in the checker; at run time a `5.0 m` is just 5.0."""
import re

TOK = re.compile(r"\s*(?:([A-Za-z_][A-Za-z_0-9]*)|(-?\d+)|(.))")


def norm(d):
    out = {}
    for n, e in d:
        out[n] = out.get(n, 0) + e
    return tuple(sorted((n, e) for n, e in out.items() if e))


def mul(a, b):
    return norm(tuple(a) + tuple(b))


def inv(a):
    return tuple((n, -e) for n, e in a)


def div(a, b):
    return mul(a, inv(b))


def power(a, k):
    return norm(tuple((n, e * k) for n, e in a))


def parse_text(s):
    """`m/s^2` or `kg*m/s^2` -> [(name, exp)] as written, or None when it is not a unit expression."""
    toks = [m.groups() for m in TOK.finditer(s) if any(m.groups())]
    pos, out, sign = 0, [], 1
    expect_name = True
    while pos < len(toks):
        name, num, op = toks[pos]
        if expect_name:
            if not name:
                return None
            exp = 1
            pos += 1
            if pos < len(toks) and toks[pos][2] == "^":
                if pos + 1 >= len(toks) or not toks[pos + 1][1]:
                    return None
                exp = int(toks[pos + 1][1])
                pos += 2
            out.append((name, sign * exp))
            expect_name = False
        else:
            if op == "*":
                sign = 1
            elif op == "/":
                sign = -1
            else:
                return None
            pos += 1
            expect_name = True
    return out if out and not expect_name else None


def from_expr(e):
    """The unit expression an AST type argument spells (`m/s^2`), as [(name, exp)], or None."""
    c = e.__class__.__name__
    if c == "Name":
        return [(e.name, 1)]
    if c == "IntLit" and e.v == 1:
        return []
    if c == "Binary" and e.op in ("*", "/"):
        l, r = from_expr(e.l), from_expr(e.r)
        if l is None or r is None:
            return None
        return l + (r if e.op == "*" else [(n, -x) for n, x in r])
    if c == "Binary" and e.op == "^" and e.r.__class__.__name__ == "IntLit" and e.l.__class__.__name__ == "Name":
        return [(e.l.name, e.r.v)]
    return None
