"""A small solver for refinement conditions (Spec 9c): linear integer arithmetic with `and`, `or`, `not`.

A *linear form* is `({atom: coefficient}, constant)`, an atom being a name, a length (`len(xs)`) or a field path.  A *formula* is
one of `("ge", lin)` (the form is >= 0), `("eq", lin)` (the form is 0), `("and", [f, ...])`, `("or", [f, ...])`, `TRUE`, `FALSE`.
`proves(facts, goal)` says whether the facts (a list of formulas) imply the goal: `"yes"`, `"no"` (the facts rule the goal out),
or `"unknown"`.  It is sound and incomplete: it eliminates variables as rationals (Fourier-Motzkin) after tightening each
constraint to integers, so what it proves is true, and what it can't prove is left to a run-time check or a guard.
"""
from math import gcd

TRUE = ("and", [])
FALSE = ("or", [])
MAX_CLAUSES = 256          # a goal or fact with more alternatives than this is not tried
MAX_ROWS = 1500            # the elimination gives up (unknown) beyond this many constraints


# ------------------------------------------------------------------ linear forms
def const(k):
    return ({}, k)


def atom(a):
    return ({a: 1}, 0)


def add(x, y):
    d = dict(x[0])
    for a, c in y[0].items():
        d[a] = d.get(a, 0) + c
        if d[a] == 0:
            del d[a]
    return (d, x[1] + y[1])


def scale(x, k):
    if k == 0:
        return ({}, 0)
    return ({a: c * k for a, c in x[0].items()}, x[1] * k)


def sub(x, y):
    return add(x, scale(y, -1))


def is_const(x):
    return not x[0]


# ------------------------------------------------------------------ formulas
def compare(op, l, r):
    """The formula for `l op r` over linear forms."""
    d = sub(l, r)                       # l - r
    if op == ">=":
        return ("ge", d)
    if op == ">":
        return ("ge", add(d, const(-1)))
    if op == "<=":
        return ("ge", scale(d, -1))
    if op == "<":
        return ("ge", add(scale(d, -1), const(-1)))
    if op == "==":
        return ("eq", d)
    if op == "~=":
        return ("or", [("ge", add(d, const(-1))), ("ge", add(scale(d, -1), const(-1)))])
    raise ValueError(op)


def neg(f):
    k = f[0]
    if k == "ge":
        return ("ge", add(scale(f[1], -1), const(-1)))          # not (x >= 0) is x <= -1
    if k == "eq":
        return ("or", [("ge", add(f[1], const(-1))), ("ge", add(scale(f[1], -1), const(-1)))])
    if k == "and":
        return ("or", [neg(g) for g in f[1]])
    return ("and", [neg(g) for g in f[1]])


def conj(*fs):
    return ("and", [f for f in fs if f is not None])


def disj(*fs):
    return ("or", list(fs))


# ------------------------------------------------------------------ deciding
def clauses(f, limit=MAX_CLAUSES):
    """The formula as a list of alternatives, each a list of `ge`/`eq` constraints (disjunctive normal form), or None if too big."""
    k = f[0]
    if k in ("ge", "eq"):
        return [[f]]
    if k == "or":
        out = []
        for g in f[1]:
            c = clauses(g, limit)
            if c is None:
                return None
            out.extend(c)
            if len(out) > limit:
                return None
        return out
    out = [[]]
    for g in f[1]:
        c = clauses(g, limit)
        if c is None:
            return None
        out = [a + b for a in out for b in c]
        if len(out) > limit:
            return None
    return out


def _rows(cs):
    """Constraints as rows `(coeffs, k)` meaning sum + k >= 0, each tightened to integers."""
    rows = []
    for c in cs:
        lin = c[1]
        pieces = [lin] if c[0] == "ge" else [lin, scale(lin, -1)]
        for p in pieces:
            r = _tighten(p)
            if r is not None:
                rows.append(r)
    return rows


def _tighten(p):
    coeffs, k = p
    if not coeffs:
        return ({}, k)
    g = 0
    for c in coeffs.values():
        g = gcd(g, abs(c))
    if g > 1:
        coeffs = {a: c // g for a, c in coeffs.items()}
        k = k // g                      # floor: sum >= -k/g, and sum is an integer
    return (coeffs, k)


def unsat(clause, atoms_nonneg=()):
    """True when the constraints of one clause have no (rational) solution after tightening: so no integer one either."""
    rows = _rows(clause)
    for a in atoms_nonneg:
        rows.append(({a: 1}, 0))
    seen = set()
    while True:
        for c, k in rows:
            if not c and k < 0:
                return True
        vars_ = set()
        for c, _k in rows:
            vars_.update(c)
        if not vars_:
            return False
        # eliminate the variable that makes the fewest new rows
        best, best_n = None, None
        for v in vars_:
            lo = sum(1 for c, _k in rows if c.get(v, 0) > 0)
            hi = sum(1 for c, _k in rows if c.get(v, 0) < 0)
            n = lo * hi - lo - hi
            if best is None or n < best_n:
                best, best_n = v, n
        v = best
        lows = [r for r in rows if r[0].get(v, 0) > 0]
        highs = [r for r in rows if r[0].get(v, 0) < 0]
        rest = [r for r in rows if v not in r[0]]
        for lc, lk in lows:
            for hc, hk in highs:
                a, b = lc[v], -hc[v]
                d = {}
                for x, c in lc.items():
                    if x != v:
                        d[x] = d.get(x, 0) + c * b
                for x, c in hc.items():
                    if x != v:
                        d[x] = d.get(x, 0) + c * a
                d = {x: c for x, c in d.items() if c != 0}
                row = _tighten((d, lk * b + hk * a))
                key = (tuple(sorted(row[0].items())), row[1])
                if key in seen:
                    continue
                seen.add(key)
                rest.append(row)
                if len(rest) > MAX_ROWS:
                    return False
        rows = rest


def _lens(f, out):
    k = f[0]
    if k in ("ge", "eq"):
        for a in f[1][0]:
            if a.__class__ is tuple and a and a[0] == "len":
                out.add(a)
    else:
        for g in f[1]:
            _lens(g, out)


def satisfiable(formulas):
    """False when the formulas together are impossible; True when we can't tell they are."""
    f = ("and", list(formulas))
    nn = set()
    _lens(f, nn)                                  # a length is never negative
    cl = clauses(f)
    if cl is None:
        return True
    return not all(unsat(c, nn) for c in cl)


def proves(facts, goal):
    """`"yes"` when the facts imply the goal, `"no"` when they contradict it, else `"unknown"`."""
    if not satisfiable(facts):
        return "yes"                              # unreachable code: anything follows
    if not satisfiable(list(facts) + [neg(goal)]):
        return "yes"
    if not satisfiable(list(facts) + [goal]):
        return "no"
    return "unknown"
