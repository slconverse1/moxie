"""Refinements in the checker (Spec 9c): `fn get(xs List[T], i Int where i >= 0 and i < len(xs)) T`.

A parameter's `where` is a condition over integer terms that the compiler proves at every call.  What it can use as facts:
the enclosing function's own `where` clauses, the branch of an `if`/`elif`/`else` it is in, what an early exit rules out,
the range of a `for i in a..b` variable, a name bound once to a linear expression, constants, and bounded integer types.
It proves with the small solver in `refine.py` (linear integer arithmetic, `and`, `or`, `not`, `len`), so an answer of "yes"
is true, "no" means the condition can never hold there (an error), and "unknown" is also an error, with advice to guard the call.
"""
from . import refine as R
from .ast import *
from .tys import *   # noqa
INTS = {"Int", "Int8", "Int16", "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64"}


class RefineMixin:
    # ------------------------------------------------------------ linear terms
    def rf_int_ty(self, t):
        t = self.base(t) if t is not None else None
        return t.__class__ is str and t in INTS or (t.__class__ is tuple and t[0] == "bounded")

    def rf_stable(self, name):
        return name not in self.unstable_names(False)

    def rf_path(self, e, sc, subst):
        """A stable name or field path as text, or None."""
        if e.__class__ is Name:
            if subst is not None:
                return subst.get(("path", e.name))
            v = sc.find(e.name)
            return e.name if v is not None and self.rf_stable(e.name) else None
        if e.__class__ is Field and isinstance(e.name, str):
            b = self.rf_path(e.obj, sc, subst)
            return None if b is None else b + "." + e.name
        return None

    def rf_fresh(self):
        self._rf_n = getattr(self, "_rf_n", 0) + 1
        return R.atom(("fresh", self._rf_n))

    def rf_lin(self, e, sc, subst=None):
        c = e.__class__
        if c is IntLit:
            return R.const(e.v)
        if c is Name:
            if subst is not None:
                v = subst.get(("v", e.name))
                if v is not None:
                    return v
                k = self.consts.get(e.name)
                return R.const(k) if isinstance(k, int) and not isinstance(k, bool) else None
            v = sc.find(e.name)
            if v is None:
                k = self.consts.get(e.name)
                return R.const(k) if isinstance(k, int) and not isinstance(k, bool) else None
            if self.rf_stable(e.name) and (self.rf_int_ty(v.ty) or id(v) in getattr(self, 'rf_intvars', ())):
                return R.atom(e.name)
            return None
        if c is Field:
            p = self.rf_path(e, sc, subst)
            if p is not None and subst is None and self.rf_int_ty(self.quick_ty(e, sc)):
                return R.atom(p)
            return None
        if c is Unary and e.op == "-":
            x = self.rf_lin(e.e, sc, subst)
            return R.scale(x, -1) if x is not None else None
        if c is Binary and e.op in ("+", "-", "*"):
            a, b = self.rf_lin(e.l, sc, subst), self.rf_lin(e.r, sc, subst)
            if a is None or b is None:
                return None
            if e.op == "+":
                return R.add(a, b)
            if e.op == "-":
                return R.sub(a, b)
            if R.is_const(a):
                return R.scale(b, a[1])
            if R.is_const(b):
                return R.scale(a, b[1])
            return None
        if c is Call and e.fn.__class__ is Name and e.fn.name == "len" and "len" not in self.fns and len(e.args or []) == 1 \
                and not e.args[0].label and not getattr(e.args[0], "mod", None):
            return self.rf_len(e.args[0].expr, sc, subst)
        return None

    def rf_len(self, arg, sc, subst):
        if subst is not None and arg.__class__ is Name:
            return subst.get(("len", arg.name))
        p = self.rf_path(arg, sc, subst)
        if p is not None:
            return R.atom(("len", p))
        return None

    # ------------------------------------------------------------ formulas
    CMP = ("<", ">", "<=", ">=", "==", "~=")

    def rf_formula(self, e, sc, subst=None, weak=False):
        """The condition as a formula, or None when some part is not linear integer arithmetic.  With `weak`, an `and` keeps
        the parts it understands (right for a fact: knowing less is safe); otherwise every part must be understood."""
        c = e.__class__
        if c is BoolLit:
            return R.TRUE if e.b else R.FALSE
        if c is Unary and e.op in ("not", "!"):
            f = self.rf_formula(e.e, sc, subst, False)
            return R.neg(f) if f is not None else None
        if c is AndE or c is OrE:
            a, b = self.rf_formula(e.l, sc, subst, weak), self.rf_formula(e.r, sc, subst, weak)
            if c is AndE:
                if weak:
                    return R.conj(*[x for x in (a, b) if x is not None]) if (a is not None or b is not None) else None
                return R.conj(a, b) if a is not None and b is not None else None
            return R.disj(a, b) if a is not None and b is not None else None
        if c is Binary and e.op in self.CMP:
            a, b = self.rf_lin(e.l, sc, subst), self.rf_lin(e.r, sc, subst)
            if a is None or b is None:
                return None
            return R.compare(e.op, a, b)
        return None

    # ------------------------------------------------------------ facts
    def rf_forget(self, name):
        """A name is bound again: every fact that mentions the old one stops holding (it becomes TRUE, so the stack keeps its shape)."""
        def mentions(f):
            if f[0] in ("ge", "eq"):
                for a in f[1][0]:
                    p = a[1] if a.__class__ is tuple and a and a[0] == "len" else a
                    if p.__class__ is str and (p == name or p.startswith(name + ".")):
                        return True
                return False
            return any(mentions(g) for g in f[1])
        fs = getattr(self, "ifacts", None)
        if fs:
            for i, f in enumerate(fs):
                if mentions(f):
                    fs[i] = R.TRUE

    def rf_push(self, f):
        if f is not None:
            self.ifacts.append(f)

    def rf_enter_fn(self, fd, sc):
        """The facts a function body starts with: its parameters' `where` clauses and the ranges of bounded integers."""
        self.ifacts = []
        for p in fd.params or []:
            if p.name and p.type is not None:
                t = self.ty_of_type(p.type)
                b = t
                if b.__class__ is tuple and b[0] == "bounded" and p.mod != "ref" and self.rf_stable(p.name):
                    a = R.atom(p.name)
                    self.rf_push(R.compare(">=", a, R.const(b[1])))
                    self.rf_push(R.compare("<=", a, R.const(b[2])))
            if getattr(p, "where", None) is not None and p.mod != "ref":
                self.rf_push(self.rf_formula(p.where, sc, None, True))

    def rf_if_branches(self, n, sc):
        """For each branch of an `if`, the formulas that hold inside it (the earlier tests false, this one true), then the `else`'s."""
        out, acc = [], []
        for cond, _body in n.branches:
            f = self.rf_formula(cond, sc, None, True)
            out.append(acc + ([f] if f is not None else []))
            g = self.rf_formula(cond, sc, None, False)
            if g is not None:
                acc = acc + [R.neg(g)]
        out.append(acc)
        return out

    def rf_fall(self, st, sc):
        """The formula that holds after an early-exit statement for the rest of its block, or None."""
        if st.__class__ is ExprStmt:
            st = st.e

        def leaves(x):
            if x is None:
                return False
            if x.__class__ is Block:
                return self.diverges(x.stmts or [])
            if x.__class__ is ExprStmt:
                x = x.e
            return x.__class__ in (Return, Break, Continue, TodoE)
        if st.__class__ is TrailIf:
            if not leaves(st.stmt):
                return None
            g = self.rf_formula(st.cond, sc, None, False)
            return R.neg(g) if g is not None else None
        if st.__class__ is IfE:
            arms, acc = [], []
            for cond, body in st.branches:
                f = self.rf_formula(cond, sc, None, True)
                if not leaves(body):
                    arms.append(R.conj(*(acc + ([f] if f is not None else []))))
                g = self.rf_formula(cond, sc, None, False)
                if g is not None:
                    acc = acc + [R.neg(g)]
            if st.else_ is None or not leaves(st.else_):
                arms.append(R.conj(*acc))
            if arms and len(arms) < len(st.branches) + 1:
                return R.disj(*arms)
        return None

    def rf_loop_facts(self, n, sc):
        """`for i in a..b`: i is at least a and below b (at most b for `..=`), when both ends are linear and the range counts up."""
        it = n.iter
        if it.__class__ is not RangeE or n.pat.__class__ is not PBind or it.lo is None or it.hi is None:
            return None
        lo, hi = self.rf_lin(it.lo, sc), self.rf_lin(it.hi, sc)
        if lo is None or hi is None:
            return None
        if it.lo.__class__ is IntLit and it.hi.__class__ is IntLit and it.lo.v > it.hi.v:
            return None                               # written backwards: it counts down
        i = R.atom(n.pat.name)
        return R.conj(R.compare(">=", i, lo), R.compare("<=" if it.incl else "<", i, hi))

    def rf_bind_fact(self, n, sc):
        """`m = len(xs) - 1` binds a name once to a linear expression: the name equals it."""
        t = n.targets
        if n.op != "=" or n.ann is not None or t.__class__ is not PBind or isinstance(n.targets, list):
            return None
        if not self.rf_stable(t.name):
            return None
        lin = self.rf_lin(n.value, sc)
        if lin is None or t.name in {a for a in lin[0] if a.__class__ is str}:
            return None
        return R.compare("==", R.atom(t.name), lin)

    # ------------------------------------------------------------ values entering a refined alias
    def e_Refine(self, n, sc):
        """`x Pos = v`: the parser put the alias's condition after the binding.  The condition has to follow from `v` and the facts here."""
        prev = getattr(self, "rf_prev_stmt", None)
        if prev is None or prev.__class__ is not Assign or prev.targets.__class__ is not PBind or prev.targets.name != n.name:
            return None, None
        expr = prev.value
        fact = self.rf_formula(n.cond, sc, None, True)
        if expr.__class__ is Call and expr.fn.__class__ is Name and sc.find(expr.fn.name) is None:
            cl = self.fns.get(expr.fn.name) or []
            rt = cl[0].ret if len(cl) == 1 else None
            if rt.__class__ is TName and rt.path == [n.alias]:
                if fact is not None:
                    self.rf_push(fact)                    # a function that returns the alias has already promised it
                return None, None
        lin = self.rf_lin(expr, sc)
        path = self.rf_path(expr, sc, None)
        subst = {("v", n.name): lin if lin is not None else self.rf_fresh(), ("path", n.name): path,
                 ("len", n.name): R.atom(("len", path)) if path is not None else self.rf_fresh()}
        goal = self.rf_formula(n.cond, None, subst, False)
        if goal is None:
            return None, None                             # not linear integer arithmetic: left to the run-time check
        r = R.proves(list(self.ifacts), goal)
        line = n.line or self.cur_line
        if r == "yes" and fact is not None:
            self.rf_push(fact)                            # from here on the name is known to meet the condition
        if r == "no":
            self.err(line, f"`{n.name}` must satisfy `{n.text}`, but the value given can never satisfy it")
        elif r == "unknown":
            self.err(line, f"can't prove `{n.text}` for `{n.name}`: check it first (`if ... then`), or give the enclosing function the same `where`")
        return None, None

    # ------------------------------------------------------------ calls
    def rf_callee(self, n, sc, extra):
        """(FnDecl, receiver expression or None, has a receiver) for a call whose callee declares refinements."""
        f = n.fn
        if f.__class__ is Name:
            if sc.find(f.name) is not None:
                return None
            cl = self.fns.get(f.name) or []
            if len(cl) == 1 and any(getattr(p, "where", None) is not None for p in cl[0].params or []):
                return cl[0], None, bool(extra)
            return None
        if f.__class__ is Field:
            m = None
            rt = self.base(self.quick_ty(f.obj, sc))
            if rt.__class__ is tuple and rt[0] in ("named", "app"):
                m = self.methods.get((rt[1], f.name))
            if m is None:
                cl = self.fns.get(f.name) or []
                m = cl[0] if len(cl) == 1 else None
            if m is not None and any(getattr(p, "where", None) is not None for p in m.params or []):
                return m, f.obj, True
        return None

    def rf_check_call(self, n, sc, extra):
        found = self.rf_callee(n, sc, extra)
        if found is None:
            return
        fd, recv, has_recv = found
        args = list(n.args or [])
        if any(getattr(a, "mod", None) == "spread" or a.expr.__class__ in (PH, Slot) for a in args) or n.trailing is not None:
            return
        params = [p for p in fd.params or []]
        if any(p.variadic for p in params):
            return
        supplied = {}
        k = 0
        if has_recv and params:
            supplied[params[0].name] = ("recv", recv)
            k = 1
        for a in args:
            if a.label is not None:
                supplied[a.label] = ("arg", a.expr)
            else:
                if k >= len(params):
                    return
                supplied[params[k].name] = ("arg", a.expr)
                k += 1
        subst = {}
        for p in params:
            if not p.name:
                continue
            src = supplied.get(p.name)
            expr = None
            if src is not None:
                expr = src[1]
            elif p.default is not None:
                expr = p.default
            lin = self.rf_lin(expr, sc) if expr is not None else None
            subst[("v", p.name)] = lin if lin is not None else self.rf_fresh()
            path = self.rf_path(expr, sc, None) if expr is not None else None
            subst[("path", p.name)] = path
            ln = None
            if expr is not None:
                if expr.__class__ is Call and expr.fn.__class__ is Name and expr.fn.name == "List" and "List" not in self.fns \
                        and not any(getattr(x, "mod", None) or getattr(x, "spread", None) or x.expr.__class__ is CompE for x in expr.args or []):
                    ln = R.const(len(expr.args or []))
                elif path is not None:
                    ln = R.atom(("len", path))
            subst[("len", p.name)] = ln if ln is not None else self.rf_fresh()
        facts = list(self.ifacts)
        for p in params:
            w = getattr(p, "where", None)
            if w is None:
                continue
            goal = self.rf_formula(w, None, subst, False)
            if goal is None:
                continue                                   # not linear integer arithmetic: left to the run-time check
            r = R.proves(facts, goal)
            text = getattr(p, "wtext", None) or "the condition"
            line = getattr(n, "line", 0) or self.cur_line
            if r == "no":
                self.err(line, f"`{fd.name}` needs `{text}` for `{p.name}`, but here it can never be true")
            elif r == "unknown":
                self.err(line, f"can't prove `{text}` for the call to `{fd.name}`: check it first (`if ... then {fd.name}(...)`), "
                               f"or give this function the same `where`")
