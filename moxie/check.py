"""Core static checks: a conservative pass over the AST (no execution).

Reports, never guessing: mismatched types, undefined names, wrong argument counts,
`ref` mismatches, non-exhaustive `when`, use-after-move, and bounded-integer misuse.
Anything the checker cannot type is "unknown" and never produces an error.
"""
from .ast import *   # noqa

INTS = {"Int", "Int8", "Int16", "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64", "BigInt"}
RES_TYPES = {"ChanR", "ChanW", "Timer", "Connection"}
RES_MAKERS = {"Chan", "Timer", "clone"}
EXTRA_NAMES = {"Ok", "Err", "self", "Self", "args", "env", "Int", "Int8", "Int16", "Int32", "Int64",
               "UInt8", "UInt16", "UInt32", "UInt64", "BigInt", "Double", "Float", "String", "Bool",
               "Char", "Unit", "Decimal", "Keyword", "Duration", "Error", "Atom", "ChanR", "ChanW",
               "Locale", "Connection", "true", "false"}


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
    return "?"


def fields_of(n):
    return n._fields


class Checker:
    def __init__(self, prelude_names):
        self.diags = []
        self.prelude = set(prelude_names) | EXTRA_NAMES
        self.tuples, self.enums, self.fns, self.aliases = {}, {}, {}, {}
        self.cases = {}            # bare case name -> [enum names]
        self.globals = set()
        self.moved = {}            # Var -> line
        self.loop_depth = 0
        self.exit_ctx = False
        self.fn_ret = None
        self.fn_tparams = ()
        self.impls = {}            # type name -> {interface names}
        self.ifaces = set()

    # ------------------------------------------------------------ reporting
    def err(self, line, msg):
        if any(d.line == line and d.msg == msg for d in self.diags):
            return
        self.diags.append(Diag(line, msg))

    # ------------------------------------------------------------ entry
    def check(self, prog):
        for st in prog.stmts:
            self.collect(st)
        top = Sc()
        for st in prog.stmts:
            self.ev(st, top)
        return self.diags

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
        elif c is AliasDecl:
            self.aliases[st.name] = st
            self.globals.add(st.name)
        elif c is IfaceDecl:
            self.globals.add(st.name)
            self.ifaces.add(st.name)
        elif c is ImplDecl:
            iname, tname = _tn(st.iface), _tn(st.target)
            if iname == "Hashable":
                self.err(st.line, "`Hashable` can only be derived: write `deriving eq, hash` in the header of `%s`" % tname)
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
        if c is Binary and e.op in ("+", "-", "*"):
            a, b = self.const_int(e.l), self.const_int(e.r)
            if a is None or b is None:
                return None
            return a + b if e.op == "+" else a - b if e.op == "-" else a * b
        return None

    def ty_of_type(self, t, depth=0):
        if t is None or depth > 8:
            return None
        c = t.__class__
        if c is TUnit:
            return "Unit"
        if c is TStatic:
            return self.ty_of_type(t.inner, depth + 1)
        if c is not TName or len(t.path) != 1:
            return None
        n = t.path[0]
        if n in self.fn_tparams:
            return None
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
        elif c is PTyped:
            self.pat_names(p.pat, out)
        return out

    def bind_pat(self, p, sc, ty=None, res=False):
        names = self.pat_names(p)
        for nm in names:
            sc.vars[nm] = Var(ty if p.__class__ is PBind else None, res, self.loop_depth)

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

    def e_FloatLit(self, n, sc):
        return "Float", None

    def e_DecLit(self, n, sc):
        return "Decimal", None

    def e_StrLit(self, n, sc):
        for p in n.parts or []:
            if hasattr(p, "_fields"):
                self.ev(p, sc)
        return "String", None

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
        if n.name in self.globals or n.name in self.prelude or sc.open:
            return None, None
        self.err(n.line, f"undefined name `{n.name}`")
        return None, None

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
        if op in ("==", "!=", "<", ">", "<=", ">="):
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

    def e_Q(self, n, sc):
        self.ev(n.e, sc)
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

    def e_Field(self, n, sc):
        t = self.t(n.obj, sc)
        if t.__class__ is tuple and t[0] == "named" and t[1] in self.tuples:
            for f in self.tuples[t[1]].fields or []:
                if f.name == n.name:
                    return self.ty_of_type(f.type), None
        return None, None

    def e_Lambda(self, n, sc):
        inner = Sc(sc, open_=not n.params)
        for p in n.params or []:
            if p.name:
                inner.vars[p.name] = Var(self.ty_of_type(p.type), False, self.loop_depth)
            if p.pat is not None:
                self.bind_pat(p.pat, inner)
        for nm in n.locals or []:
            inner.vars[nm] = Var(None, False, self.loop_depth)
        saved = (self.fn_ret, self.loop_depth, self.exit_ctx)
        self.fn_ret = None
        self.exit_ctx = False
        self.ev(n.body, inner)
        self.fn_ret, self.loop_depth, self.exit_ctx = saved
        return None, None

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
        if self.fn_ret is not None and n.e is not None:
            self.compat(self.fn_ret, t, c, n.line)
        return None, None

    def e_Break(self, n, sc):
        self.ev(n.e, sc)
        return None, None

    def is_resource_expr(self, e):
        while e.__class__ in (Q, Move):
            e = e.e
        if e.__class__ is Call:
            f = e.fn
            if f.__class__ is GenApp:
                f = f.base
            if f.__class__ is Name and f.name in RES_MAKERS:
                return True
            if f.__class__ is Field and f.obj.__class__ is Name and f.obj.name == "Connection":
                return True
        return False

    def e_Assign(self, n, sc):
        t, c = self.ev(n.value, sc)
        ann = self.ty_of_type(n.ann) if n.ann is not None else None
        if n.ann is not None and n.op == "=":
            self.compat(ann, t, c, n.line)
            if ann is not None and ann.__class__ is tuple and ann[0] == "bounded" and n.value.__class__ is IntLit:
                pass
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
            elif tgt.__class__ is PPlace:
                self.ev(tgt.expr, sc)
            else:
                self.bind_pat(tgt, sc, None, res)
        return None, None

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
                if node.__class__ is Move and node.e.__class__ is Name:
                    v = sc.find(node.e.name)
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

    def e_DaemonE(self, n, sc):
        self.loop([n.body], sc)
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
    def e_Call(self, n, sc, extra=0):
        fn = n.fn
        args = n.args or []
        # evaluate arguments
        ats = []
        indexing = fn.__class__ is not Name or sc.find(fn.name) is not None
        asc = Sc(sc, open_=True) if indexing else sc
        for a in args:
            ats.append(self.ev(a.expr, asc) if hasattr(a, "expr") else (None, None))
        if n.trailing is not None:
            self.ev(n.trailing, sc)
        if fn.__class__ is Name:
            v = sc.find(fn.name)
            if v is None:
                if fn.name not in self.globals and fn.name not in self.prelude and not sc.open:
                    self.err(n.line, f"undefined function `{fn.name}`")
                    return None, None
                return self.call_known(n, fn.name, args, ats, extra)
            elif v in self.moved:
                self.err(n.line, f"use of moved value `{fn.name}`")
            return None, None
        self.ev(fn, sc)
        return None, None

    def call_known(self, n, name, args, ats, extra):
        if name in self.tuples:
            td = self.tuples[name]
            if not td.tparams:
                self.check_tuple_args(td, args, ats, n.line)
            return ("named", name), None
        if name in self.fns and len(self.fns[name]) == 1:
            fd = self.fns[name][0]
            if fd.tparams or fd.alias is not None:
                if fd.tparams:
                    self.check_bounds(fd, n, args, ats)
                return None, None
            return self.check_call(fd, n, args, ats, extra)
        return None, None

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
                if pt is None or _tn(pt) != tp.name or getattr(pt, "groups", None):
                    continue
                for b in tp.bounds:
                    iface = _tn(b)
                    if self.implements(t, iface) is False:
                        tyname = t if isinstance(t, str) else t[1]
                        self.err(n.line, f"`{tyname}` doesn't implement `{iface}`, which `{fd.name}` requires of `{tp.name}`")

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

    def check_call(self, fd, n, args, ats, extra):
        params = list(fd.params or [])
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
        self.ev(n.l, sc)
        st = n.stage
        if st.__class__ is Call:
            return self.e_Call(st, sc, extra=1)
        self.ev(st, sc)
        return None, None

    # ------------------------------------------------------------ declarations
    def e_FnDecl(self, n, sc):
        inner = Sc(sc)
        saved = (self.fn_ret, self.fn_tparams, self.loop_depth, self.exit_ctx, self.moved)
        self.fn_tparams = tuple(t.name for t in (n.tparams or []))
        self.loop_depth, self.exit_ctx, self.moved = 0, False, {}
        for tp in n.tparams or []:
            inner.vars[tp.name] = Var(None, False, 0)
        for p in n.params or []:
            res = p.type.__class__ is TName and p.type.path[-1] in RES_TYPES
            if p.name:
                inner.vars[p.name] = Var(self.ty_of_type(p.type), res, 0)
            if p.pat is not None:
                self.bind_pat(p.pat, inner)
            self.ev(p.default, inner)
        for nm in n.locals or []:
            inner.vars[nm] = Var(None, False, 0)
        self.fn_ret = self.ty_of_type(n.ret) if n.ret is not None else None
        if n.alias is not None:
            self.ev(n.alias, inner)
        elif n.body is not None:
            if n.guard is not None:
                self.ev(n.guard, inner)
            t, c = self.ev(n.body, inner)
            self.check_tail(n.body, inner)
            if "tailrec" in (n.flags or ()):
                self.check_tailrec(n)
        self.fn_ret, self.fn_tparams, self.loop_depth, self.exit_ctx, self.moved = saved
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
            self.compat(self.fn_ret, t, c, e.line)

    def tails(self, e):
        c = e.__class__
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
        if c in (IntLit, FloatLit, StrLit, BoolLit, CharLit):
            return [e]
        return []

    def quiet(self, e, sc):
        n = len(self.diags)
        r = self.ev(e, sc) if e.__class__ in (IntLit, FloatLit, StrLit, BoolLit, CharLit) else (None, None)
        del self.diags[n:]
        return r

    def e_FnGroup(self, n, sc):
        for c in n.clauses or []:
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

    def e_ImplDecl(self, n, sc):
        for m in n.members or []:
            if n.iface is not None and m.__class__ is FnDecl and m.contracts:
                self.err(m.line, f"an impl of an interface may not add contracts to '{m.name}'; "
                                 "the contract belongs to the interface")
            inner = Sc(sc, open_=True)
            self.ev(m, inner)
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
        return None, None

    def e_TestDecl(self, n, sc):
        self.ev(n.body, Sc(sc))
        return None, None

    def e_InitDecl(self, n, sc):
        self.ev(n.body, Sc(sc))
        return None, None

    def e_GenApp(self, n, sc):
        self.ev(n.base, sc)
        return None, None

    def e_Arg(self, n, sc):
        return self.ev(n.expr, sc)

    def e_TupleE(self, n, sc):
        for it in n.items or []:
            self.ev(it[1] if isinstance(it, tuple) and len(it) > 1 else it, sc)
        return None, None

    def e_PathE(self, n, sc):
        return None, None

    def e_Deref(self, n, sc):
        self.ev(n.e, sc)
        return None, None


def check_program(prog, prelude_names):
    diags = Checker(prelude_names).check(prog)
    from .effects import check_effects
    seen = {(d.line, d.msg) for d in diags}
    for line, msg in check_effects(prog):
        if (line, msg) not in seen:
            diags.append(Diag(line, msg))
    return diags
