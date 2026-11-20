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

    @staticmethod
    def _hole_value(text, ty):
        """The value a typed hole binds, or None when the text does not read as that type."""
        import re
        if ty is None or ty == "String":
            return text
        if ty == "Int":
            return int(text) if re.fullmatch(r"-?[0-9]+", text) else None
        if ty in ("Double", "Float"):
            return float(text) if re.fullmatch(r"-?[0-9]+(\.[0-9]+)?([eE][-+]?[0-9]+)?", text) else None
        if ty == "Bool":
            return {"true": True, "false": False}.get(text)
        return None

    def match_string(self, parts, v, b):
        """Literal text anchors the match (the first piece at the start, the last at the end); a hole between pieces takes the shortest text."""
        if not isinstance(v, str) or isinstance(v, Char):
            return False
        pos, end = 0, len(v)
        if parts and isinstance(parts[0], str):
            if not v.startswith(parts[0]):
                return False
            pos = len(parts[0])
            parts = parts[1:]
        if parts and isinstance(parts[-1], str):
            tail = parts[-1]
            if end - len(tail) < pos or not v.endswith(tail):
                return False
            end -= len(tail)
            parts = parts[:-1]
        out = {}
        i = 0
        while i < len(parts):
            name, ty = parts[i]                      # a hole: ends at the next literal piece (or at `end` when it is the last)
            if i + 1 < len(parts):
                lit = parts[i + 1]
                j = v.find(lit, pos, end)
                if j < 0:
                    return False
                text, pos = v[pos:j], j + len(lit)
                i += 2
            else:
                text, pos = v[pos:end], end
                i += 1
            val = self._hole_value(text, ty)
            if val is None:
                return False
            if name != "_":
                out[name] = val
        if pos != end:
            return False
        b.update(out)
        return True

    def pmatch(self, p, v, b, env):
        c = p.__class__
        if c is PBind:
            b[p.name] = v
            return True
        if c is PWild:
            return True
        if c is PStr:
            return self.match_string(p.parts, v, b)
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
                if p.step is not None:
                    st = self.lit_value(p.step)
                    if st < 0:
                        if lo is not None and v > lo:
                            return False
                        if hi is not None and not (v >= hi if p.incl else v > hi):
                            return False
                        return lo is None or (lo - v) % -st == 0
                    if lo is not None and v < lo:
                        return False
                    if hi is not None and not (v <= hi if p.incl else v < hi):
                        return False
                    return lo is None or (v - lo) % st == 0
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
        if c is PIn:
            coll = self.run_sync(self.ev(p.expr, env))
            try:
                res = self.contains(coll, v)
            except TypeError:
                res = False
            return (not res) if p.neg else res
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
            if p.name:
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
                if q.__class__ is PRest:
                    continue                    # `(name: n, ...)`: the other fields are not looked at
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
                if q.name:
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
            if v.tag is not None:                                   # the member it was converted to, known from its static type
                return v.tag.replace(" ", "") == _tnode_text(t).replace(" ", "")
            et = t.groups[0][0]
            return all(self.pat_type_matches(x, et, env) for x in v.items)
        return self.type_matches(v, t, env)

    def is_pkg_name(self, nm, env):
        """`session.Left(e)`: the qualifier is an imported package, so the case is one the package exports."""
        return env.lookup(nm, self).__class__ is PkgV

    def match_recognizer(self, p, v, b, env):
        """`Name(a1, .., p1, ..)` where `Name` is a `pattern fn`: the first arguments (a literal or a `^pin`) are the function's leading
        parameters, the matched value is its last, and what is left are patterns for the payload of the `Some` it must give."""
        name = p.path[-1]
        f = env.lookup(name, self)
        lead = self.recognizers[name]
        items = [q for _l, q in (p.args or [])]
        vals = []
        for q in items[:lead]:
            if q.__class__ is PLit:
                vals.append(self.lit_value(q.expr))
            elif q.__class__ is PPin:
                vals.append(self.run_sync(self.ev(q.expr, env)))
            else:
                raise Abort(f"the first {lead} argument(s) of the pattern `{name}` are values (a literal or `^name`)")
        src = vals[0] if vals and vals[0].__class__ is str and name in ("Matches", "Finds") and getattr(f, "env", None) is not None else None
        if src is not None:
            vals = [self.run_sync(self.apply(f.env.lookup("must", self), [src]))] + vals[1:]
        r = self.run_sync(self.apply(f, vals + [v]))
        if not (r.__class__ is EnumV and r.case == "Some"):
            return False
        if src is not None:
            r = self.rx_typed(src, r, env)
            if r is None:
                return False
        rest = items[lead:]
        if not rest:
            return True
        payload = r.vals[0]
        if len(rest) == 1:
            return self.pmatch(rest[0], payload, b, env)
        if payload.__class__ is not TupleV or len(payload.vals) != len(rest):
            return False
        return all(self.pmatch(q, x, b, env) for q, x in zip(rest, payload.vals))

    def rx_typed(self, src, r, env):
        """The regex package's literal form: the `Some(List[Cap])` it gave, as the typed payload the checker promised (see `rxtype`):
        one value for one group, a tuple for several, `Some`/`None` for a group that may not take part."""
        from . import rxtype
        gs = rxtype.groups(src)
        caps = r.vals[0].items
        out = []
        for (name, _kind, optional), c in zip(gs, caps):
            if c.case == "CNone":
                if not optional:
                    return None
                out.append(EnumV(r.et, "None", [], []))
            else:
                x = c.vals[0]
                out.append(EnumV(r.et, "Some", [x], r.names) if optional else x)
        if not out:
            return r
        names = [g[0] for g in gs]
        payload = out[0] if len(out) == 1 else TupleV(out, names if all(names) else None)
        return EnumV(r.et, "Some", [payload], r.names)

    def match_con(self, p, v, b, env):
        name = p.path[-1]
        qual = p.path[:-1]
        args = p.args
        k = v.__class__
        if not qual and name in self.recognizers:
            return self.match_recognizer(p, v, b, env)
        if k is EnumV:
            if v.case == name and (not qual or qual[-1] == v.et.name or self.is_pkg_name(qual[-1], env)):
                if args is None:
                    return True
                hn = getattr(v.et.cases.get(v.case), "hdrnames", None)
                if hn and not all(l is not None for l, _ in args):
                    return self.match_args(args, v.vals[len(hn):], v.names[len(hn):], b, env)       # positional patterns see the payload, not the header
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
        if name in ("List", "Array") and isinstance(v, Seq) and args is None and not qual:
            return type_name(v) == name                 # a bare `List ->` is a type pattern: any list
        if name in ("List", "Array") and isinstance(v, Seq):
            if name == "Array" and v.kind == "List" and False:
                return False
            return self.match_seq(args, v, b, env)
        if name == "Dict" and k is DictV:
            used = []
            rest_pat = None
            for label, q in (args or []):
                if q.__class__ is PRest:                    # `...` skips the other entries; `...rest` binds them as a Dict
                    rest_pat = q
                    continue
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
                used.append(key)
            if rest_pat is not None and rest_pat.name:
                left = DictV({k2: x for k2, x in v.d.items() if k2 not in used})
                b[rest_pat.name] = left
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
        if args[rest_i][1].name:
            b[args[rest_i][1].name] = ListV(list(rest)) if v.kind == "List" else ArrayV(list(rest))
        return True


def _tnode_text(t):
    if not isinstance(t, TName):
        return "?"
    gs = [x for grp in t.groups or [] for x in (grp if isinstance(grp, (list, tuple)) else [grp])]
    return ".".join(t.path) + (f"[{', '.join(_tnode_text(x) for x in gs)}]" if gs else "")
