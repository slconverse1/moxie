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


NUM = re.compile(r"\s*(\d+(?:\.\d+)?)\s+(.*)$", re.S)


def split_scale(text):
    """`1000 m` -> (1000, "m"); `kg*m/s^2` -> (None, "kg*m/s^2").  A whole number stays an int, so scaled Int quantities stay exact."""
    m = NUM.match(text)
    if not m:
        return None, text
    s = m.group(1)
    return (float(s) if "." in s else int(s)), m.group(2)


def scale_of(pairs, table):
    """The factor that turns a quantity written in these units into the base units: `km/h` -> 1000/3600.  `table` maps unit name to its factor."""
    f = 1
    for nm, e in pairs:
        s = table.get(nm, 1)
        f = f * (s ** e if e >= 0 else 1 / (s ** -e))
    if isinstance(f, float) and f == int(f) and abs(f) < 2 ** 53:
        return int(f) if all(isinstance(table.get(nm, 1), int) for nm, _e in pairs) and all(e >= 0 for _n, e in pairs) else f
    return f


def decl_scale(text, table):
    """The factor of `unit NAME = text` (a leading number times other units), 1 for a base unit."""
    if text is None:
        return 1
    lead, rest = split_scale(text)
    pairs = parse_text(rest) or []
    f = scale_of(pairs, table)
    return f if lead is None else lead * f
