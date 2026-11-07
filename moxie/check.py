"""Core static checks: a conservative pass over the AST (no execution).

Reports, never guessing: mismatched types, undefined names, wrong argument counts,
`ref` mismatches, non-exhaustive `when`, use-after-move, and bounded-integer misuse.
Anything the checker cannot type is "unknown" and never produces an error.
"""
import os
from .ast import *   # noqa
from . import tys

INTS = {"Int", "Int8", "Int16", "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64", "BigInt"}
RES_TYPES = {"ChanR", "ChanW", "Timer", "Connection", "Io", "Listener", "Udp", "Child", "Terminal"}
RES_MAKERS = {"Chan", "Timer", "clone", "open_file", "connect", "listen", "accept", "connect_tls", "listen_tls", "bind_udp", "signals", "spawn", "raw_terminal", "watch", "connect_unix", "listen_unix"}
EXTRA_NAMES = {"Ok", "Err", "self", "Self", "args", "env", "Int", "Int8", "Int16", "Int32", "Int64",
               "UInt8", "UInt16", "UInt32", "UInt64", "BigInt", "Double", "Float", "String", "Bool",
               "Char", "Unit", "Decimal", "Keyword", "Duration", "Error", "Atom", "Cancel", "Secret", "ChanR", "ChanW",
               "Locale", "Connection", "true", "false", "UserData", "Events", "stdin", "stdout", "stderr", "ReadOnly", "Create", "Append", "ReadWrite", "FileMode", "Io", "Listener", "Ptr", "size_of", "Handler", "bin_build"}


INT_NAMES = {"Int", "Int8", "Int16", "Int32", "Int64", "UInt", "UInt8", "UInt16", "UInt32", "UInt64", "Byte", "BigInt"}
FLOAT_NAMES = {"Float", "Double", "LongDouble"}
NUM_NAMES = INT_NAMES | FLOAT_NAMES | {"Decimal"}
SCALAR_NAMES = NUM_NAMES | {"String", "Char", "Bool"}
VALUE_IFACES = {"Equatable", "Ordered", "Hashable", "Show", "Read", "Addable", "Numeric"}
BUILTIN_IMPLS = {
    "Equatable": SCALAR_NAMES,
    "Ordered": NUM_NAMES | {"String", "Char"},
    "Hashable": INT_NAMES | {"Decimal", "String", "Char", "Bool"},
    "Show": SCALAR_NAMES,
    "Read": SCALAR_NAMES,
    "Addable": NUM_NAMES | {"String"},
    "Numeric": NUM_NAMES,
}
DERIV_IFACE = {"eq": "Equatable", "ord": "Ordered", "show": "Show", "read": "Read", "hash": "Hashable"}


def _tn(x):
    if isinstance(x, str):
        return x
    path = getattr(x, "path", None)
    return path[-1] if path else None


NOCONST = object()
NOANY = object()
CT = [None]            # the compile-time evaluator of the program being checked (cteval.CtEval)


def names_of(e):
    out, stack = set(), [e]
    while stack:
        x = stack.pop()
        if x.__class__ is Name:
            out.add(x.name)
        for f in getattr(x, "_fields", ()):
            v = getattr(x, f, None)
            if isinstance(v, N):
                stack.append(v)
            elif isinstance(v, (list, tuple)):
                stack.extend(y for y in v if isinstance(y, N))
    return out


def show_const(v):
    return ("\"%s\"" % v) if isinstance(v, str) else (("true" if v else "false") if isinstance(v, bool) else str(v))


def const_eval(e, env):
    """The value of a constant expression (numbers, text, booleans, + - * / %, comparisons, and, or, not), else NOCONST."""
    c = e.__class__
    if c is IntLit:
        return e.v
    if c is FloatLit:
        return e.v
    if c is BoolLit:
        return bool(e.b)
    if c is StrLit:
        return "".join(e.parts) if all(isinstance(x, str) for x in e.parts) else NOCONST
    if c is Name:
        return env.get(e.name, NOCONST)
    if c is Call and CT[0] is not None and CT[0].key_of(e.fn) is not None:
        args = [a.expr for a in e.args or []]
        if any(a is None or getattr(a, "label", None) or getattr(a, "mod", None) for a in e.args or []):
            return NOCONST
        vals = [const_eval(a, env) for a in args]
        if any(v is NOCONST for v in vals):
            return NOCONST
        r = CT[0].call(CT[0].key_of(e.fn), vals, getattr(e, "line", 0))
        return r[0] if r else NOCONST
    if c is Unary:
        v = const_eval(e.e, env)
        if v is NOCONST:
            return NOCONST
        if e.op == "not" and isinstance(v, bool):
            return not v
        if e.op == "-" and isinstance(v, (int, float)) and not isinstance(v, bool):
            return -v
        return NOCONST
    if c is AndE or c is OrE:
        l = const_eval(e.l, env)
        r = const_eval(e.r, env)
        if isinstance(l, bool) and isinstance(r, bool):
            return (l and r) if c is AndE else (l or r)
        if c is AndE and (l is False or r is False):
            return False
        if c is OrE and (l is True or r is True):
            return True
        return NOCONST
    if c is Binary:
        l = const_eval(e.l, env)
        r = const_eval(e.r, env)
        if l is NOCONST or r is NOCONST or isinstance(l, bool) != isinstance(r, bool):
            return NOCONST
        if type(l) is str and type(r) is not str or type(r) is str and type(l) is not str:
            return NOCONST
        op = e.op
        cmp = {"==": lambda: l == r, "~=": lambda: l != r, "<": lambda: l < r, "<=": lambda: l <= r,
               ">": lambda: l > r, ">=": lambda: l >= r}
        if op in cmp:
            return cmp[op]()
        if isinstance(l, (int, float)) and isinstance(r, (int, float)) and not isinstance(l, bool):
            if op == "+":
                return l + r
            if op == "-":
                return l - r
            if op == "*":
                return l * r
            if op == "/" and r != 0:
                return int(l / r) if isinstance(l, int) and isinstance(r, int) else l / r
            if op == "%" and isinstance(l, int) and isinstance(r, int) and r > 0 and l >= 0:
                return l % r
        return NOCONST
    return NOCONST


class Diag:
    def __init__(self, line, msg, kind="error"):
        self.line, self.msg, self.kind = line, msg, kind

    def __str__(self):
        return f"line {self.line}: {self.kind}: {self.msg}"


class Var:
    __slots__ = ("ty", "resource", "depth")

    def __init__(self, ty=None, resource=False, depth=0):
        self.ty, self.resource, self.depth = ty, resource, depth


class Sc:
    def __init__(self, parent=None, open_=False):
        self.parent = parent
        self.vars = {}
        self.open = open_ or (parent.open if parent else False)

    def find(self, name):
        s = self
        while s is not None:
            v = s.vars.get(name)
            if v is not None:
                return v
            s = s.parent
        return None


def tshow(t):
    return tys.show(t)


def _old_tshow(t):
    if t is None:
        return "?"
    if isinstance(t, str):
        return {"Float": "Double"}.get(t, t)
    if t[0] == "named":
        return t[1]
    if t[0] == "bounded":
        return f"Int[{t[1]}..={t[2]}]"
    if t[0] == "coll":
        return f"{t[1]}[{tshow(t[2])}]"
    if t[0] == "secret":
        return "Secret"
    return "?"


def extra_bad(args):
    return any(getattr(a, "label", None) or getattr(a, "mod", None) for a in args)


def subst_t(t, binds):
    return tys.subst(t, binds)


def fields_of(n):
    return n._fields


class Checker:
    def __init__(self, prelude_names):
        self.diags = []
        self.prelude = set(prelude_names) | EXTRA_NAMES
        self.tuples, self.enums, self.fns, self.aliases = {}, {}, {}, {}
        self.callee_fields = set()
        self.mixed_lits = {}             # collection literals whose elements disagree, by call node: (line, message)
        self.cases = {}            # bare case name -> [enum names]
        self.globals = set()
        self.moved = {}            # Var -> line
        self.handle_types = {}     # handle type name -> closing fn name
        self.handle_makers = set() # foreign fns that return a handle
        self.foreign_ids = set()   # ids of foreign FnDecls
        self._later = False
        self.loop_depth = 0
        self.exit_ctx = False
        self.fn_ret = None
        self.fn_tparams = ()
        self.lam_expect = None
        self.pipe_ty = None
        self.sigs = None
        self.tp_vars = {}          # Var of a parameter typed exactly `T` -> its TParam, inside a generic function
        self.impls = {}            # type name -> {interface names}
        self.consumes = {}         # function name -> parameter positions it takes ownership of
        self.method_consumes = set()
        self.methods = {}
        self.res_tuples = set()
        self.pending_gone = []
        self.ifaces = set()
        self.iface_decls = {}
        self.tfuns = {}
        self.pv = frozenset()
        self.tf_steps = 0
        self.tf_depth = 0
        self.in_tfun = False
        self.any_params = {}             # inside a function: parameter name -> its type (an ('any', iface, key) for `any I`)
        self.any_vars = {}               # Var of a parameter typed `any I` -> ('any', iface, key)
        self.assoc = {}                  # (type name, member) -> the written type of an associated type
        self.consts = {}                 # top-level constant bindings the compiler could evaluate
        self.tf_fuel = TF_FUEL
        self.tf_big = False
        self.tf_trail = []
        self.cur_line = 0
        self.tp_decl = {}

    # ------------------------------------------------------------ reporting
    def has_local_pkg(self, parts):
        base = getattr(self, "search_dir", None) or "."
        return any(os.path.exists(p) for p in (os.path.join(base, *parts) + ".mxi", os.path.join(base, *parts, parts[-1] + ".mxi")))

    def err(self, line, msg):
        if any(d.line == line and d.msg == msg for d in self.diags):
            return
        self.diags.append(Diag(line, msg))

    # ------------------------------------------------------------ entry
    def check(self, prog):
        tys.REDUCER = self.reduce_tapp
        tys.UNFOLD = self.unfold
        tys.CALLER = self.type_call
        tys.IMPLEMENTS = self.implements
        self.collect_prelude_types()
        for st in prog.stmts:
            self.collect(st)
        self.find_consumers(prog)
        top = Sc()
        for st in prog.stmts:
            self.fold_binding(st)
            self.ev(st, top)
        if CT[0] is not None:
            seen = {(d.line, d.msg) for d in self.diags}
            for line, msg in CT[0].errors:
                if (line, msg) not in seen:
                    self.diags.append(Diag(line, msg))
            for line, msg in CT[0].warnings:
                if (line, msg) not in seen:
                    self.diags.append(Diag(line, msg, "warning"))
        return self.diags

    _prelude_types = {}              # by dialect: the tuples and enums the prelude declares in moxie (Output, Key, FileInfo, ...)

    def collect_prelude_types(self):
        """Make the prelude's own tuple and enum types known (a program's declaration of the same name replaces it), so
        `run_command(...)?.stdout` is a String.  Only the types: their case names stay out of the program's name space."""
        from .values import GC
        if GC[0] not in Checker._prelude_types:
            from .parser import parse_program
            from . import mxprelude as M
            prog = parse_program(M.SRC + (M.GC_SRC if GC[0] else ""), "<prelude>")
            Checker._prelude_types[GC[0]] = [st for st in prog.stmts if st.__class__ in (TupleDecl, EnumDecl, IfaceDecl, ImplDecl)]
        mark = len(self.diags)
        for st in Checker._prelude_types[GC[0]]:
            if st.__class__ in (TupleDecl, EnumDecl):
                (self.tuples if st.__class__ is TupleDecl else self.enums)[st.name] = st
            else:
                self.collect(st)                  # interfaces and impls, so a bound like `T: Monoid` is checked
        del self.diags[mark:]

    def fold_binding(self, st):
        """`N = fib(10)`: a top-level binding whose value the compiler can work out is a constant (a size may use it, and a call that
        aborts is a compile error)."""
        if st.__class__ is not Assign or st.op not in (None, "", "="):
            return
        tg = st.targets
        if isinstance(tg, list):
            tg = tg[0] if len(tg) == 1 else None
        if tg.__class__.__name__ == "PBind":
            name = tg.name
        elif tg.__class__.__name__ == "PCon" and len(tg.path) == 1 and tg.args is None:
            name = tg.path[0]
        else:
            return
        v = const_eval(st.value, self.consts)
        if v is not NOCONST:
            self.consts[name] = v

    # ------------------------------------------------------------ ownership
    def is_res_type(self, t):
        """A resource type: a built-in resource, a foreign handle, or a tuple that holds one."""
        return t.__class__ is TName and bool(t.path) and (t.path[-1] in RES_TYPES or t.path[-1] in self.handle_types
                                                          or t.path[-1] in self.res_tuples)

    def find_consumers(self, prog):
        """consumes[name] = {parameter positions} that a function takes ownership of: its body closes the parameter
        (or a field of it), moves it, or returns it.  A caller must hand such a resource over with `move`.
        method_consumes holds (Type, name) for the methods that take over `self`.  A tuple with a resource field is a
        resource too (res_tuples)."""
        from .effects import _children
        self.consumes, self.method_consumes, self.methods, self.res_tuples = {}, set(), {}, set()
        changed = True
        while changed:
            changed = False
            for tn, td in self.tuples.items():
                if tn not in self.res_tuples and any(self.is_res_type(f.type) for f in td.fields or [] if f.type is not None):
                    self.res_tuples.add(tn)
                    changed = True
        closers = set(self.handle_types.values())

        def root(e):
            while e.__class__ is Field:
                e = e.obj
            return e.name if e.__class__ is Name else None

        def bare(e, p):
            return e.__class__ is Name and e.name == p

        def eats(n, p):
            c = n.__class__
            if c is Move and root(n.e) == p:
                return True
            if c is Return and n.e is not None and bare(n.e, p):
                return True
            if c is Call:
                f = n.fn
                first = n.args[0].expr if n.args and hasattr(n.args[0], "expr") else None
                if f.__class__ is Name and (f.name == "close" or f.name in closers) and first is not None and root(first) == p:
                    return True
                if f.__class__ is Field and f.name == "close" and root(f.obj) == p:
                    return True
                for a in n.args:
                    if getattr(a, "mod", None) == "move" and root(a.expr) == p:
                        return True
            return any(eats(ch, p) for ch in _children(n))

        def keeps(fd, p):
            body = fd.body
            tail = body.stmts[-1] if body.__class__ is Block and body.stmts else body
            if tail.__class__ is ExprStmt:
                tail = tail.e
            return eats(body, p) or bare(tail, p)

        for name, clauses in self.fns.items():
            for fd in clauses:
                if fd.body is None or fd.alias is not None or id(fd) in self.foreign_ids:
                    continue
                for i, prm in enumerate(fd.params or []):
                    if prm.name and self.is_res_type(prm.type) and keeps(fd, prm.name):
                        self.consumes.setdefault(name, set()).add(i)
        for st in prog.stmts:
            if st.__class__ is ImplDecl and st.target.__class__ is TName and st.target.path:
                tn = st.target.path[-1]
                for m in st.members or []:
                    if m.__class__ is not FnDecl or m.body is None:
                        continue
                    self.methods[(tn, m.name)] = m
                    ps = m.params or []
                    if ps and ps[0].name == "self" and ps[0].type is None and self.is_res_type(st.target) and keeps(m, "self"):
                        self.method_consumes.add((tn, m.name))

    def mark_gone(self, n, sc, x, what):
        """The name `x` no longer owns its resource (it was closed or handed to a function that keeps it)."""
        v = sc.find(x)
        if v is None or not v.resource:
            return
        if v.depth < self.loop_depth and not self.exit_ctx:
            self.err(n.line, f"`{x}` is {what} inside a loop, so the next time round it is already gone; "
                             "do it after the loop, or leave the loop right after")
        self.moved[v] = n.line

    def check_hand_over(self, n, sc, name, args):
        """`f(c)` where f takes ownership of its resource parameter must be written `f(move c)`."""
        idx = self.consumes.get(name)
        if not idx:
            return
        clauses = self.fns.get(name) or []
        for i, a in enumerate(args):
            pos = i
            if getattr(a, "label", None):
                pos = next((k for k, pr in enumerate(clauses[0].params or []) if pr.name == a.label), None) if clauses else None
            if pos is None or pos not in idx or getattr(a, "mod", None) == "move":
                continue
            x = a.expr if hasattr(a, "expr") else None
            if x.__class__ is Name:
                v = sc.find(x.name)
                if v is not None and v.resource:
                    self.err(n.line, f"`{name}` takes ownership of `{x.name}` (it closes it, moves it, or returns it), so write `{name}(move {x.name})`; "
                                     "after that call, `%s` is gone" % x.name)

    def check_receiver(self, n, sc, fn):
        """`c.close()`, `c.f()` where f takes over its first parameter, and `j.m()` where m takes over `self`."""
        if fn.obj.__class__ is not Name:
            return
        if self.receiver_gone(sc, fn):
            self.pending_gone.append((n, sc, fn.obj.name, "closed or handed over"))

    def receiver_gone(self, sc, fn):
        """True when the call `x.m(...)` ends the use of `x`: it closes it, or m takes over its first parameter or `self`."""
        x, m = fn.obj.name, fn.name
        v = sc.find(x)
        if v is None or not v.resource:
            return False
        ty = v.ty[1] if v.ty.__class__ is tuple and len(v.ty) == 2 and v.ty[0] == "named" else None
        if m == "close" or (m in self.consumes and 0 in self.consumes[m]):
            return True
        if ty is not None:
            return (ty, m) in self.method_consumes
        # the receiver's type is not known: it is handed over when every type that has a method `m` hands over `self`
        owners = [k for k in self.methods if k[1] == m]
        return bool(owners) and all(k in self.method_consumes for k in owners)

    def check_stored(self, n, sc, name, args):
        """A resource put into a tuple must be moved in: `Conn(io: move f)`."""
        for a in args:
            x = a.expr if hasattr(a, "expr") else None
            if x.__class__ is Name and getattr(a, "mod", None) != "move":
                v = sc.find(x.name)
                if v is not None and v.resource:
                    self.err(n.line, f"`{x.name}` is a resource; write `move {x.name}` to put it in a `{name}`")

    def collect(self, st):
        c = st.__class__
        if c is TupleDecl:
            self.tuples[st.name] = st
            self.globals.add(st.name)
            self.check_derivs(st)
        elif c is EnumDecl:
            self.enums[st.name] = st
            self.globals.add(st.name)
            self.check_derivs(st)
            for cs in st.cases or []:
                self.cases.setdefault(cs.name, []).append(st.name)
                self.globals.add(cs.name)
        elif c is FnDecl:
            self.fns[st.name] = [st]
            self.globals.add(st.name)
        elif c is FnGroup:
            self.fns[st.name] = list(st.clauses or [])
            self.globals.add(st.name)
        elif c is ForeignDecl:
            for hname, closer, _ln in st.handles or []:
                self.handle_types[hname] = closer
                self.globals.add(hname)
            for d in st.fns:
                self.fns[d.name] = [d]
                self.globals.add(d.name)
                self.foreign_ids.add(id(d))
            for d in st.fns:
                if self.handle_ret(d.ret):
                    self.handle_makers.add(d.name)
        elif c is AliasDecl:
            self.aliases[st.name] = st
            self.globals.add(st.name)
        elif c is IfaceDecl:
            self.globals.add(st.name)
            self.ifaces.add(st.name)
            self.iface_decls[st.name] = st
        elif c is ImplDecl:
            iname, tname = _tn(st.iface), _tn(st.target)
            if iname == "Hashable":
                self.err(st.line, "`Hashable` can only be derived: write `deriving eq, hash` in the header of `%s`" % tname)
            for m in st.members or []:
                if m.__class__ is AliasDecl and tname:
                    self.assoc[(tname, m.name)] = m.type          # `type Item = String` in an impl
            if iname and tname:
                self.impls.setdefault(tname, set()).add(iname)
            elif tname:
                # an inherent impl that defines `<` or `==` makes the type Ordered or Equatable
                for m in st.members or []:
                    nm = getattr(m, "name", None)
                    if nm == "<":
                        self.impls.setdefault(tname, set()).add("Ordered")
                    elif nm == "==":
                        self.impls.setdefault(tname, set()).add("Equatable")
        elif c is ImportDecl:
            self.globals.add(st.alias or st.pkg[-1])
            from .stdpkg import find_std, gc_only, refusal
            from .values import GC
            if not GC[0] and gc_only(find_std(st.pkg), st.pkg) and not self.has_local_pkg(st.pkg):
                self.err(st.line, refusal(st.pkg))
            for nm in st.names or []:
                self.globals.add(nm)
        elif c is UsingDecl:
            if st.name:
                self.globals.add(st.name)
        elif c is Assign:
            for nm in self.pat_names(st.targets):
                self.globals.add(nm)

    # ------------------------------------------------------------ types
    def const_int(self, e):
        c = e.__class__
        if c is IntLit and not e.suffix:
            return e.v
        if c is IntLit:
            return e.v
        if c is Unary and e.op == "-":
            v = self.const_int(e.e)
            return -v if v is not None else None
        if c is Call:
            v = const_eval(e, {})
            return v if isinstance(v, int) and not isinstance(v, bool) else None
        if c is Binary and e.op in ("+", "-", "*"):
            a, b = self.const_int(e.l), self.const_int(e.r)
            if a is None or b is None:
                return None
            return a + b if e.op == "+" else a - b if e.op == "-" else a * b
        return None

    BUILTIN_GENERICS = {"Seq": 1, "List": 1, "Array": 1, "Dict": 2, "Set": 1, "Result": 2, "Stream": 1, "Ring": 1, "Atom": 1, "Future": 1, "ChanR": 1, "ChanW": 1, "FutureR": 1, "FutureW": 1}

    def ty_of_type(self, t, depth=0, keep=None, top=True):
        """The checker's type for a written type.  `keep` names type parameters to return as ("param", n) (a callee's own);
        the enclosing function's parameters show only inside an application, so a bare `T` stays unknown."""
        if t is None or depth > 8:
            return None
        c = t.__class__
        if c is TUnit:
            return "Unit"
        if c is TStatic:
            return self.ty_of_type(t.inner, depth + 1, keep, top)
        if c is TExpr:
            return self.type_num(t.expr, depth, keep)
        if c is TBound:
            return ("bound", ("pvar", t.name), (t.iface,) + tuple(t.also or []))
        if c is TFn:
            ps = tuple(self.ty_of_type(p[1] if isinstance(p, tuple) else p, depth + 1, keep, False) for p in (t.params or []))
            return ("fn", ps, self.ty_of_type(t.ret, depth + 1, keep, False) if t.ret is not None else "Unit")
        if c is TTuple:
            items = tuple(("spread", self.ty_of_type(ft, depth + 1, keep, False)) if lab == "..." else
                          self.ty_of_type(ft, depth + 1, keep, False) for lab, ft in t.items)
            labs = tuple(None if lab == "..." else self.tuple_label(lab, keep) for lab, ft in t.items)
            return ("tup", items, labs) if any(l is not None for l in labs) else ("tup", items)
        if c is TApp:
            from .typelam import reduce_app, TypeLambdaError
            try:
                return self.ty_of_type(reduce_app(t), depth + 1, keep, top)
            except TypeLambdaError:
                return None
        if c is TName and len(t.path) == 2 and not t.groups:
            return self.assoc_type(t.path[0], t.path[1], keep)
        if c is not TName or len(t.path) != 1:
            return None
        n = t.path[0]
        if n in self.pv and not t.groups:
            return ("pvar", n)
        if keep and n in keep:
            if not t.groups:
                return ("param", n)
            g0 = t.groups[0] if isinstance(t.groups[0], list) else [t.groups[0]]
            return ("appv", n, tuple(self.ty_of_type(x, depth + 1, keep, False) for x in g0))
        if n in self.fn_tparams:
            return None if t.groups else ("rigid", n)
        if n == "Seq" and not self.sig_mode and n not in self.tuples and n not in self.enums and n not in self.aliases \
                and n not in self.iface_decls:
            return None                                 # written in a program it is already an error, so leave it unknown
        app = self.app_type(t, n, depth, keep)
        if app is not None:
            return app
        if n in INTS:
            g = t.groups
            if g and g[0] and n != "BigInt":
                x = g[0][0] if isinstance(g[0], list) else g[0]
                if x.__class__ is TExpr and x.expr.__class__ is RangeE:
                    lo, hi = self.const_int(x.expr.lo), self.const_int(x.expr.hi)
                    if lo is not None and hi is not None:
                        return ("bounded", lo, hi if x.expr.incl else hi - 1)
            return "Int"
        if n in ("Double", "Float"):
            return "Float"
        if n in ("String", "Bool", "Char", "Unit", "Decimal"):
            return n
        if n in self.RES_NAMED and not t.groups and n not in self.tuples \
                and n not in self.enums and n not in self.aliases:
            return ("named", n)
        if n == "Secret" and n not in self.tuples and n not in self.enums and n not in self.aliases:
            return ("secret",)
        if n in self.aliases:
            a = self.aliases[n]
            if a.kind == "alias" and not a.tparams:
                return self.ty_of_type(a.type, depth + 1)
            if a.kind == "opaque" and not a.tparams:
                return ("named", n)
            return None
        if n in self.tuples and not self.tuples[n].tparams:
            return ("named", n)
        if n in self.enums and not self.enums[n].tparams:
            return ("named", n)
        return None

    def any_names(self, t):
        """The interfaces of an `any A + B` as a tuple of names, when every one is declared in this program; else None."""
        names = tuple(_tn(x) for x in [t.iface] + list(t.also or []))
        return names if all(nm in self.iface_decls for nm in names) else None

    def check_any_args(self, n, fn, args, ats):
        """A call to a function whose parameter is `any A + B` (or `any A`): a known argument type must implement every interface."""
        decls = self.fns.get(fn.name)
        if not decls or len(decls) != 1:
            return
        d = decls[0]
        for p, a, (t, _c) in zip(d.params or [], args, ats):
            if p.type.__class__ is not TAny or t is None:
                continue
            t = self.base(t)
            if t.__class__ is tuple and t[0] == "any":
                missing = [i for i in [_tn(p.type.iface)] + [_tn(x) for x in p.type.also or []] if i not in t[1]]
            else:
                missing = [i for i in [_tn(p.type.iface)] + [_tn(x) for x in p.type.also or []] if self.implements(t, i) is False]
            if missing:
                want = " + ".join([_tn(p.type.iface)] + [_tn(x) for x in p.type.also or []])
                self.err(n.line, f"`{tshow(t)}` doesn't implement `{missing[0]}`, which `any {want}` needs for `{p.name}`")

    def iface_member(self, iname, name, seen=None):
        """(the member's FnDecl, the associated-type names of its interface) for `name` in the interface or those it embeds."""
        seen = set() if seen is None else seen
        d = self.iface_decls.get(iname)
        if d is None or iname in seen:
            return None
        seen.add(iname)
        assoc = {m.name for m in d.members or [] if m.__class__ is AliasDecl}
        for m in d.members or []:
            if m.__class__ is FnDecl and m.name == name:
                return m, assoc
        for e in d.embeds or []:
            r = self.iface_member(_tn(e), name, seen)
            if r is not None:
                return r
        return None

    def any_fn_result(self, n, sc, fn, args):
        """`first_of(a)` where `fn first_of(c: any Container) c.Item` and a is itself a parameter typed `any`: the result is `a.Item`."""
        d = self.fns[fn.name][0]
        r = d.ret
        if r.__class__ is not TName or len(r.path) != 2 or r.groups or len(args) != len(d.params or []):
            return None
        for p, a in zip(d.params, args):
            if p.name == r.path[0] and p.type.__class__ is TAny and getattr(a, "expr", None).__class__ is Name:
                at = self.any_vars.get(sc.find(a.expr.name))
                if at is not None and at[1] == self.any_names(p.type):
                    return ("hid", at[2], r.path[1])
        return None

    def any_member_call(self, n, sc, fn, ats):
        """`a.m(args)` where a is a parameter typed `any I`: a member whose result or parameter is an associated type of I has the type
        `a.Item`, which belongs to this one value."""
        v = sc.find(fn.obj.name)
        at = self.any_vars.get(v) if v is not None else None
        if at is None:
            return NOANY
        found = next((f for f in (self.iface_member(i, fn.name) for i in at[1]) if f is not None), None)
        if found is None:
            return NOANY
        d, assoc = found

        def own(t):
            if t.__class__ is TName and len(t.path) == 1 and t.path[0] in assoc and not t.groups:
                return ("hid", at[2], t.path[0])
            if t.__class__ is TName and len(t.path) == 2 and t.path[0] == "Self" and t.path[1] in assoc:
                return ("hid", at[2], t.path[1])
            return None
        for p, (act, const) in zip(d.params or [], ats):
            exp = own(p.type) if p.type is not None else None
            if exp is not None and act is not None:
                self.compat(exp, self.base(act), const, n.line, "argument")
        r = own(d.ret) if d.ret is not None else None
        return r if r is not None else (None if d.ret is not None else NOANY)

    def assoc_type(self, base, member, keep):
        """`Names.Item` (a concrete type) is what its impl says; `C.Item` for a parameter stays symbolic until C is known."""
        if base in self.any_params:                        # a.Item for a parameter a: its own hidden type, or its concrete type's
            at = self.any_params[base]
            if at.__class__ is tuple and at[0] == "any":
                return ("hid", at[2], member)
            return self.assoc_of(at[1], member) if at.__class__ is tuple and at[0] in ("named", "app") else None
        if keep and base in keep:
            return ("tapp", "@" + member, (("param", base),))
        if base in self.fn_tparams:
            return ("tapp", "@" + member, (("rigid", base),))
        if base in self.pv:
            return ("tapp", "@" + member, (("pvar", base),))
        return self.assoc_of(base, member)

    def assoc_of(self, name, member):
        ast = self.assoc.get((name, member))
        if ast is None:
            return None
        saved, self.fn_tparams = self.fn_tparams, ()
        try:
            return self.ty_of_type(ast, 1, None, False)
        finally:
            self.fn_tparams = saved

    def tuple_label(self, lab, keep):
        """A field name in a tuple type.  Inside a type function's arms a name that is a parameter of the function or a variable of
        the pattern stands for a name (a string type), so `(K: T, ...Rest)` finds the field called by the type given for K."""
        if lab is None or lab == "_":
            return None
        if self.in_tfun:
            if keep and lab in keep:
                return ("param", lab)
            if lab in self.pv:
                return ("pvar", lab)
        return lab

    def unfold(self, t):
        """A declared tuple type as the labeled tuple of its fields (a generic one with its arguments filled in)."""
        td = self.tuples.get(t[1])
        if td is None or td.__class__ is not TupleDecl:
            return None
        keep = {tp.name for tp in td.tparams or []}
        binds = dict(zip([tp.name for tp in td.tparams or []], t[2])) if t[0] == "app" else {}
        if keep and t[0] != "app":
            return None
        saved, self.fn_tparams, self.in_tfun = self.fn_tparams, (), False
        try:
            items = [self.ty_of_type(f.type, 0, keep or None, False) for f in td.fields or []]
        finally:
            self.fn_tparams = saved
        r = ("tup", tuple(tys.subst_partial(i, binds) if i is not None and keep else i for i in items),
             tuple(f.name for f in td.fields or []))
        return r

    # ------------------------------------------------------------ type functions (`type alias F[T] = when T: ...`)
    def tfun(self, name):
        """(parameter names, scrutinee type, [(pattern, result)]) for a type function, built once from its declaration."""
        tf = self.tfuns.get(name)
        if tf is not None:
            return tf
        a = self.aliases[name]
        params = [tp.name for tp in a.tparams]
        self.tfuns[name] = tf = (params, None, [])         # entered first, so an arm that names the function itself finds it
        saved_pv, saved_tp, saved_tf = self.pv, self.fn_tparams, self.in_tfun
        self.fn_tparams = ()
        self.in_tfun = True
        try:
            keep = set(params)
            scrut = self.ty_of_type(a.type.scrut, 0, keep, False)
            arms = []
            for pat, res, guard in a.type.arms:
                self.pv = frozenset(self.pattern_vars(pat, keep))
                p = self.ty_of_type(pat, 0, keep, False)
                r = self.ty_of_type(res, 0, keep, False)
                arms.append((p, r, (guard, self.pv, keep) if guard is not None else None))
            self.tfuns[name] = tf = (params, scrut, arms)
        finally:
            self.pv, self.fn_tparams, self.in_tfun = saved_pv, saved_tp, saved_tf
        return tf

    def pattern_vars(self, pat, params):
        """The names a pattern binds: a bare name that is not a known type and not a parameter of the type function."""
        out = []

        def walk(x):
            c = x.__class__
            if c is TName:
                if len(x.path) == 1 and not x.groups:
                    nm = x.path[0]
                    if nm not in params and not self.known_type_name(nm) and nm not in out:
                        out.append(nm)
                for g in x.groups or []:
                    for y in g if isinstance(g, list) else [g]:
                        walk(y)
            elif c is TBound:
                if x.name not in params and x.name not in out:
                    out.append(x.name)
            elif c is TTuple:
                for lab, y in x.items:
                    if lab and lab not in ("...", "_") and lab not in params and lab not in out:
                        out.append(lab)
                    walk(y)
            elif c is TFn:
                for lab, y in x.params:
                    walk(y)
                walk(x.ret)
            elif c is TExpr and x.expr.__class__ is Name:
                nm = x.expr.name
                if nm not in params and nm not in out:
                    out.append(nm)
        walk(pat)
        return out

    def known_type_name(self, nm):
        return (nm in INTS or nm in ("Double", "Float", "String", "Bool", "Char", "Unit", "Decimal", "Secret") or nm in self.BUILTIN_GENERICS
                or nm in self.tuples or nm in self.enums or nm in self.aliases or nm in self.ifaces)

    def apply_tfun(self, name, args):
        return self.reduce_tapp(name, tuple(args))

    def reduce_tapp(self, name, args):
        """Apply the type function `name` to `args`: the first arm whose pattern matches gives the result.  When the argument is not
        known well enough to choose an arm the application stays symbolic (a type parameter) or unknown (None).  Each reduction costs
        one unit of fuel; a use that spends `tf_fuel` units is an error, so a type function that never ends cannot hang the checker."""
        if name.startswith("@"):
            base = args[0]
            if base is None:
                return None
            if tys._stuck(base) or any("pvar" in str(a) for a in args):
                return ("tapp", name, args)
            key = base if isinstance(base, str) else base[1] if base[0] in ("named", "app") else None
            return self.assoc_of(key, name[1:]) if key is not None else None
        if name not in self.aliases or self.aliases[name].type.__class__ is not TMatch:
            return None
        if any("pvar" in str(a) for a in args):
            return ("tapp", name, args)            # the arm is still being written down: leave the call as it is
        self.tf_depth += 1
        if self.tf_depth == 1:
            self.tf_steps = 0
            self.tf_trail = []
            self.tf_big = False
        try:
            self.tf_steps += 1
            self.tf_trail.append((name, args))
            big = sum(tys.tree_size(a) for a in args) > TF_MAX_NODES
            if self.tf_steps > self.tf_fuel or big:
                if self.tf_steps == self.tf_fuel + 1 or big and not self.tf_big:
                    self.tf_big = big
                    tail = "; ".join(f"{nm}[{', '.join(tys.show(a)[:40] for a in ar)}]" for nm, ar in self.tf_trail[-3:])
                    why = "grew past the size limit" if big else f"did not finish in {self.tf_fuel} reductions"
                    self.err(self.cur_line, f"type function `{name}` {why} (last: {tail}); "
                             f"it may call itself on a type that never gets smaller")
                return None
            params, scrut, arms = self.tfun(name)
            if len(args) != len(params):
                return None
            binds0 = dict(zip(params, args))
            sc = tys.subst(scrut, binds0)
            for pat, res, guard in arms:
                pb = {}
                r = tys.tmatch(tys.subst_partial(pat, binds0), sc, pb)
                if r == "yes" and guard is not None:
                    g = self.eval_guard(guard[0], {**binds0, **pb}, guard[1], guard[2])
                    if g is False:
                        continue
                    if g == "sym":
                        return ("tapp", name, args)
                    if g == "unk":
                        return None
                if r == "yes":
                    return tys.subst(res, {**binds0, **pb})
                if r == "unk":
                    return None
                if r == "sym":
                    return ("tapp", name, args)
            first = self.tf_trail[0] if self.tf_trail else (name, args)
            top = f"{first[0]}[{', '.join(tys.show(a) for a in first[1])}]"
            here = f"{name}[{', '.join(tys.show(a) for a in args)}]"
            self.err(self.cur_line, f"no arm of `{name}` matches `{tys.show(sc)}`" + (f" (while working out `{top}`)" if top != here else ""))
            return None
        finally:
            self.tf_depth -= 1

    def type_call(self, name, vals):
        """A pure function of the program run on type-level numbers or strings (a guard such as `big(N)`)."""
        if CT[0] is None:
            return None
        r = CT[0].call(name, list(vals), self.cur_line)
        if not r:
            return None
        v = r[0]
        if isinstance(v, bool):
            return ("bool", v)
        return ("lit", v) if isinstance(v, int) else ("slit", v) if isinstance(v, str) else None

    def eval_guard(self, e, env, pv, keep):
        """The guard of an arm (`if N > 3`) under the arm's bindings: True, False, or "sym"/"unk" when a type it needs is not known yet."""
        c = e.__class__
        if c is AndE or c is OrE:
            a = self.eval_guard(e.l, env, pv, keep)
            if (c is AndE and a is False) or (c is OrE and a is True):
                return a
            b = self.eval_guard(e.r, env, pv, keep)
            if (c is AndE and b is False) or (c is OrE and b is True):
                return b
            for r in ("unk", "sym"):
                if r in (a, b):
                    return r
            return c is AndE
        if c is Call:
            t = self.guard_value(e, env, pv, keep)
            if t.__class__ is tuple and t[0] == "bool":
                return t[1]
            return tys._stuck(t) or "unk"
        if c is Unary and e.op == "not":
            a = self.eval_guard(e.e, env, pv, keep)
            return (not a) if a in (True, False) else a
        if c is Binary and e.op in ("==", "~=", "<", ">", "<=", ">="):
            a, b = self.guard_value(e.l, env, pv, keep), self.guard_value(e.r, env, pv, keep)
            if a is None or b is None:
                return "unk"
            sa, sb = tys._stuck(a), tys._stuck(b)
            if sa or sb:
                return "unk" if "unk" in (sa, sb) else "sym"
            if e.op in ("==", "~="):
                return (a == b) == (e.op == "==")
            if a.__class__ is tuple and b.__class__ is tuple and a[0] == b[0] == "lit":
                x, y = a[1], b[1]
                return {"<": x < y, ">": x > y, "<=": x <= y, ">=": x >= y}[e.op]
            return "unk"
        self.err(self.cur_line, "a guard in a type function compares numbers or types with == ~= < > <= >=, and joins them with and, or, not")
        return "unk"

    def guard_value(self, e, env, pv, keep):
        saved, self.pv = self.pv, pv
        try:
            t = self.type_num(e, 0, keep)
        finally:
            self.pv = saved
        return tys.subst(t, env) if t is not None else None

    def check_tfun_decl(self, n):
        """A type function is built when it is declared (so its arms are read once); one that calls itself on a type that is not a piece
        of what it matched gets a warning, since only the fuel limit would stop it."""
        if n.type.__class__ is not TMatch or not n.tparams:
            return
        self.tfun(n.name)
        params, scrut, arms = self.tfuns[n.name]
        for pat, res, _g in arms:
            inside = set()
            self.collect_pvars(pat, inside, top=True)
            for call in self.self_calls(res, n.name):
                used = set()
                for a in call[2]:
                    self.collect_pvars(a, used, top=False)
                if not (used & inside) and not any(self.has_size_step(a) for a in call[2]):
                    self.diags.append(Diag(n.line, f"`{n.name}` calls itself on `{', '.join(tys.show(a) for a in call[2])}`, which is not a piece "
                                                   f"of what its arm matched, so it may not end (the checker stops it after {self.tf_fuel} reductions)", "warning"))
                    break

    def collect_pvars(self, t, out, top):
        if t.__class__ is not tuple:
            return
        if t[0] == "pvar":
            if not top:
                out.add(t[1])
            return
        if t[0] == "app":
            for a in t[2]:
                self.collect_pvars(a, out, False)
            if len(t) > 3 and t[3].__class__ is tuple:
                self.collect_pvars(t[3], out, False)
        elif t[0] in ("tup",):
            for a in t[1]:
                self.collect_pvars(a, out, False)
        elif t[0] == "spread":
            self.collect_pvars(t[1], out, False)
        elif t[0] == "fn":
            for a in t[1]:
                self.collect_pvars(a, out, False)
            self.collect_pvars(t[2], out, False)
        elif t[0] == "tapp":
            for a in t[2]:
                self.collect_pvars(a, out, False)
        elif t[0] == "sz":
            self.collect_pvars(t[2], out, False)
            self.collect_pvars(t[3], out, False)

    def self_calls(self, t, name, out=None):
        out = [] if out is None else out
        if t.__class__ is tuple:
            if t[0] == "tapp" and t[1] == name:
                out.append(t)
            if t[0] in ("app", "tapp"):
                for a in t[2]:
                    self.self_calls(a, name, out)
            elif t[0] == "tup":
                for a in t[1]:
                    self.self_calls(a, name, out)
            elif t[0] == "spread":
                self.self_calls(t[1], name, out)
            elif t[0] == "fn":
                for a in t[1]:
                    self.self_calls(a, name, out)
                self.self_calls(t[2], name, out)
        return out

    def has_size_step(self, t):
        return t.__class__ is tuple and t[0] == "app" and len(t) > 3 and t[3].__class__ is tuple and t[3][0] == "sz"

    def app_type(self, t, n, depth, keep):
        """("app", head, args) for `Box[Int]`, `List[T]`, a generic alias, or None when `t` is not an application the checker models."""
        g = t.groups or []
        if not g or not g[0]:
            return None
        first = g[0] if isinstance(g[0], list) else [g[0]]
        if n in self.aliases and getattr(self.aliases[n], "tparams", None):
            a = self.aliases[n]
            if a.type.__class__ is TMatch:
                if len(a.tparams) != len(first):
                    return None
                return self.apply_tfun(n, tuple(self.ty_of_type(x, depth + 1, keep, False) for x in first))
            if a.kind != "alias" or any(tp.holes for tp in a.tparams) or len(a.tparams) != len(first):
                return None
            binds = {tp.name: self.ty_of_type(x, depth + 1, keep, False) for tp, x in zip(a.tparams, first)}
            body = self.ty_of_type(a.type, depth + 1, {tp.name for tp in a.tparams}, False)
            return subst_t(body, binds)
        d = self.tuples.get(n) or self.enums.get(n)
        if d is not None:
            if not getattr(d, "tparams", None) or any(tp.holes for tp in d.tparams) or len(d.tparams) != len(first):
                return None
        elif n in self.BUILTIN_GENERICS and n not in self.aliases:
            if self.BUILTIN_GENERICS[n] != len(first):
                return None
        else:
            return None
        args = tuple(self.ty_of_type(x, depth + 1, keep, False) for x in first)
        if n == "Array" and len(g) > 1 and g[1]:
            x = g[1][0] if isinstance(g[1], list) else g[1]
            k = self.size_term(x, keep)
            if k is not None:
                return ("app", n, args, k)
        return ("app", n, args)

    def type_num(self, e, depth, keep):
        """A number written where a type goes: ("lit", n), or arithmetic on such numbers and on type functions (`1 + Length[Rest]`)."""
        c = e.__class__
        if c is IntLit:
            return ("lit", e.v)
        if c is StrLit and all(isinstance(p, str) for p in e.parts or []):
            return ("slit", "".join(e.parts or []))
        if c is Call:
            if CT[0] is None or CT[0].key_of(e.fn) is None \
                    or any(a.expr is None or getattr(a, "label", None) or getattr(a, "mod", None) for a in e.args or []):
                return None
            args = tuple(self.type_num(a.expr, depth, keep) for a in e.args or [])
            if any(a is None for a in args):
                return None
            return tys.subst_partial(("cfn", CT[0].key_of(e.fn), args), {})
        if c is Name:
            return self.ty_of_type(TName([e.name], [], line=0), depth + 1, keep, False)
        if c is GenApp and e.base.__class__ is Name:
            return self.ty_of_type(TName([e.base.name], list(e.groups), line=0), depth + 1, keep, False)
        if c is Binary and e.op in ("+", "-", "*"):
            a, b = self.type_num(e.l, depth, keep), self.type_num(e.r, depth, keep)
            if a is None or b is None:
                return None
            if a[0] == "slit" and b[0] == "slit" and e.op == "+":
                return ("slit", a[1] + b[1])
            if a[0] == "lit" and b[0] == "lit":
                return ("lit", a[1] + b[1] if e.op == "+" else a[1] - b[1] if e.op == "-" else a[1] * b[1])
            return ("sz", e.op, a, b)
        return None

    def size_term(self, x, keep):
        """A size written in a type: an int, a size variable (a pattern variable, or a parameter of the type function or callee), or
        `N - 1` and the like; None when it is not worked out."""
        if x.__class__ is TName:
            if len(x.path) == 1 and not x.groups:
                nm = x.path[0]
                if nm in self.pv:
                    return ("pvar", nm)
                if keep and nm in keep:
                    return ("param", nm)
                v = self.consts.get(nm)
                if isinstance(v, int) and not isinstance(v, bool):
                    return v                       # a constant binding such as `N = fib(10)` used as a size
            elif len(x.path) == 1 and x.path[0] in self.aliases and getattr(self.aliases[x.path[0]], "type", None).__class__ is TMatch:
                r = self.ty_of_type(x, 0, keep, False)          # a type function that computes a number: Array[Int][Length[T]]
                return r[1] if r.__class__ is tuple and r[0] == "lit" else None
            return None
        if x.__class__ is not TExpr:
            return None
        k = self.const_int(x.expr)
        if k is not None:
            return k
        return self.size_expr(x.expr, keep)

    def size_expr(self, e, keep):
        c = e.__class__
        if c is Name:
            return self.size_term(TName([e.name], [], line=0), keep)
        if c is IntLit:
            return e.v
        if c is Call:
            return self.const_int(e)
        if c is Binary and e.op in ("+", "-", "*"):
            a, b = self.size_expr(e.l, keep), self.size_expr(e.r, keep)
            if a is None or b is None:
                return None
            if a.__class__ is int and b.__class__ is int:
                return a + b if e.op == "+" else a - b if e.op == "-" else a * b
            return ("sz", e.op, a, b)
        return None

    def compat(self, exp, act, const, line, what="value"):
        """Report a mismatch between an expected and an actual type."""
        if exp is None or act is None or exp == act:
            return
        if exp.__class__ is tuple and exp[0] == "bounded":
            if act == "Int" or (act.__class__ is tuple and act[0] == "bounded"):
                if const is not None:
                    if not exp[1] <= const <= exp[2]:
                        self.err(line, f"`{const}` is out of range for `{tshow(exp)}`")
                elif act == "Int":
                    self.err(line, f"`Int` does not convert to `{tshow(exp)}`; use `cast[...]` or `try_cast[...]`")
                return
        if exp == "Int" and act.__class__ is tuple and act[0] == "bounded":
            return
        if exp == "Float" and act in ("Int", "Decimal"):
            return
        if exp == "Decimal" and act in ("Int", "Float"):
            return
        if exp == "Int" and act == "Decimal":
            return
        if exp.__class__ is tuple and act.__class__ is tuple and exp[0] == "coll" and act[0] == "coll":
            return
        if exp.__class__ is tuple and exp[0] in ("app", "fn", "tup", "param", "rigid") or act.__class__ is tuple and act[0] in ("app", "fn", "tup", "param", "rigid"):
            if tys.compatible(exp, act):
                return
        self.err(line, f"mismatched types: expected `{tshow(exp)}`, found `{tshow(act)}`")

    # ------------------------------------------------------------ patterns
    def pat_names(self, p, out=None):
        out = [] if out is None else out
        if p is None:
            return out
        c = p.__class__
        if c is PBind:
            out.append(p.name)
        elif c is PAs:
            out.append(p.name)
            self.pat_names(p.pat, out)
        elif c is PRest:
            if p.name:
                out.append(p.name)
        elif c is PTuple:
            for _, q in p.items or []:
                self.pat_names(q, out)
        elif c is PCon:
            for _, q in p.args or []:
                self.pat_names(q, out)
        elif c is PBin:
            out.extend(e[1] for e in p.elems if e[0] == "field" and e[1])
        elif c is PTyped:
            self.pat_names(p.pat, out)
        return out

    def bind_pat(self, p, sc, ty=None, res=False):
        names = self.pat_names(p)
        for nm in names:
            sc.vars[nm] = Var(ty if p.__class__ is PBind else None, res, self.loop_depth)
        # `rx, tx = Chan[Int][1]()`: each plain name gets the type of its place in a tuple whose shape is known
        if p.__class__ is PTuple and ty.__class__ is tuple and ty and ty[0] == "tup" and len(ty[1]) == len(p.items or []) \
                and not any(x.__class__ is tuple and x and x[0] == "spread" for x in ty[1]) \
                and not any(q.__class__ is PRest for _, q in p.items):
            for (_, q), et in zip(p.items, ty[1]):
                if q.__class__ is PBind and et is not None:
                    sc.vars[q.name] = Var(et, res, self.loop_depth)

    # ------------------------------------------------------------ walking
    def ev(self, n, sc):
        """Evaluate a node for checking. Returns (type, const) for expressions."""
        if n is None:
            return None, None
        if isinstance(n, (list, tuple)):
            for x in n:
                self.ev(x, sc)
            return None, None
        if not hasattr(n, "_fields"):
            return None, None
        m = getattr(self, "e_" + n.__class__.__name__, None)
        if getattr(n, "line", 0):
            self.cur_line = n.line
        if m is not None:
            r = m(n, sc)
            return r if r is not None else (None, None)
        for f in n._fields:
            self.ev(getattr(n, f), sc)
        return None, None

    def t(self, n, sc):
        return self.ev(n, sc)[0]

    # literals
    def e_IntLit(self, n, sc):
        return ("Float", None) if n.suffix == "f" else ("Int", n.v)

    def e_DurLit(self, n, sc):
        return ("named", "Duration") if "Duration" not in self.tuples and "Duration" not in self.aliases else None, None

    def e_FloatLit(self, n, sc):
        return "Float", None

    def e_DecLit(self, n, sc):
        return "Decimal", None

    def e_StrLit(self, n, sc):
        text = []
        for p in n.parts or []:
            if hasattr(p, "_fields"):
                self.ev(p, sc)
                text = None
            elif text is not None and isinstance(p, str):
                text.append(p)
            else:
                text = None
        return "String", ("".join(text) if text is not None else None)

    def e_Interp(self, n, sc):
        self.ev(n.expr, sc)
        return None, None

    def e_CharLit(self, n, sc):
        return "Char", None

    def e_BoolLit(self, n, sc):
        return "Bool", None

    def e_UnitLit(self, n, sc):
        return "Unit", None

    def e_KwLit(self, n, sc):
        return None, None

    def e_Name(self, n, sc):
        v = sc.find(n.name)
        if v is not None:
            if v in self.moved:
                self.err(n.line, f"use of moved value `{n.name}` (moved at line {self.moved[v]})")
            return v.ty, None
        ft = self.fn_value_type(n.name)
        if ft is not None:
            return ft, None
        if n.name in self.globals or n.name in self.prelude or sc.open:
            return None, None
        self.err(n.line, f"undefined name `{n.name}`")
        return None, None

    def fn_value_type(self, name):
        """The function type of a declared function used as a value (`traverse(half, xs)`): only a plain one, with one declaration,
        no type parameters, and ordinary parameters; anything else stays unknown."""
        decls = self.fns.get(name)
        if not decls or len(decls) != 1:
            return None
        d = decls[0]
        if d.__class__ is not FnDecl or d.tparams or d.ret is None or name in self.tuples or name in self.enums:
            return None
        ps = d.params or []
        if any(getattr(p, "mod", None) or getattr(p, "variadic", None) or getattr(p, "default", None) is not None
               or getattr(p, "type", None) is None for p in ps):
            return None
        pts = tuple(self.ty_of_type(p.type, 0, None, False) for p in ps) or ("Unit",)      # `() -> T` is written with one Unit parameter, as in the signature table
        ret = self.ty_of_type(d.ret, 0, None, False)
        if ret is None:
            return None
        return ("fn", pts, ret)

    def e_Gimme(self, n, sc):
        return None, None

    def e_Unary(self, n, sc):
        t, c = self.ev(n.e, sc)
        if n.op == "-" and c is not None:
            return t, -c
        if n.op == "not" or n.op == "!":
            if t is not None and t != "Bool":
                self.err(n.line, f"`not` needs a `Bool`, found `{tshow(t)}`")
            return "Bool", None
        return t if t in ("Int", "Float") else None, None

    def e_AndE(self, n, sc):
        for x in (n.l, n.r):
            t = self.t(x, sc)
            if t is not None and t != "Bool":
                self.err(n.line, f"`and` needs `Bool` operands, found `{tshow(t)}`")
        return "Bool", None

    def e_OrE(self, n, sc):
        for x in (n.l, n.r):
            t = self.t(x, sc)
            if t is not None and t != "Bool":
                self.err(n.line, f"`or` needs `Bool` operands, found `{tshow(t)}`")
        return "Bool", None

    def e_InOp(self, n, sc):
        self.ev(n.l, sc)
        self.ev(n.r, sc)
        return "Bool", None

    def e_IsOp(self, n, sc):
        self.ev(n.e, sc)
        for nm in self.pat_names(n.pat):
            sc.vars[nm] = Var(None, False, self.loop_depth)
        return "Bool", None

    SCAL = {"Int", "Float", "String", "Bool", "Char", "Decimal", "Unit"}

    @staticmethod
    def base(t):
        return "Int" if t.__class__ is tuple and t[0] == "bounded" else t

    def e_Binary(self, n, sc):
        lt, lc = self.ev(n.l, sc)
        rt, rc = self.ev(n.r, sc)
        a, b = self.base(lt), self.base(rt)
        op = n.op
        self.check_op_bound(n, sc)
        dur = ("named", "Duration")
        if (a == dur or b == dur) and "Duration" not in self.tuples and "Duration" not in self.aliases:
            r = self.duration_op(n, a, b, dur)
            if r is not NOANY:
                return r
        if op in ("==", "!=", "<", ">", "<=", ">="):
            if a == ("secret",) or b == ("secret",):
                self.err(n.line, "a Secret can't be compared with " + op + "; use secret_eq(a, b), or compare what reveal gives")
                return "Bool", None
            if a in self.SCAL and b in self.SCAL and a != b and {a, b} - {"Int", "Float", "Decimal"}:
                self.err(n.line, f"cannot compare `{tshow(a)}` and `{tshow(b)}`")
            return "Bool", None
        if op in ("+", "-", "*", "/", "%"):
            if a in self.SCAL and b in self.SCAL:
                num = {"Int", "Float", "Decimal"}
                if not (a in num and b in num) and not (op == "+" and a == b == "String"):
                    self.err(n.line, f"cannot apply `{op}` to `{tshow(a)}` and `{tshow(b)}`")
                    return None, None
                if op in ("/", "%") and a == "Int" and b == "Int" and rc == 0:
                    self.err(n.line, "division by a constant zero")
                if a == "Int" and b == "Int":
                    c = None
                    if lc is not None and rc is not None and op in ("+", "-", "*"):
                        c = lc + rc if op == "+" else lc - rc if op == "-" else lc * rc
                    return "Int", c
                if "Float" in (a, b):
                    return "Float", None
                return (a if a == b else None), None
            return None, None
        return None, None

    def duration_op(self, n, a, b, dur):
        """Arithmetic and comparison with a Duration: `+` and `-` take two Durations, `*` a Duration and an Int, `/` a Duration and
        an Int (a Duration divided by a Duration is a compile error: divide the counts, `nanos(a) / nanos(b)`).  NOANY: not decided."""
        op = n.op
        known = lambda t: t in self.SCAL or (t.__class__ is tuple and t[0] == "bounded")
        asint = lambda t: "Int" if t.__class__ is tuple and t[0] == "bounded" else t
        other = b if a == dur else a
        if other is None or (other != dur and not known(other)):
            return NOANY
        other = asint(other)
        if op in ("==", "!=", "<", ">", "<=", ">="):
            if other != dur:
                self.err(n.line, f"cannot compare `{tshow(dur)}` and `{tshow(other)}`: write the other side as a Duration such as `2s`, or compare `nanos(d)`")
            return "Bool", None
        if op in ("+", "-"):
            if a == dur and b == dur:
                return dur, None
            self.err(n.line, f"cannot apply `{op}` to `{tshow(a)}` and `{tshow(b)}`: a Duration combines only with a Duration (`2s`, `500ms`), so the unit is never a guess")
            return None, None
        if op == "*":
            if (a == dur and b == "Int") or (a == "Int" and b == dur):
                return dur, None
            self.err(n.line, f"cannot apply `*` to `{tshow(a)}` and `{tshow(b)}`: a Duration is multiplied by an Int")
            return None, None
        if op == "/":
            if a == dur and b == "Int":
                return dur, None
            self.err(n.line, f"cannot apply `/` to `{tshow(a)}` and `{tshow(b)}`: a Duration is divided by an Int; for a ratio of two Durations, divide the counts, `nanos(a) / nanos(b)`")
            return None, None
        return NOANY

    def e_Q(self, n, sc):
        t = self.base(self.ev(n.e, sc)[0])
        if t.__class__ is tuple and t[0] == "app" and t[1] == "Result" and len(t[2]) == 2 and t[2][0] is not None \
                and not tys.params_in(t[2][0]):
            return t[2][0], None                  # `spawn("cat")?` is the Child
        return None, None

    def e_Move(self, n, sc):
        e = n.e
        if e.__class__ is Name:
            v = sc.find(e.name)
            if v is not None:
                self.ev(e, sc)
                if v.depth < self.loop_depth and not self.exit_ctx:
                    self.err(n.line, f"`{e.name}` is moved inside a loop; a resource may be moved only on an exiting path")
                self.moved[v] = n.line
                return v.ty, None
        return self.ev(e, sc)

    def e_Ref(self, n, sc):
        return self.ev(n.e, sc)

    def iface_members(self, name, seen=None):
        """The member names an interface of this program provides, with those of the interfaces it embeds; None when that can't be told
        (a built-in interface such as `Numeric`, or one from another package)."""
        seen = set() if seen is None else seen
        d = self.iface_decls.get(name)
        if d is None:
            return None
        if name in seen:
            return set()
        seen.add(name)
        out = {m.name for m in d.members or [] if getattr(m, "name", None)}
        for e in d.embeds or []:
            sub = self.iface_members(_tn(e), seen)
            if sub is None:
                return None
            out |= sub
        return out

    def check_tparam_member(self, n, t):
        """`x.m` where x has the type parameter `T`: m must come from T's bounds, or be a function that takes x (`x.m()` is `m(x)`)."""
        tp = self.tp_decl.get(t[1])
        if tp is None or tp.where or n.name in self.fns or n.name in self.prelude or n.name in self.globals \
                or n.name in self.consumes or n.name in self.load_sigs():
            return
        names = [_tn(b) for b in tp.bounds or []]
        allowed = set()
        for b in names:
            m = self.iface_members(b)
            if m is None:
                return
            allowed |= m
        if n.name in allowed:
            return
        if not names:
            self.err(n.line, f"`{t[1]}` has no bound, so `{n.name}` is not available on it: add a bound that provides `{n.name}`")
        else:
            self.err(n.line, f"`{n.name}` is not provided by the bound{'s' if len(names) > 1 else ''} of `{t[1]}` ({', '.join(names)})")

    def e_Field(self, n, sc):
        t = self.t(n.obj, sc)
        if t.__class__ is tuple and t[0] == "rigid":
            self.check_tparam_member(n, t)
            return None, None
        if t.__class__ is tuple and t[0] == "named" and t[1] in self.tuples:
            for f in self.tuples[t[1]].fields or []:
                if f.name == n.name:
                    return self.ty_of_type(f.type), None
            self.no_such_field(n, t[1], self.tuples[t[1]])
        if t.__class__ is tuple and t[0] == "app" and t[1] in self.tuples:
            td = self.tuples[t[1]]
            if len(td.tparams or []) == len(t[2]):
                for f in td.fields or []:
                    if f.name == n.name:
                        ft = self.ty_of_type(f.type, 0, {tp.name for tp in td.tparams})
                        return tys.subst(ft, {tp.name: a for tp, a in zip(td.tparams, t[2])}), None
                self.no_such_field(n, t[1], td)
        return None, None

    def no_such_field(self, n, tname, td):
        """`p.nope` on a tuple with no such field (a method or function of that name is not a field, so it is left alone)."""
        nm = n.name
        if id(n) in self.callee_fields or not isinstance(nm, str) or nm.isdigit() or nm in self.fns or nm in self.globals \
                or any(k[1] == nm for k in self.methods) or nm in self.load_sigs() or getattr(td, "spread", None):
            return
        names = [f.name for f in td.fields or []]
        if any(getattr(f, "name", None) in (None, "...") for f in td.fields or []):
            return
        self.err(n.line, f"`{tname}` has no field `{nm}`" + (f"; its fields are {', '.join('`'+x+'`' for x in names)}" if names else ""))

    def settle_mixed(self, node, expected):
        """A collection literal whose elements disagree is an error unless the type expected where it is used names a union
        (`List[Int | String]`), a type parameter, or anything else the elements might convert into.  `expected` None means
        nothing is expected (a binding without an annotation, an argument of a library function)."""
        m = self.mixed_lits.pop(id(node), None)
        if m is None:
            return
        def plain(x):                                    # a type with no union, type parameter, or unknown part anywhere in it
            return x is not None and (x.__class__ is str or (x[0] == "app" and all(plain(a) for a in x[2])))
        if expected is None or plain(expected):
            hint = "d: Dict[String, Int | Bool] = ..." if "Dict(" in m[1] else "xs: List[Int | String] = ..."
            self.err(m[0], m[1] + f"; to mix them, declare a union, as in `{hint}`")

    def arity_clash(self, ft, count):
        """True when a lambda of `count` parameters cannot be used where the function type `ft` is expected.  A lambda with
        several parameters may also take apart a single tuple argument (`(k, v): ...` over the entries of a Dict), so that
        is allowed when the one parameter is a tuple of that many fields, or is not known well enough to say."""
        if not self.arity_known(ft) or len(ft[1]) == count:
            return False
        if len(ft[1]) == 1 and count > 1:
            p = self.base(ft[1][0])
            if p is None or self.has_unsettled(p) and not (p.__class__ is tuple and p[0] == "tup"):
                return False
            if p.__class__ is tuple and p[0] == "tup":
                return len(p[1]) != count
            if p.__class__ is tuple and p[0] == "named" and p[1] in self.tuples:
                return len(self.tuples[p[1]].fields or []) != count
            return True
        return True

    def arity_known(self, ft):
        """True when a function type states its parameter count (no parameter standing for a whole argument list)."""
        return all(not (p.__class__ is tuple and p[0] in ("param", "rigid", "appv", "ctor", "tapp")) for p in ft[1])

    def e_Lambda(self, n, sc):
        inner = Sc(sc, open_=not n.params)
        expect, self.lam_expect = self.lam_expect, None
        if expect and expect[0] == "fn" and n.params and self.arity_clash(expect, len(n.params)):
            self.err(n.line, f"this function takes {len(n.params)} parameter{'s' if len(n.params) != 1 else ''}, but it is used where one with {len(expect[1])} is expected")
        eps = expect[1] if expect and len(expect[1]) == len(n.params or []) else ()
        ptypes = []
        for i, p in enumerate(n.params or []):
            pty = self.ty_of_type(p.type) if p.type is not None else (self.base_free(eps[i]) if eps else None)
            ptypes.append(pty)
            if p.name:
                inner.vars[p.name] = Var(pty, False, self.loop_depth)
            if p.pat is not None:
                self.bind_pat(p.pat, inner)
        for nm in n.locals or []:
            inner.vars[nm] = Var(None, False, self.loop_depth)
        saved = (self.fn_ret, self.loop_depth, self.exit_ctx)
        self.fn_ret = None
        self.exit_ctx = False
        body = n.body
        if body.__class__ is Block and len(body.stmts or []) == 1 and body.stmts[0].__class__ is ExprStmt:
            body = body.stmts[0].e
        elif body.__class__ is ExprStmt:
            body = body.e
        bt = self.ev(body, inner)[0]
        self.fn_ret, self.loop_depth, self.exit_ctx = saved
        if body.__class__ is Block or n.partial or n.fiber:
            bt = None                     # a longer block's value is not worked out here
        return ("fn", tuple(ptypes), self.base(bt)), None

    @staticmethod
    def base_free(t):
        """An expected parameter type, or None when it still holds a type parameter that nothing has fixed."""
        return None if t is None or tys.params_in(t) else t

    def e_PH(self, n, sc):
        return None, None

    def e_DoRecv(self, n, sc):
        t = self.t(n.recv, sc)
        inner = Sc(sc, open_=True)
        self.ev(n.body, inner)
        return None, None

    def e_UpdLine(self, n, sc):
        self.ev(n.expr, sc)
        self.ev(n.nested, sc)
        return None, None

    def e_SqlE(self, n, sc):
        self.ev(n.conn, sc)
        for p in n.parts or []:
            if isinstance(p, tuple):
                self.ev(p[1], sc)
        return None, None

    # blocks and statements
    def diverges(self, stmts):
        if not stmts:
            return False
        last = stmts[-1]
        if last.__class__ is ExprStmt:
            last = last.e
        return last.__class__ in (Return, Break, Continue, TodoE)

    def e_Block(self, n, sc, new_scope=True):
        inner = Sc(sc) if new_scope else sc
        stmts = n.stmts or []
        saved = self.exit_ctx
        self.exit_ctx = saved or self.diverges(stmts)
        last = (None, None)
        for st in stmts:
            last = self.ev(st, inner)
        self.exit_ctx = saved
        if stmts and stmts[-1].__class__ is not ExprStmt:
            return None, None
        return last

    def e_ExprStmt(self, n, sc):
        return self.ev(n.e, sc)

    def e_TrailIf(self, n, sc):
        self.ev(n.cond, sc)
        self.ev(n.stmt, sc)
        return None, None

    def e_Return(self, n, sc):
        t, c = self.ev(n.e, sc)
        if n.e is not None:
            self.settle_mixed(n.e, self.fn_ret)
        if self.fn_ret is not None and n.e is not None:
            self.compat(self.fn_ret, t, c, n.line)
        return None, None

    def e_Break(self, n, sc):
        self.ev(n.e, sc)
        return None, None

    def handle_ret(self, t):
        """The handle type named by `t` (H or Result[H, E]), or None."""
        if t.__class__ is not TName or not t.path:
            return None
        if t.path[-1] in self.handle_types:
            return t.path[-1]
        if t.path[-1] == "Result" and t.groups and t.groups[0]:
            g = t.groups[0][0]
            if g.__class__ is TName and g.path and g.path[-1] in self.handle_types:
                return g.path[-1]
        return None

    def is_resource_expr(self, e):
        wrapped = False
        while e.__class__ in (Q, Move):
            wrapped = wrapped or e.__class__ is Q
            e = e.e
        if e.__class__ is Call:
            f = e.fn
            if f.__class__ is GenApp:
                f = f.base
            if f.__class__ is Name and (f.name in RES_MAKERS or f.name in self.handle_makers or f.name in self.res_tuples):
                return True
            if f.__class__ is Name and f.name in self.fns and len(self.fns[f.name]) == 1:
                r = self.fns[f.name][0].ret            # a function whose result is a resource
                if self.is_res_type(r):
                    return True
                if (wrapped and r.__class__ is TName and r.path and r.path[-1] == "Result"
                        and r.groups and r.groups[0] and self.is_res_type(r.groups[0][0])):
                    return True
            if f.__class__ is Field and f.obj.__class__ is Name and f.obj.name == "Connection":
                return True
        return False

    def literal_count(self, head, v):
        """How many elements the literal `v` of the collection `head` has, or None when that is not known from the text."""
        if head == "Array" and v.__class__ is TupleE:
            if any(sp for _l, _e, sp in v.items):
                return None
            return len(v.items)
        if v.__class__ is not Call or v.fn.__class__ is not Name or v.fn.name != head or v.trailing is not None or head in self.tuples:
            return None
        if any(getattr(a, "mod", None) or getattr(a, "spread", None) or a.expr.__class__ is CompE for a in v.args):
            return None
        if head == "Dict":
            keys = [a.label for a in v.args]
            return None if any(k is None for k in keys) else len(set(keys))
        if head == "Set":
            lits = [(a.expr.__class__.__name__, getattr(a.expr, "v", None)) for a in v.args if a.expr.__class__ in (IntLit, StrLit)]
            return len(v.args) - (len(lits) - len(set(lits)))
        return len(v.args)

    def check_literal_capacity(self, n, ann):
        """`a: Set[Int][8] = Set(1, 2)` says 8 on the left and 2 on the right; the size written on a declaration must be the literal's.
        Room is written on the constructor (`Set[Int][8](1, 2)`), and a value with no known count (a comprehension) takes the declared size."""
        from .values import GC
        a = n.ann
        if (GC[0] and a.__class__ is TName and a.path[-1] != "Array") or a.__class__ is not TName or a.path[-1] not in ("Set", "List", "Dict", "Array") or len(a.groups or []) < 2 or a.path[-1] in self.tuples:
            return
        g = a.groups[1]
        g = g[0] if isinstance(g, list) and g else g
        size = self.const_int(g.expr) if g.__class__ is TExpr else None
        if size is None and g.__class__ is TExpr and g.expr.__class__ is Name and isinstance(self.consts.get(g.expr.name), int):
            size = self.consts[g.expr.name]
        head = a.path[-1]
        k = self.literal_count(head, n.value) if size is not None else None
        if head == "Array" and n.value.__class__ is not TupleE:
            return                                  # an `Array(...)` call is checked as a type below
        if k is not None and k != 0 and k != size:        # an empty literal takes the declared size
            what = f"the declared size {size} does not match the {k} element{'' if k == 1 else 's'} of this {head} literal; "
            if head == "Array":
                self.err(n.line, what + f"an Array has exactly the elements it is written with, so write {k} or leave the size out")
            else:
                args = ", ".join("..." if x is None else tshow(x) for x in ann[2]) if ann.__class__ is tuple and ann[0] == "app" else "..."
                self.err(n.line, what + f"write the size you mean on the constructor to give it room (`{head}[{args}][{size}](...)`), "
                         f"or write {k}, or leave the size out")

    def e_Assign(self, n, sc):
        t, c = self.ev(n.value, sc)
        ann = self.ty_of_type(n.ann) if n.ann is not None else None
        self.settle_mixed(n.value, ann)
        if n.ann is not None:
            self.check_type_arity(n.ann, n.line)
        if n.ann is not None and n.op == "=":
            self.compat(ann, t, c, n.line)
            self.check_literal_capacity(n, ann)
        if n.ann is not None and n.ann.__class__ is TName and n.ann.path[-1] in INTS and n.value.__class__ is IntLit:
            self.check_fit(n.ann.path[-1], n.value.v, n.line)
        res = self.is_resource_expr(n.value)
        if n.value.__class__ is Name:
            v = sc.find(n.value.name)
            if v is not None and v.resource and n.op == "=":
                self.err(n.line, f"`{n.value.name}` is a resource; write `move {n.value.name}` to move it")
        if n.value.__class__ is Move:
            res = True
        if n.op != "=":
            return None, None
        for tgt in (n.targets if isinstance(n.targets, list) else [n.targets]):
            if tgt.__class__ is PBind:
                sc.vars[tgt.name] = Var(ann or t, res, self.loop_depth)
                self.bind_any_local(n, sc, tgt.name)
            elif tgt.__class__ is PPlace:
                self.ev(tgt.expr, sc)
            else:
                self.bind_pat(tgt, sc, ann or t, res)
        return None, None

    def bind_any_local(self, n, sc, name):
        """`x: any Container = make()` gets a hidden type of its own, as a parameter does; `x = a` (or `x: any I = a`) for an `any` parameter or
        local `a` is the same value, so it shares a's."""
        src = self.any_vars.get(sc.find(n.value.name)) if n.value.__class__ is Name and n.value.name != name else None
        if src is not None:
            at = src
        elif n.ann.__class__ is TAny and self.any_names(n.ann):
            at = ("any", self.any_names(n.ann), f"{name}@{n.line}")
        else:
            self.any_params.pop(name, None)             # a new binding of the name that is not an `any`
            return
        self.any_params[name] = at
        self.any_vars[sc.vars[name]] = at

    FIT = {"Int8": (-128, 127), "Int16": (-32768, 32767), "Int32": (-2**31, 2**31 - 1),
           "Int64": (-2**63, 2**63 - 1), "Int": (-2**63, 2**63 - 1), "UInt8": (0, 255),
           "UInt16": (0, 65535), "UInt32": (0, 2**32 - 1), "UInt64": (0, 2**64 - 1)}

    def check_fit(self, tn, v, line):
        r = self.FIT.get(tn)
        if r and not r[0] <= v <= r[1]:
            self.err(line, f"literal {v} does not fit `{tn}`")

    def e_ElseLet(self, n, sc):
        self.ev(n.value, sc)
        self.ev(n.else_, sc)
        self.bind_pat(n.pat, sc)
        return None, None

    def e_Incr(self, n, sc):
        self.ev(n.target, sc)
        return None, None

    # control flow with move-state merging
    def branches(self, bodies, sc, with_else):
        base = dict(self.moved)
        results = []
        for b in bodies:
            self.moved = dict(base)
            self.ev(b, sc)
            diverged = b.__class__ is Block and self.diverges(b.stmts or [])
            results.append(None if diverged else dict(self.moved))
        live = [r for r in results if r is not None]
        merged = dict(base)
        if with_else and live:
            common = set(live[0])
            for r in live[1:]:
                common &= set(r)
            for k in common:
                merged[k] = live[0][k]
        self.moved = merged

    def e_IfE(self, n, sc):
        types = []
        for cond, body in n.branches:
            ct = self.t(cond, sc)
            if ct is not None and ct != "Bool":
                self.err(n.line, f"`if` condition must be `Bool`, found `{tshow(ct)}`")
        bodies = [b for _, b in n.branches] + ([n.else_] if n.else_ is not None else [])
        # evaluate for types separately from move-merging
        base = dict(self.moved)
        for b in bodies:
            self.moved = dict(base)
            if b.__class__ is Block:
                types.append(self.e_Block(b, sc))
            else:
                types.append(self.ev(b, sc))
        self.moved = base
        self.branches_moves(bodies, sc, n.else_ is not None)
        ts = [t for t, _ in types]
        if n.else_ is not None and ts and all(t == ts[0] for t in ts) and ts[0] is not None:
            return ts[0], None
        return None, None

    def branches_moves(self, bodies, sc, with_else):
        """Merge move state after a branching construct (bodies were already walked)."""
        # Re-walking would double-report; approximate: keep only moves common to all non-diverging bodies.
        # Moves were recorded during the walk in self.moved of the last branch; recompute quietly.
        saved_diags = len(self.diags)
        base = dict(self.moved)
        results = []
        for b in bodies:
            self.moved = dict(base)
            self.collect_moves(b, sc)
            diverged = b.__class__ is Block and self.diverges(b.stmts or [])
            results.append(None if diverged else dict(self.moved))
        del self.diags[saved_diags:]
        live = [r for r in results if r is not None]
        merged = dict(base)
        if with_else and live:
            common = set(live[0])
            for r in live[1:]:
                common &= set(r)
            for k in common:
                merged[k] = live[0][k]
        self.moved = merged

    def collect_moves(self, b, sc):
        # find top-level `move name` in the body (shallow) and mark them
        stmts = b.stmts if b.__class__ is Block else [b]
        for st in stmts:
            e = st.e if st.__class__ is ExprStmt else st
            for node in self.iter_nodes(e):
                name = None
                if node.__class__ is Move and node.e.__class__ is Name:
                    name = node.e.name
                elif node.__class__ is Arg and getattr(node, "mod", None) == "move" and node.expr.__class__ is Name:
                    name = node.expr.name
                elif node.__class__ is Call:
                    f = node.fn
                    first = node.args[0].expr if node.args and hasattr(node.args[0], "expr") else None
                    if f.__class__ is Name and f.name == "close" and first.__class__ is Name:
                        name = first.name
                    elif f.__class__ is Field and f.obj.__class__ is Name and self.receiver_gone(sc, f):
                        name = f.obj.name
                if name is not None:
                    v = sc.find(name)
                    if v is not None:
                        self.moved[v] = node.line

    def iter_nodes(self, n):
        if isinstance(n, (list, tuple)):
            for x in n:
                yield from self.iter_nodes(x)
        elif hasattr(n, "_fields"):
            if n.__class__ in (Lambda, FnDecl):
                return
            yield n
            for f in n._fields:
                yield from self.iter_nodes(getattr(n, f))

    def loop(self, body_nodes, sc):
        saved = (self.loop_depth, self.exit_ctx)
        self.loop_depth += 1
        self.exit_ctx = False
        for b in body_nodes:
            self.ev(b, sc)
        self.loop_depth, self.exit_ctx = saved

    def e_ForE(self, n, sc):
        self.ev(n.iter, sc)
        inner = Sc(sc)
        self.bind_pat(n.pat, inner)
        self.loop([n.body], inner)
        self.ev(n.else_, sc)
        return None, None

    def e_WhileE(self, n, sc):
        ct = self.t(n.cond, sc)
        if ct is not None and ct != "Bool":
            self.err(n.line, f"`while` condition must be `Bool`, found `{tshow(ct)}`")
        self.loop([n.body], sc)
        self.ev(n.else_, sc)
        return None, None

    def e_ForAll(self, n, sc):
        inner = Sc(sc)
        for nm, ty in n.binds:
            inner.vars[nm] = Var(self.ty_of_type(ty), False, self.loop_depth)
        self.ev(n.body, inner)
        return None, None

    def e_DaemonE(self, n, sc):
        self.loop([n.body], sc)
        return None, None

    def e_ScopeE(self, n, sc):
        inner = Sc(sc)
        if n.name:
            inner.vars[n.name] = Var(None, False, self.loop_depth)
        self.ev(n.body, inner)
        return None, None

    def e_DoE(self, n, sc):
        self.loop([n.body], sc)
        return None, None

    def e_SelectE(self, n, sc):
        for a in n.arms or []:
            inner = Sc(sc)
            self.ev(a.expr, sc)
            if a.bind:
                if isinstance(a.bind, str):
                    inner.vars[a.bind] = Var(None, False, self.loop_depth)
                else:
                    self.bind_pat(a.bind, inner)
            self.ev(a.body, inner)
        return None, None

    def e_ForM(self, n, sc):
        inner = Sc(sc)
        for line in n.lines or []:
            kind, pat, expr, else_ = line
            self.ev(expr, inner)
            if pat is not None:
                self.bind_pat(pat, inner)
            self.ev(else_, inner)
        self.ev(n.yield_, inner)
        return None, None

    def e_CompE(self, n, sc):
        inner = Sc(sc)
        self.ev(n.iter, sc)
        if n.pat is not None:
            self.bind_pat(n.pat, inner)
        self.ev(n.cond, inner)
        self.ev(n.elem, inner)
        self.ev(n.key, inner)
        return None, None

    def e_SeqE(self, n, sc):
        for pr, st in n.arms or []:
            self.ev(pr, Sc(sc, open_=True))
            if st.__class__ is Call:
                self.e_Call(st, sc, extra=1)
            else:
                self.ev(st, sc)
        return None, None

    def e_RunE(self, n, sc):
        self.ev(n.target, sc)
        self.ev(n.limit, sc)
        # a resource handed to `run f(x)` belongs to the new fiber, which closes it when it ends
        names = []
        t = n.target
        if t.__class__ is Call:
            names = [a.expr.name for a in (t.args or []) if getattr(a, "expr", None).__class__ is Name]
        elif t.__class__ is Lambda:
            names = [p.name for p in (t.params or [])]
        for x in names:
            self.mark_gone(n, sc, x, "handed to the new fiber")
        return None, None

    # ------------------------------------------------------------ when
    def e_WhenE(self, n, sc):
        st = None
        if n.scrut is not None:
            st = self.t(n.scrut, sc)
        base = dict(self.moved)
        for a in n.arms:
            inner = Sc(sc)
            self.moved = dict(base)
            for p in a.pats or []:
                self.bind_pat(p, inner)
                self.check_pat_names(p, inner)
            if a.guard is not None:
                self.ev(a.guard, inner)
            self.ev(a.body, inner)
        self.moved = base
        self.branches_moves([a.body for a in n.arms], sc, True)
        if n.scrut is not None:
            self.exhaustive(n, st)
        return None, None

    def check_pat_names(self, p, sc):
        c = p.__class__
        if c is PPin:
            self.ev(p.expr, sc)
        elif c is PRel:
            if p.operand.__class__ not in (IntLit, FloatLit, StrLit, CharLit, DecLit):
                self.ev(p.operand, sc)
        elif c is PTuple:
            for _, q in p.items or []:
                self.check_pat_names(q, sc)
        elif c is PCon:
            for _, q in p.args or []:
                self.check_pat_names(q, sc)
        elif c is PAs:
            self.check_pat_names(p.pat, sc)

    def catch_all(self, p, enum_cases):
        c = p.__class__
        if c is PWild:
            return True
        if c is PBind:
            return p.name not in enum_cases
        if c is PAs:
            return self.catch_all(p.pat, enum_cases)
        if c is PTyped:
            return False
        return False

    def exhaustive(self, n, st):
        arms = n.arms
        # find the enum from patterns
        enum = None
        if st.__class__ is tuple and st[0] == "named" and st[1] in self.enums:
            enum = st[1]
        pats = [(a, p) for a in arms for p in (a.pats or [])]
        names = set(self.cases)
        names |= {"Ok", "Err"}
        if enum is None:
            cand = set()
            for _, p in pats:
                if p.__class__ is PCon:
                    last = p.path[-1]
                    if len(p.path) == 2 and p.path[0] in self.enums:
                        cand.add(p.path[0])
                    elif last in self.cases and len(self.cases[last]) == 1:
                        cand.add(self.cases[last][0])
                    elif last in ("Ok", "Err"):
                        cand.add("Result")
            if len(cand) == 1:
                enum = cand.pop()
        for a, p in pats:
            if a.guard is None and self.catch_all(p, names):
                return
        if enum is None and pats and all(q.__class__ is PBin for _, q in pats):
            self.bin_cover(n, pats)
            return
        if enum is None:
            if st in ("Int", "String", "Char", "Bool") and pats:
                if st == "Bool":
                    lits = {p.expr.b for _, p in pats if p.__class__ is PLit and p.expr.__class__ is BoolLit}
                    if lits >= {True, False}:
                        return
                    miss = "true" if True not in lits else "false"
                    self.err(n.line, f"`when` does not cover `{miss}`")
                elif all(p.__class__ in (PLit, PRange, PRel) for _, p in pats):
                    self.err(n.line, f"`when` on `{tshow(st)}` needs a `_` arm")
            elif st.__class__ is tuple and st[0] == "bounded":
                self.bounded_cover(n, st, pats)
            return
        if enum == "Result":
            required = ["Ok", "Err"]
        else:
            required = [c.name for c in self.enums[enum].cases or []]
        covered = set()
        for a, p in pats:
            q = p
            while q.__class__ is PAs:
                q = q.pat
            if q.__class__ is PCon and q.path[-1] in required and a.guard is None:
                covered.add(q.path[-1])
            elif q.__class__ is PBind and q.name in required and a.guard is None:
                covered.add(q.name)
        miss = [c for c in required if c not in covered]
        if miss:
            self.err(n.line, "`when` does not cover " + ", ".join(f"`{m}`" for m in miss))

    def bin_cover(self, n, pats):
        """A `when` of only Bin arms: the arms without literals or field-sized runs, and without a guard, cover byte lengths."""
        iv = []
        for a, p in pats:
            if a.guard is not None:
                continue
            m, open_, ok = 0, False, True
            for e in p.elems:
                if e[0] == "lit":
                    ok = False
                    break
                _t, nm, kind, arg = e
                if kind == "bits":
                    m += arg
                elif kind == "bytes":
                    if arg is None:
                        open_ = True
                    elif isinstance(arg, int):
                        m += 8 * arg
                    else:
                        ok = False
                        break
                else:
                    m += 8 * (1 if kind in ("u8", "i8") else int(kind[1:-2]) // 8)
            if ok:
                iv.append((m // 8, None if open_ else m // 8))
        pos = 0
        for lo, hi in sorted(iv, key=lambda t: t[0]):
            if lo > pos:
                break
            if hi is None:
                return
            pos = max(pos, hi + 1)
        self.err(n.line, f"`when` on bytes does not cover length {pos}: add a `_` arm")

    def bounded_cover(self, n, st, pats):
        lo, hi = st[1], st[2]
        have = set()
        for a, p in pats:
            if a.guard is not None:
                continue
            if p.__class__ is PLit and p.expr.__class__ is IntLit:
                have.add((p.expr.v, p.expr.v))
            elif p.__class__ is PRel:
                k = self.const_int(p.operand)
                if k is None:
                    return
                have.add({">=": (k, hi), ">": (k + 1, hi), "<=": (lo, k), "<": (lo, k - 1)}[p.op])
            elif p.__class__ is PRange:
                a_, b_ = self.const_int(p.lo) if p.lo else lo, self.const_int(p.hi) if p.hi else hi
                if a_ is None or b_ is None:
                    return
                have.add((a_, b_ if p.incl else b_ - 1))
            else:
                return
        pos = lo
        for a_, b_ in sorted(have):
            if a_ > pos:
                break
            pos = max(pos, b_ + 1)
        if pos <= hi:
            self.err(n.line, f"`when` does not cover `{pos}..={hi}` of `{tshow(st)}`")

    # ------------------------------------------------------------ calls
    # ---------------------------------------------------------------- curry and uncurry (Spec 11)
    def fn_params(self, e, sc):
        """The declared parameters of a function value that is a lambda or a plain named function, else None."""
        if e.__class__ is Lambda:
            return list(e.params or [])
        if e.__class__ is Name and sc.find(e.name) is None and e.name in self.fns and len(self.fns[e.name]) == 1:
            fd = self.fns[e.name][0]
            if fd.tparams or fd.alias is not None:
                return None
            return list(fd.params or [])
        return None

    def curry_name(self, fn, sc):
        if fn.__class__ is Name and fn.name == "curry" \
                and sc.find(fn.name) is None and fn.name not in self.fns:
            return fn.name
        return None

    def uncurry_count(self, fn, sc):
        """For `uncurry[n]`, the constant n (or False when it is not a constant of 2 or more); None when fn is not uncurry."""
        if fn.__class__ is GenApp and fn.base.__class__ is Name and fn.base.name == "uncurry" \
                and sc.find("uncurry") is None and "uncurry" not in self.fns:
            g = fn.groups[0][0] if fn.groups and fn.groups[0] else None
            v = const_eval(g.expr, {}) if g.__class__ is TExpr else NOCONST
            return v if isinstance(v, int) and not isinstance(v, bool) and v >= 2 else False
        return None

    def curry_shape(self, e, sc):
        """("curried", k): k one-argument calls remain.  ("uncurried", n): takes n arguments at once.  Else None."""
        if e.__class__ is not Call:
            return None
        cn = self.curry_name(e.fn, sc)
        if cn is not None and len(e.args or []) == 1:
            ps = self.fn_params(e.args[0].expr, sc)
            if ps is None:
                return None
            return ("curried", len(ps)) if len(ps) >= 2 else None
        un = self.uncurry_count(e.fn, sc)
        if un:
            return ("uncurried", un)
        inner = self.curry_shape(e.fn, sc)
        if inner and inner[0] == "curried" and len(e.args or []) == 1 and inner[1] > 1:
            return ("curried", inner[1] - 1) if inner[1] - 1 > 0 else None
        return None

    def check_curry_call(self, n, sc):
        """Typing rules for `curry(f)`, `curryN(f)`, and `uncurry[n](g)` themselves."""
        fn, args = n.fn, n.args or []
        cn = self.curry_name(fn, sc)
        if cn is not None:
            if len(args) != 1:
                self.err(n.line, f"`{cn}` takes one function")
                return
            ps = self.fn_params(args[0].expr, sc)
            if ps is None:
                return
            bad = [p.name for p in ps if p.mod in ("ref", "lazy", "using") or p.variadic]
            if bad:
                self.err(n.line, f"`{cn}` cannot take a function with a ref, lazy, using, or variadic parameter (`{bad[0]}`)")
            want = int(cn[5:]) if len(cn) > 5 else None
            if len(ps) < 2:
                self.err(n.line, f"`{cn}` needs a function of two or more parameters, but this one has {len(ps)}")
            elif want is not None and len(ps) != want:
                self.err(n.line, f"`{cn}` is for functions of {want} parameters, but this one has {len(ps)}")
            return
        un = self.uncurry_count(fn, sc)
        if un is False:
            self.err(n.line, "`uncurry[n]` needs a constant n of 2 or more, as in `uncurry[2](g)`")
            return
        if un:
            if len(args) != 1:
                self.err(n.line, "`uncurry[n]` takes one function")
                return
            ps = self.fn_params(args[0].expr, sc)
            if ps is not None and len(ps) != 1:
                self.err(n.line, f"`uncurry[{un}]` takes a function of one parameter that returns a function, but this one has {len(ps)} parameters")

    def check_curried_application(self, n, sc):
        shape = self.curry_shape(n.fn, sc)
        args = n.args or []
        if shape is None or any(getattr(a, "mod", None) for a in args) or any(self.has_ph(a.expr) for a in args):
            return
        if shape[0] == "curried" and len(args) != 1:
            self.err(n.line, f"a curried function takes one argument at a time ({shape[1]} to go), but this call gives {len(args)}; "
                             "write f(a)(b), or use the function itself for f(a, b)")
        elif shape[0] == "uncurried" and len(args) != shape[1] and not any(a.expr.__class__ is TupleE for a in args):
            self.err(n.line, f"`uncurry[{shape[1]}]` makes a function of {shape[1]} arguments, but this call gives {len(args)}")

    def e_Call(self, n, sc, *a, **k):
        mark = len(self.pending_gone)
        r = self._e_Call(n, sc, *a, **k)
        for item in self.pending_gone[mark:]:
            self.mark_gone(*item)          # the receiver is gone once the call has been checked
        del self.pending_gone[mark:]
        return r

    def _e_Call(self, n, sc, extra=0):
        r = self._e_Call0(n, sc, extra)
        f = n.fn
        if f.__class__ is Name and f.name == "Error" and (r is None or r[0] is None) \
                and not any(f.name in d for d in (self.fns, self.tuples, self.aliases, self.enums)) and sc.find("Error") is None:
            return ("named", "Error"), None            # `Error(code, message)` is an Error
        return r

    def _e_Call0(self, n, sc, extra=0):
        fn = n.fn
        if fn.__class__ is Field:
            self.callee_fields.add(id(fn))
        args = n.args or []
        if fn.__class__ is Name and fn.name == "Err" and len(args) == 1 and hasattr(args[0], "expr") \
                and args[0].expr.__class__ is Call and args[0].expr.fn.__class__ is Name and args[0].expr.fn.name == "fail" \
                and all(x not in self.fns and x not in self.tuples and sc.find(x) is None for x in ("Err", "fail")):
            self.err(n.line, "`Err(fail(...))` wraps an `Err` in an `Err`: `fail(...)` already returns the whole `Err`, so write `fail(code, msg)` alone (or `Err(Error(code, msg))`)")
        args = n.args or []
        if fn.__class__ is Call or fn.__class__ is Name:
            if fn.__class__ is Call:
                self.check_curried_application(n, sc)
            else:
                self.check_curry_call(n, sc)
        elif fn.__class__ is GenApp:
            self.check_curry_call(n, sc)
        # evaluate arguments
        ats = []
        indexing = fn.__class__ is not Name or sc.find(fn.name) is not None
        asc = Sc(sc, open_=True) if indexing else sc
        plan = self.arg_plan(fn, args, sc, extra)       # (parameter types, type parameters) when the callee's signature is known
        binds = {}
        sigres = None
        ufcs = False
        if fn.__class__ is Field and n.trailing is None and not extra and fn.name in self.load_sigs() \
                and not any(getattr(a, "label", None) for a in args):
            rt = self.ev(fn.obj, sc)[0]                 # `xs.map(f)` is `xs |> map(f)`; the receiver is evaluated here, once
            ufcs = True
            if rt is not None:
                self.pipe_ty = rt
                extra = 1
            else:
                ufcs = "skip"
        sargs, opt_ats = self.split_options(n, fn, args, sc, extra, asc)
        ov = self.sig_overloads(fn, sargs, sc, extra, ufcs=ufcs is True) if n.trailing is None and plan is None and ufcs != "skip" else None
        if ov is not None and not ov[0] and n.trailing is None and all(hasattr(a, "expr") for a in sargs):
            sg_all = self.load_sigs().get(fn.name) or []
            top = max((len(sg[1]) for sg in sg_all), default=0)
            if len(sargs) + extra > top > 0:                # more arguments than any form of the function takes
                self.err(n.line, f"`{fn.name}` takes at most {top} argument{'s' if top != 1 else ''}, but {len(sargs) + extra} given")
        if ov is not None and ov[0] and all(hasattr(a, "expr") for a in sargs):
            ats, sigres = self.sig_args(n, ov[0], ov[1], sargs, asc, sc, extra)
            if sargs is not args:
                ats = ats + opt_ats
            args_iter = ()
        else:
            self.pipe_ty = None
            args_iter = enumerate(args)
        for i, a in args_iter:
            if hasattr(a, "expr") and getattr(a, "mod", None) == "move" and a.expr.__class__ is Name:
                ats.append(self._move_name(a, a.expr, asc))         # `f(move c)` hands c over
                continue
            pt = plan[0][i] if plan and i < len(plan[0]) else None
            if pt is not None and hasattr(a, "expr") and a.expr.__class__ is Lambda:
                self.lam_expect = tys.subst(pt, binds) if pt[0] == "fn" else None
            r = self.ev(a.expr, asc) if hasattr(a, "expr") else (None, None)
            self.lam_expect = None
            ats.append(r)
            if pt is not None and r[0] is not None:
                tys.unify(pt, self.base(r[0]), binds)           # what this argument tells the later ones (a lambda's parameters)
        if n.trailing is not None:
            if plan and n.trailing.__class__ is Lambda and len(args) < len(plan[0]) and plan[0][len(args)] is not None \
                    and plan[0][len(args)][0] == "fn":
                self.lam_expect = tys.subst(plan[0][len(args)], binds)
            self.ev(n.trailing, sc)
            self.lam_expect = None
        if fn.__class__ is Name and sc.find(fn.name) is None and fn.name not in self.fns and fn.name not in self.tuples \
                and (fn.name in ("Ok", "Err", "List", "Set", "Array", "Dict")):
            for a in args:                                # a mixed literal inside `Ok(...)` or a collection: whatever holds it decides
                x = getattr(a, "expr", None)
                if x is not None and id(x) in self.mixed_lits:
                    m = self.mixed_lits.pop(id(x))
                    self.mixed_lits.setdefault(id(n), m)
        decl = None                                       # the tuple or enum case a constructor call builds
        if fn.__class__ is Name and sc.find(fn.name) is None and fn.name not in self.fns:
            if fn.name in self.tuples:
                decl = (self.tuples[fn.name], self.tuples[fn.name].fields)
            elif fn.name in self.cases and len(self.cases[fn.name]) == 1:
                ed = self.enums[self.cases[fn.name][0]]
                decl = (ed, next((c.fields for c in ed.cases if c.name == fn.name), None))
        elif fn.__class__ is Field and fn.obj.__class__ is Name and fn.obj.name in self.enums and sc.find(fn.obj.name) is None:
            ed = self.enums[fn.obj.name]
            decl = (ed, next((c.fields for c in ed.cases if c.name == fn.name), None))
        if decl is not None and any(id(getattr(a, "expr", None)) in self.mixed_lits for a in args):
            d, fields = decl
            flds = [f for f in fields or [] if getattr(f, "name", None) not in (None, "...")]
            for i, a in enumerate(args):
                x = getattr(a, "expr", None)
                if x is None or id(x) not in self.mixed_lits:
                    continue
                if getattr(d, "tparams", None):               # generic: the type arguments decide, so the holder of the whole value does
                    self.mixed_lits.setdefault(id(n), self.mixed_lits.pop(id(x)))
                    continue
                f = next((f for f in flds if f.name == getattr(a, "label", None)), None) if getattr(a, "label", None) \
                    else (flds[i] if i < len(flds) else None)
                self.settle_mixed(x, self.ty_of_type(f.type) if f is not None and getattr(f, "type", None) is not None else ("param", "?"))
        for i, a in enumerate(args):                      # a mixed literal given to a call: the parameter's type says if it may mix
            x = getattr(a, "expr", None)
            if x is not None and id(x) in self.mixed_lits:
                if plan is not None and i < len(plan[0]):
                    self.settle_mixed(x, plan[0][i])
                elif ov is not None and ov[0]:
                    self.settle_mixed(x, None)            # a library function takes no union
        if fn.__class__ is Field and id(fn.obj) in self.mixed_lits:
            self.settle_mixed(fn.obj, None)               # `List(1, "a").map(...)`
        if fn.__class__ is Name and sc.find(fn.name) is None:
            self.check_hand_over(n, sc, fn.name, args)
            if fn.name in self.tuples:
                self.check_stored(n, sc, fn.name, args)
            if fn.name == "close" and args and args[0].__class__ is not None and hasattr(args[0], "expr") and args[0].expr.__class__ is Name:
                self.mark_gone(n, sc, args[0].expr.name, "closed")
        if fn.__class__ is Field:
            self.check_receiver(n, sc, fn)
            if fn.obj.__class__ is Name and self.any_vars:
                r = self.any_member_call(n, sc, fn, ats)
                if r is not NOANY:
                    return r, None
        if fn.__class__ is Name and sc.find(fn.name) is None and len(self.fns.get(fn.name, ())) == 1:
            self.check_any_args(n, fn, args, ats)
        if fn.__class__ is Name and self.any_vars and sc.find(fn.name) is None and len(self.fns.get(fn.name, ())) == 1:
            r = self.any_fn_result(n, sc, fn, args)
            if r is not None:
                return r, None
        if fn.__class__ is Name and fn.name in self.handle_types.values():
            for a in args:        # the function that closes a handle consumes it
                x = a.expr if hasattr(a, "expr") else None
                if x.__class__ is Name:
                    hv = sc.find(x.name)
                    if hv is not None:
                        self.moved[hv] = n.line
        if fn.__class__ is Name:
            v = sc.find(fn.name)
            if v is None:
                if fn.name not in self.globals and fn.name not in self.prelude and not sc.open:
                    self.err(n.line, f"undefined function `{fn.name}`")
                    return None, None
                if sigres is not None:
                    return sigres, None
                return self.call_known(n, fn.name, args, ats, extra)
            elif v in self.moved:
                self.err(n.line, f"use of moved value `{fn.name}`")
            return None, None
        if fn.__class__ is Field and ufcs:
            return sigres, None                         # the receiver was evaluated above
        if fn.__class__ is GenApp and fn.base.__class__ is Name and fn.base.name == "Atom" and len(args) == 1 and n.trailing is None \
                and "Atom" not in self.fns and "Atom" not in self.tuples and "Atom" not in self.aliases \
                and len(fn.groups or []) == 1 and len(fn.groups[0]) == 1 and not extra_bad(args):
            self.ev(fn, sc)                             # `Atom[Int](0)` is an Atom[Int], and 0 must be an Int
            el = self.ty_of_type(fn.groups[0][0], 0, None, False)
            self.compat(el, ats[0][0], ats[0][1], n.line)
            return ("app", "Atom", (el,)), None
        ends = {"Chan": ("ChanR", "ChanW"), "Future": ("FutureR", "FutureW")}
        if fn.__class__ is GenApp and fn.base.__class__ is Name and fn.base.name in ends and not args and n.trailing is None \
                and not any(x in self.fns or x in self.tuples or x in self.aliases or x in self.enums for x in (fn.base.name,) + ends[fn.base.name]) \
                and 1 <= len(fn.groups or []) <= 2 and len(fn.groups[0]) == 1:
            self.ev(fn, sc)                             # `Chan[Int][4]()` is (ChanR[Int], ChanW[Int]); `Future[Int]()` is (FutureR[Int], FutureW[Int])
            el = self.ty_of_type(fn.groups[0][0], 0, None, False)
            rd, wr = ends[fn.base.name]
            return ("tup", (("app", rd, (el,)), ("app", wr, (el,)))), None
        self.ev(fn, sc)
        return None, None

    def collection_ctor(self, name, args, ats, n=None):
        """`List(1, 2)` is `List[Int]`: the elements share one type; an unknown element leaves it unknown.  Two settled
        elements of different plain types (`Int` and `String`, or `Result[Int, String]` and `Result[Int, Int]`) are an error."""
        if extra_bad(args):
            return None
        el = None
        for (t, _c) in ats:
            t = self.base(t)
            if t is None:
                return ("app", name, (None,))
            prev = el
            el = tys.join(el, t)
            if el == "conflict":
                plain = lambda x: not self.has_unsettled(x) and (x.__class__ is str or x[0] == "app")
                if n is not None and plain(prev) and plain(t):
                    self.mixed_lits[id(n)] = (n.line, f"the elements of `{name}(...)` must share one type, but found `{tshow(prev)}` and `{tshow(t)}`")
                return ("app", name, (None,))
        if name == "Array":
            return ("app", name, (el,), len(ats))
        return ("app", name, (el,))

    def dict_ctor(self, args, ats, n=None):
        """`Dict(1: 2)` is `Dict[Int, Int]`: a number key is an Int, and a string or a bare name is a String key; `Dict((k, v), ...)`
        takes both from the pairs.  Anything not known leaves that part unknown."""
        if any(getattr(a, "mod", None) for a in args):
            return None
        kt = vt = None
        for a, (t, _c) in zip(args, ats):
            t = self.base(t)
            if getattr(a, "label", None) is not None:
                lb = a.label
                k = "Int" if isinstance(lb, int) and not isinstance(lb, bool) else "String" if isinstance(lb, (str, tuple)) else None
                v = t
            elif t is not None and t.__class__ is tuple and t[0] == "tup" and len(t[1]) == 2:
                k, v = t[1]
            else:
                return ("app", "Dict", (None, None))
            if k is None or v is None:
                return ("app", "Dict", (None, None))
            pk, pv = kt, vt
            kt, vt = tys.join(kt, k), tys.join(vt, v)
            if "conflict" in (kt, vt):
                plain = lambda x: x is not None and not self.has_unsettled(x) and (x.__class__ is str or x[0] == "app")
                for what, pr, cur, new in (("keys", pk, kt, k), ("values", pv, vt, v)):
                    if cur == "conflict" and n is not None and plain(pr) and plain(new):
                        self.mixed_lits[id(n)] = (n.line, f"the {what} of `Dict(...)` must share one type, but found `{tshow(pr)}` and `{tshow(new)}`")
                return ("app", "Dict", (None, None))
        return ("app", "Dict", (kt, vt))

    def load_sigs(self):
        """name -> [(type-parameter names, parameter types, result type)] from sigs.SRC, read once for all checkers."""
        from .values import GC
        if Checker._sigs.get(GC[0]) is None:
            from .parser import parse_program
            from . import sigs as S
            from .prelude import REG
            tmp, out = Checker(()), {}
            tmp.sig_mode = True
            tmp.collect_prelude_types()
            for st in parse_program(S.SRC + (S.SRC_GC if GC[0] else S.SRC_MOXIE), "<sigs>").stmts:
                for fd in (st.clauses if st.__class__ is FnGroup else [st]):
                    keep = {tp.name for tp in fd.tparams or []}
                    out.setdefault(fd.name, []).append(
                        (keep, [tmp.ty_of_type(p.type, 0, keep) for p in fd.params], tmp.ty_of_type(fd.ret, 0, keep),
                         REG[fd.name][1] if fd.name in REG else "first"))
            Checker._sigs[GC[0]] = out
        return Checker._sigs[GC[0]]

    sig_mode = False                # True only in the checker that reads sigs.py, where `Seq` is a real type
    _sigs = {}                      # by dialect: GC[0] False (moxie) or True (moxie/gc)

    # Named options of builtins: name -> {option: type}.  A call with only these labels is checked against the signature.
    RES_NAMED = {"Io", "Listener", "Udp", "Child", "Terminal", "Duration", "Error"}        # built-in types that are exactly themselves
    OPTIONS = {"retry": {"when": None}, "par_map": {"limit": "Int"}, "par_traverse": {"limit": "Int"}, "connect": {"timeout": None}, "accept": {"timeout": None}, "wait_child": {"timeout": None},
               "run_command": {"stdin": "String", "timeout": None, "env": ("app", "Dict", ("String", "String")), "cwd": "String"},
               "spawn": {"env": ("app", "Dict", ("String", "String")), "cwd": "String"}}

    def split_options(self, n, fn, args, sc, extra, asc):
        """For `run_command("ls", stdin: "x")`: the positional arguments, and the evaluated option values after checking each
        label is one the function takes and its value fits.  Calls with any other labels are returned unchanged."""
        opts = self.OPTIONS.get(fn.name) if fn.__class__ is Name else None
        labeled = [a for a in args if getattr(a, "label", None)]
        if fn.__class__ is Name and fn.name in ("par_map", "par_traverse") and not extra and sc.find(fn.name) is None \
                and fn.name not in self.fns and fn.name not in self.tuples and all(hasattr(a, "expr") for a in args):
            lim = next((a for a in labeled if a.label == "limit"), None)
            v = self.const_int(lim.expr) if lim is not None else None
            if v is None and lim is not None and lim.expr.__class__ is Name:
                c = self.consts.get(lim.expr.name)
                v = c if isinstance(c, int) and not isinstance(c, bool) else None
            if lim is None or v is None or v < 1:
                self.err(n.line, f"`{fn.name}` needs `limit:` with a constant number of 1 or more (the fibers are counted before the program runs)")
        if fn.__class__ is Name and fn.name == "map_all" and not extra and sc.find(fn.name) is None \
                and fn.name not in self.fns and fn.name not in self.tuples and args and all(hasattr(a, "expr") for a in args) \
                and args[0].expr.__class__ is Lambda:
            want, have = len(args) - 1, len(args[0].expr.params or [])
            if want >= 2 and have != want:
                self.err(n.line, f"`map_all` combines {want} results, so its function takes {want} parameters, but this one takes {have}")
        if opts is None or not labeled or extra or sc.find(fn.name) is not None or fn.name in self.fns or fn.name in self.tuples \
                or any(k[1] == fn.name for k in self.methods) or any(getattr(a, "mod", None) for a in args) \
                or not all(hasattr(a, "expr") for a in args):
            return args, []
        ats = []
        for a in labeled:
            if a.label not in opts:
                self.err(n.line, f"`{fn.name}` has no option `{a.label}`; it takes " + ", ".join(f"`{k}`" for k in opts))
                return args, []
            r = self.ev(a.expr, asc)
            ats.append(r)
            want, got = opts[a.label], self.base(r[0])
            if want is not None and got is not None and not self.has_unsettled(got) and not tys.compatible(want, got):
                self.err(n.line, f"option `{a.label}` of `{fn.name}` expects `{tshow(want)}`, found `{tshow(got)}`")
        return [a for a in args if not getattr(a, "label", None)], ats

    def sig_overloads(self, fn, args, sc, extra, ufcs=False):
        """The prelude signatures for a call of a builtin by its plain name (or as a method of a receiver of known type), or None."""
        if not ufcs and (fn.__class__ is not Name or sc.find(fn.name) is not None):
            return None
        if extra > 1:
            return None
        name = fn.name
        if name in self.fns or name in self.tuples or name in self.aliases or name in self.cases \
                or any(k[1] == name for k in self.methods) or extra_bad(args):
            return None
        sigs = self.load_sigs().get(name)
        if sigs is None:
            return None
        pos = sigs[0][3]
        return [sg for sg in sigs if len(sg[1]) == len(args) + extra], pos

    def has_unsettled(self, t):
        """True when a type holds an unknown part or a type parameter, so a failed match proves nothing."""
        if t is None:
            return True
        if t.__class__ is not tuple:
            return False
        if t[0] == "named" and t[1] in self.RES_NAMED and t[1] not in self.tuples and t[1] not in self.enums:
            return False                      # a resource type is exactly itself
        if t[0] in ("param", "rigid", "appv", "ctor", "named"):
            return True
        if t[0] == "app":
            return any(self.has_unsettled(a) for a in t[2])
        if t[0] == "fn":
            return any(self.has_unsettled(a) for a in t[1]) or self.has_unsettled(t[2])
        if t[0] == "tup":
            return any(self.has_unsettled(a) for a in t[1])
        return False

    def sig_fit(self, sg, full, strict=False):
        """The type-parameter bindings if the argument types `full` (None for unknown) fit the signature `sg`, else None."""
        if len(full) > len(sg[1]):
            return None                          # more arguments than the function has parameters
        binds = {}
        for pt, t in zip(sg[1], full):
            if not tys.match(pt, self.base(t) if t is not None else None, binds, strict):
                return None
        return binds

    def sig_pick(self, over, full):
        """The one overload that fits; when several fit by number conversion, the one that fits exactly (`abs(3)` is the Int one)."""
        cands = [sg for sg in over if self.sig_fit(sg, full) is not None]
        if len(cands) > 1 and all(t is not None for t in full):
            exact = [sg for sg in cands if self.sig_fit(sg, full, True) is not None]
            if len(exact) == 1:
                return exact
        return cands

    def sig_hint(self, n):
        """Extra advice for a mistake people make often."""
        if getattr(n.fn, "name", None) in ("print", "println", "eprint", "eprintln") and len(n.args or []) == 2:
            return "; with two arguments the first is the stream to write to (`stdout`, a file, a socket), and to print several values build one string, as in `println(\"$a $b\")`"
        return ""

    def sig_args(self, n, over, pos, args, asc, sc, extra):
        """Evaluate the arguments of a call of an overloaded builtin: the ones that are not lambdas first, so the lambdas
        can be given parameter types; returns the types in argument order and the call's result type (or None)."""
        piped, self.pipe_ty = self.pipe_ty, None
        ats = [None] * len(args)
        for i, a in enumerate(args):
            if a.expr.__class__ is not Lambda:
                ats[i] = self.ev(a.expr, asc) if getattr(a, "mod", None) != "move" or a.expr.__class__ is not Name \
                    else self._move_name(a, a.expr, asc)

        def full(lams):
            ts = [(r[0] if r else None) for r in ats]
            if extra:
                ts = ts + [piped] if pos == "last" else [piped] + ts
            return ts
        cands = self.sig_pick(over, full(None))
        lam_at = [i for i, a in enumerate(args) if a.expr.__class__ is Lambda]
        for i in lam_at:
            expect = None
            if len(cands) == 1:
                sg = cands[0]
                slot = i + (1 if extra and pos == "first" else 0)
                pt = sg[1][slot]
                if pt is not None and pt[0] == "fn":
                    binds = self.sig_fit(sg, full(None)) or {}
                    expect = tys.subst(pt, binds)
            if expect is None and len(cands) > 1:
                slot = i + (1 if extra and pos == "first" else 0)
                fts = [sg[1][slot] for sg in cands if slot < len(sg[1])]
                binds0 = self.sig_fit(cands[0], full(None)) or {}
                fts = [tys.subst(f, binds0) if f is not None else f for f in fts]
                if fts and all(f is not None and f[0] == "fn" and self.arity_known(f) for f in fts) and len({len(f[1]) for f in fts}) == 1 \
                        and args[i].expr.params and self.arity_clash(fts[0], len(args[i].expr.params)):
                    self.err(n.line, f"this function takes {len(args[i].expr.params)} parameter{'s' if len(args[i].expr.params) != 1 else ''}, "
                             f"but it is used where one with {len(fts[0][1])} is expected")
            self.lam_expect = expect
            ats[i] = self.ev(args[i].expr, asc)
            self.lam_expect = None
        cands = self.sig_pick(over, full(None))
        if len(cands) > 1 and all(not tys.params_in(sg[2]) for sg in cands) and len({sg[2] for sg in cands}) == 1:
            return ats, cands[0][2]               # every overload that fits gives the same type (`contains` is a Bool)
        if not cands and over:
            ft = full(None)
            if getattr(n.fn, "name", None) == "len" and any(t is not None and (t[0] == "tup" or t[0] == "named" and t[1] in self.tuples)
                                                           for t in ft if t.__class__ is tuple):
                return ats, "Int"                 # `len` of a tuple counts its fields
            known = [t if t is not None and t[0] != "fn" and not self.has_unsettled(t) else None for t in ft]
            alone0 = lambda sg: all(tys.match(pt, self.base(t), {}) for pt, t in zip(sg[1], known) if t is not None)
            if any(t is not None for t in known) and not any(self.sig_fit(sg, known) is not None for sg in over) \
                    and not any(alone0(sg) for sg in over):
                shown = [("a function" if (t is not None and t[0] == "fn") else tshow(t)) for t in ft]
                self.err(n.line, f"`{getattr(n.fn, 'name', '?')}` can't take ({', '.join(shown)}); it takes "
                         + " or ".join("(" + ", ".join(tshow(p) for p in sg[1]) + ")" for sg in over[:3]) + self.sig_hint(n))
                return ats, None
            alone = lambda sg: all(tys.match(pt, self.base(t), {}) for pt, t in zip(sg[1], known) if t is not None)
            if any(t is not None for t in known) and not any(self.sig_fit(sg, known) is not None for sg in over) \
                    and any(alone(sg) for sg in over):         # each argument fits its own parameter; only the shared type parameter clashes
                ft = [t for t in known if t is not None]          # the settled arguments alone already clash (a repeated type parameter)
                self.err(n.line, f"`{getattr(n.fn, 'name', '?')}` can't take these arguments: they do not agree on one type for a repeated type parameter "
                         f"({', '.join(tshow(t) for t in ft)}); it takes " + " or ".join("(" + ", ".join(tshow(p) for p in sg[1]) + ")" for sg in over[:1]))
                return ats, None
            if all(t is not None and not self.has_unsettled(t) for t in ft) or (len(over) == 1 and any(
                    t is not None and not self.has_unsettled(t) and pt is not None and t[0] != "fn" and (pt.__class__ is not tuple or pt[0] != "fn")
                    and not tys.match(pt, self.base(t), {}) for pt, t in zip(over[0][1], ft))):
                self.err(n.line, f"`{getattr(n.fn, 'name', '?')}` can't take ({', '.join(tshow(t) for t in ft)}); it takes "
                         + " or ".join("(" + ", ".join(tshow(p) for p in sg[1]) + ")" for sg in over[:3]) + self.sig_hint(n))
            return ats, None
        if len(cands) != 1:
            return ats, None
        sg = cands[0]
        binds = {}
        for pt, t in zip(sg[1], full(None)):
            if t is not None:
                tys.unify(pt, self.base(t), binds)
        ret = tys.subst(sg[2], binds)
        return ats, ret

    def arg_plan(self, fn, args, sc, extra):
        """The parameter types of a call to one known declared function, as (types, type-parameter names), or None."""
        if extra or fn.__class__ is not Name or sc.find(fn.name) is not None:
            return None
        fds = self.fns.get(fn.name)
        if not fds or len(fds) != 1:
            return None
        fd = fds[0]
        if fd.alias is not None or id(fd) in self.foreign_ids or any(p.variadic or p.mod for p in fd.params or []):
            return None
        if any(getattr(a, "label", None) or getattr(a, "mod", None) for a in args):
            return None
        keep = {tp.name for tp in fd.tparams or []}
        return [self.ty_of_type(p.type, 0, keep) for p in fd.params or []], keep

    # Builtins whose result type does not depend on what they are given.  A builtin that works on several kinds of value
    # (`upper` on a String or a Char, `floor` giving an Int or a Double) is left out: the checker has no overloads yet.
    BUILTIN_RET = {"len": "Int", "trim": "String", "starts_with": "Bool", "ends_with": "Bool", "is_ok": "Bool", "is_err": "Bool",
                   "is_nan": "Bool", "is_inf": "Bool", "is_finite": "Bool", "show": "String", "sqrt": "Float",
                   "is_cancelled": "Bool", "hash": "Int", "hostname": "String", "cwd": "String", "os_name": "String",
                   "temp_dir": "String", "path_join": "String", "char_count": "Int", "grapheme_count": "Int"}

    def call_known(self, n, name, args, ats, extra):
        if name in self.BUILTIN_RET and name not in self.fns and name not in self.tuples and name not in self.aliases \
                and name not in self.cases and not extra_bad(args) and not any(k[1] == name for k in self.methods):
            return self.BUILTIN_RET[name], None
        if name in ("Ok", "Err") and not extra and len(args) == 1 and name not in self.fns and name not in self.tuples \
                and name not in self.cases and not extra_bad(args):
            t = self.base(ats[0][0])
            return ("app", "Result", (t, None) if name == "Ok" else (None, t)), None
        if name in ("List", "Array", "Set") and not extra and name not in self.fns and name not in self.tuples \
                and name not in self.aliases and args and n.trailing is None:
            return self.collection_ctor(name, args, ats, n), None
        if name == "Dict" and not extra and name not in self.fns and name not in self.tuples and name not in self.aliases \
                and args and n.trailing is None:
            return self.dict_ctor(args, ats, n), None
        if name == "secret" and name not in self.fns:
            return ("secret",), None
        if name in self.tuples:
            td = self.tuples[name]
            if not td.tparams:
                self.check_tuple_args(td, args, ats, n.line)
            elif not any(tp.holes for tp in td.tparams):
                return self.generic_tuple(td, n, args, ats), None
            return ("named", name), None
        if name in self.fns and len(self.fns[name]) == 1:
            fd = self.fns[name][0]
            if fd.tparams or fd.alias is not None:
                if fd.tparams:
                    self.check_bounds(fd, n, args, ats)
                    return self.generic_call(fd, n, args, ats, extra), None
                return None, None
            r = self.check_call(fd, n, args, ats, extra)
            if fd.contracts and not extra and n.trailing is None:
                self.check_const_requires(fd, n, args)
            return r
        return None, None

    def check_const_requires(self, fd, n, args):
        """A `requires` whose arguments are all constants and that fails is a compile error (Spec 9b)."""
        params = list(fd.params or [])
        if any(getattr(a, "mod", None) for a in args) or len(args) > len(params) or any(p.variadic for p in params):
            return
        env = {}
        for i, a in enumerate(args):
            nm = a.label if getattr(a, "label", None) else params[i].name
            v = const_eval(a.expr, {})
            if v is NOCONST:
                continue
            env[nm] = v
        for p in params:
            if p.name not in env and p.default is not None:
                v = const_eval(p.default, {})
                if v is not NOCONST:
                    env[p.name] = v
        for kw, expr, ln, text in fd.contracts:
            if kw != "requires":
                continue
            if const_eval(expr, env) is False:
                used = ", ".join(f"{k} = {show_const(env[k])}" for k in sorted(names_of(expr)) if k in env)
                self.err(n.line, f"this call to `{fd.name}` always fails its precondition `{text}` ({used})")

    def check_derivs(self, st):
        d = st.derivs or []
        if "hash" in d and "eq" not in d:
            self.err(st.line, f"`deriving hash` on `{st.name}` needs `eq` in the same header, so equal values have equal hashes")

    def implements(self, ty, iface):
        """True, False, or None when the checker cannot tell."""
        if iface not in VALUE_IFACES and iface not in self.ifaces:
            return None
        if ty.__class__ is tuple and len(ty) == 2 and ty[0] == "named":
            name = ty[1]
            decl = self.tuples.get(name) or self.enums.get(name)
            if decl is None:
                return None
            if iface in self.impls.get(name, ()):
                return True
            derived = {DERIV_IFACE[d] for d in (decl.derivs or []) if d in DERIV_IFACE}
            if iface in derived:
                return True
            if iface in VALUE_IFACES and not self.fn_tparams:
                return False
            return False if iface in self.ifaces else None
        if isinstance(ty, str) and ty in SCALAR_NAMES:
            if iface in self.impls.get(ty, ()):
                return True
            if iface in BUILTIN_IMPLS:
                return ty in BUILTIN_IMPLS[iface]
            return False
        return None

    def check_bounds(self, fd, n, args, ats):
        """A call to a generic function: each argument bound to a bounded type parameter must implement the bound."""
        if any(getattr(a, "label", None) or getattr(a, "mod", None) == "spread" for a in args):
            return
        params = list(fd.params or [])
        for tp in fd.tparams or []:
            if not getattr(tp, "bounds", None):
                continue
            for p, a, (t, _c) in zip(params, args, ats):
                pt = p.type
                if pt is None:
                    continue
                found = []
                self.tparam_types(pt, self.base(t), tp.name, found)     # `T` itself, or the T inside `List[T]`, `Seq[T]`, `Dict[K, T]`
                for t in found:
                    for b in tp.bounds:
                        iface = _tn(b)
                        if self.implements(t, iface) is False:
                            tyname = t if isinstance(t, str) else (t[1] if isinstance(t[1], str) else tshow(t))
                            self.err(n.line, f"`{tyname}` doesn't implement `{iface}`, which `{fd.name}` requires of `{tp.name}`")

    def tparam_types(self, pt, t, name, out):
        """The argument types that stand for the type parameter `name`, found by walking the declared parameter type `pt`
        alongside the type `t` of the argument; filled into `out`."""
        if pt is None or t is None or pt.__class__ is not TName:
            return
        if len(pt.path) == 1 and pt.path[0] == name and not pt.groups:
            out.append(t)
            return
        if pt.groups and pt.groups[0] and t.__class__ is tuple and t[0] == "app" and len(pt.groups[0]) == len(t[2]) \
                and (pt.path[-1] == t[1] or (pt.path[-1] == "Seq" and t[1] in tys.SEQ_HEADS)):
            for sub, st in zip(pt.groups[0], t[2]):
                self.tparam_types(sub, self.base(st) if st is not None else None, name, out)

    # ------------------------------------------------------------ generics (Spec section 8: bounds)
    def bare_tparam(self, fd, t):
        """The TParam of `fd` that the type `t` names on its own (`T`, no arguments), else None."""
        if t.__class__ is TName and len(t.path) == 1 and not t.groups:
            for tp in fd.tparams or []:
                if tp.name == t.path[0]:
                    return tp
        return None

    OP_NEEDS = {"==": ({"Equatable", "Hashable"}, "Equatable"), "!=": ({"Equatable", "Hashable"}, "Equatable"),
                "<": ({"Ordered"}, "Ordered"), ">": ({"Ordered"}, "Ordered"), "<=": ({"Ordered"}, "Ordered"),
                ">=": ({"Ordered"}, "Ordered"), "+": ({"Addable", "Numeric"}, "Addable"),
                "-": ({"Numeric"}, "Numeric"), "*": ({"Numeric"}, "Numeric"), "/": ({"Numeric"}, "Numeric"),
                "%": ({"Numeric"}, "Numeric")}

    def check_op_bound(self, n, sc):
        """`a < b` on values of an unbounded (or wrongly bounded) type parameter is an error: the body may use only what the bound provides."""
        need = self.OP_NEEDS.get(n.op)
        if need is None or not self.tp_vars:
            return
        for side in (n.l, n.r):
            if side.__class__ is not Name:
                continue
            v = sc.find(side.name)
            tp = self.tp_vars.get(v) if v is not None else None
            if tp is None or tp.where:
                continue
            names = [_tn(b) for b in tp.bounds or []]
            if any(b not in VALUE_IFACES for b in names):
                continue          # a user interface may embed what is needed; the checker cannot tell
            if not set(names) & need[0]:
                self.err(n.line, f"`{n.op}` on a `{tp.name}` needs a `{need[1]}` bound: write `{tp.name}: {need[1]}`")
                return

    def check_type_arity(self, t, line, depth=0):
        """A declared generic type is written with as many type arguments as it has parameters: `Pair[Int]` for a two-parameter `Pair` is an error."""
        if t is None or depth > 8:
            return
        c = t.__class__
        if c is TStatic:
            self.check_type_arity(t.inner, line, depth + 1)
            return
        if c is TLambda:
            names = [p.name for p in t.params]
            if len(set(names)) != len(names):
                self.err(line, "a type lambda names the same parameter twice")
            self.check_type_arity(t.body, line, depth + 1)
            return
        if c is TApp:
            from .typelam import reduce_app, TypeLambdaError
            self.check_type_arity(t.fn, line, depth + 1)
            try:
                reduce_app(t)
            except TypeLambdaError as e:
                self.err(line, str(e))
            return
        if c is not TName:
            if c is TTuple:
                for _, ft in t.items:
                    self.check_type_arity(ft, line, depth + 1)
            return
        for g in t.groups or []:
            for x in g if isinstance(g, list) else [g]:
                self.check_type_arity(x, line, depth + 1)
        if t.path == ["Seq"] and "Seq" not in self.tuples and "Seq" not in self.enums and "Seq" not in self.aliases \
                and "Seq" not in self.iface_decls:
            self.err(line, "`Seq` is not a type you can write: name the collection (`List[T]`, `Array[T]`, `Set[T]`, `Stream[T]`)")
            return
        if len(t.path) != 1 or len(t.groups or []) != 1 or not t.groups[0]:
            return
        al = self.aliases.get(t.path[0])
        if al is not None and al.kind == "alias" and getattr(al, "tparams", None) and not any(tp.holes for tp in al.tparams):
            want, got = len(al.tparams), len(t.groups[0])
            if want != got:
                self.err(line, f"`{t.path[0]}` takes {want} type argument{'s' if want != 1 else ''}, but {got} given")
            return
        d = self.tuples.get(t.path[0]) or self.enums.get(t.path[0])
        if d is None or not getattr(d, "tparams", None) or any(tp.holes for tp in d.tparams):
            return
        want, got = len(d.tparams), len(t.groups[0])
        if want != got:
            self.err(line, f"`{t.path[0]}` takes {want} type argument{'s' if want != 1 else ''}, but {got} given")

    def generic_call(self, fd, n, args, ats, extra):
        """The result type of a call to a generic function when it follows from the arguments: every argument for the same `T` has one type."""
        if extra or any(getattr(a, "label", None) or getattr(a, "mod", None) for a in args):
            return None
        bound = {}
        params = list(fd.params or [])
        for p, a, (t, _c) in zip(params, args, ats):
            tp = self.bare_tparam(fd, p.type)
            if tp is None or t is None or t == ("secret",) and False:
                continue
            t = self.base(t)
            if t.__class__ is tuple and t[0] != "named":
                continue
            if tp.name in bound:
                u = bound[tp.name]
                if u != t and not ({u, t} <= {"Int", "Float", "Decimal"}):
                    self.err(n.line, f"`{fd.name}` needs one type for `{tp.name}`, but it is given `{tshow(u)}` and `{tshow(t)}`")
                    return None
            else:
                bound[tp.name] = t
        r = self.bare_tparam(fd, fd.ret)
        if r is not None and r.name in bound and not (bound[r.name] in ("Int", "Float", "Decimal")):
            return bound[r.name]
        return self.structured_call(fd, n, args, ats)

    def structured_call(self, fd, n, args, ats):
        """Unify parameter types that mention a type parameter inside an application (`List[T]`, `Box[T]`, `(T) -> U`) with the
        arguments; report a clash, and give the return type with the parameters filled in."""
        keep = {tp.name for tp in fd.tparams or []}
        params = list(fd.params or [])
        if len(args) > len(params) or any(p.variadic for p in params):
            return None
        binds = {}
        singles = set()                 # a parameter used inside a type function keeps a literal argument's own type ("name", 3)
        for p in params:
            self.tapp_params(self.ty_of_type(p.type, 0, keep), singles, False)
        if fd.ret is not None:
            self.tapp_params(self.ty_of_type(fd.ret, 0, keep), singles, False)
        for p, a, (t, _c) in zip(params, args, ats):
            pt = self.ty_of_type(p.type, 0, keep)
            if pt.__class__ is not tuple or t is None:
                continue
            if pt[0] == "param":
                bt = self.base(t)
                if pt[1] in singles and bt in ("String", "Int") and _c is not None and bt != "Bool":
                    binds[pt[1]] = ("slit", _c) if bt == "String" else ("lit", _c)
                elif bt.__class__ is not tuple or bt[0] in ("app", "fn", "tup", "named"):
                    j = tys.join(binds.get(pt[1]), bt)
                    if j != "conflict":
                        binds[pt[1]] = j
                continue
            clash = tys.unify(pt, self.base(t), binds)
            if clash:
                self.err(n.line, f"`{fd.name}` needs one type for its type parameters, but `{p.name}` gets `{tshow(t)}` where `{tshow(clash[0])}` was fixed by another argument"
                         if clash[0] is not None else f"mismatched types in call to `{fd.name}`")
                return None
            if not tys.compatible(tys.subst(pt, binds), t) and not (tys.params_in(pt) - set(binds)):
                self.err(n.line, f"mismatched types: expected `{tshow(tys.subst(pt, binds))}`, found `{tshow(t)}`")
                return None
        ret = self.ty_of_type(fd.ret, 0, keep) if fd.ret is not None else None
        if ret is None:
            return None
        if ret.__class__ is tuple and ret[0] == "param":
            return binds.get(ret[1])
        if ret.__class__ is tuple and ret[0] in ("app", "fn", "tup", "appv", "tapp"):
            return tys.subst(ret, binds)
        return ret if not tys.params_in(ret) else None

    def tapp_params(self, t, out, inside):
        """Collect the type parameters that appear inside a type-function application."""
        if t.__class__ is not tuple:
            return
        if t[0] == "param" and inside:
            out.add(t[1])
        for x in t[1:]:
            if x.__class__ is tuple:
                if x and x[0].__class__ is str and x[0] in ("param", "app", "tapp", "tup", "fn", "spread", "appv"):
                    self.tapp_params(x, out, inside or t[0] == "tapp")
                else:
                    for y in x:
                        self.tapp_params(y, out, inside or t[0] == "tapp")

    def generic_tuple(self, td, n, args, ats):
        """`Box(v: 1)`: unify the field types with the arguments, giving `Box[Int]`; a field that clashes is an error."""
        keep = {tp.name for tp in td.tparams}
        fields = list(td.fields or [])
        binds, i = {}, 0
        for a, (t, c) in zip(args, ats):
            if getattr(a, "mod", None) == "spread":
                return None
            if a.label is not None:
                f = next((f for f in fields if f.name == a.label), None)
            else:
                f = fields[i] if i < len(fields) else None
                i += 1
            if f is None:
                continue
            ft = self.ty_of_type(f.type, 0, keep)
            clash = tys.unify(ft, self.base(t), binds)
            if clash:
                self.err(n.line, f"mismatched types in `{td.name}(...)`: field `{f.name}` expects `{tshow(clash[0])}`, found `{tshow(clash[1])}`")
                return None
        return ("app", td.name, tuple(binds.get(tp.name) for tp in td.tparams))

    def check_tuple_args(self, td, args, ats, line):
        fields = {f.name: f for f in td.fields or []}
        pos = [f for f in td.fields or []]
        i = 0
        for a, (t, c) in zip(args, ats):
            if getattr(a, "mod", None) == "spread":
                return
            if a.label is not None:
                f = fields.get(a.label)
                if f is None:
                    self.err(line, f"`{td.name}` has no field `{a.label}`")
                    continue
            else:
                if i >= len(pos):
                    return
                f = pos[i]
                i += 1
            self.compat(self.ty_of_type(f.type), t, c, line)

    def hidden_foreign_param(self, p):
        """A foreign parameter the caller does not supply: a length filled in by the call, or an out-handle."""
        d = p.default
        if d is not None and d.__class__ is Call and d.fn.__class__ is Name and d.fn.name in ("len", "size_of"):
            return True
        if p.type.__class__ is TName and p.type.path[-1] == "UserData":
            return True
        return p.mod == "ref" and p.type.__class__ is TName and p.type.path[-1] in self.handle_types

    def check_call(self, fd, n, args, ats, extra):
        params = list(fd.params or [])
        if id(fd) in self.foreign_ids:
            params = [p for p in params if not self.hidden_foreign_param(p)]
        if any(p.mod == "using" for p in params):
            return self.ret_of(fd), None
        if any(a.mod == "spread" or a.expr.__class__ in (PH, Slot) for a in args if hasattr(a, "expr")):
            return self.ret_of(fd), None
        if any(p.variadic for p in params) or any(self.has_ph(a.expr) for a in args):
            return self.ret_of(fd), None
        given = len(args) + extra + (1 if n.trailing is not None else 0)
        required = [p for p in params if p.default is None]
        if given == 1 and len(params) > 1 and not (len(ats) == 1 and ats[0][0] in self.SCAL and not extra):
            return self.ret_of(fd), None        # may be an implicit tuple unpack
        if given > len(params) or (given < len(required) and not any(a.label for a in args)):
            self.err(n.line, f"`{fd.name}` takes {len(params)} argument{'s' if len(params) != 1 else ''}, but {given} given")
            return self.ret_of(fd), None
        byname = {p.name: p for p in params}
        for i, (a, (t, c)) in enumerate(zip(args, ats)):
            p = byname.get(a.label) if a.label else (params[i + (0)] if i < len(params) and not extra else None)
            if p is None:
                continue
            if p.mod == "ref" and a.mod != "ref":
                self.err(n.line, f"parameter `{p.name}` is `ref`; write `ref {self.arg_name(a)}`")
            elif a.mod == "ref" and p.mod != "ref":
                self.err(n.line, f"parameter `{p.name}` is not `ref`; drop the `ref`")
            if id(fd) in self.foreign_ids and p.type.__class__ is TName and p.type.path[-1] == "Events" \
                    and a.expr.__class__ is not Move and a.mod != "move":
                self.err(n.line, f"parameter `{p.name}` is kept by the library; write `move {self.arg_name(a)}`")
            if p.type is not None:
                self.compat(self.ty_of_type(p.type), t, c, n.line)
        return self.ret_of(fd), None

    def arg_name(self, a):
        e = a.expr
        return e.name if e.__class__ is Name else "x"

    def has_ph(self, e):
        return any(x.__class__ in (PH, Slot) for x in self.iter_nodes(e))

    def ret_of(self, fd):
        return self.ty_of_type(fd.ret)

    def e_Pipe(self, n, sc):
        lt = self.ev(n.l, sc)[0]
        st = n.stage
        if st.__class__ is Call:
            self.pipe_ty = lt
            r = self.e_Call(st, sc, extra=1)
            self.pipe_ty = None
            return r
        self.ev(st, sc)
        return None, None

    # ------------------------------------------------------------ declarations
    def e_FnDecl(self, n, sc):
        later, self._later = self._later, False         # a later clause of a function takes the first clause's return type
        inner = Sc(sc)
        saved = (self.fn_ret, self.fn_tparams, self.loop_depth, self.exit_ctx, self.moved, self.tp_vars)
        self.tp_vars = {}
        saved_any, self.any_params = self.any_params, {}
        saved_decl, self.tp_decl = self.tp_decl, {t.name: t for t in (n.tparams or [])}
        self.fn_tparams = tuple(t.name for t in (n.tparams or []))
        self.loop_depth, self.exit_ctx, self.moved = 0, False, {}
        for tp in n.tparams or []:
            inner.vars[tp.name] = Var(None, False, 0)
        for p in n.params or []:
            res = self.is_res_type(p.type)
            if p.name:
                pty = self.ty_of_type(p.type)
                if p.type.__class__ is TAny and self.any_names(p.type) and not p.variadic:
                    self.any_params[p.name] = ("any", self.any_names(p.type), f"{p.name}@{n.line}")
                elif pty.__class__ is tuple and pty[0] in ("named", "app"):
                    self.any_params[p.name] = pty
                if p.variadic:
                    from .values import GC
                    pty = ("app", "List" if GC[0] else "Array", (pty,))       # inside the body, `...T` is an Array of T (a List in moxie/gc)
                inner.vars[p.name] = Var(pty, res, 0)
                if self.any_params.get(p.name, (None,))[0] == "any":
                    self.any_vars[inner.vars[p.name]] = self.any_params[p.name]
                tp = self.bare_tparam(n, p.type)
                if tp is not None:
                    self.tp_vars[inner.vars[p.name]] = tp
            if p.pat is not None:
                self.bind_pat(p.pat, inner)
            self.ev(p.default, inner)
            self.check_type_arity(p.type, n.line)
        for nm in n.locals or []:
            inner.vars[nm] = Var(None, False, 0)
        self.fn_ret = self.ty_of_type(n.ret) if n.ret is not None else None
        self.check_type_arity(n.ret, n.line)
        if n.ret is None and not later and n.body is not None and n.alias is None and id(n) not in self.foreign_ids:
            self.err(n.line, f"function '{n.name}' has no return type: write it after the parameters, and write Unit if it returns nothing")
        if not later and n.body is not None and n.alias is None and id(n) not in self.foreign_ids:
            for p in n.params or []:
                if p.name and p.type is None and p.name != "self":
                    self.err(n.line, f"parameter '{p.name}' of function '{n.name}' has no type: write it after the name, as in `{p.name}: Int`")
        if n.alias is not None:
            self.ev(n.alias, inner)
        elif n.body is not None:
            if n.guard is not None:
                self.ev(n.guard, inner)
            t, c = self.ev(n.body, inner)
            self.check_tail(n.body, inner)
            if "tailrec" in (n.flags or ()):
                self.check_tailrec(n)
        self.fn_ret, self.fn_tparams, self.loop_depth, self.exit_ctx, self.moved, self.tp_vars = saved
        self.any_params = saved_any
        self.tp_decl = saved_decl
        return None, None

    def check_tailrec(self, n):
        """`tailrec fn`: every call to the function itself must be in tail position."""
        ok = set()

        def mark(e):
            c = e.__class__
            if c is ExprStmt:
                mark(e.e)
            elif c is Block:
                s = e.stmts or []
                if s:
                    last = s[-1]
                    if last.__class__ is ExprStmt:
                        mark(last.e)
                    elif last.__class__ is Return and last.e is not None:
                        mark(last.e)
                    elif last.__class__ is ElseLet:
                        pass
                for st in s:
                    if st.__class__ is Return and st.e is not None:
                        mark(st.e)
                    elif st.__class__ is ElseLet and st.else_ is not None:
                        mark(st.else_)
            elif c is IfE:
                for _, b in e.branches:
                    mark(b)
                if e.else_ is not None:
                    mark(e.else_)
            elif c is WhenE:
                for a in e.arms or []:
                    mark(a.body)
            elif c is Call:
                ok.add(id(e))
        mark(n.body)
        bad = []

        def walk(x):
            if isinstance(x, N):
                if x.__class__ is Call and x.fn.__class__ is Name and x.fn.name == n.name and id(x) not in ok:
                    bad.append(x)
                for f in x._fields:
                    walk(getattr(x, f, None))
            elif isinstance(x, (list, tuple)):
                for y in x:
                    walk(y)
        walk(n.body)
        for b in bad:
            self.err(b.line or n.line, f"`{n.name}` is marked `tailrec`, but this recursive call is not in tail position")

    def check_tail(self, body, sc):
        if self.fn_ret is None:
            return
        for e in self.tails(body):
            t, c = self.quiet(e, sc)
            self.settle_mixed(e, self.fn_ret)
            self.compat(self.fn_ret, t, c, e.line)

    def tails(self, e):
        c = e.__class__
        if c is ExprStmt:
            return self.tails(e.e)
        if c is Block:
            s = e.stmts or []
            if s and s[-1].__class__ is ExprStmt:
                return self.tails(s[-1].e)
            return []
        if c is IfE and e.else_ is not None:
            out = []
            for _, b in e.branches:
                out += self.tails(b)
            return out + self.tails(e.else_)
        if c in (IntLit, FloatLit, StrLit, BoolLit, CharLit) or self.simple_tail(e):
            return [e]
        return []

    def simple_tail(self, e):
        """A name, or a call whose arguments are literals and names: checked again for the function's result type without side effects."""
        if e.__class__ is Name:
            return True
        if e.__class__ is Call and e.fn.__class__ is Field and e.fn.obj.__class__ is Name and e.trailing is None \
                and self.any_params.get(e.fn.obj.name, (None,))[0] == "any":
            return all(hasattr(a, "expr") and not getattr(a, "mod", None) and
                       (a.expr.__class__ in (IntLit, FloatLit, StrLit, BoolLit, CharLit, Name) or self.simple_tail(a.expr))
                       for a in e.args or [])           # a member call on an `any` parameter has a type of its own
        if e.__class__ is not Call or e.fn.__class__ is not Name or e.trailing is not None:
            return False
        return all(hasattr(a, "expr") and not getattr(a, "mod", None) and
                   (a.expr.__class__ in (IntLit, FloatLit, StrLit, BoolLit, CharLit, Name) or self.simple_tail(a.expr))
                   for a in e.args or [])

    def quiet(self, e, sc):
        n = len(self.diags)
        anyc = (self.any_vars and e.__class__ is Call and e.fn.__class__ is Field and e.fn.obj.__class__ is Name
                and sc.find(e.fn.obj.name) in self.any_vars)          # a member call on an `any` parameter has a known type
        r = self.ev(e, sc) if e.__class__ in (IntLit, FloatLit, StrLit, BoolLit, CharLit) or anyc or self.simple_tail(e) else (None, None)
        del self.diags[n:]
        return r

    def e_FnGroup(self, n, sc):
        for k, c in enumerate(n.clauses or []):
            self._later = k > 0
            self.e_FnDecl(c, sc)
        self.group_cover(n)
        return None, None

    def group_cover(self, n):
        """A multi-clause function ends with a catch-all clause or covers every enum case."""
        cl = n.clauses or []
        if len(cl) < 2:
            return
        names = set(self.cases) | {"Ok", "Err"}

        def ca(pm):
            return pm.pat is None or self.catch_all(pm.pat, names)
        last = cl[-1]
        if all(ca(pm) for pm in last.params or []):
            return
        if len(cl[0].params or []) != 1:
            return
        pats = [c.params[0].pat for c in cl if c.params and c.params[0].pat is not None]
        enum = None
        cand = set()
        for q in pats:
            while q.__class__ is PAs:
                q = q.pat
            if q.__class__ is PCon:
                if len(q.path) == 2 and q.path[0] in self.enums:
                    cand.add(q.path[0])
                elif q.path[-1] in self.cases and len(self.cases[q.path[-1]]) == 1:
                    cand.add(self.cases[q.path[-1]][0])
        if len(cand) == 1:
            enum = cand.pop()
        line = getattr(last, "line", 0)
        if enum is not None:
            required = [c.name for c in self.enums[enum].cases or []]
            covered = set()
            for q in pats:
                while q.__class__ is PAs:
                    q = q.pat
                if q.__class__ is PCon:
                    covered.add(q.path[-1])
            miss = [c for c in required if c not in covered]
            if miss:
                self.err(line, f"`{n.name}` does not cover " + ", ".join(f"`{m}`" for m in miss))
        elif pats and all(q.__class__ in (PLit, PRange, PRel) for q in pats):
            self.err(line, f"`{n.name}` needs a final `_` clause")

    def _tname(self, t):
        return t.path[-1] if t.__class__ is TName and len(t.path) == 1 and not t.groups else None

    def check_generatable(self, n):
        """`impl Generatable for T` needs `static fn generate(g: Gen) Self`; `fn shrink() List[Self]` is optional."""
        fns = {m.name: m for m in n.members or [] if m.__class__ is FnDecl}
        line = n.line
        def is_self(t):
            if t.__class__ is not TName:
                return False
            if t.path == ["Self"] and not t.groups:
                return True
            return t.path == n.target.path and t.groups == n.target.groups
        g = fns.get("generate")
        if g is None:
            self.err(line, "impl Generatable needs `static fn generate(g: Gen) Self`")
        else:
            if "static" not in (g.flags or ()):
                self.err(g.line, "generate must be `static`: it makes a value, so there is no value to call it on")
            ps = g.params or []
            if len(ps) != 1 or self._tname(ps[0].type) != "Gen":
                self.err(g.line, "generate takes one parameter of type Gen: `static fn generate(g: Gen) Self`")
            if g.ret is None or not is_self(g.ret):
                self.err(g.line, "generate must return Self (the type being generated)")
        sh = fns.get("shrink")
        if sh is not None:
            if "static" in (sh.flags or ()):
                self.err(sh.line, "shrink is a method on the value being shrunk, not `static`")
            if sh.params:
                self.err(sh.line, "shrink takes no parameters: `fn shrink() List[Self]`")
            r = sh.ret
            ok = (r.__class__ is TName and r.path == ["List"] and len(r.groups) == 1
                  and len(r.groups[0]) == 1 and is_self(r.groups[0][0]))
            if not ok:
                self.err(sh.line, "shrink must return List[Self]: smaller values to try when a property fails")
        for name in fns:
            if name not in ("generate", "shrink"):
                self.err(fns[name].line, f"Generatable has no method '{name}' (it has generate and shrink)")

    def e_ImplDecl(self, n, sc):
        if n.iface is not None and n.iface.__class__ is TName and n.iface.path == ["Generatable"]:
            self.check_generatable(n)
        for m in n.members or []:
            if n.iface is not None and m.__class__ is FnDecl and m.contracts:
                self.err(m.line, f"an impl of an interface may not add contracts to '{m.name}'; "
                                 "the contract belongs to the interface")
            inner = Sc(sc, open_=True)
            self.ev(m, inner)
        return None, None

    def e_ForeignDecl(self, n, sc):
        from .effects import Effects
        for d in n.fns:
            if Effects.declared(d) is None:
                self.err(d.line, f"foreign fn '{d.name}' needs an effect declaration: pure, prints, parks, or impure")
            if "parks" in (d.flags or ()) and any(p.type.__class__ is TFn for p in d.params or []):
                self.err(d.line, f"foreign fn '{d.name}' takes a callback, so it cannot be declared parks: "
                                 "the callback would run on the OS helper thread")
        return None, None

    def e_IfaceDecl(self, n, sc):
        for m in n.members or []:
            if m.__class__ in (FnDecl,) and m.body is not None:
                self.e_FnDecl(m, Sc(sc, open_=True))
        return None, None

    def e_TupleDecl(self, n, sc):
        return None, None

    def e_EnumDecl(self, n, sc):
        return None, None

    def e_AliasDecl(self, n, sc):
        self.check_type_arity(n.type, n.line)
        self.check_tfun_decl(n)
        return None, None

    def e_TestDecl(self, n, sc):
        self.ev(n.body, Sc(sc))
        return None, None

    def e_InitDecl(self, n, sc):
        self.ev(n.body, Sc(sc))
        return None, None

    def e_GenApp(self, n, sc):
        self.ev(n.base, sc)
        if n.base.__class__ is Name and n.groups and n.groups[0]:
            fds = self.fns.get(n.base.name)
            if fds and len(fds) == 1 and fds[0].tparams:
                self.check_ctor_targs(fds[0], n.groups[0], n.line)
            for g in n.groups:
                for x in g:
                    self.check_type_arity(x, n.line)
        return None, None

    def ctor_arity(self, t):
        """How many type arguments the constructor `t` takes, or None when the checker cannot tell."""
        c = t.__class__
        if c is TLambda:
            return len(t.params)
        if c is TName and len(t.path) == 1:
            n = t.path[0]
            if not t.groups:
                d = self.aliases.get(n) if n in self.aliases and self.aliases[n].kind == "alias" else self.tuples.get(n) or self.enums.get(n)
                if d is not None and getattr(d, "tparams", None):
                    return len(d.tparams)
                return None
            if len(t.groups) == 1 and any(x.__class__ is THole for x in t.groups[0]):
                return sum(1 for x in t.groups[0] if x.__class__ is THole)
        return None

    def check_ctor_targs(self, fd, targs, line):
        """A type lambda, alias, or constructor given for a constructor parameter `F[_]` takes as many arguments as the parameter has holes."""
        for tp, ta in zip(fd.tparams or [], targs):
            if not tp.holes:
                continue
            have = self.ctor_arity(ta)
            if have is not None and have != tp.holes:
                self.err(line, f"`{tp.name}` of `{fd.name}` is a constructor of {tp.holes} type argument{'s' if tp.holes != 1 else ''}, but this one takes {have}")

    def e_Arg(self, n, sc):
        if n.mod == "move" and n.expr.__class__ is Name:       # `f(move c)` hands c over, as `move c` does
            return self._move_name(n, n.expr, sc)
        return self.ev(n.expr, sc)

    def _move_name(self, n, e, sc):
        v = sc.find(e.name)
        if v is not None:
            self.ev(e, sc)
            if v.depth < self.loop_depth and not self.exit_ctx:
                self.err(getattr(n, "line", 0) or getattr(e, "line", 0), f"`{e.name}` is moved inside a loop; a resource may be moved only on an exiting path")
            self.moved[v] = getattr(e, "line", 0)
            return v.ty, None
        return self.ev(e, sc)

    def e_TupleE(self, n, sc):
        types, labs = [], []
        plain = True
        for it in n.items or []:
            t = self.ev(it[1] if isinstance(it, tuple) and len(it) > 1 else it, sc)[0]
            types.append(self.base(t))
            if isinstance(it, tuple) and len(it) > 1:
                labs.append(it[0])
            else:
                labs.append(None)
            if not (isinstance(it, tuple) and len(it) > 1 and not (len(it) > 2 and it[2])):
                plain = False
        if plain and len(types) >= 2:
            return (("tup", tuple(types), tuple(labs)) if any(labs) else ("tup", tuple(types))), None
        return None, None

    def e_PathE(self, n, sc):
        return None, None

    def e_Deref(self, n, sc):
        self.ev(n.e, sc)
        return None, None


def package_visibility(search_dir, parts):
    """({name: "export" | "internal" | "file"}) for a package's top-level declarations, or None when it can't be read."""
    from .packages import package_files, parse_package
    try:
        found = package_files(search_dir, parts)
        if found is None:
            return None
        prog = parse_package(found[0])[1]
    except Exception:
        return None
    vis = {}
    for st in prog.stmts:
        c = st.__class__
        if c is FnDecl or c is FnGroup:
            flags = (st.flags if c is FnDecl else st.clauses[0].flags) or ()
            v = "export" if "export" in flags else "internal" if "internal" in flags else "file"
            vis[st.name] = v
        elif c in (TupleDecl, EnumDecl, IfaceDecl, AliasDecl):
            vis[st.name] = st.vis if st.vis in ("export", "internal") else "file"
        elif c is Assign:
            for t in st.targets if isinstance(st.targets, (list, tuple)) else [st.targets]:
                if t.__class__ in (Name, PBind):
                    vis[t.name] = st.vis if st.vis in ("export", "internal") else "file"
    return vis


def check_package_access(prog, search_dir):
    """Using another package's `internal` or file-local name is a compile error (Spec section 4)."""
    from .effects import _children
    diags, pkgs = [], {}
    for st in prog.stmts:
        if st.__class__ is not ImportDecl:
            continue
        vis = package_visibility(search_dir, st.pkg)
        if vis is None:
            continue
        key = ".".join(st.pkg)
        if st.names:
            for nm in st.names:
                nm = nm if isinstance(nm, str) else getattr(nm, "name", None)
                v = vis.get(nm)
                if v in ("internal", "file"):
                    diags.append(Diag(st.line, hidden_msg(key, nm, v)))
        else:
            pkgs[st.alias or st.pkg[-1]] = (key, vis)
    if pkgs:
        todo = [(prog, 0)]
        while todo:
            n, line = todo.pop()
            line = getattr(n, "line", None) or line
            member = None
            if n.__class__ is Field and n.obj.__class__ is Name and n.obj.name in pkgs:
                member = (n.obj.name, n.name)
            elif n.__class__ is TName and len(n.path) >= 2 and n.path[0] in pkgs:
                member = (n.path[0], n.path[1])
            if member is not None:
                key, vis = pkgs[member[0]]
                v = vis.get(member[1])
                if v in ("internal", "file"):
                    diags.append(Diag(line, hidden_msg(key, member[1], v)))
            todo.extend((c, line) for c in _children(n))
    return diags


def hidden_msg(pkg, name, v):
    if v == "internal":
        return f"'{name}' is internal to package {pkg} and cannot be used from outside it"
    return f"'{name}' in package {pkg} is not exported (add `export` to its declaration to use it from another package)"


def check_package_access_diags(prog, search_dir):
    return check_package_access(prog, search_dir) if search_dir is not None else []


TF_MAX_NODES = 4000       # a type function's argument larger than this (counted as a tree) stops the reduction too
TF_FUEL = 64               # reductions of type functions allowed in one use before the checker gives up (see apply_tfun)
KEY_WARN_DEFAULT = 64        # bytes: a Dict key or Set element above this gets a warning (Spec section 6)


def check_key_sizes(prog, threshold):
    """Warn about a Dict key or Set element type whose fixed size is above the threshold."""
    from .effects import _children
    from .layout import layout, type_decls
    decls = type_decls(prog)
    diags, todo = [], [(prog, 0)]
    while todo:
        n, line = todo.pop()
        line = getattr(n, "line", None) or line
        if n.__class__ is TName and len(n.path) == 1 and n.path[0] in ("Dict", "Set") and n.groups and len(n.groups[0]) >= 1:
            kt = n.groups[0][0]
            r = layout(kt, decls)
            if r is not None and r[0] > threshold:
                what = "key" if n.path[0] == "Dict" else "element"
                diags.append(Diag(line, f"a {n.path[0]} {what} of {r[0]} bytes is above the {threshold}-byte warning size: "
                                        f"keys are copied and hashed whole, so key on a small id or a Keyword instead", "warning"))
        todo.extend((c, line) for c in _children(n))
    return diags


def check_program(prog, prelude_names, search_dir=None, key_warn=KEY_WARN_DEFAULT, type_fuel=None, eval_fuel=None):
    from .cteval import CtEval
    CT[0] = CtEval(prog, search_dir, eval_fuel)
    try:
        return _check_program(prog, prelude_names, search_dir, key_warn, type_fuel)
    finally:
        CT[0] = None


def _check_program(prog, prelude_names, search_dir, key_warn, type_fuel):
    ck = Checker(prelude_names)
    if type_fuel:
        ck.tf_fuel = type_fuel
    ck.search_dir = search_dir
    diags = ck.check(prog)
    diags.extend(check_package_access_diags(prog, search_dir))
    if key_warn:
        diags.extend(check_key_sizes(prog, key_warn))
    from .effects import check_effects
    seen = {(d.line, d.msg) for d in diags}
    for line, msg in check_effects(prog, search_dir):
        if (line, msg) not in seen:
            diags.append(Diag(line, msg))
    return diags
