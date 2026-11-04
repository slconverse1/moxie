"""The Moxie tree-walking evaluator (generator based, so fibers can park)."""
import os
import sys
from .ast import *   # noqa
from .values import *   # noqa
from .core import *   # noqa
from .types_ import *   # noqa
from .lexer import MoxieSyntaxError, tokenize
from .calls import CallsMixin, LazyV, SLOT, USING, RecvCell, END
from .decls import DeclsMixin
from .patterns import PatternsMixin
from .places import PlacesMixin
from .parser import parse_program


class Interp(TypesMixin, CallsMixin, DeclsMixin, PatternsMixin, PlacesMixin):
    def __init__(self, out=None, err=None, search_dir=None, test_mode=False, inp=None):
        self.inp = inp if inp is not None else sys.stdin
        self.out = out if out is not None else sys.stdout
        self.err = err if err is not None else sys.stderr
        self.search_dir = search_dir
        self.test_mode = test_mode
        from .pools import Pools
        from .perms import Perms
        self.pools = Pools()
        self._perms = Perms.open()
        self.pkg_ceilings = {}        # package name -> Perms (Spec 19d, per-package ceilings)
        self.mod_pkg = {}             # id(module env) -> package name
        self.cur_mod = None
        self.manifest = {}
        self.tuples = {}
        self.enums = {}
        self.ifaces = {}
        self.iface_impls = {}
        self.aliases = {}
        self.impls = {}        # type name -> {method -> [Closure]}
        self.statics = {}      # type name -> {name -> [Closure]}
        self.froms = {}        # error type -> [(source type name, Closure)]
        self.cases = {}        # bare case name -> [EnumType]
        self.packages = {}
        self.tests = []
        self.free_cache = {}
        self.sched = None
        self.cur_fiber = None
        self.line = 0
        self.file = "<input>"
        self.disp = {}
        for name in dir(self):
            if name.startswith("ev_"):
                cls = globals().get(name[3:])
                if cls is not None:
                    self.disp[cls] = getattr(self, name)
        from .prelude import install_prelude
        self.prelude = Env()
        self.prelude.mod = self.prelude
        install_prelude(self)
        self.module_env = None
        from .mxprelude import install as _install_mx
        _install_mx(self)

    # ------------------------------------------------------------ driving
    def run_sync(self, gen):
        try:
            r = next(iter(gen)) if False else None
        except Exception:
            raise
        it = iter(gen)
        try:
            while True:
                req = next(it)
                raise Abort("this expression cannot park or wait here")
        except StopIteration as s:
            return s.value

    def ev(self, n, env):
        return self.disp[n.__class__](n, env)

    def evh(self, n, env, hint):
        """Evaluate with an expected type (for bare enum case names)."""
        c = n.__class__
        if hint is not None:
            if c is Name:
                return self.ev_Name(n, env, hint)
            if c is Call:
                return self.ev_Call(n, env, hint=hint)
            if c is IfE:
                return self.ev_IfE(n, env, hint)
            if c is WhenE:
                return self.ev_WhenE(n, env, hint)
            if c is Block:
                return self.ev_Block(n, env, hint=hint)
            if c is DoE:
                return self.ev_DoE(n, env, hint)
        return self.disp[c](n, env)

    @property
    def perms(self):
        if self.pkg_ceilings:
            key = self.mod_pkg.get(id(self.cur_mod))
            ceil = self.pkg_ceilings.get(key)
            if ceil is not None:
                from .perms import Combined
                return Combined(self._perms, ceil, key)
        return self._perms

    @perms.setter
    def perms(self, pm):
        self._perms = pm

    def new_module_env(self):
        env = Env(self.prelude)
        env.mod = env
        env.func = FnCtx("<main>")
        env.func.is_entry = True
        return env

    def run_source(self, src, file="<input>", check=True):
        """Run a program. Returns the exit code. Core static checks run first (compile errors stop the run)."""
        try:
            prog = self.load_source(src, file)
        except MoxieSyntaxError as e:
            self.err.write(str(e) + "\n")
            return 2
        if check:
            errs = [d for d in self.static_check(prog) if d.kind == "error"]
            if errs:
                for d in errs:
                    self.err.write(f"{file}:{d.line}: error: {d.msg}\n")
                return 2
        env = self.new_module_env()
        self.module_env = env
        self.main_prog = prog

        def body():
            r = yield from self.exec_stmts(prog.stmts, env)
            return r
        try:
            try:
                self.sched.run_main(body())
            finally:
                for sk in self.__dict__.get("event_sinks", []):
                    if sk.dropped:
                        self.err.write(f"warning: {sk.dropped} event(s) from {sk.name} were dropped because the channel was full\n")
                if self.__dict__.get("live_io"):
                    from .prelude import close_live_io
                    close_live_io(self)
                if self.__dict__.get("live_handles"):
                    from .ffi import drop_live_handles
                    drop_live_handles(self)
        except ProgramExit as e:
            if e.msg and not getattr(e, "printed", False):
                self.err.write(e.msg + "\n")
            return e.code
        except Abort as a:
            self.err.write(f"abort (line {a.line or self.line}): {a.msg}\n")
            return 1
        return 0

    DECL_NODES = ("FnDecl", "FnGroup", "TupleDecl", "EnumDecl", "IfaceDecl", "ImplDecl", "AliasDecl",
                  "ImportDecl", "UsingDecl", "TestDecl", "Assign", "ForeignDecl")

    EFFECTS = {"println", "print", "dbg", "sql", "read", "write", "sleep", "run", "transaction"}

    def _has_effect(self, node):
        if isinstance(node, (list, tuple)):
            return any(self._has_effect(x) for x in node)
        if not hasattr(node, "_fields"):
            return False
        if node.__class__.__name__ in ("SqlE", "Run"):
            return True
        if node.__class__.__name__ == "Call" and node.fn.__class__.__name__ == "Name" and node.fn.name in self.EFFECTS:
            return True
        return any(self._has_effect(getattr(node, f, None)) for f in node._fields)

    def run_tests(self, src, file="<input>", only=None):
        """`moxie test`: define everything, skip the entry body, run each test block in its own fiber.
        Returns (passed, failed, exit code)."""
        try:
            prog = self.load_source(src, file)
        except MoxieSyntaxError as e:
            self.err.write(str(e) + "\n")
            return 0, 0, 2
        env = self.new_module_env()
        self.module_env = env
        self.main_prog = prog
        decls = [st for st in prog.stmts if st.__class__.__name__ in self.DECL_NODES
                 and not (st.__class__.__name__ == "Assign" and self._has_effect(st.value))]

        def setup():
            return (yield from self.exec_stmts(decls, env))
        try:
            self.sched.run_main(setup())
        except (Abort, ProgramExit) as e:
            self.err.write(f"cannot set up {file}: {getattr(e, 'msg', e)}\n")
            return 0, 0, 1
        passed = failed = 0
        for name, body, tenv in list(self.tests):
            if only and only not in name:
                continue

            def one(body=body, tenv=tenv):
                return (yield from self.ev(body, tenv.child()))
            saved_err = self.err
            import io as _io
            self.err = _io.StringIO()
            try:
                self.sched.run_main(one())
                passed += 1
                self.out.write(f"ok    {name}\n")
            except Abort as a:
                failed += 1
                self.out.write(f"FAIL  {name}: {a.msg}" + (f" (line {a.line})" if a.line else "") + "\n")
            except ProgramExit as e:
                failed += 1
                msg = self.err.getvalue().strip().replace("abort in fiber main ", "") or e.msg or f"exit {e.code}"
                self.out.write(f"FAIL  {name}: {msg}\n")
            finally:
                self.err = saved_err
        self.out.write(f"{passed} passed, {failed} failed\n")
        return passed, failed, (1 if failed else 0)

    def static_check(self, prog):
        from .check import check_program, Diag
        diags = check_program(prog, set(self.prelude.vars))
        from .values import GC
        if not GC[0]:
            from .tally import tally_problems
            for line, msg in tally_problems(prog):
                diags.append(Diag(line, msg))
        pm = self._perms
        if pm.restricted:
            for line, name, want in self.unmet_needs(pm, prog):
                diags.append(Diag(line, f"'{name}' needs {want}, which is not granted ({pm.source})"))
        if self.pkg_ceilings:
            diags.extend(self.package_diags(prog, Diag))
        return diags

    @staticmethod
    def kind_unmet(pm, kind):
        """The description of what `kind` needs if `pm` grants nothing that satisfies it, else None."""
        if kind == "fs":
            ok, want = pm.allows_kind("fs.read") or pm.allows_kind("fs.write"), "fs.read or fs.write"
        elif kind == "net":
            ok, want = pm.allows_kind("net.connect") or pm.allows_kind("net.listen"), "net.connect or net.listen"
        elif kind.startswith("ffi:"):
            ok, want = pm.ffi_ok(kind[4:]), f"ffi for '{kind[4:]}'"
        else:
            ok, want = pm.allows_kind(kind), kind
        return None if ok else want

    def unmet_needs(self, pm, prog):
        from .effects import permission_needs
        out = []
        for kind, (line, name) in sorted(permission_needs(prog).items(), key=lambda kv: kv[1][0]):
            want = self.kind_unmet(pm, kind)
            if want:
                out.append((line, name, want))
        return out

    def find_package(self, parts):
        base = self.search_dir or "."
        cands = [os.path.join(base, *parts) + ".mxi", os.path.join(base, *parts, parts[-1] + ".mxi")]
        return next((p for p in cands if os.path.exists(p)), None)

    def package_diags(self, prog, Diag):
        """Per-package ceilings (Spec 19d): everything a package's code can reach must fit its own table and the program's."""
        from .effects import Needs
        from .perms import Combined
        diags, seen, queue = [], set(), [(prog, 0)]
        while queue:
            cur, via = queue.pop(0)
            for st in cur.stmts:
                if st.__class__ is not ImportDecl:
                    continue
                key = ".".join(st.pkg)
                if key in seen:
                    continue
                seen.add(key)
                path = self.find_package(st.pkg)
                if path is None:
                    continue
                try:
                    pp = parse_program(open(path, encoding="utf-8").read(), path)
                except (OSError, MoxieSyntaxError):
                    continue
                queue.append((pp, via or st.line))
                ceil = self.pkg_ceilings.get(key)
                if ceil is None:
                    continue
                pm = Combined(self._perms, ceil, key)
                nd = Needs(pp)
                acc = dict(nd.solve())
                for s in nd.sum.values():
                    for eff, w in s.eff.items():
                        acc.setdefault(eff, w)
                for kind, w in sorted(acc.items(), key=lambda kv: kv[1][1]):
                    want = self.kind_unmet(pm, kind)
                    if want:
                        diags.append(Diag(via or st.line, f"package '{key}' ({os.path.basename(path)}:{w[1]}): '{w[2]}' needs {want}, "
                                                       f"which is not granted to it ({ceil.source})"))
        for key, ceil in self.pkg_ceilings.items():
            if key not in seen:
                diags.append(Diag(1, f"no imported package is named '{key}' ({ceil.source})", "warning"))
        return diags

    def check_source(self, src, file="<input>"):
        """`moxie check`: parse and run the core static checks. Returns an exit code."""
        try:
            prog = self.load_source(src, file)
        except MoxieSyntaxError as e:
            self.err.write(str(e) + "\n")
            return 2
        diags = self.static_check(prog)
        for d in diags:
            self.err.write(f"{file}:{d.line}: {d.kind}: {d.msg}\n")
        errs = [d for d in diags if d.kind == "error"]
        if not errs:
            self.out.write(f"{file}: ok\n")
        return 1 if errs else 0

    def load_source(self, src, file="<input>"):
        self.file = file
        return parse_program(src, file)

    # ------------------------------------------------------------ literals / names
    def ev_IntLit(self, n, env):
        v = n.v
        s = n.suffix
        if s:
            cls = INT_CLASSES.get({"i8": "Int8", "i16": "Int16", "i32": "Int32", "i64": "Int64",
                                   "u8": "UInt8", "u16": "UInt16", "u32": "UInt32", "u64": "UInt64"}.get(s, ""))
            if cls is not None:
                if not cls.fits(v):
                    raise Abort(f"literal {v} does not fit {cls.tname}")
                return Done(cls(v))
            if s == "f":
                return Done(F32.of(float(v)))
        return Done(v)

    def ev_FloatLit(self, n, env):
        if n.suffix == "f":
            return Done(F32.of(n.v))
        return Done(n.v)

    def ev_DecLit(self, n, env):
        t = n.text
        sc = len(t.split(".")[1]) if "." in t else 0
        return Done(Dec(Decimal(t), sc))

    def ev_CharLit(self, n, env):
        return Done(Char(n.c))

    def ev_BytesLit(self, n, env):
        return Done(ArrayV([Byte_(b) for b in n.b]))

    def ev_ByteChar(self, n, env):
        return Done(Byte_(n.v))

    def ev_KwLit(self, n, env):
        return Done(Kw(n.name))

    def ev_DurLit(self, n, env):
        return Done(Dur(int(n.v * DUR_UNITS[n.unit])) if not isinstance(n.v, float) else Dur(int(n.v * DUR_UNITS[n.unit])))

    def ev_BoolLit(self, n, env):
        return Done(n.b)

    def ev_UnitLit(self, n, env):
        return Done(UNIT)

    def ev_StrLit(self, n, env):
        parts = n.parts
        if len(parts) == 1 and parts[0].__class__ is str:
            return Done(parts[0])
        if not parts:
            return Done("")
        return self._str_interp(n, env)

    def _str_interp(self, n, env):
        out = []
        for p in n.parts:
            if p.__class__ is str:
                out.append(p)
            else:
                v = yield from self.ev(p.expr, env)
                if p.spec:
                    out.append(apply_spec(v, p.spec, self, self.find_locale(env)))
                else:
                    out.append(display(v, self))
        return "".join(out)

    def find_locale(self, env):
        e = env
        while e is not None:
            if e.usings:
                for v in e.usings.values():
                    if isinstance(v, TupleV) and v.tname == "Locale":
                        return {n: x for n, x in zip(v.names, v.vals)}
            e = e.parent
        return None

    def ev_Name(self, n, env, hint=None):
        name = n.name
        v = env.lookup(name, self)
        if v is MISSING:
            return self._name_missing(n, env, hint)
        if v.__class__ is LazyV:
            return self._force_lazy(v)
        return Done(v)

    def _force_lazy(self, lz):
        r = yield from self.ev(lz.expr, lz.env)
        return r

    def _name_missing(self, n, env, hint):
        c = self.resolve_case(n.name, hint)
        if c is not None:
            et, ci = c
            return Done(self.case_value(et, ci))
        raise Abort(f"undefined name '{n.name}'", n.line)

    def ev_PH(self, n, env):
        v = env.lookup(f"_{n.idx}", self)
        if v is MISSING:
            raise Abort("placeholder used outside a function literal", n.line)
        return Done(v)

    def ev_Slot(self, n, env):
        return Done(SLOT)

    def ev_Dollar(self, n, env):
        return self.ev(n.expr, env)

    def ev_Gimme(self, n, env):
        e = self.gimme_scope(n, env)
        return Done(e.vars[n.name])

    def gimme_scope(self, n, env):
        layers = []
        e = env
        while e is not None:
            if not e.hidden:
                layers.append(e)
            if e.parent is None or e is e.mod:
                break
            e = e.parent
        count = 0
        for e in layers[1:]:
            if n.name in e.vars:
                count += 1
                if count == n.n:
                    return e
        raise Abort(f"no enclosing block binds '{n.name}' at gimme.{n.n}", n.line)

    # ------------------------------------------------------------ compound literals
    def ev_TupleE(self, n, env):
        vals = []
        names = []
        any_name = False
        for label, e, spread in n.items:
            if spread:
                sv = yield from self.ev(e, env)
                if isinstance(sv, TupleV):
                    for i, x in enumerate(sv.vals):
                        nm = sv.names[i] if sv.names else None
                        if nm is not None and nm in names:
                            vals[names.index(nm)] = x
                        else:
                            vals.append(x)
                            names.append(nm)
                            any_name = any_name or nm is not None
                continue
            v = yield from self.ev(e, env)
            if label is not None and not isinstance(label, int):
                if label in names:
                    vals[names.index(label)] = v
                    continue
                any_name = True
            elif isinstance(label, int):
                label = None
            vals.append(v)
            names.append(label)
        return TupleV(vals, names if any_name else None)

    def ev_MArr(self, n, env):
        rows = []
        cur_dims = []
        flat = []
        # rows: list of (cells, sepLevel) ; level 1 = ';' , 2 = ';;'
        counts = []
        for cells, level in n.rows:
            vs = []
            for label, e, spread in cells:
                v = yield from self.ev(e, env)
                vs.append(v)
            rows.append((vs, level))
        cols = len(rows[0][0])
        nrows_per_layer = []
        cnt = 0
        layers = 1
        for vs, level in rows:
            flat.extend(vs)
            cnt += 1
            if level >= 2:
                nrows_per_layer.append(cnt)
                cnt = 0
        if cnt:
            nrows_per_layer.append(cnt)
        r = nrows_per_layer[0]
        if len(nrows_per_layer) > 1:
            shape = (len(nrows_per_layer), r, cols)
        else:
            shape = (r, cols)
        return MultiV(flat, shape)

    def ev_PathE(self, n, env):
        return Done(PathV(n.segs[0], n.segs[1:]))

    def ev_RangeE(self, n, env):
        lo = hi = None
        if n.lo is not None:
            lo = yield from self.ev(n.lo, env)
        if n.hi is not None:
            hi = yield from self.ev(n.hi, env)
        step = 1
        if (isinstance(n.lo, IntLit) or (isinstance(n.lo, Unary))) and n.hi is not None and lo is not None and hi is not None:
            if isinstance(lo, int) and isinstance(hi, int) and lo > hi and self._is_lit(n.lo) and self._is_lit(n.hi):
                step = -1
        return RangeV(lo, hi, step, n.incl)

    def _is_lit(self, e):
        return isinstance(e, (IntLit,)) or (isinstance(e, Unary) and isinstance(e.e, IntLit))

    # ------------------------------------------------------------ operators
    def ev_Unary(self, n, env):
        v = yield from self.ev(n.e, env)
        op = n.op
        if op == "not":
            return not v
        if op == "-":
            u = self.user_unary(v, "-")
            if u is not None:
                return (yield from self.apply(u, [v]))
            return negate(v)
        if op == "~":
            return bit_not(v)
        raise Abort(f"bad unary {op}")

    def user_unary(self, v, op):
        return None

    def ev_AndE(self, n, env):
        l = yield from self.ev(n.l, env)
        if not l:
            return False
        return (yield from self.ev(n.r, env))

    def ev_OrE(self, n, env):
        l = yield from self.ev(n.l, env)
        if l:
            return True
        return (yield from self.ev(n.r, env))

    def ev_Binary(self, n, env):
        l = yield from self.ev(n.l, env)
        r = yield from self.ev(n.r, env)
        return (yield from self.binop(n.op, l, r, n.line))

    def binop(self, op, l, r, line=0):
        tl = l.__class__
        tr = r.__class__
        # primitives fast paths
        if (tl is int or tl is float) and tl is tr:
            if op in ("+", "-", "*", "/", "%"):
                return Done(arith(op, l, r))
            if op == "<":
                return Done(l < r)
            if op == ">":
                return Done(l > r)
            if op == "<=":
                return Done(l <= r)
            if op == ">=":
                return Done(l >= r)
            if op == "==":
                return Done(l == r)
            if op == "~=":
                return Done(l != r)
        return self._binop_slow(op, l, r, line)

    def _binop_slow(self, op, l, r, line):
        # user-defined operator?
        u = self.find_op(op, l, r)
        if u is not None:
            return (yield from self.apply_method(u, l, [r]))
        if op == "~=":
            u = self.find_op("==", l, r)
            if u is not None:
                v = yield from self.apply_method(u, l, [r])
                return not v
            return not self.values_eq(l, r)
        if op == "==":
            return self.values_eq(l, r)
        if op in ("<", ">", "<=", ">="):
            ul = self.find_op("<", l, r)
            if ul is not None:
                if op == "<":
                    return (yield from self.apply_method(ul, l, [r]))
                if op == ">":
                    return (yield from self.apply_method(ul, r, [l]))
                lt_ = yield from self.apply_method(ul, l, [r])
                gt_ = yield from self.apply_method(ul, r, [l])
                if op == "<=":
                    return not gt_
                return not lt_
            if op == "<":
                return lt(l, r)
            if op == ">":
                return lt(r, l)
            if op == "<=":
                return not lt(r, l)
            return not lt(l, r)
        if op in ("|>>", "<$>", "<*>", "~>", "<~"):
            return (yield from self.functor_op(op, l, r))
        if op == "+":
            if isinstance(l, str) and isinstance(r, str):
                return l + r
            if isinstance(l, Seq):
                if isinstance(r, Seq) and l.kind == r.kind:
                    return self.new_seq(l, l.items + r.items)
                return self.new_seq(l, l.items + [r])
            if isinstance(l, DictV) and isinstance(r, TupleV):
                d = dict(l.d)
                d[r.vals[0]] = r.vals[1]
                return DictV(d, l.cap)
            if isinstance(l, SetV):
                d = dict(l.items)
                if isinstance(r, SetV):
                    d.update(r.items)
                else:
                    d[r] = True
                return SetV(d, l.cap)
        if op == "*":
            if isinstance(l, Seq) and isinstance(r, int):
                return self.new_seq(l, l.items * r)
            if isinstance(l, str) and isinstance(r, int):
                return l * r
        return arith(op, l, r)

    def new_seq(self, like, items):
        if like.kind == "Ring":
            return RingV(items[-like.cap:] if len(items) > like.cap else items, like.cap)
        if like.kind == "List":
            if len(items) > like.cap:
                # a literal-sized list (capacity == length) grows to fit a concatenation;
                # a list with a declared, larger capacity does not
                if len(like.items) != like.cap:
                    raise Abort(f"List capacity {like.cap} exceeded")
                return ListV(items, len(items))
            return ListV(items, like.cap)
        return ArrayV(items, len(items))

    def values_eq(self, a, b):
        return eq(a, b)

    def functor_op(self, op, l, r):
        if op == "|>>":
            m = self.find_method_for(l, "flat_map")
            if m is not None:
                return (yield from self.apply_method(m, l, [r]))
            if isinstance(l, EnumV) and l.et is RESULT_T:
                if l.case == "Ok":
                    return (yield from self.apply(r, [l.vals[0]]))
                return l
            if isinstance(l, (ListV, ArrayV)):
                out = []
                for x in l.items:
                    y = yield from self.apply(r, [x])
                    out.extend(y.items if isinstance(y, Seq) else [y])
                return ListV(out, len(out)) if isinstance(l, ListV) else ArrayV(out, len(out))
            raise Abort("'|>>' needs a Monad on the left")
        if op == "<$>":
            m = self.find_method_for(r, "map")
            if m is not None:
                return (yield from self.apply_method(m, r, [l]))
            if isinstance(r, EnumV) and r.et is RESULT_T:
                if r.case == "Ok":
                    return Ok((yield from self.apply(l, [r.vals[0]])))
                return r
            if isinstance(r, (ListV, ArrayV)):
                out = []
                for x in r.items:
                    out.append((yield from self.apply(l, [x])))
                return ListV(out, len(out)) if isinstance(r, ListV) else ArrayV(out, len(out))
            raise Abort("'<$>' needs a Functor on the right")
        if op == "<*>":
            m = self.find_method_for(l, "ap")
            if m is not None:
                return (yield from self.apply_method(m, l, [r]))
            if isinstance(l, EnumV) and l.et is RESULT_T:
                if l.case == "Err":
                    return l
                if r.case == "Err":
                    return r
                return Ok((yield from self.apply(l.vals[0], [r.vals[0]])))
            raise Abort("'<*>' needs an Applicative on the left")
        if op == "~>":
            return ComposeV([l, r])
        if op == "<~":
            return ComposeV([r, l])
        raise Abort(f"bad operator {op}")

    def ev_Tick(self, n, env):
        l = yield from self.ev(n.l, env)
        r = yield from self.ev(n.r, env)
        f = env.lookup(n.fname, self)
        if f is MISSING:
            raise Abort(f"undefined function '{n.fname}'", n.line)
        return (yield from self.apply(f, [l, r]))

    def ev_InOp(self, n, env):
        l = yield from self.ev(n.l, env)
        r = yield from self.ev(n.r, env)
        res = self.contains(r, l)
        return (not res) if n.neg else res

    def contains(self, coll, x):
        if isinstance(coll, RangeV):
            lo, hi = coll.start, coll.limit
            if lo is not None and x < lo:
                return False
            if hi is not None:
                if coll.incl:
                    return x <= hi
                return x < hi
            return True
        if isinstance(coll, Seq):
            return x in coll.items
        if isinstance(coll, SetV):
            return x in coll.items
        if isinstance(coll, DictV):
            return x in coll.d
        if isinstance(coll, str):
            return x in coll
        raise Abort(f"'in' does not work on {type_name(coll)}")

    def ev_IsOp(self, n, env):
        v = yield from self.ev(n.e, env)
        b = {}
        if self.pmatch(n.pat, v, b, env):
            env.vars.update(b)
            return True
        return False

    def ev_Q(self, n, env):
        v = yield from self.ev(n.e, env)
        if isinstance(v, EnumV) and v.et is RESULT_T:
            if v.case == "Ok":
                return v.vals[0]
            err = v.vals[0]
            err = self.convert_error(err, env)
            func = env.func
            if func is not None and func.is_entry and not func.closure:
                raise ProgramExit(1, "error: " + self.describe_error(err))
            raise ReturnEx(Err(err))
        raise Abort("'?' needs a Result", n.line)

    def describe_error(self, e):
        if isinstance(e, TupleV) and e.tname == "Error":
            code = e.vals[0]
            nm = ERR_NAMES.get(code, str(code))
            return f"{nm}: {e.vals[1]}"
        return display(e, self)

    def convert_error(self, err, env):
        func = env.func
        if func is None or func.ret is None:
            return err
        r = func.ret
        if isinstance(r, TName) and r.path[-1] == "Result" and r.groups and len(r.groups[0]) >= 2:
            et = r.groups[0][1]
            en = self.rtype_name(et)
            if en and type_name(err) != en and en in self.froms:
                src = type_name(err)
                for sn, clo in self.froms[en]:
                    if sn == src:
                        return self.run_sync(self.apply(clo, [err]))
        return err

    # ------------------------------------------------------------ control flow expressions
    def ev_IfE(self, n, env, hint=None):
        for cond, body in n.branches:
            c = yield from self.ev(cond, env)
            if c:
                return (yield from self.ev_body(body, env, hint))
        if n.else_ is not None:
            return (yield from self.ev_body(n.else_, env, hint))
        return UNIT

    def ev_body(self, body, env, hint=None):
        if body.__class__ is Block:
            return self.ev_Block(body, env, hint=hint)
        return self.exec_stmt(body, env, hint)

    def ev_WhenE(self, n, env, hint=None):
        if n.scrut is None:
            for arm in n.arms:
                g = arm.guard
                if isinstance(g, PH) or (isinstance(g, Name) and g.name == "_"):
                    return (yield from self.ev_body(arm.body, env, hint))
                c = yield from self.ev(g, env)
                if c:
                    return (yield from self.ev_body(arm.body, env, hint))
            raise Abort("no arm of 'when:' matched", n.line)
        v = yield from self.ev(n.scrut, env)
        for arm in n.arms:
            for p in arm.pats:
                b = {}
                if self.pmatch(p, v, b, env):
                    scope = Env(env)
                    scope.vars.update(b)
                    if arm.guard is not None:
                        g = yield from self.ev(arm.guard, scope)
                        if not g:
                            continue
                    return (yield from self.ev_body(arm.body, scope, hint))
        raise Abort(f"no arm of 'when' matched {show(v, self)}", n.line)

    def ev_DoE(self, n, env, hint=None):
        try:
            return (yield from self.ev_body(n.body, env, hint))
        except BreakEx as b:
            if n.label is not None and b.label == n.label:
                return b.value if b.value is not None else UNIT
            raise

    def ev_Block(self, n, env, hint=None, scope=True):
        e = Env(env) if scope else env
        last = UNIT
        stmts = n.stmts
        k = len(stmts) - 1
        for i, s in enumerate(stmts):
            if i == k:
                last = yield from self.exec_stmt(s, e, hint)
            else:
                yield from self.exec_stmt(s, e)
        return last

    def exec_stmts(self, stmts, e):
        last = UNIT
        for s in stmts:
            last = yield from self.exec_stmt(s, e)
        return last

    def exec_stmt(self, s, env, hint=None):
        c = s.__class__
        if hint is not None and c in (Name, Call, IfE, WhenE, Block, DoE):
            return self.evh(s, env, hint)
        if c is ExprStmt:
            return self.evh(s.e, env, hint) if hint is not None else self.ev(s.e, env)
        return self.disp[c](s, env)

    def ev_ExprStmt(self, n, env):
        return self.ev(n.e, env)

    def ev_TrailIf(self, n, env):
        c = yield from self.ev(n.cond, env)
        if c:
            yield from self.exec_stmt(n.stmt, env)
        return UNIT

    def ev_Return(self, n, env):
        v = UNIT
        if n.e is not None:
            hint = env.func.ret if env.func is not None else None
            v = yield from self.evh(n.e, env, hint)
        raise ReturnEx(v)

    def ev_Break(self, n, env):
        v = None
        if n.e is not None:
            v = yield from self.ev(n.e, env)
        raise BreakEx(n.label, v, n.daemon)
        yield

    def ev_Continue(self, n, env):
        raise ContinueEx(n.label)
        yield

    def ev_TodoE(self, n, env):
        msg = "todo"
        if n.msg is not None:
            msg = yield from self.ev(n.msg, env)
        raise Abort(f"todo: {msg}", n.line)
        yield

    # ------------------------------------------------------------ loops
    def loop_body(self, body, I):
        if body.__class__ is Block:
            return self.exec_stmts(body.stmts, I)
        return self.exec_stmt(body, I)

    def carry(self, I, L, env, skip=()):
        for k, v in I.vars.items():
            if k in skip:
                continue
            if env.lookup(k, None) is not MISSING or k in L.vars:
                L.vars[k] = v

    def ev_ForE(self, n, env):
        src = yield from self.ev(n.iter, env)
        it = self.make_iter(src)
        L = Env(env, hidden=True)
        pnames = self.pattern_names(n.pat)
        result = None
        broke = False
        while True:
            x = yield from self.iter_next(it)
            if x is END:
                break
            I = Env(L)
            b = {}
            if not self.pmatch(n.pat, x, b, env):
                raise Abort("for pattern did not match", n.line)
            I.vars.update(b)
            try:
                yield from self.loop_body(n.body, I)
            except ContinueEx as c:
                if c.label is not None and c.label != n.label:
                    raise
                self.carry(I, L, env, pnames)
                continue
            except BreakEx as br:
                if br.daemon or (br.label is not None and br.label != n.label):
                    raise
                broke = True
                result = br.value if br.value is not None else UNIT
                break
            self.carry(I, L, env, pnames)
        if broke:
            return result
        if n.else_ is not None:
            return (yield from self.ev_body(n.else_, L))
        return UNIT

    def ev_WhileE(self, n, env):
        L = Env(env, hidden=True)
        broke = False
        result = None
        while True:
            if n.cond is not None:
                c = yield from self.ev(n.cond, L)
                if not c:
                    break
            I = Env(L)
            try:
                yield from self.loop_body(n.body, I)
            except ContinueEx as c:
                if c.label is not None and c.label != n.label:
                    raise
                self.carry(I, L, env)
                continue
            except BreakEx as br:
                if br.daemon or (br.label is not None and br.label != n.label):
                    raise
                broke = True
                result = br.value if br.value is not None else UNIT
                break
            self.carry(I, L, env)
        if broke:
            return result
        if n.else_ is not None:
            return (yield from self.ev_body(n.else_, L))
        return UNIT

    def ev_DaemonE(self, n, env):
        L = Env(env, hidden=True)
        while True:
            I = Env(L)
            try:
                yield from self.loop_body(n.body, I)
            except ContinueEx as c:
                self.carry(I, L, env)
                continue
            except BreakEx as br:
                if br.daemon or br.label is None:
                    return br.value if br.value is not None else UNIT
                raise
            self.carry(I, L, env)
            yield ("tick",)

    def pattern_names(self, p):
        out = set()
        self._pnames(p, out)
        return out

    def _pnames(self, p, out):
        c = p.__class__
        if c is PBind:
            out.add(p.name)
        elif c is PAs:
            out.add(p.name)
            self._pnames(p.pat, out)
        elif c is PTuple:
            for _, q in p.items:
                self._pnames(q, out)
        elif c is PCon:
            for _, q in (p.args or []):
                self._pnames(q, out)
        elif c is PBin:
            out.update(e[1] for e in p.elems if e[0] == "field" and e[1])
        elif c is PRest:
            out.add(p.name)

    def ev_SelectE(self, n, env):
        from .sched import select_op
        try:
            return (yield from select_op(self, n, env))
        except BreakEx as br:
            if br.label is None and not br.daemon:
                return br.value if br.value is not None else UNIT
            raise

    def ev_SeqE(self, n, env):
        raise Abort("'seq:' is only valid after '|>'", n.line)
        yield

    # ------------------------------------------------------------ for: comprehension
    def ev_ForM(self, n, env):
        return (yield from self.for_m(n, 0, Env(env)))

    def for_m(self, n, i, env):
        lines = n.lines
        # find next generator
        while i < len(lines) and lines[i][0] in ("=", "if"):
            kind, pat, ex, el = lines[i]
            if kind == "=":
                v = yield from self.ev(ex, env)
                b = {}
                if not self.pmatch(pat, v, b, env):
                    if el is not None:
                        return (yield from self.ev_body(el, env))
                    raise Abort("pattern did not match in for:", n.line)
                env.vars.update(b)
            else:
                c = yield from self.ev(ex, env)
                if not c:
                    return UNIT
            i += 1
        if i >= len(lines):
            return (yield from self.ev_body(n.yield_, env))
        kind, pat, ex, el = lines[i]
        m = yield from self.ev(ex, env)
        last = not any(l[0] == "in" for l in lines[i + 1:])
        if isinstance(m, EnumV) and m.et is RESULT_T:
            if m.case == "Err":
                return m
            x = m.vals[0]
            env2 = Env(env)
            b = {}
            if not self.pmatch(pat, x, b, env2):
                if el is not None:
                    return (yield from self.ev_body(el, env2))
                raise Abort("pattern did not match in for:", n.line)
            env2.vars.update(b)
            r = yield from self.for_m(n, i + 1, env2)
            if last:
                return Ok(r)
            return r

        def k(I, args, kw, targs=None):
            x = args[0]
            env2 = Env(env)
            b = {}
            if not self.pmatch(pat, x, b, env2):
                raise Abort("pattern did not match in for:", n.line)
            env2.vars.update(b)
            r = yield from self.for_m(n, i + 1, env2)
            return r
        kb = Builtin(k, "<for>", gen=True)
        meth = "map" if last else "flat_map"
        f = self.find_method_for(m, meth)
        if f is not None:
            return (yield from self.apply_method(f, m, [kb]))
        bf = self.prelude.lookup(meth)
        return (yield from self.apply(bf, [m, kb]))

    # ------------------------------------------------------------ receiver blocks
    def ev_DoRecv(self, n, env):
        recv = yield from self.ev(n.recv, env)
        if n.kind == "do":
            renv = Env(env)
            renv.recv = RecvCell(recv, False)
            renv.vars["self"] = recv
            return (yield from self.ev_body(n.body, renv))
        return (yield from self.update_value(recv, n.body, env))

    def update_value(self, recv, lines, env):
        renv = Env(env)
        renv.recv = RecvCell(recv, False)
        cur = recv
        for ln in lines:
            if ln.nested is not None:
                sub = self.field_get(recv, ln.name)
                nv = yield from self.update_value(sub, ln.nested, renv)
            else:
                nv = yield from self.ev(ln.expr, renv)
            cur = yield from self.field_set(cur, ln.name, nv)
        return cur

    # ------------------------------------------------------------ misc
    def ev_RunE(self, n, env):
        from .sched import run_op
        return (yield from run_op(self, n, env))

    def ev_Ref(self, n, env):
        return self.ev(n.e, env)

    def ev_Move(self, n, env):
        return self.ev(n.e, env)

    def ev_Deref(self, n, env):
        v = yield from self.ev(n.e, env)
        if hasattr(v, "atom_value"):
            return v.atom_value
        if hasattr(v, "snapshot"):
            return v.snapshot()
        raise Abort("'@' needs an Atom", n.line)

    def ev_Lambda(self, n, env):
        return Done(self.make_closure(n, env, None))

    def ev_SqlE(self, n, env):
        from .sqlrt import sql_op
        return (yield from sql_op(self, n, env))


def Byte_(v):
    return INT_CLASSES["Byte"](v)
