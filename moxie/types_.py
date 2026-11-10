"""Type helpers for the interpreter: aliases, coercion by annotation, runtime type tests."""
from .ast import *   # noqa
from .values import *   # noqa
from .core import *   # noqa

BASIC_TYPES = {"Int", "UInt", "Double", "Float", "LongDouble", "Bool", "Unit", "Char", "String", "Byte",
               "Int8", "Int16", "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64", "Keyword", "Duration",
               "Error", "Decimal", "BigInt", "Range"}
COLL_TYPES = {"Array", "List", "Set", "Dict", "MultiArray"}


class TypeInfo:
    """Declared tuple type."""

    def __init__(self, name, tparams, fields, derivs, positional=None):
        self.name = name
        self.tparams = tparams
        self.fields = fields          # list of FieldDecl
        self.derivs = derivs or []
        self.positional = positional
        self.delegates = {f.name: f.delegate for f in fields if f.delegate is not None}
        self.props = {}               # property name -> PropertyDecl (filled when the declaration runs)
        self.env = None

    @property
    def names(self):
        return [f.name for f in self.fields]


class EnumInfo:
    def __init__(self, et, decl):
        self.et = et
        self.decl = decl


class TypesMixin:
    # ------------------------------------------------------------ names
    def tname_of(self, t):
        """Final path component of a type node (None if not a plain named type)."""
        if isinstance(t, TName):
            return t.path[-1]
        return None

    def rtype_name(self, t):
        """Registry name for an impl target / type test."""
        if isinstance(t, TName):
            n = t.path[-1]
            a = self.aliases.get(n)
            if a is not None and a[1] is not t:
                inner = a[1]
                r = self.rtype_name(inner)
                if r:
                    return r
            return n
        if isinstance(t, TFn):
            return "Function"
        if isinstance(t, TTuple):
            return "Tuple"
        if isinstance(t, TUnit):
            return "Unit"
        return None

    def resolve_alias(self, t):
        seen = 0
        while isinstance(t, TName) and t.path[-1] in self.aliases and seen < 20:
            kind, inner, tparams = self.aliases[t.path[-1]]
            if kind == "opaque":
                t = inner
            else:
                t = inner
            seen += 1
            if isinstance(t, TName) and t.path[-1] in tparams:
                break
        return t

    # ------------------------------------------------------------ constants in types
    def type_const(self, e, env):
        return self.run_sync(self.ev(e, env))

    def bounded_range(self, t, env):
        """For Int[lo..=hi] return (lo, hi) or None."""
        if isinstance(t, TName) and t.groups:
            g = t.groups[0]
            if len(g) == 1 and isinstance(g[0], TExpr) and isinstance(g[0].expr, RangeE):
                r = g[0].expr
                lo = self.type_const(r.lo, env) if r.lo is not None else None
                hi = self.type_const(r.hi, env) if r.hi is not None else None
                if hi is not None and not r.incl:
                    hi -= 1
                return lo, hi
        return None

    # ------------------------------------------------------------ coercion by annotation
    def coerce(self, v, t, env, what=None):
        """Shape a value to a declared type (numeric widths, collections from tuple literals, ...)."""
        if t is None:
            return v
        c = t.__class__
        if c is TName:
            return self.coerce_name(v, t, env)
        if c is TTuple:
            if isinstance(v, TupleV) and len(v.vals) == len(t.items):
                vals = [self.coerce(x, ft, env) for x, (_, ft) in zip(v.vals, t.items)]
                names = v.names
                if names is None and all(l is not None for l, _ in t.items):
                    names = [l for l, _ in t.items]
                return TupleV(vals, names, v.tname)
            return v
        if c is TStatic:
            return self.coerce(v, t.inner, env)
        return v

    def coerce_name(self, v, t, env):
        name = t.path[-1]
        if name in self.aliases:
            kind, inner, tparams = self.aliases[name]
            if kind == "union":
                return v
            if kind == "assoc":
                return v
            if isinstance(inner, TName) and inner.path[-1] == name:
                return v
            if tparams and t.groups:
                inner = self.subst_type(inner, tparams, t.groups[0])
            r = self.coerce(v, inner, env)
            if kind == "opaque":
                return r
            return r
        cls = INT_CLASSES.get(name)
        if cls is not None:
            return self.to_intclass(v, cls, name)
        if name == "Int":
            rng = self.bounded_range(t, env)
            if isinstance(v, FixedInt):
                v = int(v)
            if isinstance(v, int) and not isinstance(v, bool) and rng is not None:
                lo, hi = rng
                if (lo is not None and v < lo) or (hi is not None and v > hi):
                    raise Abort(f"{v} is out of range for {self.show_type(t)}")
            return v
        if name == "BigInt":
            if t.groups and t.groups[0]:
                bits = self.type_const(t.groups[0][0].expr, env) if isinstance(t.groups[0][0], TExpr) else 128
                cls = bigint_class(bits)
                return self.to_intclass(v, cls, cls.tname)
            return v
        if name in ("Double", "LongDouble"):
            if isinstance(v, F32):
                return float(v)
            if isinstance(v, int) and not isinstance(v, bool):
                return float(v)
            return v
        if name == "Float":
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return F32.of(float(v))
            return v
        if name == "Decimal":
            scale = None
            if len(t.groups) and len(t.groups[0]) >= 2:
                scale = self.type_const(t.groups[0][1].expr, env) if isinstance(t.groups[0][1], TExpr) else None
            if isinstance(v, Dec):
                return Dec(v.v, scale if scale is not None else v.scale)
            if isinstance(v, int):
                return Dec(Decimal(int(v)), scale)
            return v
        if name in COLL_TYPES:
            return self.coerce_coll(v, t, name, env)
        if name == "Result" and isinstance(v, EnumV) and v.et is RESULT_T and t.groups and len(t.groups[0]) >= 1:
            if v.case == "Ok":
                nv = self.coerce(v.vals[0], t.groups[0][0], env)
                if nv is not v.vals[0]:
                    return Ok(nv)
            elif len(t.groups[0]) >= 2 and v.case == "Err":
                nv = self.coerce(v.vals[0], t.groups[0][1], env)
                if nv is not v.vals[0]:
                    return Err(nv)
            return v
        if name in self.tuples:
            info = self.tuples[name]
            if isinstance(v, TupleV) and v.tname != name:
                return self.tuple_from_anon(info, v)
            return v
        if name == "Self":
            return v
        return v

    def to_intclass(self, v, cls, name):
        if isinstance(v, bool):
            return v
        if isinstance(v, int):
            if v.__class__ is cls:
                return v
            iv = int(v)
            if not cls.fits(iv):
                raise Abort(f"{iv} does not fit {name}")
            return cls(iv)
        return v

    def coerce_coll(self, v, t, name, env):
        groups = t.groups
        elem_t = None
        caps = None
        if name == "Dict":
            kt = vt = None
            if groups and len(groups[0]) >= 2:
                kt, vt = groups[0][0], groups[0][1]
            if len(groups) > 1 and groups[1]:
                caps = self.const_of(groups[1][0], env)
            if isinstance(v, DictV):
                if vt is not None or kt is not None:
                    d = {}
                    for k, x in v.d.items():
                        d[self.coerce(k, kt, env)] = self.coerce(x, vt, env)
                    v = DictV(d, v.cap)
                if caps is not None and not GC[0]:
                    v.cap = caps
            return v
        if groups and groups[0]:
            elem_t = groups[0][0]
        if len(groups) > 1 and groups[1]:
            if name == "MultiArray":
                caps = [self.const_of(g, env) for g in groups[1]]
            else:
                caps = self.const_of(groups[1][0], env)
        if name == "MultiArray":
            if isinstance(v, MultiV):
                return v
            return v
        items = None
        if isinstance(v, TupleV):
            items = list(v.vals)
        elif isinstance(v, Seq):
            items = list(v.items)
        elif isinstance(v, SetV):
            items = list(v.items)
        else:
            return v
        if elem_t is not None and not isinstance(elem_t, THole):
            items = [self.coerce(x, elem_t, env) for x in items]
        if name == "Array":
            return ArrayV(items, caps if isinstance(caps, int) else len(items))
        if name == "List":
            cap = caps if isinstance(caps, int) else len(items)
            if len(items) > cap:
                raise Abort(f"list literal has {len(items)} elements but capacity is {cap}")
            return ListV(items, cap)
        if name == "Set":
            d = {}
            for x in items:
                d[x] = True
            return SetV(d, caps if isinstance(caps, int) else len(d))
        return v

    def const_of(self, g, env):
        if isinstance(g, TExpr):
            return self.type_const(g.expr, env)
        if isinstance(g, TName) and len(g.path) == 1:
            x = env.lookup(g.path[0], self)
            if x is not MISSING:
                return x
        return None

    def tuple_from_anon(self, info, v):
        names = info.names
        vals = []
        if v.names:
            for n in names:
                if n in v.names:
                    vals.append(v.vals[v.names.index(n)])
                else:
                    vals.append(None)
            if any(x is None for x in vals) and len(v.vals) == len(names):
                vals = list(v.vals)
        else:
            vals = list(v.vals)
        return TupleV(vals, names, info.name)

    def subst_type(self, t, tparams, args):
        return t

    def show_type(self, t):
        if isinstance(t, TName):
            s = ".".join(t.path)
            for g in t.groups:
                s += "[" + ", ".join(self.show_type(x) for x in g) + "]"
            return s
        if isinstance(t, TExpr):
            return "<expr>"
        if isinstance(t, TUnit):
            return "()"
        if isinstance(t, TTuple):
            return "(" + ", ".join(self.show_type(x) for _, x in t.items) + ")"
        if isinstance(t, TFn):
            return "(" + ", ".join(self.show_type(x) for _, x in t.params) + ") -> " + self.show_type(t.ret)
        if isinstance(t, TUnion):
            return " | ".join(self.show_type(x) for x in t.members)
        return "?"

    # ------------------------------------------------------------ runtime type tests
    def type_matches(self, v, t, env=None, tp=None):
        """Best-effort test that runtime value v belongs to type node t. Unknown shapes answer True."""
        c = t.__class__
        if c is TName:
            name = t.path[-1]
            if tp and name in tp:
                return True
            if name in self.aliases:
                kind, inner, tparams = self.aliases[name]
                if kind == "union":
                    return any(self.type_matches(v, m, env, tp) for m in self.flatten_union(inner))
                if isinstance(inner, TName) and inner.path[-1] == name:
                    return True
                r = self.type_matches(v, inner, env, tp)
                if r and kind == "alias":
                    rng = self.bounded_range(inner, env or self.module_env) if isinstance(inner, TName) else None
                    if rng is not None and isinstance(v, int):
                        lo, hi = rng
                        if (lo is not None and v < lo) or (hi is not None and v > hi):
                            return False
                return r
            return self.name_matches(v, name, t, env)
        if c is TUnion:
            return any(self.type_matches(v, m, env, tp) for m in t.members)
        if c is TUnit:
            return isinstance(v, UnitT)
        if c is TTuple:
            return isinstance(v, TupleV) and len(v.vals) == len(t.items)
        if c is TFn:
            return isinstance(v, (Closure, Builtin, PartialV, ComposeV, PathV))
        if c is TStatic:
            return self.type_matches(v, t.inner, env, tp)
        return True

    def flatten_union(self, t):
        if isinstance(t, TUnion):
            out = []
            for m in t.members:
                out.extend(self.flatten_union(m))
            return out
        if isinstance(t, TName) and t.path[-1] in self.aliases and self.aliases[t.path[-1]][0] == "union":
            return self.flatten_union(self.aliases[t.path[-1]][1])
        return [t]

    def name_matches(self, v, name, t, env):
        if name == "Int":
            if v.__class__ is not int:
                return False
            rng = self.bounded_range(t, env or self.module_env) if t.groups else None
            if rng is not None:
                lo, hi = rng
                if (lo is not None and v < lo) or (hi is not None and v > hi):
                    return False
            return True
        if name in INT_CLASSES:
            return isinstance(v, INT_CLASSES[name]) or (v.__class__ is int and INT_CLASSES[name].fits(v))
        if name in ("Double", "LongDouble"):
            return v.__class__ is float
        if name == "Float":
            return isinstance(v, F32)
        if name == "BigInt":
            return isinstance(v, int) and not isinstance(v, bool)
        if name == "Bool":
            return isinstance(v, bool)
        if name == "String":
            return v.__class__ is str
        if name == "Char":
            return v.__class__ is Char
        if name == "Unit":
            return isinstance(v, UnitT)
        if name == "Decimal":
            return isinstance(v, Dec)
        if name in ("Keyword",):
            return isinstance(v, Kw)
        if name == "Duration":
            return isinstance(v, Dur)
        if name in COLL_TYPES:
            return type_name(v) == name
        if name == "Result":
            return isinstance(v, EnumV) and v.et is RESULT_T
        if name == "Error":
            return isinstance(v, TupleV) and v.tname == "Error"
        if name in self.tuples:
            return isinstance(v, TupleV) and v.tname == name
        if name in self.enums:
            return isinstance(v, EnumV) and v.et.name == name
        if name in self.ifaces:
            tn = type_name(v)
            return self.implements(tn, name)
        return True

    def implements(self, tn, iface):
        s = self.iface_impls.get(tn)
        if s and iface in s:
            return True
        if iface in self.ifaces:
            # structural: interfaces made of properties/methods satisfied by impl
            return False
        return False

    # ------------------------------------------------------------ generic parameter inference
    def infer_tparams(self, node, args, env):
        """Bind type/size parameters of a generic function from runtime arguments."""
        out = {}
        tps = node.tparams
        if not tps:
            return out
        names = {tp.name: tp for tp in tps}
        params = node.params
        for p, a in zip(params, args):
            if p.type is not None:
                self.match_tparam(p.type, a, names, out)
        return out

    def match_tparam(self, t, v, names, out):
        c = t.__class__
        if c is TName:
            n = t.path[-1]
            if n in names:
                tp = names[n]
                if n not in out:
                    if tp.holes:
                        out[n] = TypeV(type_name(v), self.type_info_for(type_name(v)), self.value_targs(v))
                    else:
                        out[n] = TypeV(type_name(v), self.type_info_for(type_name(v)))
                return
            if t.groups:
                # F[A]  where F is a constructor parameter handled above; sizes: Array[T][N]
                if len(t.groups) >= 2 and (isinstance(v, (Seq,)) or (isinstance(v, TupleV) and t.path[-1] == "Array")):
                    ln = len(v.items) if isinstance(v, Seq) else len(v.vals)       # a literal `(1, 2)` given to an Array parameter has its length
                    for g in t.groups[1:]:
                        for x in g:
                            if isinstance(x, TName) and x.path[-1] in names and len(x.path) == 1:
                                out.setdefault(x.path[-1], ln)
                            elif isinstance(x, TExpr) and isinstance(x.expr, Name) and x.expr.name in names:
                                out.setdefault(x.expr.name, ln)
                if isinstance(v, MultiV) and len(t.groups) >= 2:
                    for g_i, x in enumerate(t.groups[1]):
                        nm = x.path[-1] if isinstance(x, TName) else (x.expr.name if isinstance(x, TExpr) and isinstance(x.expr, Name) else None)
                        if nm in names and g_i < len(v.shape):
                            out.setdefault(nm, v.shape[g_i])
                elem = t.groups[0][0] if t.groups[0] else None
                if elem is not None and isinstance(v, Seq) and v.items:
                    self.match_tparam(elem, v.items[0], names, out)
                if isinstance(v, EnumV) and v.vals and t.groups[0]:
                    pass
        elif c is TTuple and isinstance(v, TupleV):
            for (_, ft), x in zip(t.items, v.vals):
                self.match_tparam(ft, x, names, out)

    def value_targs(self, v):
        """The type arguments a generic tuple value remembers, as the groups of a type value (a hole where unknown)."""
        if v.__class__ is TupleV and v.targs is not None:
            return [[x if x is not None else TName(["_"], []) for x in v.targs]]
        return None

    def type_info_for(self, name):
        if name in self.tuples:
            return self.tuples[name]
        if name in self.enums:
            return self.enums[name]
        return None
