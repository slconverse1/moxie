"""Expression parser (mixin)."""
from .pbase import PBase, HARD
from .lexer import MoxieSyntaxError
from .ast import *   # noqa

T_PIPE, T_OR, T_AND, T_COMP, T_RANGE, T_BT, T_BOR, T_BXOR, T_BAND, T_SHIFT, T_ADD, T_MUL, T_OTHER = range(13)

COMP_OPS = {"==", "~=", "<", ">", "<=", ">=", "<$>", "<*>", "<~"}
BINTIER = {
    "|": T_BOR, "|>>": T_BOR, "^": T_BXOR, "&": T_BAND, "<<": T_SHIFT, ">>": T_SHIFT,
    "+": T_ADD, "-": T_ADD, "*": T_MUL, "/": T_MUL, "%": T_MUL, "~>": T_OTHER, "+%": T_OR, "-%": T_OR,
    "..": T_RANGE, "..=": T_RANGE,
}
for _o in COMP_OPS:
    BINTIER[_o] = T_COMP


def contains_ph(e):
    """True when e holds a placeholder that is not inside a nested lambda."""
    if isinstance(e, PH):
        return True
    if isinstance(e, Lambda):
        return False
    if isinstance(e, N):
        for f in e._fields:
            if contains_ph(getattr(e, f, None)):
                return True
        return False
    if isinstance(e, (list, tuple)):
        for x in e:
            if contains_ph(x):
                return True
    return False


def max_ph(e):
    if isinstance(e, PH):
        return e.idx
    if isinstance(e, Lambda):
        return 0
    m = 0
    if isinstance(e, N):
        for f in e._fields:
            m = max(m, max_ph(getattr(e, f, None)))
    elif isinstance(e, (list, tuple)):
        for x in e:
            m = max(m, max_ph(x))
    return m


def split_sql(text, parser):
    """Split SQL text into literal strings and parameter expressions ($name or ${expr})."""
    import re
    from .lexer import tokenize
    out = []
    i = 0
    n = len(text)
    buf = []
    while i < n:
        c = text[i]
        if c == "$" and i + 1 < n:
            if text[i + 1] == "{":
                j = text.index("}", i)
                src = text[i + 2:j]
                sub = type(parser)(tokenize(src), parser.file)
                out.append("".join(buf)); buf = []
                out.append(("param", sub.parse_expr()))
                i = j + 1
                continue
            m = re.match(r"[A-Za-z_][A-Za-z_0-9]*", text[i + 1:])
            if m:
                out.append("".join(buf)); buf = []
                out.append(("param", Name(m.group(0))))
                i += 1 + len(m.group(0))
                continue
        buf.append(c)
        i += 1
    out.append("".join(buf))
    return [p for p in out if p != ""]


def ph_lambda(body, line):
    n = max(1, max_ph(body))
    params = [Param(None, f"_{i}", None, None, None, False, line=line) for i in range(1, n + 1)]
    return Lambda(params, body, None, None, None, line=line)


class ExprParser(PBase):
    stop_bol = 0

    # ------------------------------------------------------------ entry
    def parse_expr(self):
        return self.parse_bin(T_PIPE)

    def parse_bin(self, minp):
        if minp == T_PIPE:
            left = self.parse_bin(T_OR)
            while self.at_op("|>") and not (self.stop_bol and self.peek().bol):
                line = self.next().line
                self.skip_nl_soft()
                stage = self.parse_pipe_stage()
                left = Pipe(left, stage, line=line)
            return left
        left = self.parse_unary() if minp > T_OTHER else None
        return self._bin_loop(minp)

    def skip_nl_soft(self):
        pass

    def parse_pipe_stage(self):
        if self.at_name("seq") and self.nl_indent_at(1):
            line = self.next().line
            self.expect_nl_indent()
            arms = []
            while self.peek().kind != "DEDENT":
                self.skip_nl()
                if self.peek().kind == "DEDENT":
                    break
                if self.at_name("else"):                                     # `else stage` runs only when no earlier arm applied
                    self.next()
                    self.no_block_colon()
                    pred = None
                else:
                    save = self.no_trailing
                    self.no_trailing = True
                    pred = self.parse_expr()
                    self.no_trailing = save
                if pred is not None:
                    self.expect_op("->")
                save = self.stop_bol
                self.stop_bol += 1
                stage = self.parse_pipe_stage_inner()
                self.stop_bol = save
                arms.append((pred, stage))
                self.end_line()
                if pred is None:
                    self.after_else_arm()
            self.expect_dedent()
            return SeqE(arms, line=line)
        return self.parse_pipe_stage_inner()

    def parse_pipe_stage_inner(self):
        save = self.stop_bol
        self.stop_bol += 1
        e = self.parse_postfix()
        self.stop_bol = save
        return e

    def _bin_loop(self, minp):
        # operator precedence climbing from tier T_OR upward
        return self._climb(max(minp, T_OR))

    def _tier_of(self, t):
        if t.kind == "OP":
            if t.val == "|>":
                return None
            return BINTIER.get(t.val)
        if t.kind == "BTICK":
            return T_BT
        if t.kind == "NAME":
            if t.val == "and":
                return T_AND
            if t.val == "or":
                return T_OR
            if t.val in ("in", "is"):
                return T_COMP
            if t.val == "not" and self.peek(1).kind == "NAME" and self.peek(1).val == "in":
                return T_COMP
        return None

    def _climb(self, minp):
        left = self.parse_unary()
        while True:
            t = self.peek()
            if self.stop_bol and t.bol:
                break
            tier = self._tier_of(t)
            if tier is None or tier < minp:
                break
            # a '-' or '&' etc. at start of a continuation line is still binary
            line = t.line
            if t.kind == "NAME" and t.val in ("and", "or"):
                self.next()
                right = self._climb(tier + 1)
                left = (AndE if t.val == "and" else OrE)(left, right, line=line)
            elif t.kind == "NAME" and t.val == "is":
                self.next()
                pat = self.parse_pattern()
                left = IsOp(left, pat, line=line)
            elif t.kind == "NAME" and (t.val == "in" or t.val == "not"):
                neg = False
                if t.val == "not":
                    self.next()
                    neg = True
                self.next()
                right = self._climb(tier + 1)
                left = InOp(left, right, neg, line=line)
            elif t.kind == "BTICK":
                self.next()
                right = self._climb(tier + 1)
                left = Tick(left, t.val, right, line=line)
            elif t.val in ("..", "..="):
                self.next()
                nt = self.peek()
                hi = None
                if not self._ends_operand(nt):
                    hi = self._climb(tier + 1)
                left = RangeE(left, hi, t.val == "..=", line=line)
            elif t.val in ("+%", "-%"):
                self.next()
                right = self._climb(tier + 1)
                left = self.listener_op(t.val, left, right, line)
            else:
                self.next()
                right = self._climb(tier + 1)
                left = Binary(t.val, left, right, line=line)
        return left

    def listener_op(self, op, l, r, line):
        """`thing.prop +% handler` subscribes to a property (`on_change`), `thing.prop -% token` unsubscribes (`off_change`)."""
        if l.__class__ is not Field or not isinstance(l.name, str):
            self.err(f"`{op}` goes after a property: `thing.property {op} " + ("handler" if op == "+%" else "token") + "`")
        if op == "+%":
            return Call(Name("on_change", line=line), [Arg(None, l.obj, None, line=line),
                                                        Arg(None, StrLit([l.name], line=line), None, line=line),
                                                        Arg(None, r, None, line=line)], None, line=line)
        return Call(Name("off_change", line=line), [Arg(None, l.obj, None, line=line), Arg(None, r, None, line=line)], None, line=line)

    def _ends_operand(self, t):
        if t.kind in ("NL", "DEDENT", "INDENT", "EOF"):
            return True
        if t.kind == "OP" and t.val in (")", "]", ",", ":", "->", ";", "}"):
            return True
        if t.kind == "NAME" and t.val in ("else", "elif", "and", "or", "if"):
            return True
        return False

    # ------------------------------------------------------------ unary
    def parse_unary(self):
        t = self.peek()
        line = t.line
        if t.kind == "NAME" and t.val == "not":
            if not (self.peek(1).kind == "NAME" and self.peek(1).val == "in"):
                self.next()
                return Unary("not", self.parse_unary(), line=line)
        if t.kind == "OP":
            if t.val == "-":
                self.next()
                nt = self.peek()
                if nt.kind in ("INT", "FLOAT", "DEC") and not nt.sp:
                    # negative literal: let postfix operations see the literal
                    e = self.parse_postfix()
                    if isinstance(e, IntLit):
                        return IntLit(-e.v, e.suffix, line=line)
                    if isinstance(e, FloatLit):
                        return FloatLit(-e.v, e.suffix, line=line)
                    return Unary("-", e, line=line)
                return Unary("-", self.parse_unary(), line=line)
            if t.val == "~":
                self.next()
                return Unary("~", self.parse_unary(), line=line)
            if t.val == "@":
                self.next()
                return Deref(self.parse_unary(), line=line)
            if t.val == "+":
                self.next()
                return self.parse_unary()
            if t.val in ("..", "..="):
                self.next()
                hi = None
                if not self._ends_operand(self.peek()):
                    hi = self._climb(T_RANGE + 1)
                return RangeE(None, hi, t.val == "..=", line=line)
            if t.val == "/" and self.peek(1).kind == "NAME" and not self.peek(1).sp:
                segs = []
                while self.at_op("/") and self.peek(1).kind == "NAME" and not self.peek(1).sp:
                    self.next()
                    segs.append(self.next().val)
                return PathE(segs, line=line)
        return self.parse_postfix()

    # ------------------------------------------------------------ postfix
    def parse_postfix(self):
        e = self.parse_atom()
        return self.postfix_loop(e)

    def postfix_loop(self, e):
        while True:
            t = self.peek()
            if t.kind != "OP":
                break
            if self.stop_bol and t.bol and t.val not in (".",):
                break
            v = t.val
            if v == "(" and not t.sp:
                e = self.parse_call(e)
            elif v == "[" and not t.sp and self._can_generic(e):
                groups = []
                while self.at_op("[") and not self.peek().sp:
                    groups.append(self.parse_targ_group())
                e = GenApp(e, groups, line=t.line)
            elif v == ".":
                nt = self.peek(1)
                if nt.kind == "NAME":
                    self.next()
                    self.next()
                    name = nt.val
                    if (name == "do" and (self.at_block() or self.at_op("->"))) or (name == "update" and (self.at_block() or (self.peek().kind == "NAME" and self.at_op(":", 1)))):
                        e = self.parse_recv_block(e, name, nt.line)
                    else:
                        e = Field(e, name, line=nt.line)
                elif nt.kind == "INT":
                    self.next()
                    self.next()
                    e = Field(e, nt.val, line=nt.line)
                elif nt.kind == "OP" and nt.val == "(":
                    break
                else:
                    break
            elif v == "?":
                self.next()
                e = Q(e, line=t.line)
            else:
                break
        return e

    def _can_generic(self, e):
        if isinstance(e, Name):
            return True
        if isinstance(e, Field):
            return self._can_generic(e.obj)
        if isinstance(e, GenApp):
            return True
        return False

    def matching(self, k):
        """Index of the token matching the opening bracket at offset k."""
        depth = 0
        i = self.p + k
        while i < len(self.toks):
            t = self.toks[i]
            if t.kind == "OP":
                if t.val in ("(", "[", "{"):
                    depth += 1
                elif t.val in (")", "]", "}"):
                    depth -= 1
                    if depth == 0:
                        return i
            elif t.kind == "EOF":
                break
            i += 1
        return None

    # ------------------------------------------------------------ calls
    def parse_call(self, fn):
        line = self.peek().line
        args = self.parse_args()
        call = self.finish_call(fn, args, line)
        # trailing lambda forms
        while True:
            if self.no_trailing:
                break
            t = self.peek()
            if t.kind == "OP" and t.val == "(" and not t.sp:
                m = self.matching(0)
                if m is not None and self.toks[m + 1].kind == "OP" and self.toks[m + 1].val == "->":
                    params = self.parse_params()
                    self.expect_op("->")
                    body = self.parse_lambda_body()
                    lam = Lambda(params, body, None, None, None, line=line)
                    call.trailing = lam
                    continue
                call = self.parse_call(call)
                return call
            if t.kind == "OP" and t.val == "->":
                self.next()
                body = self.parse_lambda_body()
                call.trailing = ph_lambda(body, line)
                continue
            break
        return call

    def parse_lambda_body(self):
        if self.peek().kind == "NL" and self.peek(1).kind == "INDENT":
            return self.parse_block()
        save = self.stop_bol
        self.stop_bol += 1
        save_nt = self.no_trailing
        self.no_trailing = False
        e = self.parse_stmt_inline()
        self.no_trailing = save_nt
        self.stop_bol = save
        return e

    def parse_args(self):
        self.expect_op("(")
        save = (self.no_trailing, self.stop_bol)
        self.no_trailing = False
        self.stop_bol = 0
        args = []
        self.skip_nl()
        while not self.at_op(")"):
            a0 = self.parse_arg()
            if not args and self.at_name("for") and a0.mod is None:
                a0 = self.parse_comprehension(a0)
            args.append(a0)
            self.skip_nl()
            if not self.eat_op(","):
                break
            self.skip_nl()
        self.skip_nl()
        self.expect_op(")", "to close the argument list")
        self.no_trailing, self.stop_bol = save
        return args

    def parse_comprehension(self, first):
        """Container comprehension: List(x * x for x in xs if x > 1) / Dict(k: v for k in ks)."""
        line = self.next().line          # 'for'
        ct = getattr(self, "_colon_of", {}).get(id(first))
        if ct is not None:
            if PBase.RECORD is not None:
                PBase.RECORD.append(("dict", ct))
            else:
                self.err("a `Dict` entry is written `key -> value`, not `key: value`", ct)
        pats = [self.parse_pattern()]
        while self.eat_op(","):
            pats.append(self.parse_pattern())
        pat = pats[0] if len(pats) == 1 else PTuple([(None, p) for p in pats], line=line)
        self.expect_name("in")
        save = self.no_trailing
        self.no_trailing = True
        it = self.parse_expr_until_if()
        cond = None
        if self.at_name("if"):
            self.next()
            cond = self.parse_expr()
        self.no_trailing = save
        key = None
        lab = first.label
        if lab is not None:
            key = Name(lab[1] if isinstance(lab, tuple) else lab, line=line)
        return Arg(None, CompE(None, first.expr, key, pat, it, cond, line=line), "comp", line=line)

    def parse_expr_until_if(self):
        return self.parse_expr()

    def parse_arg(self):
        t = self.peek()
        arrow = t.kind in ("NAME", "INT", "STR") and self.at_op("->", 1)
        colon = self.peek(1) if (t.kind in ("NAME", "INT", "STR") and self.at_op(":", 1)) else None
        a = self.parse_arg0()
        if colon is not None:
            if not hasattr(self, "_colon_of"):
                self._colon_of = {}
            self._colon_of[id(a)] = colon
        if arrow:
            if not hasattr(self, "_arrow_args"):
                self._arrow_args = set()
            self._arrow_args.add(id(a))
        return a

    def parse_arg0(self):
        t = self.peek()
        line = t.line
        label = None
        if t.kind in ("NAME", "INT") and self.at_op("->", 1):
            label = t.val
            self.next()
            self.next()
        elif t.kind == "STR" and self.at_op("->", 1):
            label = "".join(p for p in t.val if isinstance(p, str))
            self.next()
            self.next()
            label = ("str", label)
        elif t.kind in ("NAME", "INT") and self.at_op(":", 1):
            label = t.val
            self.next()
            self.next()
        elif t.kind == "STR" and self.at_op(":", 1):
            label = "".join(p for p in t.val if isinstance(p, str))
            self.next()
            self.next()
            label = ("str", label)
        t = self.peek()
        if t.kind == "NAME" and t.val in ("ref", "move", "using") :
            nt = self.peek(1)
            if t.val == "using" and (nt.kind == "OP" and nt.val in (",", ")")):
                self.next()
                return Arg(label, None, "using", line=line)
            if t.val != "using":
                self.next()
                e = self.parse_expr()
                return Arg(label, e, t.val, line=line)
            self.next()
            e = self.parse_expr()
            return Arg(label, e, "using", line=line)
        if t.kind == "OP" and t.val == "...":
            self.next()
            if self.at_op(",") or self.at_op(")"):
                return Arg(label, None, "spread", line=line)
            e = self.parse_expr()
            return Arg(label, e, "spread", line=line)
        e = self.parse_expr()
        return Arg(label, e, None, line=line)

    def finish_call(self, fn, args, line):
        base = fn.base if fn.__class__ is GenApp else fn
        is_dict = base.__class__ is Name and base.name == "Dict"
        arrows = getattr(self, "_arrow_args", set())
        for a in args:
            if id(a) in arrows and not is_dict:
                self.err("`key -> value` is how a `Dict` entry is written; a named argument is `name: value`", None)
            ct = getattr(self, "_colon_of", {}).get(id(a))
            if is_dict and ct is not None:
                if PBase.RECORD is not None:
                    PBase.RECORD.append(("dict", ct))
                else:
                    self.err("a `Dict` entry is written `key -> value`, not `key: value`", ct)
        partial = False
        new_args = []
        for a in args:
            if a.expr is not None and contains_ph(a.expr):
                if isinstance(a.expr, PH):
                    partial = True
                else:
                    a = Arg(a.label, ph_lambda(a.expr, a.line), a.mod, line=a.line)
            new_args.append(a)
        # `shared.on_change(balance, h)` and `on_change(shared, balance, h)`: the property is named by a bare name
        if fn.__class__ is Field and fn.name == "on_change" and len(new_args) == 2 and new_args[0].label is None \
                and new_args[0].expr.__class__ is Name:
            nm = new_args[0].expr.name
            new_args = [Arg(None, fn.obj, None, line=line), Arg(None, StrLit([nm], line=line), None, line=line), new_args[1]]
            fn = Name("on_change", line=line)
        elif fn.__class__ is Name and fn.name == "on_change" and len(new_args) == 3 and new_args[1].label is None \
                and new_args[1].expr.__class__ is Name:
            new_args[1] = Arg(None, StrLit([new_args[1].expr.name], line=line), None, line=line)
        call = Call(fn, new_args, None, line=line)
        if partial:
            lam = ph_lambda(call, line)
            lam.partial = True
            return lam
        return call

    # ------------------------------------------------------------ atoms
    def parse_bin_build(self, line):
        """Bin(0xCA, v: bits(4), n: u16be, body: bytes): build an Array[Byte] (Spec section 8). Desugars to bin_build(spec, values...)."""
        self.next()
        self.expect_op("(")
        spec, args, bitrun = [], [], 0
        while not self.at_op(")"):
            t = self.peek()
            nt = self.toks[self.p + 1]
            if t.kind in ("INT", "BYTES") and nt.kind == "OP" and nt.val in (",", ")"):
                self.next()
                if t.kind == "INT":
                    if not 0 <= t.val <= 255:
                        self.err("a literal in a Bin is one byte (0 to 255); write several, or use b\"...\"")
                    spec.append("lit:" + format(t.val, "02x"))
                else:
                    spec.append("lit:" + bytes(t.val).hex())
                if bitrun % 8:
                    self.err("the bit fields before this literal do not add up to whole bytes")
            else:
                args.append(Arg(None, self.parse_expr(), None))
                self.expect_op(":")
                kt = self.peek()
                if kt.kind != "NAME":
                    self.err("expected a Bin kind such as u8, u16be, bits(4), or bytes")
                kind = self.next().val
                arg = None
                if kind in ("bits", "bytes") and self.at_op("("):
                    self.next()
                    at = self.peek()
                    if at.kind != "INT":
                        self.err(f"the size of {kind}(...) in a built Bin is a number")
                    arg = self.next().val
                    self.expect_op(")")
                if kind == "bits":
                    if not isinstance(arg, int) or not 1 <= arg <= 64:
                        self.err("bits(n) needs a literal n from 1 to 64")
                    bitrun += arg
                else:
                    if kind != "bytes" and kind not in self.BIN_KINDS:
                        self.err(f"unknown Bin kind '{kind}' (u8, i8, u16be, u16le, ..., bits(n), bytes)")
                    if bitrun % 8:
                        self.err("the bit fields before this one do not add up to whole bytes")
                    bitrun = 0
                spec.append(kind if arg is None else f"{kind}:{arg}")
            if not self.eat_op(","):
                break
        self.expect_op(")")
        if bitrun % 8:
            self.err("the bit fields in this Bin do not add up to whole bytes")
        return Call(Name("bin_build", line=line), [Arg(None, StrLit(["|".join(spec)], line=line), None)] + args, None, line=line)

    def parse_atom(self):
        t = self.peek()
        k = t.kind
        line = t.line
        if k == "INT":
            self.next()
            return IntLit(t.val, t.extra, line=line)
        if k == "FLOAT":
            self.next()
            return FloatLit(t.val, t.extra, line=line)
        if k == "DEC":
            self.next()
            return DecLit(t.val, line=line)
        if k == "STR":
            self.next()
            return StrLit(self.convert_parts(t.val, t), line=line)
        if k == "CHAR":
            self.next()
            return CharLit(t.val, line=line)
        if k == "BYTES":
            self.next()
            return BytesLit(t.val, line=line)
        if k == "NAME" and t.val == "Bin" and self.at_op("(", 1) and not self.toks[self.p + 1].sp:
            return self.parse_bin_build(line)
        if k == "BCHAR":
            self.next()
            return ByteChar(t.val, line=line)
        if k == "DUR":
            self.next()
            return DurLit(t.val, t.extra, line=line)
        if k == "HASH":
            nt = self.peek(1)
            if nt.kind == "NAME" and nt.val in ("for", "while", "do"):
                self.next()
                e = self.parse_atom()
                e.label = t.val
                return e
            self.next()
            return KwLit(t.val, line=line)
        if k == "OP":
            v = t.val
            if v == "(":
                if not self.no_trailing and self._bare_lambda_ahead():
                    return self.parse_bare_lambda()
                return self.parse_paren()
            if v == "&":
                self.next()
                return Slot(line=line)
            if v == "$":
                self.next()
                nm = self.expect_ident("a variable name after '$'")
                return Dollar(Name(nm.val, line=line), line=line)
            if v == "\\":
                self.err("`\\` discards a value, so it can only start a statement")
            if v == "{":
                self.err("'{' does not start an expression in moxie")
            self.err(f"unexpected {self.describe(t)}")
        if k == "NAME":
            return self.parse_name_atom(t)
        if k == "SQL":
            self.err("unexpected SQL text")
        self.err(f"unexpected {self.describe(t)}")

    def parse_name_atom(self, t):
        v = t.val
        line = t.line
        if v == "true" or v == "false":
            self.next()
            return BoolLit(v == "true", line=line)
        if v == "if":
            return self.parse_if()
        if v == "when":
            return self.parse_when()
        if v == "for":
            return self.parse_for()
        if v == "while":
            return self.parse_while()
        if v == "do" and self.peek(1).kind == "NAME" and self.peek(1).val == "with" and self.peek(2).kind == "NAME":
            self.next()
            self.next()
            names = [self.next().val]
            while self.at_op(","):
                self.next()
                names.append(self.next().val)
            return WithE(names, self.parse_body("->", "a `do with`"), line=line)
        if v == "do" and self.nl_indent_at(1):
            self.next()
            return DoE(self.parse_block(), None, line=line)
        if v == "scope" and (self.nl_indent_at(1) or (self.peek(1).kind == "NAME" and self.nl_indent_at(2))):
            self.next()
            name = self.next().val if self.peek().kind == "NAME" else None
            return ScopeE(name, self.parse_block(), line=line)
        if v == "select" and self.nl_indent_at(1):
            return self.parse_select()
        if v == "daemon" and self.nl_indent_at(1):
            self.next()
            return DaemonE(self.parse_block(), line=line)
        if v == "run":
            return self.parse_run()
        if v == "fn":
            return self.parse_anon_fn()
        if v == "todo":
            self.next()
            msg = None
            if self.at_op("(") and not self.peek().sp:
                args = self.parse_args()
                msg = args[0].expr if args else None
            elif self.peek().kind == "STR":
                msg = self.parse_atom()
            return TodoE(msg, line=line)
        if v in ("ref", "move") and not (self.peek(1).kind == "OP" and self.peek(1).val in (",", ")", ":", "=")):
            self.next()
            e = self.parse_unary()
            return (Ref if v == "ref" else Move)(e, line=line)
        if v == "sql" and self.at_op("(", 1) and not self.peek(1).sp:
            m = self.matching(1)
            if m is not None and self.toks[m + 1].kind == "OP" and self.toks[m + 1].val == ":" and self.toks[m + 2].kind == "SQL":
                self.next()
                args = self.parse_args()
                self.expect_op(":")
                tk = self.next()
                return SqlE(args[0].expr, split_sql(tk.val, self), line=line)
        if v == "gimme" and self.at_op(".", 1):
            self.next()
            self.next()
            n = self.next()
            if n.kind != "INT":
                self.err("expected a layer number after 'gimme.'", n)
            self.expect_op(".")
            nm = self.next().val
            return Gimme(n.val, nm, line=line)
        if v == "_":
            self.next()
            return PH(1, line=line)
        if v[0] == "_" and len(v) > 1 and v[1:].isdigit():
            self.next()
            return PH(int(v[1:]), line=line)
        if v in HARD and v not in ("self", "Self"):
            self.err(f"unexpected '{v}'")
        self.next()
        return Name(v, line=line)

    _NOT_RET = ("if", "else", "and", "or", "in", "is", "not", "for", "while", "when", "elif", "as")

    def parse_ret_type(self):
        """A lambda's result type, `(x) Int -> body`: no unparenthesized function type, since its `->` would be the lambda's."""
        t = self.parse_type_prim()
        if self.at_op("|"):
            members = [t]
            while self.eat_op("|"):
                members.append(self.parse_type_prim())
            return TUnion(members, line=t.line)
        return t

    def _bare_lambda_ahead(self):
        """`(params): body` or `(params) Ret: body` where an expression may start."""
        m = self.matching(0)
        if m is None or m + 1 >= len(self.toks):
            return False
        after = self.toks[m + 1]
        if after.kind == "OP" and after.val == "->":
            return True
        if (after.kind == "NAME" and after.val not in self._NOT_RET) or (after.kind == "OP" and after.val == "("):
            save = self.p
            self.p = m + 1
            try:
                self.parse_ret_type()
                return self.at_op("->")
            except Exception:
                return False
            finally:
                self.p = save
        return False

    def parse_bare_lambda(self):
        line = self.peek().line
        params = self.parse_params()
        ret = None
        if not self.at_op("->"):
            ret = self.parse_ret_type()
        self.expect_op("->")
        body = self.parse_lambda_body()
        return Lambda(params, body, None, None, ret, line=line)

    def parse_paren(self):
        t = self.next()
        line = t.line
        save = (self.no_trailing, self.stop_bol)
        self.no_trailing = False
        self.stop_bol = 0
        self.skip_nl()
        if self.eat_op(")"):
            self.no_trailing, self.stop_bol = save
            return UnitLit(line=line)
        items = []
        rows = []
        cur = []
        trailing_comma = False
        multi = False
        one_marker = False
        while True:
            self.skip_nl()
            label = None
            spread = False
            tt = self.peek()
            if tt.kind in ("NAME", "INT") and self.at_op(":", 1):
                label = tt.val
                self.next()
                self.next()
            elif tt.kind == "OP" and tt.val == "%" and not cur:
                self.next()
                label = 0
                one_marker = True
            elif tt.kind == "OP" and tt.val == "...":
                self.next()
                spread = True
            e = self.parse_expr()
            cur.append((label, e, spread))
            self.skip_nl()
            if self.eat_op(","):
                trailing_comma = True
                self.skip_nl()
                if self.at_op(")"):
                    break
                continue
            trailing_comma = False
            if self.at_op(";"):
                multi = True
                level = 1
                self.next()
                while self.at_op(";"):
                    self.next()
                    level += 1
                rows.append((cur, level))
                cur = []
                self.skip_nl()
                continue
            break
        self.skip_nl()
        self.expect_op(")", "to close the parentheses")
        self.no_trailing, self.stop_bol = save
        if one_marker and (len(cur) != 1 or multi):
            self.err("`%` marks a one-item tuple: write `(%40)`", t)
        if multi:
            rows.append((cur, 0))
            return MArr(rows, line=line)
        if len(cur) == 1 and cur[0][0] is None and not cur[0][2] and not trailing_comma:
            e = cur[0][1]
            return e if not isinstance(e, (Pipe,)) else e
        return TupleE(cur, line=line)

    # ------------------------------------------------------------ lambda
    def parse_anon_fn(self):
        """`fn (params) [Ret] -> body`: an anonymous function that may have effects (a lambda, `(params): body`, is pure)."""
        t = self.next()   # fn
        if not self.at_op("("):
            self.err("'fn' here begins an anonymous function, `fn (params) -> body`; a named function is a declaration", t)
        params = self.parse_params()
        ret = None
        if not self.at_op("->"):
            ret = self.parse_ret_type()
        self.expect_op("->")
        body = self.parse_lambda_body()
        lam = Lambda(params, body, None, None, ret, line=t.line)
        lam.fiber = True        # effects allowed (the flag also marks an inline fiber)
        return lam

    def parse_lambda(self, run=True):
        """The inline fiber `run fn (args)(params): body` (the arguments come first, like `run name(args)`).
        An anonymous function elsewhere is written `(params): body` (parse_bare_lambda)."""
        t = self.next()   # fn
        line = t.line
        if self.at_op("("):
            m = self.matching(0)
            t2 = self.toks[m + 1] if m is not None else None
            if t2 is not None and t2.kind == "OP" and t2.val == "(" and not t2.sp:
                m2 = self.matching(m + 1 - self.p)
                t3 = self.toks[m2 + 1] if m2 is not None else None
                if t3 is not None and t3.kind == "OP" and t3.val == "->":
                    args = self.parse_args()
                    params = self.parse_params()
                    self.expect_op("->")
                    body = self.parse_lambda_body()
                    lam = Lambda(params, body, None, None, None, line=line)
                    lam.fiber = True
                    return Call(lam, args, None, line=line)
        params = self.parse_params()
        self.expect_op("->")
        body = self.parse_lambda_body()
        lam = Lambda(params, body, None, None, None, line=line)
        lam.fiber = True
        return lam

    def _paren_is_type(self):
        m = self.matching(0)
        if m is None:
            return False
        after = self.toks[m + 1]
        return after.kind == "OP" and after.val == "->"

    def parse_type_prim_name(self):
        t = self.next()
        return TName([t.val], [], line=t.line)

    def parse_params(self):
        """Parameter list in parentheses."""
        self.expect_op("(")
        save = (self.no_trailing, self.stop_bol)
        self.no_trailing = False
        self.stop_bol = 0
        out = []
        self.skip_nl()
        while not self.at_op(")"):
            out.append(self.parse_param())
            self.skip_nl()
            if not self.eat_op(","):
                break
            self.skip_nl()
        self.expect_op(")", "to close the parameter list")
        self.no_trailing, self.stop_bol = save
        return out

    def parse_param(self):
        t = self.peek()
        line = t.line
        mod = None
        if t.kind == "NAME" and t.val in ("ref", "lazy", "using", "move") and self.peek(1).kind == "NAME" \
                and (self.at_op(",", 2) or self.at_op(")", 2) or self.at_op("=", 2) or self.at_op(":", 2) or self.type_follows(2)):
            mod = t.val
            self.next()
            t = self.peek()
            if mod == "using" and not (self.type_follows(1) or self.at_op(":", 1)):
                self.err("a `using` parameter needs a name and a type: write `using ctx Context`", t)
        pat = None
        name = None
        if t.kind == "NAME" and (t.val not in HARD or t.val == "self") and (self.at_op(",", 1) or self.at_op(")", 1) or self.at_op("=", 1) or self.at_op(":", 1) or self.type_follows(1)):
            name = t.val
            self.next()
        else:
            pat = self.parse_pattern()
            if isinstance(pat, PBind):
                name, pat = pat.name, None
        typ = None
        variadic = False
        default = None
        self.no_decl_colon("a parameter")
        if not (self.at_op(",") or self.at_op(")") or self.at_op("=")):
            if self.at_op("..."):
                self.next()
                variadic = True
            typ = self.parse_type()
        if self.at_op("="):
            self.next()
            default = self.parse_expr()
        if mod == "using" and (name is None or name == "_"):
            self.err("a `using` parameter needs a name and a type: write `using ctx Context`", t)
        return Param(pat, name, typ, default, mod, variadic, line=line)

    # ------------------------------------------------------------ blocks
    def expect_nl_indent(self):
        if self.peek().kind != "NL" or self.peek(1).kind != "INDENT":
            self.err("expected an indented block")
        self.next()
        self.next()

    def expect_dedent(self):
        t = self.peek()
        if t.kind == "DEDENT":
            self.next()
        elif t.kind != "EOF":
            self.err(f"unexpected {self.describe(t)}")

    def end_line(self):
        t = self.peek()
        if t.kind == "NL":
            self.next()
        elif self.p > 0 and self.toks[self.p - 1].kind == "DEDENT":
            pass
        elif t.kind in ("DEDENT", "EOF"):
            pass
        else:
            self.err(f"unexpected {self.describe(t)}")

    def parse_block(self):
        """NL INDENT stmts DEDENT"""
        line = self.peek().line
        self.expect_nl_indent()
        stmts = self.parse_stmts_until_dedent()
        self.expect_dedent()
        return Block(stmts, line=line)

    def no_block_colon(self):
        if self.at_op(":"):
            self.err("a block does not begin with a colon: delete the `:` (a one-line body follows `then`, `do`, `->` or `=`)")

    def at_block(self):
        return self.peek().kind == "NL" and self.peek(1).kind == "INDENT"

    def nl_indent_at(self, k):
        """An indented block starts after the next `k` tokens."""
        return self.peek(k).kind == "NL" and self.peek(k + 1).kind == "INDENT"

    def expect_nl_indent_block(self):
        self.no_block_colon()
        if not self.at_block():
            self.err("expected an indented block")

    def parse_block_or_inline(self):
        """The body after a header: an indented block, or a one-line statement."""
        if self.at_block():
            return self.parse_block()
        save = (self.no_trailing,)
        self.no_trailing = False
        e = self.parse_stmt_inline()
        self.no_trailing = save[0]
        return e

    def expect_sep(self, sep, what):
        """The word or arrow between a header and a one-line body."""
        t = self.peek()
        ok = (t.kind == "NAME" and t.val == sep) if sep.isalpha() else (t.kind == "OP" and t.val == sep)
        if not ok:
            self.err(f"write `{sep}` before the one-line body of {what}, or put the body on an indented line", t)
        self.next()

    def parse_body(self, sep, what):
        """After a header: an indented block, or on the same line `sep` and one statement."""
        self.no_block_colon()
        if self.at_block():
            return self.parse_block()
        self.expect_sep(sep, what)
        return self.parse_block_or_inline()

    # ------------------------------------------------------------ control
    def parse_header_expr(self):
        save = self.no_trailing
        self.no_trailing = True
        e = self.parse_expr()
        self.no_trailing = save
        return e

    def parse_if(self):
        line = self.next().line
        branches = []
        else_ = None
        kinds = []
        cond = self.parse_header_expr()
        body = self.parse_body("then", "an `if`")
        kinds.append(body.__class__ is Block)
        branches.append((cond, body))
        while True:
            self.check_if_continues(kinds)
            if self.at_name("elif"):
                self.next()
                cond = self.parse_header_expr()
                body = self.parse_body("then", "an `elif`")
                kinds.append(body.__class__ is Block)
                branches.append((cond, body))
                continue
            if self.at_name("else"):
                self.next()
                self.no_block_colon()
                else_ = self.parse_block_or_inline()
                kinds.append(else_.__class__ is Block)
            break
        if len(set(kinds)) > 1:
            self.err_at(line, "an `if` is written all on one line or all with indented blocks, not a mix of the two")
        return IfE(branches, else_, line=line)

    def check_if_continues(self, kinds):
        """After a one-line branch, `elif` and `else` stay on that line."""
        if kinds and not kinds[-1] and self.peek().kind == "NL":
            nt = self.peek(1)
            if nt.kind == "NAME" and nt.val in ("elif", "else"):
                self.err(f"`{nt.val}` goes on the same line as a one-line `if`, or write every branch as an indented block", nt)

    def after_else_arm(self):
        """`else:` is the last arm: another arm after it is an error."""
        self.skip_nl()
        if self.peek().kind not in ("DEDENT", "EOF"):
            self.err("`else:` must be the last arm")

    def parse_when(self):
        line = self.next().line
        scrut = None
        if self.peek().kind != "NL":
            scrut = self.parse_header_expr()
        self.no_block_colon()
        self.expect_nl_indent()
        arms = []
        while True:
            self.skip_nl()
            if self.peek().kind in ("DEDENT", "EOF"):
                break
            aline = self.peek().line
            if self.at_name("else"):                                   # `else body` is `_ -> body`
                self.next()
                self.no_block_colon()
                body = self.parse_block_or_inline()
                if scrut is None:
                    arms.append(Arm(None, PH(1, line=aline), body, line=aline))
                else:
                    arms.append(Arm([PWild()], None, body, line=aline))
                self.end_line()
                self.after_else_arm()
                continue
            if scrut is None:
                save = self.no_trailing
                self.no_trailing = True
                cond = self.parse_expr()
                self.no_trailing = save
                self.expect_op("->")
                body = self.parse_block_or_inline()
                arms.append(Arm(None, cond, body, line=aline))
                self.end_line()
                continue
            pats = [self.parse_pattern()]
            while self.eat_op(","):
                pats.append(self.parse_pattern())
            guard = None
            if self.at_name("if"):
                self.next()
                save = self.no_trailing
                self.no_trailing = True
                guard = self.parse_expr()
                self.no_trailing = save
            self.expect_op("->")
            body = self.parse_block_or_inline()
            arms.append(Arm(pats, guard, body, line=aline))
            self.end_line()
        self.expect_dedent()
        return WhenE(scrut, arms, line=line)

    def parse_for(self):
        line = self.next().line
        if self.peek().kind == "NL":
            return self.parse_for_monad(line)
        pats = [self.parse_pattern()]
        while self.eat_op(","):
            pats.append(self.parse_pattern())
        pat = pats[0] if len(pats) == 1 else PTuple([(None, p) for p in pats], line=line)
        self.expect_name("in")
        it = self.parse_header_expr()
        body = self.parse_body("do", "a `for`")
        else_ = self.parse_loop_else()
        return ForE(pat, it, body, else_, None, line=line)

    def parse_loop_else(self):
        if self.at_name("else"):
            self.next()
            self.no_block_colon()
            return self.parse_block_or_inline()
        return None

    def parse_while(self):
        line = self.next().line
        cond = None
        if self.peek().kind != "NL":
            cond = self.parse_header_expr()
        body = self.parse_body("do", "a `while`")
        else_ = self.parse_loop_else()
        return WhileE(cond, body, else_, None, line=line)

    def parse_for_monad(self, line):
        self.expect_nl_indent()
        lines = []
        yield_ = None
        while True:
            self.skip_nl()
            if self.peek().kind in ("DEDENT", "EOF"):
                break
            if self.at_name("and") :
                self.next()
            if self.at_name("yield"):
                self.next()
                yield_ = self.parse_block_or_inline()
                self.end_line()
                continue
            # pat in expr  |  pat = expr  |  if cond
            if self.at_name("if"):
                self.next()
                c = self.parse_expr()
                lines.append(("if", None, c, None))
                self.end_line()
                continue
            pat = self.parse_pattern()
            if self.at_name("in"):
                self.next()
                kind = "in"
            else:
                self.expect_op("=")
                kind = "="
            ex = self.parse_expr()
            else_ = None
            if self.at_name("else"):
                self.next()
                self.no_block_colon()
                else_ = self.parse_block_or_inline()
            lines.append((kind, pat, ex, else_))
            self.end_line()
        self.expect_dedent()
        return ForM(lines, yield_, line=line)

    def parse_select(self):
        line = self.next().line
        self.expect_nl_indent()
        arms = []
        while True:
            self.skip_nl()
            if self.peek().kind in ("DEDENT", "EOF"):
                break
            aline = self.peek().line
            used_else = self.at_name("else")                            # `else body` is `case _ -> body`
            if not used_else:
                self.expect_name("case")
            kind = "read"
            bind = None
            ex = None
            if used_else or (self.at_name("_") and self.at_op("->", 1)):
                self.next()
                kind = "default"
            elif self.at_name("cancelled") and self.at_op("(", 1):
                self.next()
                self.next()
                ex = self.parse_expr()
                self.expect_op(")")
                kind = "cancelled"
            elif self.at_name("closed") and self.at_op("(", 1):
                self.next()
                self.next()
                ex = self.parse_expr()
                self.expect_op(")")
                kind = "closed"
            else:
                if self.peek().kind == "NAME" and self.at_op("=", 1):
                    bind = self.next().val
                    self.next()
                elif self.at_op("(") :
                    # tuple binding or pattern
                    bind = self.parse_pattern()
                    self.expect_op("=")
                ex = self.parse_header_expr()
            if not used_else:
                self.expect_op("->")
            else:
                self.no_block_colon()
            body = self.parse_block_or_inline()
            arms.append(SelArm(kind, bind, ex, body, line=aline))
            self.end_line()
            if used_else:
                self.after_else_arm()
        self.expect_dedent()
        return SelectE(arms, line=line)

    def parse_run(self):
        line = self.next().line
        if self.at_name("fn"):
            lam = self.parse_lambda(run=True)
            return RunE(lam, None, line=line)
        target = self.parse_postfix()
        return RunE(target, None, line=line)

    def parse_recv_block(self, recv, kind, line):
        if kind == "do":
            if self.at_op("->"):
                self.next()
                body = self.parse_block_or_inline()
            else:
                self.expect_nl_indent_block()
                body = self.parse_block()
            return DoRecv(recv, "do", body, line=line)
        lines = self.parse_upd_lines()
        return DoRecv(recv, "update", lines, line=line)

    def parse_upd_lines(self):
        if self.peek().kind == "NL" and self.peek(1).kind == "INDENT":
            self.expect_nl_indent()
            out = []
            while True:
                self.skip_nl()
                if self.peek().kind in ("DEDENT", "EOF"):
                    break
                out.append(self.parse_upd_line())
            self.expect_dedent()
            return out
        # single inline: field: value
        return [self.parse_upd_line(inline=True)]

    def parse_upd_line(self, inline=False):
        t = self.next()
        if t.kind != "NAME":
            self.err("expected a field name", t)
        self.expect_op(":")
        if self.peek().kind == "NL" and self.peek(1).kind == "INDENT":
            nested = self.parse_upd_lines()
            return UpdLine(t.val, None, nested, line=t.line)
        e = self.parse_expr()
        if not inline:
            self.end_line()
        return UpdLine(t.val, e, None, line=t.line)
