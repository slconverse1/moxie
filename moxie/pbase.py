"""Parser base: token helpers, types, patterns."""
from .lexer import MoxieSyntaxError, tokenize
from .ast import *   # noqa

HARD = {
    "fn", "tuple", "enum", "interface", "impl", "forward", "inline", "fiber", "import", "export",
    "internal", "using",
    "if", "elif", "else", "when", "select", "for", "while", "in", "is", "break", "continue",
    "return", "daemon", "do",
    "go", "try_go", "ref", "move", "static",
    "and", "or", "not", "true", "false", "Self", "self", "todo",
}

ASSIGN_OPS = {"=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="}


def edit_row(row, edits):
    """`row` with the old-style colons at the 1-based columns in `edits` ({col: kind}) rewritten: a declaration colon is
    deleted, a Dict entry colon becomes ` ->`."""
    for col, kind in sorted(edits.items(), reverse=True):
        if col - 1 >= len(row) or row[col - 1] != ":":
            continue
        after = row[col:col + 1]
        gap = " " if after not in (" ", "") else ""
        if kind == "dict":
            row = row[:col - 1] + " ->" + gap + row[col:]
        else:
            row = row[:col - 1] + gap + row[col:]
    return row


class PBase:
    def __init__(self, toks, file="<input>"):
        self.toks = toks
        self.p = 0
        self.file = file
        self.no_trailing = False
        self.nl_stop = False
        self.units = {}             # unit name -> its factor to the base unit, for the units declared so far in this file (`unit m`): a number then a unit is a quantity

    # ---------------------------------------------------------------- tokens
    def peek(self, k=0):
        i = self.p + k
        if i >= len(self.toks):
            return self.toks[-1]
        return self.toks[i]

    def next(self):
        t = self.toks[self.p]
        if self.p < len(self.toks) - 1:
            self.p += 1
        return t

    def err(self, msg, tok=None):
        t = tok or self.peek()
        raise MoxieSyntaxError(msg, t.line, t.col, self.file)

    def at_op(self, v, k=0):
        t = self.peek(k)
        return t.kind == "OP" and t.val == v

    def at_name(self, v, k=0):
        t = self.peek(k)
        return t.kind == "NAME" and t.val == v

    def eat_op(self, v):
        if self.at_op(v):
            return self.next()
        return None

    def eat_name(self, v):
        if self.at_name(v):
            return self.next()
        return None

    def expect_op(self, v, what=None):
        t = self.peek()
        if t.kind == "OP" and t.val == v:
            return self.next()
        self.err(f"expected '{v}'" + (f" {what}" if what else "") + f" but found {self.describe(t)}")

    def expect_name(self, v):
        t = self.peek()
        if t.kind == "NAME" and t.val == v:
            return self.next()
        self.err(f"expected '{v}' but found {self.describe(t)}")

    def expect_ident(self, what="a name"):
        t = self.peek()
        if t.kind == "NAME" and t.val not in HARD:
            return self.next()
        self.err(f"expected {what} but found {self.describe(t)}")

    def describe(self, t):
        if t.kind in ("NL",):
            return "end of line"
        if t.kind == "INDENT":
            return "an indent"
        if t.kind == "DEDENT":
            return "a dedent"
        if t.kind == "EOF":
            return "end of file"
        if t.kind == "STR":
            return "a string"
        return repr(t.val)

    def skip_nl(self):
        while self.peek().kind == "NL":
            self.next()

    def is_ident_tok(self, t):
        return t.kind == "NAME" and t.val not in HARD

    # ---------------------------------------------------------------- types
    NOT_TYPE_WORDS = ("where", "in", "then", "do", "else", "if", "elif", "and", "or", "not", "is", "as")

    def type_follows(self, k=0):
        """True when the token at offset k can begin a type that follows a declared name (`x Int`, `xs ...Int`, `f (A) -> B`)."""
        t = self.peek(k)
        if t.kind == "NAME":
            return t.val not in self.NOT_TYPE_WORDS
        return t.kind == "OP" and (t.val == "..." or (t.val in ("(", "[") and t.sp))

    RECORD = None       # a list while tools/declcolon.py converts old source: old colons are recorded and skipped, not errors

    def no_decl_colon(self, what="a declaration"):
        if self.at_op(":"):
            if PBase.RECORD is not None:
                PBase.RECORD.append(("decl", self.next()))
                return
            self.err(f"{what} has no colon: write the name and then its type, as in `x Int`")

    def colon_label_at(self, k, msg):
        """A name followed by an old-style colon at offset k (declaration position): an error, or in record mode skipped."""
        if self.peek(k).kind == "NAME" and self.at_op(":", k + 1):
            if PBase.RECORD is not None:
                PBase.RECORD.append(("decl", self.peek(k + 1)))
                return True
            self.err(msg, self.peek(k + 1))
        return False

    def parse_type(self):
        t = self.parse_type_fn()
        if self.at_op("|"):
            members = [t]
            while self.eat_op("|"):
                members.append(self.parse_type_fn())
            return TUnion(members, line=t.line)
        return t

    def parse_type_fn(self, inner=False):
        line = self.peek().line
        t = self.parse_type_prim()
        if self.at_op("->"):
            self.next()
            ret = self.parse_type_fn(inner=True)
            if isinstance(t, TTuple):
                f = TFn(t.items, ret, None, line=line)
            else:
                f = TFn([(None, t)], ret, None, line=line)
            if not inner and self.at_name("with") and self.at_op("(", 1):
                self.next()
                f.caps = self.parse_caps()
            return f
        return t

    def parse_caps(self):
        """`with (Int, String)` after a function type: the types of the values a closure of this type captures (order does not matter)."""
        self.expect_op("(")
        out = []
        while not self.at_op(")"):
            out.append(self.parse_type())
            if not self.eat_op(","):
                break
        self.expect_op(")")
        return out

    def parse_type_prim(self):
        t = self.peek()
        line = t.line
        if t.kind == "OP" and t.val == "[":
            # a type lambda:  [A] -> Result[String, A]   or   [M[_], A] -> StateT[M, Int, A]
            params = self.parse_tparams_v2()
            self.expect_op("->")
            return TLambda(params, self.parse_type_fn(), line=line)
        if t.kind == "OP" and t.val == "(":
            self.next()
            items = []
            if self.eat_op(")"):
                return TUnit(line=line)
            while True:
                label = None
                if self.at_op("..."):                       # (H, ...Rest): the rest of a tuple type, in a type function
                    self.next()
                    if self.at_op(")") or self.at_op(","):  # (name String, ...): any tuple that has at least these fields
                        items.append(("...", None))
                        if not self.eat_op(","):
                            break
                        continue
                    items.append(("...", self.parse_type()))
                    if not self.eat_op(","):
                        break
                    continue
                colon = self.colon_label_at(0, "a tuple type has no colon: write `(name String, age Int)`")
                if self.peek().kind == "NAME" and (colon or (self.peek().val not in ("any", "static") and self.type_follows(1))):
                    label = self.next().val
                    if colon:
                        self.next()
                items.append((label, self.parse_type()))
                if not self.eat_op(","):
                    break
                if self.at_op(")"):                         # (Bool,): a trailing comma makes a one-item tuple type
                    break
            self.expect_op(")")
            if len(items) == 1 and items[0][0] is None and items[0][1].__class__ is TLambda and self.at_op("[") and not self.peek().sp:
                groups = []
                while self.at_op("[") and not self.peek().sp:
                    groups.append(self.parse_targ_group())
                return TApp(items[0][1], groups, line=line)
            return TTuple(items, line=line)
        if t.kind == "OP" and t.val == "...":
            self.err("unexpected '...' in a type")
        if t.kind == "NAME":
            if t.val == "_":
                self.next()
                return THole(line=line)
            if t.val == "any" and self.peek(1).kind == "NAME" and self.peek(1).val not in HARD:
                self.next()
                first = self.parse_type_prim()
                also = []
                while self.at_op("+") and self.peek(1).kind == "NAME" and self.peek(1).val not in HARD:
                    self.next()                                  # any A + B: a value that implements both
                    also.append(self.parse_type_prim())
                return TAny(first, also, line=line)
            if t.val == "static":
                self.next()
                return TStatic(self.parse_type_prim(), line=line)
            if t.val in HARD and t.val not in ("Self", "self"):
                self.err(f"expected a type but found {self.describe(t)}")
            path = [self.next().val]
            while self.at_op(".") and self.peek(1).kind == "NAME":
                self.next()
                path.append(self.next().val)
            # receiver function type:  Config.() -> Config
            if self.at_op(".") and self.at_op("(", 1):
                self.next()
                self.next()
                params = []
                if not self.at_op(")"):
                    while True:
                        label = None
                        colon = self.colon_label_at(0, "a function type has no colon: write `(x Int) -> Int`")
                        if self.peek().kind == "NAME" and (colon or (self.peek().val not in ("any", "static") and self.type_follows(1))):
                            label = self.next().val
                            if colon:
                                self.next()
                        params.append((label, self.parse_type()))
                        if not self.eat_op(","):
                            break
                self.expect_op(")")
                self.expect_op("->")
                ret = self.parse_type_fn()
                return TFn(params, ret, TName(path, [], line=line), line=line)
            groups = []
            while self.at_op("[") and not self.peek().sp:
                groups.append(self.parse_targ_group())
            return TName(path, groups, line=line)
        self.err(f"expected a type but found {self.describe(t)}")

    def parse_targ_group(self):
        self.expect_op("[")
        args = []
        save_nt, save_ns = self.no_trailing, self.nl_stop
        self.no_trailing = False
        self.nl_stop = False
        if not self.at_op("]"):
            while True:
                args.append(self.parse_targ())
                if not self.eat_op(","):
                    break
        self.expect_op("]")
        self.no_trailing, self.nl_stop = save_nt, save_ns
        return args

    def unit_power_group(self):
        """A unit with a power in a type argument (`m/s^2`, `(m/s)^2`): `^` binds to the unit before it, and parentheses distribute,
        so the tree comes out as products and quotients of `unit^n` (the expression parser would read `^` as the lowest-precedence xor)."""
        i, depth, has_pow = 0, 0, False
        while True:
            t = self.peek(i)
            if t.kind == "OP" and t.val == "(":
                depth += 1
            elif t.kind == "OP" and t.val == ")":
                depth -= 1
            elif depth == 0 and t.kind == "OP" and t.val in (",", "]"):
                break
            elif t.kind == "OP" and t.val == "^":
                has_pow = True
            elif not (t.kind in ("NAME", "INT") or t.kind == "OP" and t.val in ("*", "/")):
                return None
            if t.kind == "EOF" or depth < 0:
                return None
            i += 1
        if not has_pow:
            return None
        save = self.p

        def expr():
            fs = term()
            while self.peek().kind == "OP" and self.peek().val in ("*", "/"):
                sign = 1 if self.next().val == "*" else -1
                fs += [(n, sign * e) for n, e in term()]
            return fs

        def term():
            t = self.next()
            if t.kind == "NAME":
                fs = [(t.val, 1)]
            elif t.kind == "INT" and t.val == 1:
                fs = []
            elif t.kind == "OP" and t.val == "(":
                fs = expr()
                self.expect_op(")")
            else:
                raise MoxieSyntaxError("a unit is a name, `1`, or a parenthesised unit expression", t.line)
            if self.peek().kind == "OP" and self.peek().val == "^":
                self.next()
                k = self.next()
                if k.kind != "INT":
                    raise MoxieSyntaxError("a unit power is a whole number: `s^2`", k.line)
                fs = [(n, e * k.val) for n, e in fs]
            return fs
        try:
            fs = expr()
        except MoxieSyntaxError:
            self.p = save
            return None
        if not (self.at_op(",") or self.at_op("]")):
            self.p = save
            return None
        line = self.peek().line
        e = None
        for n, x in fs:
            node = Name(n, line=line) if abs(x) == 1 else Binary("^", Name(n, line=line), IntLit(abs(x), None, line=line), line=line)
            if e is None:
                e = node if x > 0 else Binary("/", IntLit(1, None, line=line), node, line=line)
            else:
                e = Binary("*" if x > 0 else "/", e, node, line=line)
        return TExpr(e, line=line) if e is not None else None

    def parse_targ(self):
        u = self.unit_power_group()
        if u is not None:
            return u
        save = self.p
        try:
            t = self.parse_type()
            if self.at_op(",") or self.at_op("]"):
                return t
        except MoxieSyntaxError:
            pass
        self.p = save
        e = self.parse_expr()
        return TExpr(e, line=e.line)

    # ----------------------------------------------------------- type params
    def parse_tparams(self):
        """[T, N where N > 0, F[_] Monad, S Speaker[T]]"""
        self.expect_op("[")
        out = []
        where = None
        while not self.at_op("]"):
            name = self.expect_ident("a type parameter name").val
            holes = 0
            if self.at_op("["):
                self.next()
                holes = 1
                while self.eat_op(","):
                    holes += 1
                # consume the underscores
                self.p -= 0
                # (the first '_' was consumed as part of the loop below)
            tp = TParam(name, holes, [], None)
            if holes:
                pass
            self.no_decl_colon("a type parameter bound")
            if self.type_follows() and not self.at_name("where"):
                tp.bounds.append(self.parse_type_prim())
                while self.eat_op("+"):
                    tp.bounds.append(self.parse_type_prim())
            if self.at_name("where"):
                self.next()
                w = self.parse_expr()
                tp.where = w
                where = w
            out.append(tp)
            if not self.eat_op(","):
                break
        self.expect_op("]")
        return out

    def parse_hole_kind(self):
        """One entry of a constructor parameter's kind: `_`, or `_[_, ...]` for a parameter that is itself a constructor."""
        self.expect_name("_")
        if self.at_op("[") and not self.peek().sp:
            self.next()
            while True:
                self.parse_hole_kind()
                if not self.eat_op(","):
                    break
            self.expect_op("]")

    def parse_tparams_v2(self):
        """Proper parser for type parameter lists."""
        self.expect_op("[")
        out = []
        while not self.at_op("]"):
            name = self.expect_ident("a type parameter name").val
            holes = 0
            if self.at_op("[") and not self.peek().sp:
                self.next()
                while True:
                    self.parse_hole_kind()
                    holes += 1
                    if not self.eat_op(","):
                        break
                self.expect_op("]")
            tp = TParam(name, holes, [], None)
            self.no_decl_colon("a type parameter bound")
            if self.type_follows() and not self.at_name("where"):
                tp.bounds.append(self.parse_type_prim())
                while self.eat_op("+"):
                    tp.bounds.append(self.parse_type_prim())
            if self.at_name("where"):
                self.next()
                tp.where = self.parse_expr()
            out.append(tp)
            if not self.eat_op(","):
                break
        self.expect_op("]")
        return out

    # -------------------------------------------------------------- patterns
    def parse_pattern(self):
        """One pattern.  Alternatives nested in it (`Some(1 | 2)`) are only for a `when` arm or an `is` test, which call
        `parse_pattern_alts`; anywhere else they are an error."""
        alts = self.parse_pattern_alts(top=False)
        if len(alts) > 1:
            self.err("alternatives (`|`) are only for a `when` arm and an `is` test")
        return alts[0]

    def parse_pattern_alts(self, top=True):
        """The patterns of `A | B` (joined at the top), with alternatives nested inside a pattern expanded: `Some(1 | 2)` is
        `Some(1)` and `Some(2)`, and `(1 | 2, x | y)` is four tuples."""
        out = self.expand_or(self.parse_pattern_primary())
        while top and self.eat_op("|"):
            out += self.expand_or(self.parse_pattern_primary())
        return out

    def parse_pattern_nested(self):
        p = self.parse_pattern_primary()
        if self.at_op("|"):
            alts = [p]
            while self.eat_op("|"):
                alts.append(self.parse_pattern_primary())
            return POrN(alts, line=getattr(p, "line", 0))
        return p

    MAX_ALTS = 512

    def expand_or(self, p):
        """The list of patterns a pattern with nested alternatives stands for (a copy for each combination)."""
        import copy
        c = p.__class__
        if c is POrN:
            return [q for a in p.alts for q in self.expand_or(a)]
        if c in (PTuple, PCon):
            field = "items" if c is PTuple else "args"
            kids = getattr(p, field) or []
            if not any(self._has_or(q) for _l, q in kids):
                return [p]
            combos = [[]]
            for lab, q in kids:
                exp = self.expand_or(q)
                if len(combos) * len(exp) > self.MAX_ALTS:
                    self.err(f"this pattern's alternatives multiply into more than {self.MAX_ALTS} combinations: split it into separate arms")
                combos = [cb + [(lab, a)] for cb in combos for a in exp]
            out = []
            for cb in combos:
                n = copy.copy(p)
                setattr(n, field, cb)
                out.append(n)
            return out
        if c in (PAs, PTyped) and self._has_or(p.pat):
            out = []
            for a in self.expand_or(p.pat):
                n = copy.copy(p)
                n.pat = a
                out.append(n)
            return out
        return [p]

    def _has_or(self, p):
        c = p.__class__
        if c is POrN:
            return True
        if c in (PTuple, PCon):
            return any(self._has_or(q) for _l, q in (p.items if c is PTuple else p.args) or [])
        if c in (PAs, PTyped):
            return self._has_or(p.pat)
        return False

    BIN_KINDS = {f"{sg}{w}{en}" for sg in "ui" for w in (16, 32, 64) for en in ("be", "le")} | {"u8", "i8"}

    def parse_bin_pattern(self, line):
        """Bin(0xCA, version: bits(4), kind: bits(4), len: u16be, body: bytes(len), rest: bytes)  (Spec section 8)."""
        self.next()
        self.expect_op("(")
        elems, names, bitrun = [], set(), 0
        while not self.at_op(")"):
            t = self.peek()
            if t.kind == "INT":
                self.next()
                if not 0 <= t.val <= 255:
                    self.err("a literal in a Bin pattern is one byte (0 to 255); write several, or use b\"...\"")
                elems.append(("lit", [t.val]))
                bitrun_ok = bitrun % 8 == 0
            elif t.kind == "BYTES":
                self.next()
                elems.append(("lit", list(t.val)))
                bitrun_ok = bitrun % 8 == 0
            elif t.kind == "NAME":
                name = self.next().val
                self.expect_op(":")
                kt = self.peek()
                if kt.kind != "NAME":
                    self.err("expected a Bin kind such as u8, u16be, bits(4), or bytes(n)")
                kind = self.next().val
                arg = None
                if kind in ("bits", "bytes") and self.at_op("("):
                    self.next()
                    at = self.peek()
                    if at.kind == "INT":
                        arg = self.next().val
                    elif at.kind == "NAME" and at.val in names:
                        arg = self.next().val
                    else:
                        self.err(f"the size of {kind}(...) is a number or an earlier field")
                    self.expect_op(")")
                if kind == "bits":
                    if not isinstance(arg, int) or not 1 <= arg <= 64:
                        self.err("bits(n) needs a literal n from 1 to 64")
                elif kind == "bytes":
                    pass
                elif kind not in self.BIN_KINDS:
                    self.err(f"unknown Bin kind '{kind}' (u8, i8, u16be, u16le, ..., bits(n), bytes(n))")
                nm = None if name == "_" else name
                if nm is not None:
                    if nm in names:
                        self.err(f"the name '{nm}' is used twice in this Bin pattern")
                    names.add(nm)
                elems.append(("field", nm, kind, arg))
                bitrun_ok = True
                if kind == "bits":
                    bitrun += arg
                else:
                    if bitrun % 8:
                        self.err("the bit fields before this one do not add up to whole bytes")
                    bitrun = 0
            else:
                self.err("expected a byte, a name, or ')' in a Bin pattern")
            if elems[-1][0] == "lit" and bitrun % 8:
                self.err("the bit fields before this literal do not add up to whole bytes")
            if not self.eat_op(","):
                break
        self.expect_op(")")
        if bitrun % 8:
            self.err("the bit fields in this Bin pattern do not add up to whole bytes")
        for i, e in enumerate(elems):
            if e[0] == "field" and e[2] == "bytes" and e[3] is None and i != len(elems) - 1:
                self.err("bytes with no size takes the rest, so it must be the last element")
        return PBin(elems, line=line)

    def parse_in_pattern(self, neg, line):
        """`in RANGE ->` and `not in RANGE ->`: the arm matches when the value is in the range (or any collection).  Literal
        number bounds stay a range pattern, so the compiler can still see which numbers the arms cover."""
        save = self.p
        t = self.peek()
        if not neg and (t.kind in ("INT", "FLOAT", "CHAR") or (t.kind == "OP" and t.val in ("-", "..", "..="))):
            try:
                if t.kind == "OP" and t.val in ("..", "..="):
                    self.next()
                    hi = self._pat_lit_expr()
                    pr = PRange(None, hi, t.val == "..=", self._pat_step(), line=line)
                else:
                    lit = self._pat_lit_expr()
                    pr = self._range_tail(PLit(lit, line=line), lit, allow=True)
                nx = self.peek()
                if pr.__class__ is PRange and ((nx.kind == "OP" and nx.val in ("->", ",", "|")) or (nx.kind == "NAME" and nx.val == "if")):
                    return pr
            except MoxieSyntaxError:
                pass
            self.p = save
        e = self.parse_header_expr()
        return PIn(e, neg, line=line)

    def _pat_step(self):
        t0, t1 = self.peek(), self.peek(1)
        if t0.kind == "NAME" and t0.val == "step" and (t1.kind == "INT" or (t1.kind == "OP" and t1.val == "-" and not self.peek(2).sp)):
            self.next()
            return self._pat_lit_expr()
        return None

    def parse_pattern_primary(self):
        t = self.peek()
        line = t.line
        if t.kind == "NAME" and t.val == "in":
            self.next()
            return self.parse_in_pattern(False, line)
        if t.kind == "NAME" and t.val == "not" and self.peek(1).kind == "NAME" and self.peek(1).val == "in":
            self.next()
            self.next()
            return self.parse_in_pattern(True, line)
        if t.kind == "NAME":
            v = t.val
            if v == "_":
                self.next()
                return PWild(line=line)
            if v in ("true", "false"):
                self.next()
                return PLit(BoolLit(v == "true", line=line), line=line)
            if v in HARD and v not in ("Self", "self"):
                self.err(f"expected a pattern but found '{v}'")
            if v == "Bin" and self.at_op("(", 1):
                return self.parse_bin_pattern(line)
            if self.at_op("@", 1):
                self.next()
                self.next()
                return PAs(v, self.parse_pattern_primary(), line=line)
            path = [self.next().val]
            while self.at_op(".") and self.peek(1).kind == "NAME":
                self.next()
                path.append(self.next().val)
            if self.at_op("[") and not self.peek().sp and path[-1][:1].isupper():
                groups = []                                  # `List[Int] ->`: a type with arguments, as a union member pattern
                while self.at_op("[") and not self.peek().sp:
                    groups.append(self.parse_targ_group())
                return PTyped(PWild(line=line), TName(path, groups, line=line), line=line)
            if self.at_op("(") and not self.peek().sp or (self.at_op("(") and v[:1].isupper()):
                self.next()
                args = self.parse_pattern_args(path == ["Dict"])
                return PCon(path, args, line=line)
            if len(path) == 1 and not v[:1].isupper():
                return PBind(v, line=line)
            return PCon(path, None, line=line)
        if t.kind == "OP":
            if t.val == "^":
                self.next()
                if self.eat_op("("):
                    save_nt = self.no_trailing
                    self.no_trailing = False
                    e = self.parse_expr()
                    self.no_trailing = save_nt
                    self.expect_op(")")
                else:
                    nm = self.expect_ident().val
                    e = Name(nm, line=line)
                return PPin(e, line=line)
            if t.val == "(":
                self.next()
                items = []
                if self.eat_op(")"):
                    return PTuple([], line=line)
                while True:
                    label = None
                    if self.peek().kind == "NAME" and self.at_op(":", 1):
                        label = self.next().val
                        self.next()
                    if self.at_op("...") or self.at_op("*"):
                        self.next()
                        nm = None if self.at_op(",") or self.at_op(")") else self.next().val      # a bare `...` (or `*`) skips the rest
                        items.append((label, PRest(nm, line=line)))
                    else:
                        items.append((label, self.parse_pattern_nested()))
                    if not self.eat_op(","):
                        break
                self.expect_op(")")
                if len(items) == 1 and items[0][0] is None and not isinstance(items[0][1], PRest):
                    return items[0][1]
                return PTuple(items, line=line)
            if t.val == "-" and self.peek(1).kind in ("INT", "FLOAT"):
                self.next()
                n = self.next()
                lit = IntLit(-n.val, n.extra, line=line) if n.kind == "INT" else FloatLit(-n.val, n.extra, line=line)
                return self._range_tail(PLit(lit, line=line), lit)
            if t.val in (">=", ">", "<=", "<"):
                self.next()
                nt = self.peek()
                if nt.kind == "OP" and nt.val == "^":
                    self.next()
                    if self.eat_op("("):
                        save_nt = self.no_trailing
                        self.no_trailing = False
                        e = self.parse_expr()
                        self.no_trailing = save_nt
                        self.expect_op(")")
                    else:
                        e = Name(self.expect_ident().val, line=line)
                elif nt.kind == "NAME" and nt.val[:1].isupper():
                    e = Name(self.next().val, line=line)
                else:
                    e = self._pat_lit_expr()
                return PRel(t.val, e, line=line)
            if t.val in ("..", "..="):
                self.err("a range in a pattern is written with `in`: `in ..9 -> ...`")
        if t.kind == "STR" and any(not isinstance(x, str) for x in t.val):
            self.next()
            return self.parse_string_pattern(t, line)
        if t.kind in ("INT", "FLOAT", "STR", "CHAR", "HASH", "DEC"):
            self.next()
            lit = self._lit_from_tok(t)
            return self._range_tail(PLit(lit, line=line), lit)
        self.err(f"expected a pattern but found {self.describe(t)}")

    HOLE_TYPES = ("Int", "Double", "Float", "Bool", "String")

    def parse_string_pattern(self, tok, line):
        """`"--port=${p Int}"`, `"${stem}.mxi"`: literal text with holes that bind.  A hole is `${name}` (a String) or `${name Type}`
        (Int, Double or Bool: the text must read as one); `${_}` skips.  Holes need literal text between them."""
        parts = []
        for part in tok.val:
            if isinstance(part, str):
                if parts and isinstance(parts[-1], str):
                    parts[-1] += part
                else:
                    parts.append(part)
                continue
            _k, src, spec, pline = part
            words = src.split()
            if spec or not 1 <= len(words) <= 2 or not (words[0] == "_" or (words[0][:1].islower() and words[0].replace("_", "a").isalnum())):
                self.err("a hole in a string pattern is `${name}` or `${name Type}`", tok)
            if len(words) == 2 and words[1] not in self.HOLE_TYPES:
                self.err(f"a hole in a string pattern can be typed `Int`, `Double`, `Bool` or `String`, not `{words[1]}`", tok)
            if parts and not isinstance(parts[-1], str):
                self.err("two holes in a string pattern need literal text between them: there is no way to tell where one ends", tok)
            parts.append((words[0], words[1] if len(words) == 2 else None))
        names = [x[0] for x in parts if not isinstance(x, str) and x[0] != "_"]
        if len(set(names)) != len(names):
            self.err("a name is bound twice in this string pattern", tok)
        return PStr(parts, line=line)

    def _pat_lit_expr(self):
        t = self.next()
        neg = False
        if t.kind == "OP" and t.val == "-":
            neg = True
            t = self.next()
        lit = self._lit_from_tok(t)
        if neg:
            lit = IntLit(-lit.v, lit.suffix, line=t.line) if isinstance(lit, IntLit) else FloatLit(-lit.v, lit.suffix, line=t.line)
        return lit

    def _range_tail(self, plit, lo, allow=False):
        if self.at_op("..") or self.at_op("..="):
            if not allow:
                self.err("a range in a pattern is written with `in`: `in 1..9 -> ...` (or `not in 1..9 -> ...`)")
            op = self.next().val
            nt = self.peek()
            if nt.kind in ("INT", "FLOAT", "CHAR") or (nt.kind == "OP" and nt.val == "-"):
                hi = self._pat_lit_expr()
            else:
                hi = None
            return PRange(lo, hi, op == "..=", self._pat_step(), line=plit.line)
        return plit

    def parse_pattern_args(self, dict_entries=False):
        args = []
        if self.eat_op(")"):
            return args
        save_nt = self.no_trailing
        self.no_trailing = False
        while True:
            label = None
            if self.at_op("...") or self.at_op("*"):
                self.next()
                nm = None if self.at_op(",") or self.at_op(")") else self.next().val          # a bare `...` (or `*`) skips the rest
                args.append((None, PRest(nm, line=self.peek().line)))
            else:
                if dict_entries and self.peek().kind in ("NAME", "STR") and self.at_op(":", 1):
                    if PBase.RECORD is not None:
                        PBase.RECORD.append(("dict", self.peek(1)))
                    else:
                        self.err("a `Dict` pattern entry is written `key -> value`, not `key: value`", self.peek(1))
                if (self.peek().kind in ("NAME", "STR")) and (self.at_op(":", 1) or (dict_entries and self.at_op("->", 1))):
                    t = self.next()
                    label = t.val if t.kind == "NAME" else "".join(p for p in t.val if isinstance(p, str))
                    self.next()
                args.append((label, self.parse_pattern_nested()))
            if not self.eat_op(","):
                break
        self.no_trailing = save_nt
        self.expect_op(")")
        return args

    def _lit_from_tok(self, t):
        k = t.kind
        if k == "INT":
            return IntLit(t.val, t.extra, line=t.line)
        if k == "FLOAT":
            return FloatLit(t.val, t.extra, line=t.line)
        if k == "DEC":
            return DecLit(t.val, line=t.line)
        if k == "STR":
            return StrLit(self.convert_parts(t.val, t), line=t.line)
        if k == "CHAR":
            return CharLit(t.val, line=t.line)
        if k == "HASH":
            return KwLit(t.val, line=t.line)
        self.err("expected a literal", t)

    def convert_parts(self, parts, tok):
        out = []
        for part in parts:
            if isinstance(part, str):
                out.append(part)
            else:
                _, src, spec, line = part
                sub = type(self)(tokenize(src, self.file), self.file)
                sub.units = self.units                  # `${d in km}` in a string knows the units declared so far
                for tk in sub.toks:
                    tk.line = line
                outer = PBase.RECORD
                if outer is not None:
                    PBase.RECORD = []
                try:
                    e = sub.parse_expr()
                    sub.skip_nl()
                    if sub.peek().kind != "EOF":
                        sub.err("unexpected text in interpolation")
                finally:
                    if outer is not None:
                        inner, PBase.RECORD = PBase.RECORD, outer
                        if inner and "\n" not in src:
                            outer.append(("interp", line, src, edit_row(src, {(t.col): k for k, t in inner})))
                out.append(Interp(e, spec, src, line=line))
        return out
