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
import os

from .ast import *   # noqa

PARKS, PRINTS = "parks", "prints"
SYSTEM = "uses the system"     # the clock, random numbers, exit, signals, and facts about the host
SYSTEM_CALLS = ("now", "monotonic", "random", "random_int", "random_bytes", "exit", "signals", "cwd", "home_dir",
                "temp_dir", "hostname", "os_name", "is_terminal", "terminal_size")
BUILTIN = {"println": PRINTS, "print": PRINTS, "eprintln": PRINTS, "eprint": PRINTS,
           "read": PARKS, "write": PARKS, "sleep": PARKS,
           "read_line": PARKS, "read_all": PARKS, "stdin_lines": PARKS,
           "lines": PARKS, "open_file": PARKS, "read_file": PARKS, "write_file": PARKS, "read_bytes": PARKS,
           "write_bytes": PARKS, "list_dir": PARKS, "file_info": PARKS, "path_exists": PARKS, "make_dir": PARKS,
           "remove_file": PARKS, "remove_dir": PARKS, "rename_path": PARKS, "connect": PARKS, "listen": PARKS, "bind_udp": PARKS, "send_to": PARKS, "receive": PARKS, "connect_tls": PARKS, "listen_tls": PARKS, "accept": PARKS,
           "lookup_host": PARKS, "run_command": PARKS, "spawn": PARKS, "wait_child": PARKS, "kill_child": PARKS, "make_temp_file": PARKS, "make_temp_dir": PARKS, **{n: SYSTEM for n in SYSTEM_CALLS}}
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


def find_package(search_dir, parts):
    base = search_dir or "."
    cands = [os.path.join(base, *parts) + ".mxi", os.path.join(base, *parts, parts[-1] + ".mxi")]
    return next((p for p in cands if os.path.exists(p)), None)


class Effects:
    BUILT = BUILTIN

    def __init__(self, prog, search_dir=None, _shared=None):
        self.prog = prog
        self.search_dir = search_dir
        self.label = ""                       # "" for the entry file, else the package key
        self._shared = _shared if _shared is not None else {}       # package key -> analysis of that package
        self.pkgs = {}                        # alias -> analysis of an imported package
        self.imported = {}                    # name brought in by `import p (name)` -> (analysis, name)
        self.import_line = {}
        self.methods = set()                  # names defined in impl blocks, reachable as x.name(...) by UFCS
        self._done = False
        self.defs = {}           # name -> [FnDecl]
        self.sum = {}            # name -> Summary
        self.diags = []
        self.where = {}
        self.bounds = {}
        self.callbacks = {}          # foreign fn name -> indices of its callback parameters
        self._collect(prog)
        self._collect_methods(prog, False)
        self._imports()

    def _collect_methods(self, n, in_impl):
        if n.__class__ is FnDecl and in_impl and n.name:
            self.methods.add(n.name)
        for ch in _children(n):
            self._collect_methods(ch, in_impl or n.__class__ is ImplDecl)

    def _imports(self):
        """Analyze each imported package once (shared by key), so a call into it can use its function summaries."""
        if self.search_dir is None:
            return
        from .parser import parse_program
        for st in self.prog.stmts:
            if st.__class__ is not ImportDecl:
                continue
            key = ".".join(st.pkg)
            self.import_line.setdefault(key, st.line)
            sub = self._shared.get(key)
            if sub is None:
                path = find_package(self.search_dir, st.pkg)
                if path is None:
                    continue
                try:
                    pp = parse_program(open(path, encoding="utf-8").read(), path)
                except Exception:
                    continue
                sub = type(self).__new__(type(self))
                self._shared[key] = sub                      # registered first, so an import cycle cannot recurse
                sub.__init__(pp, self.search_dir, self._shared)
                sub.label = key
            if st.names:
                for nm in st.names:
                    if isinstance(nm, str):
                        self.imported[nm] = (sub, nm)
            else:
                self.pkgs[st.alias or st.pkg[-1]] = sub

    def _subs(self):
        seen, out = set(), []
        for s in list(self.pkgs.values()) + [s for s, _n in self.imported.values()]:
            if id(s) not in seen:
                seen.add(id(s))
                out.append(s)
        return out

    def ensure_subs(self):
        for s in self._subs():
            s.ensure()

    def ensure(self):
        if self._done:
            return
        self._done = True
        self.ensure_subs()
        self.compute()

    def compute(self):
        self.summaries()

    def pk(self, f):
        """(analysis, function name) when the callee `f` is a function of an imported package, else None."""
        c = f.__class__
        if c is GenApp:
            return self.pk(f.base)
        if c is Field and f.obj.__class__ is Name and f.obj.name in self.pkgs:
            sub = self.pkgs[f.obj.name]
            return (sub, f.name) if f.name in sub.defs else None
        if c is Name and f.name in self.imported and f.name not in self.defs:
            sub, orig = self.imported[f.name]
            return (sub, orig) if orig in sub.defs else None
        return None

    def pk_methods(self, f):
        """UFCS: `x.name(...)` can reach an impl method of that name in any imported package."""
        if f.__class__ is GenApp:
            return self.pk_methods(f.base)
        if f.__class__ is not Field or (f.obj.__class__ is Name and f.obj.name in self.pkgs):
            return []
        return [(s, f.name) for s in self._subs() if f.name in s.methods]

    def add_pkg(self, sub, nm, args, fnnames, acc, line, is_method):
        s = sub.sum.get(nm)
        if not s:
            return
        for eff, (callee, ln, root) in s.eff.items():
            acc.setdefault(eff, (f"{sub.label}.{nm}", line, root))
        ds = sub.defs.get(nm) or []
        for idx in s.param_calls:
            off = idx - (1 if is_method and ds and ds[0].params and getattr(ds[0].params[0], "name", None) == "self" else 0)
            if 0 <= off < len(args):
                self.arg_effects(args[off], fnnames, acc)

    def _collect(self, n, ctx="top"):
        c = n.__class__
        if c is FnDecl and n.name:
            self.defs.setdefault(n.name, []).append(n)
            self.where[id(n)] = ctx
            if n.body is None and self.declared(n) is not None:
                self.bounds[(ctx[1] if isinstance(ctx, tuple) else None, n.name)] = self.declared(n)
        if c is ForeignDecl:
            hnames = {h[0] for h in n.handles or []}

            def hidden(p):
                df = p.default
                if df is not None and df.__class__ is Call and df.fn.__class__ is Name and df.fn.name in ("len", "size_of"):
                    return True
                tn = _last(p.type) if p.type.__class__ is TName else None
                return tn == "UserData" or (p.mod == "ref" and tn in hnames)
            for d in n.fns:
                visible = [p for p in d.params or [] if not hidden(p)]
                idx = [i for i, p in enumerate(visible) if p.type.__class__ is TFn]
                if idx:
                    self.callbacks[d.name] = idx
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
            if e.name in self.imported and e.name not in self.defs:
                sub, orig = self.imported[e.name]
                self.add_pkg(sub, orig, [], fnnames, acc, 0, False)
            else:
                self.add_named(e.name, 0, acc, fnnames=None)
        else:
            self.walk(e, fnnames, acc, None)

    def add_named(self, name, line, acc, fnnames=None):
        if name in self.defs:
            s = self.sum.get(name)
            if s:
                for eff, (callee, ln, root) in s.eff.items():
                    acc.setdefault(eff, (name, line, root))
        elif name in self.BUILT:
            acc.setdefault(self.BUILT[name], (name, line, name))

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
        definite = self.pk(fn)
        if definite is not None:
            self.add_pkg(definite[0], definite[1], args, fnnames, acc, line, is_method)
        elif name is None:
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
        elif name in self.BUILT:
            if not (name == "read" and fn.__class__ is GenApp):     # read[T](text) parses, it does not park
                acc.setdefault(self.BUILT[name], (name, line, name))
        else:
            # any other builtin: a function passed to it is assumed to be called
            for a in args:
                if a.__class__ is Lambda or (a.__class__ is Name and (a.name in self.defs or a.name in self.BUILT)):
                    self.arg_effects(a, fnnames, acc)
        for sub, nm in self.pk_methods(fn):
            self.add_pkg(sub, nm, args, fnnames, acc, line, True)
        if name in self.callbacks and not is_method:
            for i in self.callbacks[name]:
                if i < len(args):
                    sub = {}
                    self.arg_effects(args[i], fnnames, sub)
                    if PARKS in sub:
                        self.diags.append((line, f"the callback given to '{name}' may park (it calls '{sub[PARKS][2]}'); "
                                                 "a callback that C calls must not park"))
                    for eff, w in sub.items():
                        acc.setdefault(eff, w)
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
        self.ensure_subs()
        self.summaries()
        return self.finish()

    def summaries(self):
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

    def finish(self):
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
        self.lamnames = set()
        self.collect_lamnames(self.prog)
        self.check_lambdas(self.prog)
        return self.diags

    @staticmethod
    def _plain(lam):
        return lam.__class__ is Lambda and not getattr(lam, "partial", False) and not getattr(lam, "fiber", False)

    def collect_lamnames(self, n):
        if n is None:
            return
        if n.__class__ is Assign and self._plain(n.value) and n.targets.__class__ is PBind:
            self.lamnames.add(n.targets.name)
            if self._mentions(n.value.body, n.targets.name):
                self.diags.append((n.line, f"a lambda cannot call itself: '{n.targets.name}' is not bound until its body is "
                                           "compiled; declare it with fn if it needs recursion"))
        for ch in _children(n):
            self.collect_lamnames(ch)

    def _mentions(self, n, name):
        if n.__class__ is Name:
            return n.name == name
        return any(self._mentions(c, name) for c in _children(n)) if n is not None else False

    def check_lambdas(self, n, in_test=False):
        """A lambda is pure: it may not print, park, or otherwise have an effect (a partial call
        takes its callee's effects, and an inline fiber is a function of its own)."""
        if n is None:
            return
        if n.__class__ is Lambda and not getattr(n, "partial", False) and not getattr(n, "fiber", False):
            acc = {}
            self.walk(n.body, None, acc, None)
            for eff, (callee, ln, root) in acc.items():
                self.diags.append((ln or n.line, f"a lambda must be pure, but it {eff} (calls '{root}'); "
                                                 "write fn (...) for an anonymous function that may have effects, or declare a function with fn"))
        if n.__class__ is RunE and n.target.__class__ is Call and n.target.fn.__class__ is Name \
                and n.target.fn.name in self.lamnames and n.target.fn.name not in self.defs:
            self.diags.append((n.line, f"'{n.target.fn.name}' is bound to a lambda and cannot be run; "
                                       "declare it with fn (fiber limits attach to declarations)"))
        if n.__class__ is ForAll:
            if not in_test:
                self.diags.append((n.line, "forall belongs inside a test block"))
            acc = {}
            self.walk(n.body, [nm for nm, _ in n.binds], acc, None)
            for eff, (callee, ln, root) in acc.items():
                self.diags.append((ln or n.line, f"the body of forall must be pure, but it {eff} (calls '{root}')"))
        inside = in_test or n.__class__ is TestDecl
        for ch in _children(n):
            self.check_lambdas(ch, inside)

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
                        if eff == SYSTEM and dec:
                            self.diags.append((ln or d.line, f"fn '{d.name}' {eff} (calls '{root}'), so it must be declared impure"))
                            continue
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


# ---------------------------------------------------------------- permissions needed (Spec 19d)
NEEDS = {"signals": "platform:signals", "open_file": "fs", "read_file": "fs", "write_file": "fs", "connect": "net", "listen": "net", "bind_udp": "net", "send_to": "net", "connect_tls": "net", "listen_tls": "net",
         "list_dir": "fs", "file_info": "fs", "path_exists": "fs", "make_dir": "fs", "remove_file": "fs",
         "remove_dir": "fs", "rename_path": "fs", "lookup_host": "net", "run_command": "process", "spawn": "process", "make_temp_file": "fs", "make_temp_dir": "fs", "read_line": "stdin", "read_all": "stdin", "stdin_lines": "stdin"}


class Needs(Effects):
    """Which permission kinds the program can reach from its top-level code: fs, net, stdin, env, ffi:LIB.
    The same walk as effects, with permissions in place of parks/prints.  Reading from a given stream
    or file (`lines`, `read_line(io)`) is not a need of its own: the stream was opened with one."""
    BUILT = NEEDS

    def __init__(self, prog, search_dir=None, _shared=None):
        self.foreign = []
        super().__init__(prog, search_dir, _shared)
        self._foreign(prog)

    def _foreign(self, n):
        if n.__class__ is ForeignDecl:
            self.foreign.append((n.lib, [d.name for d in n.fns]))
        for ch in _children(n):
            self._foreign(ch)

    def walk(self, n, fnnames, acc, summ):
        if n.__class__ is Name and n.name == "env" and "env" not in (fnnames or []):
            acc.setdefault("env", ("env", getattr(n, "line", 0), "env"))
        super().walk(n, fnnames, acc, summ)

    def handle_call(self, call, extra, fnnames, acc, summ):
        name, is_method = self.callee_name(call.fn)
        if name in ("read_line", "read_all", "read_bytes", "lines") and not is_method and name not in self.defs:
            args = [a.expr for a in call.args if a.expr is not None]
            if extra is None and (not args or (args[0].__class__ is Name and args[0].name == "stdin")):
                acc.setdefault("stdin", (name, getattr(call, "line", 0), name))
            for a in call.args:
                self.walk(a.expr, fnnames, acc, summ)
            return                       # a read from a file or socket was permitted when it was opened
        super().handle_call(call, extra, fnnames, acc, summ)

    def summaries(self):
        for name in self.defs:
            self.sum[name] = Summary()
        for lib, names in self.foreign:
            for nm in names:
                self.sum[nm].eff.setdefault("ffi:" + lib, (nm, 0, nm))
        for _ in range(50):
            changed = False
            for name, ds in self.defs.items():
                s = self.sum[name]
                for d in ds:
                    before = (len(s.eff), len(s.param_calls))
                    for eff, w in self.run_def(d, s).items():
                        s.eff.setdefault(eff, w)
                    if (len(s.eff), len(s.param_calls)) != before:
                        changed = True
            if not changed:
                break

    def top_acc(self):
        acc = {}
        for st in self.prog.stmts:
            if st.__class__ not in (FnDecl, FnGroup, TupleDecl, EnumDecl, IfaceDecl, ImplDecl, AliasDecl):
                self.walk(st, None, acc, None)
        return acc

    def compute(self):
        self.summaries()
        self.top = self.top_acc()

    def solve(self):
        self.ensure_subs()
        self.summaries()
        acc = self.top_acc()
        for key, sub in self._shared.items():          # a package runs its top level when it is imported
            sub.ensure()
            for kind, w in sub.top.items():
                acc.setdefault(kind, (key, self.import_line.get(key, 1), w[2]))
        return acc


def permission_needs(prog, search_dir=None):
    """{kind: (line, name)} for what the program's top-level code can reach."""
    acc = Needs(prog, search_dir).solve()
    return {k: (w[1], w[2]) for k, w in acc.items()}


def check_effects(prog, search_dir=None):
    """Return [(line, message)] for effect violations."""
    seen, out = set(), []
    for line, msg in Effects(prog, search_dir).solve():
        if (line, msg) not in seen:
            seen.add((line, msg))
            out.append((line, msg))
    return out
