"""Pattern matching (mixin)."""
from .ast import *   # noqa
from .values import *   # noqa
from .core import *   # noqa
from .types_ import *   # noqa
from .calls import LazyV


class PatternsMixin:
    def lit_value(self, e):
        c = e.__class__
        if c is IntLit:
            s = e.suffix
            if s and s != "f":
                cls = INT_CLASSES.get({"i8": "Int8", "i16": "Int16", "i32": "Int32", "i64": "Int64",
                                       "u8": "UInt8", "u16": "UInt16", "u32": "UInt32", "u64": "UInt64"}.get(s, ""))
                if cls:
                    return cls(e.v)
            return e.v
        if c is FloatLit:
            return e.v
        if c is StrLit:
            return "".join(p for p in e.parts if isinstance(p, str))
        if c is CharLit:
            return Char(e.c)
        if c is KwLit:
            return Kw(e.name)
        if c is BoolLit:
            return e.b
        if c is DecLit:
            return Dec(Decimal(e.text))
        raise Abort("bad literal in pattern")

    def pmatch(self, p, v, b, env):
        c = p.__class__
        if c is PBind:
            b[p.name] = v
            return True
        if c is PWild:
            return True
        if c is PLit:
            lv = self.lit_value(p.expr)
            if isinstance(lv, bool) or isinstance(v, bool):
                return lv is v
            if isinstance(lv, (int, float)) and isinstance(v, (int, float)):
                return lv == v
            return lv == v and type(lv) is type(v) or (isinstance(lv, str) and isinstance(v, str) and lv == v and (isinstance(lv, Char) == isinstance(v, Char)))
        if c is PRange:
            if isinstance(v, bool):
                return False
            lo = self.lit_value(p.lo) if p.lo is not None else None
            hi = self.lit_value(p.hi) if p.hi is not None else None
            try:
                if lo is not None and v < lo:
                    return False
                if hi is not None:
                    return v <= hi if p.incl else v < hi
            except TypeError:
                return False
            return True
        if c is PAs:
            if self.pmatch(p.pat, v, b, env):
                b[p.name] = v
                return True
            return False
        if c is PPin:
            x = self.run_sync(self.ev(p.expr, env))
            return eq(x, v)
        if c is PRel:
            if isinstance(v, bool):
                return False
            if p.operand.__class__ in (IntLit, FloatLit, StrLit, CharLit, DecLit):
                x = self.lit_value(p.operand)
            else:
                x = self.run_sync(self.ev(p.operand, env))
            try:
                if p.op == ">=":
                    return v >= x
                if p.op == ">":
                    return v > x
                if p.op == "<=":
                    return v <= x
                return v < x
            except TypeError:
                return False
        if c is PTuple:
            return self.match_tuple(p, v, b, env)
        if c is PCon:
            return self.match_con(p, v, b, env)
        if c is PRest:
            b[p.name] = v
            return True
        if c is PPlace:
            raise Abort("a place cannot be used as a pattern")
        raise Abort(f"unsupported pattern {c.__name__}")

    def match_tuple(self, p, v, b, env):
        items = p.items
        if not items and v is UNIT:
            return True   # the empty tuple pattern matches Unit
        if v.__class__ is ArrayV and all(l is None for l, _ in items):
            # an Array of known length can be unpacked with a tuple pattern
            if len(items) != len(v.items):
                return False
            return all(self.pmatch(q, x, b, env) for (_, q), x in zip(items, v.items))
        if v.__class__ is not TupleV:
            return False
        if any(l is not None for l, _ in items):
            for l, q in items:
                if l is None:
                    return False
                if not v.names or l not in v.names:
                    return False
                if not self.pmatch(q, v.vals[v.names.index(l)], b, env):
                    return False
            return True
        if len(items) != len(v.vals):
            return False
        for (_, q), x in zip(items, v.vals):
            if not self.pmatch(q, x, b, env):
                return False
        return True

    def match_args(self, args, vals, names, b, env):
        """args: [(label, pat)]; vals/names: payload."""
        if args is None:
            return True
        i = 0
        n = len(vals)
        for label, q in args:
            if q.__class__ is PRest:
                b[q.name] = ListV(list(vals[i:]))
                i = n
                continue
            if label is not None:
                if not names or label not in names:
                    return False
                x = vals[names.index(label)]
            else:
                if i >= n:
                    return False
                x = vals[i]
                i += 1
            if not self.pmatch(q, x, b, env):
                return False
        if args and not any(l is not None or q.__class__ is PRest for l, q in args) and len(args) != n:
            return False
        return True

    def match_con(self, p, v, b, env):
        name = p.path[-1]
        qual = p.path[:-1]
        args = p.args
        k = v.__class__
        if k is EnumV:
            if v.case == name and (not qual or qual[-1] == v.et.name):
                if args is None:
                    return True
                return self.match_args(args, v.vals, v.names, b, env)
            if args is None and not qual and name == v.et.name:
                return True
            if args is None and name in self.aliases:
                return self.type_matches(v, TName([name], []), env)
            return False
        if k is TupleV:
            if name == v.tname:
                return self.match_args(args, v.vals, v.names, b, env)
            if args is None and name in self.aliases:
                return self.type_matches(v, TName([name], []), env)
            return False
        if name in ("List", "Array") and isinstance(v, Seq):
            if name == "Array" and v.kind == "List" and False:
                return False
            return self.match_seq(args, v, b, env)
        if name == "Dict" and k is DictV:
            for label, q in (args or []):
                if label is None:
                    return False
                key = label
                if key not in v.d:
                    if isinstance(label, str) and label.lstrip("-").isdigit():
                        key = int(label)
                    if key not in v.d:
                        return False
                if not self.pmatch(q, v.d[key], b, env):
                    return False
            return True
        if args is None and not qual:
            # a type name (union member) or a named constant
            if name in self.aliases or name in BASIC_TYPES or name in COLL_TYPES or name in self.tuples or name in self.enums or name in self.ifaces:
                return self.type_matches(v, TName([name], []), env)
            cv = env.lookup(name, self)
            if cv is not MISSING:
                return eq(cv, v)
            if name in self.cases:
                return False
            return self.type_matches(v, TName([name], []), env)
        return False

    def match_seq(self, args, v, b, env):
        args = args or []
        items = v.items
        rest_i = None
        for i, (l, q) in enumerate(args):
            if q.__class__ is PRest:
                rest_i = i
        if rest_i is None:
            if len(args) != len(items):
                return False
            for (_, q), x in zip(args, items):
                if not self.pmatch(q, x, b, env):
                    return False
            return True
        head = args[:rest_i]
        tail = args[rest_i + 1:]
        if len(items) < len(head) + len(tail):
            return False
        for (_, q), x in zip(head, items):
            if not self.pmatch(q, x, b, env):
                return False
        mid_end = len(items) - len(tail)
        for (_, q), x in zip(tail, items[mid_end:]):
            if not self.pmatch(q, x, b, env):
                return False
        rest = items[len(head):mid_end]
        b[args[rest_i][1].name] = ListV(list(rest)) if v.kind == "List" else ArrayV(list(rest))
        return True
