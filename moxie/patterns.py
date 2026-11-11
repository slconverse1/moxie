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
        if c is PTyped:
            return self.pat_type_matches(v, p.type, env) and self.pmatch(p.pat, v, b, env)
        if c is PTuple:
            return self.match_tuple(p, v, b, env)
        if c is PCon:
            return self.match_con(p, v, b, env)
        if c is PBin:
            return self.match_bin(p, v, b)
        if c is PRest:
            b[p.name] = v
            return True
        if c is PPlace:
            raise Abort("a place cannot be used as a pattern")
        raise Abort(f"unsupported pattern {c.__name__}")

    BIN_INT = {"u8": ("UInt8", 1, False), "i8": ("Int8", 1, True)}
    for _w in (16, 32, 64):
        for _sg, _nm in (("u", "UInt"), ("i", "Int")):
            for _en in ("be", "le"):
                BIN_INT[f"{_sg}{_w}{_en}"] = (f"{_nm}{_w}", _w // 8, _sg == "i")

    def match_bin(self, p, v, b):
        """A Bin(...) pattern on an Array[Byte]: fields are read left to right; too short or a wrong literal fails."""
        if v.__class__ is not ArrayV:
            return False
        data = [int(x) for x in v.items]
        pos, bitpos, vals = 0, 0, {}
        bind = {}

        def mk(tname, x):
            cls = INT_CLASSES.get(tname)
            return cls(x) if cls is not None else x
        for e in p.elems:
            if e[0] == "lit":
                lit = e[1]
                if data[pos:pos + len(lit)] != lit:
                    return False
                pos += len(lit)
                continue
            _tag, name, kind, arg = e
            if kind == "bits":
                nbits = arg
                x = 0
                for _ in range(nbits):
                    if pos >= len(data):
                        return False
                    x = (x << 1) | ((data[pos] >> (7 - bitpos)) & 1)
                    bitpos += 1
                    if bitpos == 8:
                        bitpos, pos = 0, pos + 1
                tn = "UInt8" if nbits <= 8 else "UInt16" if nbits <= 16 else "UInt32" if nbits <= 32 else "UInt64"
                val = mk(tn, x)
                num = x
            elif kind == "bytes":
                n = arg if isinstance(arg, int) else (len(data) - pos if arg is None else vals.get(arg))
                if n is None or n < 0 or pos + n > len(data):
                    return False
                val = ArrayV([mk("UInt8", x) for x in data[pos:pos + n]])
                pos += n
                num = None
            else:
                tname, width, signed = self.BIN_INT[kind]
                if pos + width > len(data):
                    return False
                chunk = data[pos:pos + width]
                pos += width
                x = int.from_bytes(bytes(chunk), "little" if kind.endswith("le") else "big", signed=signed)
                val = mk(tname, x)
                num = x
            if name:
                bind[name] = val
                if num is not None:
                    vals[name] = num
        if pos < len(data) and not (p.elems and p.elems[-1][0] == "field" and p.elems[-1][2] == "bytes" and p.elems[-1][3] is None):
            return False             # trailing bytes that no element describes: the layout does not match
        b.update(bind)
        return True

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

    def pat_type_matches(self, v, t, env):
        """`List[Int]` as a pattern: the head must match and every item must match the item type (an empty list has no
        items, so it matches any `List[...]`)."""
        if t.__class__ is TName and t.groups and t.groups[0] and t.path[-1] in ("List", "Array"):
            if not (isinstance(v, Seq) and type_name(v) == t.path[-1]):
                return False
            et = t.groups[0][0]
            return all(self.pat_type_matches(x, et, env) for x in v.items)
        return self.type_matches(v, t, env)

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
