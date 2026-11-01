"""Bindings, assignment to places, and updates (mixin)."""
from .ast import *   # noqa
from .values import *   # noqa
from .core import *   # noqa
from .types_ import *   # noqa
from .calls import LazyV, RecvCell


class PlacesMixin:
    def ev_Assign(self, n, env):
        pat = n.targets
        op = n.op
        if op != "=":
            cur = yield from self.read_place(pat, env)
            rhs = yield from self.ev(n.value, env)
            value = yield from self.binop(op[:-1], cur, rhs, n.line)
        else:
            if n.ann is not None:
                value = yield from self.evh(n.value, env, n.ann)
                value = self.coerce(value, n.ann, env)
            else:
                value = yield from self.ev(n.value, env)
        yield from self.bind_pattern(pat, value, env, n)
        if n.vis:
            self.note_export(env, pat.name if isinstance(pat, PBind) else "", n.vis)
        return UNIT

    def read_place(self, pat, env):
        c = pat.__class__
        if c is PBind:
            v = env.lookup(pat.name, self)
            if v is MISSING:
                raise Abort(f"undefined name '{pat.name}'")
            return v
        if c is PPlace:
            e = pat.expr
            if e.__class__ is Gimme:
                return env_scope_val(self.gimme_scope(e, env), e.name)
            if e.__class__ is Call:
                coll = yield from self.ev(e.fn, env)
                if coll.__class__ is DictV:
                    keys = yield from self.index_keys(coll, e, env)
                    k = keys[0]
                    if k not in coll.d:
                        raise Abort(f"no such key {show(k)}")
                    return coll.d[k]
            return (yield from self.ev(e, env))
        raise Abort("cannot update this kind of target")

    def index_keys(self, coll, call, env):
        keyed = coll.__class__ is DictV or (coll.__class__ is TupleV and coll.names is not None)
        out = []
        for a in call.args:
            e = a.expr
            if keyed and e.__class__ is Name:
                out.append(e.name)
            elif e.__class__ is Dollar:
                out.append((yield from self.ev(e.expr, env)))
            else:
                out.append((yield from self.ev(e, env)))
        return out

    def bind_pattern(self, pat, value, env, node=None):
        c = pat.__class__
        if c is PBind:
            yield from self.rebind(env, pat.name, value)
            return
        if c is PWild:
            return
        if c is PPlace:
            yield from self.assign_place_value(pat.expr, value, env)
            return
        b = {}
        if not self.pmatch(pat, value, b, env):
            raise Abort("destructuring pattern did not match", getattr(node, "line", 0))
        for k, v in b.items():
            yield from self.rebind(env, k, v)

    def rebind(self, env, name, value):
        e = env
        while e is not None:
            if name in e.vars:
                break
            r = e.recv
            if r is not None and r.ref and self._has_field(r.value, name):
                r.value = yield from self.field_set(r.value, name, value)
                return
            e = e.parent
        env.vars[name] = value

    def _has_field(self, v, name):
        if v.__class__ is TupleV:
            return bool(v.names) and name in v.names
        if v.__class__ is EnumV:
            return bool(v.names) and name in v.names
        return False

    def ev_ElseLet(self, n, env):
        value = yield from self.ev(n.value, env)
        b = {}
        if self.pmatch(n.pat, value, b, env):
            for k, v in b.items():
                yield from self.rebind(env, k, v)
            return UNIT
        hint = env.func.ret if env.func is not None else None
        r = yield from self.ev_body(n.else_, env, hint)
        raise ReturnEx(r)

    def ev_Incr(self, n, env):
        t = n.target
        pat = PBind(t.name) if isinstance(t, Name) else PPlace(t)
        cur = yield from self.read_place(pat, env)
        nv = yield from self.binop("+", cur, n.delta, n.line)
        yield from self.bind_pattern(pat, nv, env, n)
        return UNIT

    # ------------------------------------------------------------ places
    def assign_place_value(self, expr, value, env):
        c = expr.__class__
        if c is Name:
            yield from self.rebind(env, expr.name, value)
            return
        if c is Gimme:
            self.gimme_scope(expr, env).vars[expr.name] = value
            return
        if c is Field:
            cur = yield from self.ev(expr.obj, env)
            new = yield from self.field_set(cur, expr.name, value)
            yield from self.assign_place_value(expr.obj, new, env)
            return
        if c is Call:
            coll = yield from self.ev(expr.fn, env)
            keys = yield from self.index_keys(coll, expr, env)
            new = self.set_index(coll, keys, value)
            yield from self.assign_place_value(expr.fn, new, env)
            return
        if c is Ref:
            yield from self.assign_place_value(expr.e, value, env)
            return
        raise Abort("cannot assign to this expression")

    def field_set(self, cur, name, value):
        k = cur.__class__
        if k is TupleV:
            if not (cur.names and name in cur.names) and not isinstance(name, int):
                raise Abort(f"{cur.tname or 'tuple'} has no field '{name}'")
            info = self.tuples.get(cur.tname) if cur.tname else None
            if info is not None and not isinstance(name, int):
                f = next(f for f in info.fields if f.name == name)
                if f.type is not None:
                    value = self.coerce(value, f.type, info.env)
                if f.delegate is not None:
                    dv = cur.get(name)
                    ms = self.methods_of(dv, "set_value")
                    if ms:
                        r = yield from self.apply_method(ms[0], dv, [value])
                        value = self._last_self
                    else:
                        value = TupleV([value], dv.names, dv.tname)
            return cur.replace(name, value)
        if k is EnumV:
            vals = list(cur.vals)
            vals[cur.names.index(name)] = value
            return EnumV(cur.et, cur.case, vals, cur.names)
        raise Abort(f"cannot set a field of {type_name(cur)}")

    def set_index(self, coll, keys, value):
        k = coll.__class__
        key = keys[0]
        if k is ListV or k is ArrayV:
            if not isinstance(key, int) or key < 0 or key >= len(coll.items):
                raise Abort(f"index {key} out of range (length {len(coll.items)})")
            items = list(coll.items)
            items[key] = value
            return k(items, coll.cap)
        if k is DictV:
            d = dict(coll.d)
            if key not in d and len(d) >= coll.cap:
                raise Abort(f"Dict is full (capacity {coll.cap})")
            d[key] = value
            return DictV(d, coll.cap)
        if k is TupleV:
            return coll.replace(key, value)
        if k is MultiV:
            idx = self.multi_flat(coll, keys)
            items = list(coll.items)
            items[idx] = value
            return MultiV(items, coll.shape)
        raise Abort(f"cannot assign into {type_name(coll)}")

    def multi_flat(self, m, keys):
        off = 0
        for k, d in zip(keys, m.shape):
            if not 0 <= k < d:
                raise Abort(f"index {k} out of range")
            off = off * d + k
        return off


def env_scope_val(scope, name):
    return scope.vars[name]
