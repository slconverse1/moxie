"""Calls, argument binding, indexing and field access (mixin)."""
from .ast import *   # noqa
from .values import *   # noqa
from .core import *   # noqa
from .types_ import *   # noqa
from . import heap


class _Sentinel:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return self.n


SLOT = _Sentinel("&")
USING = _Sentinel("using")
NOPIPE = _Sentinel("nopipe")
END = _Sentinel("END")


class LazyV:
    __slots__ = ("expr", "env")

    def __init__(self, expr, env):
        self.expr = expr
        self.env = env


class RecvCell:
    __slots__ = ("value", "ref")

    def __init__(self, value, ref=False):
        self.value = value
        self.ref = ref


class GenV:
    __slots__ = ("base", "targs")

    def __init__(self, base, targs):
        self.base = base
        self.targs = targs


class CaseV:
    """Enum case constructor with a payload."""
    __slots__ = ("et", "ci")

    def __init__(self, et, ci):
        self.et = et
        self.ci = ci


class CallsMixin:
    # ------------------------------------------------------------ closures
    def free_names(self, node):
        key = id(node)
        r = self.free_cache.get(key)
        if r is not None:
            return r
        out = set()
        self._walk_names(node, out)
        self.free_cache[key] = (out, node)
        return (out, node)

    def _walk_names(self, n, out):
        if isinstance(n, Name):
            out.add(n.name)
        elif isinstance(n, Gimme):
            out.add(n.name)
        if isinstance(n, N):
            for f in n._fields:
                self._walk_names(getattr(n, f, None), out)
        elif isinstance(n, (list, tuple)):
            for x in n:
                self._walk_names(x, out)

    def make_closure(self, node, env, name):
        mod = env.mod
        if env is mod:
            c = Closure(node, env, name)
            return c
        fv, _ = self.free_names(node)
        snap = Env(mod)
        snap.func = env.func
        e = env
        while e is not None and e is not mod:
            if e.vars:
                for k in fv:
                    if k in e.vars and k not in snap.vars:
                        snap.vars[k] = e.vars[k]
            if e.recv is not None and snap.recv is None:
                snap.recv = RecvCell(e.recv.value, False)
            if e.usings:
                if snap.usings is None:
                    snap.usings = {}
                for k, v in e.usings.items():
                    snap.usings.setdefault(k, v)
            e = e.parent
        c = Closure(node, snap, name)
        if name and isinstance(node, (FnDecl, FnGroup)):
            snap.vars[name] = c
        return c

    # ------------------------------------------------------------ receiver members
    def recv_member(self, cell, name):
        v = cell.value
        if name == "self":
            return v
        if v.__class__ is TupleV:
            if v.names and name in v.names:
                x = v.vals[v.names.index(name)]
                if v.tname and v.tname in self.tuples and name in self.tuples[v.tname].delegates:
                    return self.delegate_get_sync(x)
                return x
        elif v.__class__ is EnumV:
            if v.names and name in v.names:
                return v.vals[v.names.index(name)]
        ms = self.methods_of(v, name)
        if ms:
            return self.bind_method(ms[0], v)
        return MISSING

    def bind_method(self, c, selfv):
        b = Closure(c.node, c.env, c.name)
        b.bound = selfv
        b.impl = c.impl
        b.owner = c.owner
        b.iface_contracts = c.iface_contracts
        return b

    def methods_of(self, v, name):
        tn = type_name(v)
        d = self.impls.get(tn)
        if d is not None:
            r = d.get(name)
            if r:
                return r
        if v.__class__ is str or v.__class__ is Char:
            pass
        return None

    def find_method_for(self, v, name):
        ms = self.methods_of(v, name)
        if ms:
            return ms[0]
        return None

    def find_op(self, op, l, r):
        tn = type_name(l)
        d = self.impls.get(tn)
        if d is not None:
            ms = d.get(op)
            if ms:
                return self.pick_overload(ms, [r])
        if l.__class__ in (int, float, bool, str) or isinstance(l, FixedInt):
            tn2 = type_name(r)
            # extension on the left operand's type
            d = self.impls.get(tn)
            if d is not None:
                ms = d.get(op)
                if ms:
                    return self.pick_overload(ms, [r])
        return None

    def pick_overload(self, ms, args):
        if len(ms) == 1:
            return ms[0]
        for c in ms:
            node = c.node
            ps = node.params if isinstance(node, FnDecl) else None
            if ps is None:
                continue
            ok = True
            for p, a in zip(ps, args):
                if p.type is not None and not self.type_matches(a, p.type, c.env):
                    ok = False
                    break
            if ok:
                return c
        return ms[0]

    def apply_method(self, c, selfv, args, named=None):
        if isinstance(c, Closure):
            return self.apply(self.bind_method(c, selfv), list(args), named)
        return self.apply(c, [selfv] + list(args), named)

    # ------------------------------------------------------------ enum cases
    def resolve_case(self, name, hint=None):
        if name == "Ok" or name == "Err":
            return (RESULT_T, RESULT_T.cases[name])
        lst = self.cases.get(name)
        if not lst:
            return None
        if hint is not None:
            hn = self.rtype_name(hint) if isinstance(hint, (TName,)) else None
            if hn:
                for et in lst:
                    if et.name == hn:
                        return (et, et.cases[name])
        et = lst[-1] if len(lst) == 1 else lst[0]
        return (et, et.cases[name])

    def enum_instance(self, et, ci, vals):
        v = EnumV(et, ci.name, vals, list(ci.fields) if ci.fields else None)
        return v

    # ------------------------------------------------------------ call evaluation
    def ev_GenApp(self, n, env):
        base = yield from self.ev(n.base, env)
        return GenV(base, n.groups)

    def ev_Field(self, n, env):
        obj = yield from self.ev(n.obj, env)
        return self.field_get(obj, n.name, n.line)

    def ev_Pipe(self, n, env):
        v = yield from self.ev(n.l, env)
        st = n.stage
        c = st.__class__
        if c is SeqE:
            for pred, stage in st.arms:
                pf = yield from self.ev(pred, env)
                ok = yield from self.apply(pf, [v])
                if ok:
                    if stage.__class__ is Call:
                        v = yield from self.ev_Call(stage, env, piped=v)
                    else:
                        f = yield from self.ev(stage, env)
                        v = yield from self.apply(f, [v])
            return v
        if c is Call:
            return (yield from self.ev_Call(st, env, piped=v))
        f = yield from self.ev(st, env)
        return (yield from self.apply(f, [v]))

    def comp_items(self, c, env):
        """Elements produced by a container comprehension: `elem for pat in iter if cond`."""
        from .streams import make_iter
        src = yield from self.ev(c.iter, env)
        it = make_iter(self, src)
        out = []
        while True:
            x = yield from it.nxt()
            if x is END:
                break
            e = env.child()
            b = {}
            if not self.pmatch(c.pat, x, b, e):
                continue
            e.vars.update(b)
            if c.cond is not None:
                ok = yield from self.ev(c.cond, e)
                if not ok:
                    continue
            v = yield from self.ev(c.elem, e)
            if c.key is not None:
                k = yield from self.ev(c.key, e)
                v = TupleV([k, v])
            out.append(v)
        return out

    def eval_args(self, n, env, params, hint_params=None):
        pos = []
        named = {}
        refspec = {}
        spreads = []
        trailing = n.trailing
        for i, a in enumerate(n.args):
            mod = a.mod
            if mod == "using" and a.expr is None:
                pos.append(USING)
                continue
            if mod == "spread":
                if a.expr is None:
                    cell = self.find_recv(env)
                    sv = cell.value if cell is not None else None
                else:
                    sv = yield from self.ev(a.expr, env)
                spreads.append((len(pos), sv))
                continue
            if mod == "comp":
                items = yield from self.comp_items(a.expr, env)
                pos.extend(items)
                continue
            lab = a.label
            if isinstance(lab, tuple):
                lab = lab[1]
            idx = len(pos)
            ptype = None
            if params is not None:
                if lab is None:
                    if idx < len(params):
                        p = params[idx]
                        ptype = p.type
                        if p.mod == "lazy":
                            pos.append(LazyV(a.expr, env))
                            continue
                else:
                    for p in params:
                        if p.name == lab:
                            ptype = p.type
                            if p.mod == "lazy":
                                named[lab] = LazyV(a.expr, env)
                            break
                    if lab in named:
                        continue
            if mod == "ref":
                if not isinstance(a.expr, Name):
                    raise Abort("the argument after 'ref' must be a name", a.line)
                v = yield from self.ev(a.expr, env)
                refspec[idx if lab is None else lab] = a.expr.name
            else:
                if ptype is not None:
                    v = yield from self.evh(a.expr, env, ptype)
                else:
                    v = yield from self.ev(a.expr, env)
            if lab is None:
                pos.append(v)
            else:
                named[lab] = v
        if trailing is not None:
            lam = yield from self.ev(trailing, env)
            pos.append(lam)
        return pos, named, refspec, spreads

    def find_recv(self, env):
        e = env
        while e is not None:
            if e.recv is not None:
                return e.recv
            e = e.parent
        return None

    def ev_Call(self, n, env, piped=NOPIPE, hint=None, defer=False):
        fnn = n.fn
        c = fnn.__class__
        selfv = None
        has_self = False
        targs = None
        callee = None
        if c is Name:
            callee = env.lookup(fnn.name, self)
            if callee is MISSING:
                cs = self.resolve_case(fnn.name, hint)
                if cs is None:
                    raise Abort(f"undefined function '{fnn.name}'", n.line)
                callee = self.case_value(*cs)
            elif callee.__class__ is LazyV:
                callee = yield from self._force_lazy(callee)
            elif callee.__class__ is Closure and callee.bound is not None and isinstance(callee.node, FnDecl):
                # a receiver method found by bare name: if the call has more args than it takes,
                # the name means an outer/prelude function instead
                ps = [p for p in callee.node.params if p.name != "self" and p.mod != "using"]
                if len(n.args) > len(ps):
                    alt = env.lookup(fnn.name, None)
                    if alt is MISSING:
                        alt = self.prelude.lookup(fnn.name)
                    if alt is not MISSING:
                        callee = alt
        elif c is Field:
            obj = yield from self.ev(fnn.obj, env)
            callee, selfv, has_self = self.field_callee(obj, fnn.name, env, n.line)
        elif c is GenApp:
            gb = fnn.base
            if gb.__class__ is Field:
                obj = yield from self.ev(gb.obj, env)
                callee, selfv, has_self = self.field_callee(obj, gb.name, env, n.line)
            else:
                callee = yield from self.ev(gb, env)
            targs = fnn.groups
        else:
            callee = yield from self.ev(fnn, env)
        if callee.__class__ is GenV:
            targs = callee.targs
            callee = callee.base
        k = callee.__class__
        # indexing
        if k in (ListV, ArrayV, RingV, DictV, MultiV, str, SetV) or (k is TupleV and piped is NOPIPE):
            return (yield from self.index_call(callee, n, env))
        params = None
        if k is Closure and isinstance(callee.node, (FnDecl, Lambda)):
            params = callee.node.params
        pos, named, refspec, spreads = yield from self.eval_args(n, env, params)
        if has_self and k is Builtin and getattr(callee, "pre", None) == "last":
            pos.append(selfv)
            has_self = False
            selfv = None
        if has_self:
            pos.insert(0, selfv)
            refspec = {(i + 1 if isinstance(i, int) else i): v for i, v in refspec.items()}
            spreads = [(i + 1, s) for i, s in spreads]
        # pipe insertion
        if piped is not NOPIPE:
            pos = self.insert_piped(callee, pos, piped, n.trailing is not None)
        if spreads:
            if k is TypeV or k is CaseV:
                pass
            else:
                pos, named = self.expand_spreads(pos, named, spreads)
                spreads = []
        if defer:
            return callee, pos, named
        if self.pkg_ceilings:
            self.cur_mod = env.mod
        r = yield from self.apply(callee, pos, named, refspec=refspec, env=env, targs=targs,
                                  spreads=spreads, line=n.line, hint=hint)
        # ref Self methods: rebind the receiver
        if (c is Field or (c is GenApp and fnn.base.__class__ is Field)) and k is Closure and callee.node.__class__ is FnDecl \
                and "ref_self" in callee.node.flags and (has_self or callee.bound is not None):
            newself = self._last_self
            yield from self.assign_place_value(fnn.obj if c is Field else fnn.base.obj, newself, env)
        return r

    def insert_piped(self, callee, pos, piped, has_trailing):
        if SLOT in pos:
            i = pos.index(SLOT)
            pos = list(pos)
            pos[i] = piped
            return pos
        k = callee.__class__
        if k is Builtin:
            if getattr(callee, "pre", None) == "last":
                return pos + [piped]
            return [piped] + pos
        if k is Closure and isinstance(callee.node, FnDecl):
            ps = [p for p in callee.node.params if p.mod != "using"]
            if len(ps) >= 2:
                first, last = ps[0], ps[-1]
                m_first = first.type is not None and self.type_matches(piped, first.type, callee.env)
                m_last = last.type is not None and self.type_matches(piped, last.type, callee.env)
                if not m_first and m_last and len(pos) == len(ps) - 1:
                    return pos + [piped]
                if m_first and m_last and has_trailing and len(pos) == len(ps) - 1:
                    # trailing lambda took the last slot; first gets the piped value
                    pass
        return [piped] + pos

    def expand_spreads(self, pos, named, spreads):
        pos = list(pos)
        named = dict(named)
        shift = 0
        for at, sv in spreads:
            ins = []
            if isinstance(sv, TupleV):
                if sv.names:
                    for nm, x in zip(sv.names, sv.vals):
                        named.setdefault(nm, x)
                else:
                    ins = list(sv.vals)
            elif isinstance(sv, Seq):
                ins = list(sv.items)
            pos[at + shift:at + shift] = ins
            shift += len(ins)
        return pos, named

    # ------------------------------------------------------------ field callee resolution
    def field_callee(self, obj, name, env, line):
        """Resolve obj.name used as a callee. Returns (callee, selfv, has_self)."""
        k = obj.__class__
        if k is TypeV:
            return self.type_member(obj, name, line), None, False
        if k is PkgV:
            v = obj.env.vars.get(name, MISSING)
            if v is MISSING:
                raise Abort(pkg_missing(obj, name), line)
            return v, None, False
        if k is TupleV and obj.names and name in obj.names:
            f = obj.vals[obj.names.index(name)]
            if isinstance(f, (Closure, Builtin, PartialV, ComposeV, PathV)):
                return f, None, False
        if k is EnumV and obj.names and name in obj.names:
            f = obj.vals[obj.names.index(name)]
            if isinstance(f, (Closure, Builtin, PartialV, ComposeV, PathV)):
                return f, None, False
        ms = self.methods_of(obj, name)
        if ms:
            c = ms[0]
            if len(ms) > 1:
                c = ms[0]
            if isinstance(c.node, FnDecl) and c.node.params and c.node.params[0].name == "self":
                return c, obj, True
            return self.bind_method(c, obj), None, False
        # generic-target impls (e.g. impl[A] Maybe[A])
        # UFCS: free function
        f = env.lookup(name, self)
        if f is MISSING or f.__class__ is LazyV:
            f = self.prelude.lookup(name)
        if f is MISSING:
            # field of a result-wrapped tuple etc.
            raise Abort(f"no method or function '{name}' for {type_name(obj)}", line)
        return f, obj, True

    def type_member(self, t, name, line):
        if t.name == "Locale" and name in self.locales:
            return self.locales[name]
        info = t.info
        if isinstance(info, EnumInfo):
            et = info.et
            ci = et.cases.get(name)
            if ci is not None:
                return self.case_value(et, ci)
            if name == "values":
                return Builtin(lambda I, a, kw, ta: ArrayV([self.case_value(et, et.cases[x]) for x in et.order]), "values")
            if name == "value_of":
                return Builtin(lambda I, a, kw, ta: self._enum_value_of(et, a[0]), "value_of")
            if name == "from_index":
                return Builtin(lambda I, a, kw, ta: self._enum_from_index(et, a[0]), "from_index")
        d = self.statics.get(t.name)
        if d is not None and name in d:
            return d[name][0]
        d = self.impls.get(t.name)
        if d is not None and name in d:
            return d[name][0]
        if t.name == "Connection" and name in ("open", "memory"):
            from .sqlrt import open_connection
            if name == "memory":
                return Builtin(lambda I, a, kw, ta: _counted(I, open_connection(":memory:")), "memory")
            def _open_db(I, a, kw, ta):
                if a[0] != ":memory:" and not (I.perms.path_ok("fs.read", a[0]) and I.perms.path_ok("fs.write", a[0])):
                    from .prelude import denied
                    return denied(a[0], "fs.read and fs.write")
                return _counted(I, open_connection(a[0]))
            return Builtin(_open_db, "open")
        if name == "pure" and t.name in ("Result", "List", "Array", "Stream"):
            if t.name == "Result":
                return Builtin(lambda I, a, kw, ta: Ok(a[0]), "pure")
            if t.name == "List":
                return Builtin(lambda I, a, kw, ta: ListV([a[0]], 1), "pure")
            if t.name == "Array":
                return Builtin(lambda I, a, kw, ta: ArrayV([a[0]], 1), "pure")
            return Builtin(lambda I, a, kw, ta: self.stream_of(ListV([a[0]], 1)), "pure")
        if name in self.prelude.vars and t.name in ("Result",):
            return self.prelude.vars[name]
        if t.name in NUM_TYPE_NAMES or t.name == "String":
            if name == "zero":
                return Builtin(lambda I, a, kw, ta: _num_const(t.name, 0), "zero")
            if name == "one" and t.name != "String":
                return Builtin(lambda I, a, kw, ta: _num_const(t.name, 1), "one")
        if name == "read" and (t.name in NUM_TYPE_NAMES or t.name in ("String", "Bool", "Char")):
            return Builtin(lambda I, a, kw, ta: _read_scalar(t.name, a[0]), "read")
        raise Abort(f"{t.name} has no member '{name}'", line)

    def _enum_value_of(self, et, s):
        if s in et.cases and not et.cases[s].fields or (s in et.cases and et.header):
            return Ok(et.consts[s] if hasattr(et, "consts") and s in et.consts else self.enum_instance(et, et.cases[s], []))
        return err_reserved("MISSING", "no such case")

    def _enum_from_index(self, et, i):
        if 0 <= i < len(et.order):
            nm = et.order[i]
            return Ok(et.consts[nm] if hasattr(et, "consts") and nm in et.consts else self.enum_instance(et, et.cases[nm], []))
        return err_reserved("OUT_OF_RANGE")

    # ------------------------------------------------------------ field access
    def field_get(self, obj, name, line=0):
        k = obj.__class__
        if k is TupleV:
            if obj.names and name in obj.names:
                x = obj.vals[obj.names.index(name)]
                if obj.tname and obj.tname in self.tuples and name in self.tuples[obj.tname].delegates:
                    return self.delegate_get_sync(x)
                return x
            if isinstance(name, int):
                return obj.vals[name]
            raise Abort(f"{obj.tname or 'tuple'} has no field '{name}'", line)
        if k is EnumV:
            if obj.et is RESULT_T and not (name in ("value", "error")):
                # Result field forwarding
                if obj.case == "Err":
                    return obj
                inner = obj.vals[0]
                return Ok(self.field_get(inner, name, line))
            if obj.names and name in obj.names:
                return obj.vals[obj.names.index(name)]
            if isinstance(name, int):
                return obj.vals[name]
            raise Abort(f"{obj.et.name}.{obj.case} has no field '{name}'", line)
        if k is TypeV:
            return self.type_member(obj, name, line)
        if k is PkgV:
            v = obj.env.vars.get(name, MISSING)
            if v is MISSING:
                raise Abort(pkg_missing(obj, name), line)
            return v
        if k is RangeV:
            return {"start": obj.start, "limit": obj.limit, "step": obj.step}[name]
        if isinstance(name, int) and isinstance(obj, Seq):
            return obj.items[name]
        # zero-argument method / function used as a value
        ms = self.methods_of(obj, name)
        if ms:
            return self.run_sync(self.apply_method(ms[0], obj, []))
        raise Abort(f"{type_name(obj)} has no field '{name}'", line)

    def delegate_get_sync(self, dv):
        ms = self.methods_of(dv, "get_value")
        if ms:
            return self.run_sync(self.apply_method(ms[0], dv, []))
        return dv.vals[0]

    def has_delegate(self, tname, fname):
        info = self.tuples.get(tname)
        return info is not None and fname in info.delegates

    def try_user_show(self, v):
        ms = self.methods_of(v, "show")
        if ms:
            return self.run_sync(self.apply_method(ms[0], v, []))
        return None

    # ------------------------------------------------------------ indexing
    def index_call(self, coll, n, env):
        keyed = coll.__class__ is DictV or (coll.__class__ is TupleV and coll.names is not None)
        args = []
        for a in n.args:
            e = a.expr
            if keyed and e.__class__ is Name:
                v = env.lookup(e.name, self)
                # bareword key: a literal name
                args.append(e.name)
                continue
            if e.__class__ is Dollar:
                v = yield from self.ev(e.expr, env)
            else:
                v = yield from self.ev(e, env)
            args.append(v)
        if n.trailing is not None:
            raise Abort("an index cannot take a trailing lambda", n.line)
        return self.index_get(coll, args, n.line)

    def index_get(self, coll, args, line=0):
        k = coll.__class__
        if k is DictV:
            key = args[0]
            if key in coll.d:
                return Ok(coll.d[key])
            return err_reserved("MISSING", "no such key")
        if k is TupleV:
            key = args[0]
            if isinstance(key, int):
                if not 0 <= key < len(coll.vals):
                    raise Abort("tuple index out of range", line)
                return coll.vals[key]
            return self.field_get(coll, key, line)
        if k is ListV or k is ArrayV or k is RingV:
            i = args[0]
            if isinstance(i, RangeV):
                s, e = self.slice_bounds(i, len(coll.items), line)
                return self.new_seq_like(coll, coll.items[s:e])
            if not isinstance(i, int):
                raise Abort(f"cannot index with {type_name(i)}", line)
            if i < 0 or i >= len(coll.items):
                raise Abort(f"index {i} out of range (length {len(coll.items)})", line)
            return coll.items[i]
        if k is str:
            i = args[0]
            b = coll.encode("utf-8")
            if isinstance(i, RangeV):
                s, e = self.slice_bounds(i, len(b), line)
                return b[s:e].decode("utf-8", errors="replace")
            if i < 0 or i >= len(b):
                raise Abort(f"index {i} out of range", line)
            return INT_CLASSES["Byte"](b[i])
        if k is MultiV:
            return self.multi_index(coll, args, line)
        if k is SetV:
            return args[0] in coll.items
        raise Abort(f"cannot index {type_name(coll)}", line)

    def new_seq_like(self, like, items):
        if like.kind == "List":
            return ListV(items, max(like.cap, len(items)))
        return ArrayV(items, len(items))

    def slice_bounds(self, r, n, line=0):
        s = r.start if r.start is not None else 0
        if r.limit is None:
            e = n
        else:
            e = r.limit + 1 if r.incl else r.limit
        if s < 0 or e > n or s > e:
            raise Abort(f"slice {s}..{e} out of range (length {n})", line)
        return s, e

    def multi_index(self, m, args, line=0):
        shape = m.shape
        if len(args) != len(shape):
            raise Abort("wrong number of indices for MultiArray", line)
        ranges = []
        keep = []
        for a, dim in zip(args, shape):
            if isinstance(a, RangeV):
                s, e = self.slice_bounds(a, dim, line)
                ranges.append(list(range(s, e)))
                keep.append(True)
            else:
                if not 0 <= a < dim:
                    raise Abort(f"index {a} out of range", line)
                ranges.append([a])
                keep.append(False)
        strides = []
        st = 1
        for d in reversed(shape):
            strides.insert(0, st)
            st *= d
        items = []

        def rec(dim, off):
            if dim == len(shape):
                items.append(m.items[off])
                return
            for i in ranges[dim]:
                rec(dim + 1, off + i * strides[dim])
        rec(0, 0)
        newshape = [len(r) for r, kp in zip(ranges, keep) if kp]
        if not newshape:
            return items[0]
        if len(newshape) == 1:
            return ArrayV(items, len(items))
        return MultiV(items, newshape)

    # ------------------------------------------------------------ apply
    def apply(self, f, pos, named=None, refspec=None, env=None, targs=None, spreads=None, line=0, hint=None):
        k = f.__class__
        named = named or {}
        if k is Closure:
            return self.call_closure(f, pos, named, refspec, env, targs, line)
        if k is Builtin:
            self.call_env = env
            return self.call_builtin(f, pos, named, targs, line)
        if k.__name__ == "ForeignFn":
            from .ffi import call_foreign
            return call_foreign(self, f, pos, named, refspec, env, line)
        if k is PartialV:
            return self.apply(f.fn, f.pre + list(pos) + f.post, named, refspec, env, targs, None, line)
        if k is ComposeV:
            return self.call_compose(f, pos, named)
        if k is TypeV:
            return self.construct(f, pos, named, spreads or [], env, line, hint)
        if k is CaseV:
            return self.construct_case(f, pos, named, spreads or [], env, line)
        if k is GenV:
            return self.apply(f.base, pos, named, refspec, env, f.targs, spreads, line, hint)
        if k is PathV:
            return Done(self.path_get(f, pos[0]))
        if k in (ListV, ArrayV, RingV, DictV, MultiV, str, TupleV):
            return Done(self.index_get(f, pos, line))
        raise Abort(f"{type_name(f)} is not callable", line)

    def call_compose(self, f, pos, named):
        v = yield from self.apply(f.fns[0], pos, named)
        for g in f.fns[1:]:
            v = yield from self.apply(g, [v])
        return v

    def call_builtin(self, f, pos, named, targs, line):
        if line:
            self.line = line
        if f.gen:
            return f.fn(self, pos, named, targs)
        return Done(f.fn(self, pos, named, targs))

    def path_get(self, p, v):
        for s in p.segs:
            v = self.field_get(v, s)
        return v

    # ------------------------------------------------------------ closure calls
    def call_closure(self, c, pos, named, refspec, cenv, targs, line):
        node = c.node
        if node.__class__ is FnGroup:
            return self.call_group(c, pos, named, refspec, cenv, targs, line)
        return self.call_one(c, node, pos, named, refspec, cenv, targs, line)

    def call_group(self, c, pos, named, refspec, cenv, targs, line):
        grp = c.node
        for clause in grp.clauses:
            r = self.try_bind(c, clause, pos, named, targs)
            if r is not None:
                if getattr(clause, "guard", None) is not None:
                    ok = yield from self.ev(clause.guard, r)
                    if ok is not True:
                        continue
                return (yield from self.run_bound(c, clause, r, refspec, cenv, line))
        raise Abort(f"no clause of '{grp.name}' matches the arguments", line)

    def call_one(self, c, node, pos, named, refspec, cenv, targs, line):
        r = self.try_bind(c, node, pos, named, targs, strict=True)
        return (yield from self.run_bound(c, node, r, refspec, cenv, line))

    def try_bind(self, c, node, pos, named, targs, strict=False):
        """Bind arguments to parameters. Returns the call Env or None when a clause doesn't match."""
        params = node.params or []
        pos = list(pos)
        base = c.env
        recvenv = None
        if c.bound is not None:
            recvenv = Env(base)
            recvenv.recv = RecvCell(c.bound, "ref_self" in (node.flags or ()) if isinstance(node, FnDecl) else False)
            recvenv.vars["Self"] = self.type_value(type_name(c.bound))
            base = recvenv
            if params and params[0].name == "self" and not isinstance(node, Lambda):
                pos = [c.bound] + pos
                recvenv.recv = RecvCell(c.bound, False)
        if node.__class__ is Lambda and (node.recv is not None or c.recv) and pos:
            # a receiver function: the first value is the receiver (its fields are in scope)
            rv = pos.pop(0)
            recvenv = Env(base)
            recvenv.recv = RecvCell(rv, False)
            recvenv.vars["self"] = rv
            base = recvenv
        env = Env(base)
        env.func = FnCtx(getattr(node, "name", "<lambda>"), getattr(node, "ret", None), c)
        # implicit tuple unpack
        nreal = len([p for p in params if p.mod != "using" and not p.variadic])
        if len(pos) == 1 and isinstance(pos[0], TupleV) and nreal >= 2 and not named:
            tv = pos[0]
            if len(tv.vals) == nreal or (len(tv.vals) >= nreal and any(p.variadic for p in params)):
                if tv.names and all(n in [p.name for p in params] for n in tv.names):
                    named = dict(zip(tv.names, tv.vals))
                    pos = []
                else:
                    pos = list(tv.vals)
        # generic parameters
        if node.__class__ is FnDecl and node.tparams:
            tp = self.infer_tparams(node, pos, env)
            if targs:
                names = [t.name for t in node.tparams]
                for nm, ta in zip(names, targs[0]):
                    tp[nm] = self.targ_value(ta, c.env)
            for k2, v2 in tp.items():
                env.vars[k2] = v2
        i = 0
        npos = len(pos)
        remaining_nonusing = len([p for p in params if p.mod != "using"])
        used_named = set()
        for pi, p in enumerate(params):
            pname = p.name
            if p.mod == "using":
                if i < npos and (pos[i] is USING or npos - i > remaining_nonusing):
                    v = pos[i]
                    i += 1
                    if v is USING:
                        v = self.find_using(c.env, env, p)
                elif pname in named:
                    v = named[pname]
                    used_named.add(pname)
                else:
                    v = self.find_using(c.env, env, p)
                if pname:
                    env.vars[pname] = v
                continue
            remaining_nonusing -= 1
            if p.variadic:
                rest = pos[i:]
                i = npos
                if pname in named:
                    nv = named[pname]
                    rest = list(nv.items) if isinstance(nv, Seq) else [nv]
                    used_named.add(pname)
                arr = (ListV if GC[0] else ArrayV)([self.coerce(x, p.type, c.env) for x in rest])
                if pname:
                    env.vars[pname] = arr
                continue
            if i < npos:
                v = pos[i]
                i += 1
            elif pname is not None and pname in named:
                v = named[pname]
                used_named.add(pname)
            elif p.default is not None:
                v = self.run_sync(self.evh(p.default, c.env, p.type))
            else:
                if strict:
                    raise Abort(f"missing argument '{pname}' in call to {getattr(node, 'name', 'function')}")
                return None
            if v is USING:
                v = self.find_using(c.env, env, p)
            if p.pat is not None:
                b = {}
                if not self.pmatch(p.pat, v, b, env):
                    if strict:
                        raise Abort("argument does not match the parameter pattern")
                    return None
                env.vars.update(b)
                if p.type is not None and not strict:
                    pass
                continue
            if p.type is not None:
                if not strict and v.__class__ is not LazyV and p.mod != "lazy":
                    if not self.type_matches(v, p.type, c.env, self.tparam_names(node)):
                        return None
                if v.__class__ is not LazyV:
                    v = self.coerce(v, p.type, c.env)
                if p.type.__class__ is TFn and p.type.recv is not None and v.__class__ is Closure \
                        and v.node.__class__ is Lambda and not v.recv:
                    nv = Closure(v.node, v.env, v.name)
                    nv.recv = True
                    v = nv
            if pname is not None:
                env.vars[pname] = v
        if i < npos and strict:
            raise Abort(f"too many arguments in call to {getattr(node, 'name', 'function')}")
        if i < npos and not strict:
            return None
        loc = getattr(node, "locals", None)
        if loc:
            for pn, ln in zip([p.name for p in params], loc):
                if pn in env.vars and pn != ln:
                    env.vars[ln] = env.vars[pn]
        if node.__class__ is Lambda and not params:
            pass
        return env

    def tparam_names(self, node):
        if node.__class__ is FnDecl and node.tparams:
            return {t.name for t in node.tparams}
        return None

    def targ_value(self, ta, env):
        if isinstance(ta, TName):
            if len(ta.path) == 1 and ta.path[0] in self.tuples:
                return TypeV(ta.path[0], self.tuples[ta.path[0]])
            return TypeV(ta.path[-1], self.type_info_for(ta.path[-1]), ta.groups)
        if isinstance(ta, TExpr):
            return self.run_sync(self.ev(ta.expr, env))
        return TypeV("?", None)

    def find_using(self, cenv, env, p):
        e = env
        cands = []
        while e is not None:
            if e.usings:
                for k, v in e.usings.items():
                    cands.append(v)
                if cands:
                    break
            e = e.parent
        if not cands:
            e = cenv
            while e is not None:
                if e.usings:
                    cands.extend(e.usings.values())
                    break
                e = e.parent
        for v in cands:
            if p.type is None or self.type_matches(v, p.type, cenv):
                return v
        if cands:
            return cands[0]
        raise Abort(f"no 'using' value in scope for parameter '{p.name}'")

    def run_bound(self, c, node, env, refspec, cenv, line):
        body = node.body
        if body is None:
            raise Abort(f"function '{getattr(node, 'name', '?')}' has no body", line)
        contracts = getattr(node, "contracts", None) if CONTRACTS[0] else None
        cenv0 = env
        ic = getattr(c, "iface_contracts", None) if CONTRACTS[0] else None
        if ic:
            # the interface's contract, with its parameter names mapped onto the implementation's
            cenv0 = env.child()
            for ip, np_ in zip(ic[0], node.params or []):
                if ip.name != np_.name and np_.name in env.vars:
                    cenv0.vars[ip.name] = env.vars[np_.name]
            contracts = list(contracts or []) + list(ic[1])
        if contracts:
            for kw, expr, ln, text in contracts:
                if kw == "requires":
                    ok = yield from self.ev(expr, cenv0.child())
                    if ok is not True:
                        raise Abort(f"requires failed in {node.name}: {text} (caller bug)", line)
        if self.heap_limit is not None:
            heap.tick(self)
        depth = self.depth = getattr(self, "depth", 0) + 1
        try:
            if node.__class__ is FnDecl and node.ret is not None:
                hint = node.ret
            else:
                hint = None
            try:
                if body.__class__ is Block:
                    v = yield from self.exec_body(body.stmts, env, hint)
                else:
                    v = yield from self.exec_stmt(body, env, hint)
            except ReturnEx as r:
                v = r.value
        finally:
            self.depth = depth - 1
        if node.__class__ is FnDecl and node.ret is not None:
            v = self.coerce(v, node.ret, c.env)
        elif node.__class__ is Lambda and node.ret is not None:
            v = self.coerce(v, node.ret, c.env)
        if contracts:
            cenv2 = cenv0.child()
            cenv2.vars["result"] = v
            for kw, expr, ln, text in contracts:
                if kw == "ensures":
                    ok = yield from self.ev(expr, cenv2)
                    if ok is not True:
                        raise Abort(f"ensures failed in {node.name}: {text} (supplier bug)", line)
        if refspec and cenv is not None:
            params = node.params or []
            for key, cname in refspec.items():
                if isinstance(key, int):
                    real = [p for p in params]
                    if c.bound is not None and not (params and params[0].name == "self"):
                        idx = key
                    else:
                        idx = key
                    pn = real[idx].name if idx < len(real) else None
                else:
                    pn = key
                if pn is not None and pn in env.vars:
                    (cenv.find_scope(cname) or cenv).vars[cname] = env.vars[pn]
        if c.bound is not None:
            e = env.parent
            if e is not None and e.recv is not None:
                self._last_self = e.recv.value
        return v

    def exec_body(self, stmts, env, hint):
        last = UNIT
        k = len(stmts) - 1
        for i, s in enumerate(stmts):
            if i == k:
                last = yield from self.exec_stmt(s, env, hint)
            else:
                yield from self.exec_stmt(s, env)
        return last

    def type_value(self, name):
        if name in self.tuples:
            return TypeV(name, self.tuples[name])
        if name in self.enums:
            return TypeV(name, self.enums[name])
        return TypeV(name)


NUM_TYPE_NAMES = {"Int", "Int8", "Int16", "Int32", "Int64", "UInt", "UInt8", "UInt16", "UInt32", "UInt64",
                  "Byte", "BigInt", "Float", "Double", "LongDouble", "Decimal"}


def _num_const(name, k):
    if name == "String":
        return ""
    if name in ("Float", "Double", "LongDouble"):
        return float(k)
    if name == "Decimal":
        from decimal import Decimal
        return Dec(Decimal(k))
    return k


def _read_scalar(name, text):
    s = text.strip()
    try:
        if name == "String":
            return Ok(text)
        if name == "Bool":
            if s in ("true", "false"):
                return Ok(s == "true")
            raise ValueError
        if name == "Char":
            if len(s) == 1:
                return Ok(s)
            raise ValueError
        if name in ("Float", "Double", "LongDouble"):
            return Ok(float(s))
        if name == "Decimal":
            from decimal import Decimal
            return Ok(Dec(Decimal(s)))
        return Ok(int(s))
    except ValueError:
        return err_reserved("MISSING", "cannot read " + name)


def _counted(I, r):
    """Count an opened Connection in the observed pool report."""
    if getattr(r, "case", None) == "Ok":
        r.vals[0].pools = I.pools
        I.pools.acquire("Connection")
    return r


def pkg_missing(pkg, name):
    if name in getattr(pkg, "internal", ()):
        return f"'{name}' is internal to package {pkg.name} and cannot be used from outside it"
    return f"package {pkg.name} has no export '{name}'"
