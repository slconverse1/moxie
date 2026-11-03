"""Effect inference (Spec section 14), first version.

An effect is "parks" (read, write, sleep, select without default, a database
query) or "prints".  Using a resource is not tracked yet.

A function's effects are the union of the effects of the calls in its body.
Recursion is solved by iterating to a fixed point.  A call through a function
parameter takes the effects of the function passed at the call site.  Methods
are resolved by name: a call `x.f()` has the union of the effects of every
function or method named `f` in the program.

Consumers: `pure fn` (and `tailrec` is unaffected), the function given to
`swap` (must not park), `debug_assert` conditions, and contract conditions
(must be pure).
"""
from .ast import *   # noqa

PARKS, PRINTS = "parks", "prints"
BUILTIN = {"println": PRINTS, "print": PRINTS, "eprintln": PRINTS, "eprint": PRINTS,
           "read": PARKS, "write": PARKS, "sleep": PARKS,
           "read_line": PARKS, "read_all": PARKS, "stdin_lines": PARKS,
           "lines": PARKS, "open_file": PARKS, "read_file": PARKS, "write_file": PARKS, "read_bytes": PARKS,
           "write_bytes": PARKS, "connect": PARKS, "listen": PARKS, "accept": PARKS}
EXEMPT = {"dbg", "trace"}


def _last(t):
    p = getattr(t, "path", None)
    return p[-1] if p else None


def _children(n):
    for f in n._fields:
        v = getattr(n, f, None)
        yield from _flat(v)


def _flat(v):
    if isinstance(v, N):
        yield v
    elif isinstance(v, (list, tuple)):
        for x in v:
            yield from _flat(x)


class Summary:
    def __init__(self):
        self.eff = {}            # effect -> (callee, line, root)
        self.param_calls = set()  # indices of parameters the body calls


class Effects:
    def __init__(self, prog):
        self.prog = prog
        self.defs = {}           # name -> [FnDecl]
        self.sum = {}            # name -> Summary
        self.diags = []
        self.where = {}
        self.bounds = {}
        self._collect(prog)

    def _collect(self, n, ctx="top"):
        c = n.__class__
        if c is FnDecl and n.name:
            self.defs.setdefault(n.name, []).append(n)
            self.where[id(n)] = ctx
            if n.body is None and self.declared(n) is not None:
                self.bounds[(ctx[1] if isinstance(ctx, tuple) else None, n.name)] = self.declared(n)
        if c is IfaceDecl:
            sub = ("iface", n.name)
        elif c is ImplDecl:
            sub = ("impl", _last(n.iface)) if n.iface is not None else "top"
        elif c in (FnDecl, FnGroup, Lambda):
            sub = "top"
        else:
            sub = ctx
        for ch in _children(n):
            self._collect(ch, sub)

    @staticmethod
    def declared(d):
        """The declared effects of `d`: a set, 'some' for impure, or None when nothing is declared."""
        f = d.flags or ()
        if "impure" in f:
            return "some"
        names = set()
        if "parks" in f:
            names.add(PARKS)
        if "prints" in f:
            names.add(PRINTS)
        if names:
            return names
        if "pure" in f:
            return set()
        return None

    # ---------------------------------------------------------------- walking
    def callee_name(self, f):
        c = f.__class__
        if c is Name:
            return f.name, False
        if c is Field:
            return f.name, True
        if c is GenApp:
            nm, m = self.callee_name(f.base)
            return nm, m
        return None, False

    def arg_effects(self, e, fnnames, acc):
        """Effects of running the function value `e` (a lambda, a function name, or a partial call)."""
        c = e.__class__
        if c is Lambda:
            self.walk(e.body, fnnames, acc, None)
        elif c is Name:
            self.add_named(e.name, 0, acc, fnnames=None)
        else:
            self.walk(e, fnnames, acc, None)

    def add_named(self, name, line, acc, fnnames=None):
        if name in self.defs:
            s = self.sum.get(name)
            if s:
                for eff, (callee, ln, root) in s.eff.items():
                    acc.setdefault(eff, (name, line, root))
        elif name in BUILTIN:
            acc.setdefault(BUILTIN[name], (name, line, name))

    def handle_call(self, call, extra, fnnames, acc, summ):
        fn = call.fn
        name, is_method = self.callee_name(fn)
        args = [a.expr for a in call.args if a.expr is not None]
        if extra is not None:
            if any(a.__class__ is Slot for a in args):
                args = [extra if a.__class__ is Slot else a for a in args]
            else:
                args = [extra] + args
        line = getattr(call, "line", 0)
        if name is None:
            self.walk(fn, fnnames, acc, summ)
        elif not is_method and fnnames is not None and name in fnnames:
            if summ is not None:
                summ.param_calls.add(fnnames.index(name))
        elif name in EXEMPT and name not in self.defs:
            pass
        elif name in self.defs:
            self.add_named(name, line, acc)
            for d in self.defs[name]:
                s = self.sum.get(name)
                if s:
                    for idx in s.param_calls:
                        off = idx - (1 if is_method and d.params and getattr(d.params[0], "name", None) == "self" else 0)
                        if 0 <= off < len(args):
                            self.arg_effects(args[off], fnnames, acc)
                    break
        elif name in BUILTIN:
            if not (name == "read" and fn.__class__ is GenApp):     # read[T](text) parses, it does not park
                acc.setdefault(BUILTIN[name], (name, line, name))
        else:
            # any other builtin: a function passed to it is assumed to be called
            for a in args:
                if a.__class__ is Lambda or (a.__class__ is Name and (a.name in self.defs or a.name in BUILTIN)):
                    self.arg_effects(a, fnnames, acc)
        if name == "swap" and name not in self.defs and len(args) >= 2:
            sub = {}
            self.arg_effects(args[1], fnnames, sub)
            if PARKS in sub:
                c_, ln_, root = sub[PARKS]
                self.diags.append((line, f"the function given to swap may park (it calls '{root}'); swap's function must not park"))
        if name == "debug_assert" and name not in self.defs and args:
            sub = {}
            self.walk(args[0], fnnames, sub, None)
            if sub:
                eff = next(iter(sub))
                self.diags.append((line, f"a debug_assert condition must be pure, but it {eff} (calls '{sub[eff][2]}')"))
        # evaluate the callee expression and the arguments themselves
        if fn.__class__ not in (Name,):
            for c in _children(fn):
                self.walk(c, fnnames, acc, summ)
        for a in call.args:
            self.walk(a.expr, fnnames, acc, summ)

    def walk(self, n, fnnames, acc, summ):
        if n is None:
            return
        c = n.__class__
        if c is Lambda or c is FnDecl or c is FnGroup:
            return
        if c is Call:
            self.handle_call(n, None, fnnames, acc, summ)
            if n.trailing is not None:
                self.walk(n.trailing, fnnames, acc, summ)
            return
        if c is Pipe:
            self.walk(n.l, fnnames, acc, summ)
            st = n.stage
            if st.__class__ is Call:
                self.handle_call(st, n.l, fnnames, acc, summ)
            elif st.__class__ is Lambda:
                self.walk(st.body, fnnames, acc, summ)
            elif st.__class__ is Name:
                fake = Call(st, [], None, line=getattr(n, "line", 0))
                self.handle_call(fake, n.l, fnnames, acc, summ)
            else:
                self.walk(st, fnnames, acc, summ)
            return
        if c is SqlE:
            acc.setdefault(PARKS, ("query", getattr(n, "line", 0), "query"))
        if c is SelectE:
            if not any(getattr(a, "kind", None) == "default" for a in n.arms or []):
                acc.setdefault(PARKS, ("select", getattr(n, "line", 0), "select"))
        for ch in _children(n):
            self.walk(ch, fnnames, acc, summ)

    def run_def(self, d, summ):
        fnnames = [getattr(p, "name", None) for p in (d.params or [])]
        acc = {}
        if d.body is not None:
            self.walk(d.body, fnnames, acc, summ)
        if d.guard is not None:
            self.walk(d.guard, fnnames, acc, summ)
        return acc

    # ---------------------------------------------------------------- solving
    def solve(self):
        for name in self.defs:
            self.sum[name] = Summary()
        for name, ds in self.defs.items():
            for d in ds:
                dec = self.declared(d) if d.body is None else None
                if dec:
                    for eff in (dec if dec != "some" else (PARKS, PRINTS)):
                        self.sum[name].eff.setdefault(eff, (name, d.line, name))
        changed = True
        rounds = 0
        while changed and rounds < 50:
            changed = False
            rounds += 1
            for name, ds in self.defs.items():
                s = self.sum[name]
                for d in ds:
                    before = (len(s.eff), len(s.param_calls))
                    acc = self.run_def(d, s)
                    ctx = self.where.get(id(d))
                    bounded = d.body is not None and (ctx[1] if isinstance(ctx, tuple) else None, name) in self.bounds
                    for eff, w in acc.items():
                        if not bounded:          # a declared interface member stands for all its impls
                            s.eff.setdefault(eff, w)
                    if (len(s.eff), len(s.param_calls)) != before:
                        changed = True
        self.diags = []          # discard diagnostics from the iteration rounds
        for name, ds in self.defs.items():
            for d in ds:
                self.check_def(d)
        self.check_contracts()
        # the consumer checks inside bodies were produced during the walk; do one clean pass
        for name, ds in self.defs.items():
            for d in ds:
                self.run_def(d, Summary())
        self.run_top()
        return self.diags

    def run_top(self):
        acc = {}
        for st in self.prog.stmts:
            if st.__class__ not in (FnDecl, FnGroup, TupleDecl, EnumDecl, IfaceDecl, ImplDecl, AliasDecl):
                self.walk(st, None, acc, None)

    def check_def(self, d):
        dec = self.declared(d)
        f = d.flags or ()
        if ("pure" in f) and (("parks" in f) or ("prints" in f) or ("impure" in f)):
            self.diags.append((d.line, f"'{d.name}' is declared both pure and impure"))
            return
        if d.body is None:
            return
        acc = self.run_def(d, Summary())
        if dec is not None:
            if dec == "some":
                if not acc:
                    self.diags.append((d.line, f"fn '{d.name}' is declared impure but has no effect"))
            else:
                for eff, (callee, ln, root) in acc.items():
                    if eff not in dec:
                        who = "pure " if not dec else ""
                        self.diags.append((ln or d.line, f"{who}fn '{d.name}' {eff} (calls '{root}'), but it is not declared {eff}"
                                           if dec else f"pure fn '{d.name}' {eff} (calls '{root}')"))
                for eff in dec:
                    if eff not in acc:
                        self.diags.append((d.line, f"fn '{d.name}' is declared {eff} but never does"))
        ctx = self.where.get(id(d))
        key = (ctx[1] if isinstance(ctx, tuple) else None, d.name)
        if key in self.bounds and ctx != "top" or (ctx == "top" and (None, d.name) in self.bounds):
            bound = self.bounds.get(key)
            allowed = {PARKS, PRINTS} if bound == "some" else (bound or set())
            for eff, (callee, ln, root) in acc.items():
                if eff not in allowed:
                    self.diags.append((ln or d.line, f"'{d.name}' {eff} (calls '{root}'), which its declaration does not allow"))

    def check_contracts(self):
        for ds in self.defs.values():
            for d in ds:
                for kw, expr, ln, text in (getattr(d, "contracts", None) or []):
                    acc = {}
                    self.walk(expr, [getattr(p, "name", None) for p in (d.params or [])], acc, None)
                    for eff, (callee, l2, root) in acc.items():
                        self.diags.append((ln, f"the condition of {kw} must be pure, but it {eff} (calls '{root}')"))


def check_effects(prog):
    """Return [(line, message)] for effect violations."""
    seen, out = set(), []
    for line, msg in Effects(prog).solve():
        if (line, msg) not in seen:
            seen.add((line, msg))
            out.append((line, msg))
    return out
