"""Expression parser (mixin)."""
from .pbase import PBase, HARD
from .lexer import MoxieSyntaxError
from .ast import *   # noqa
from . import units as units_mod
MUT_RE = set()      # ids of `Assign` nodes that assign to a `mutable` block's name

T_PIPE, T_OR, T_AND, T_COMP, T_RANGE, T_BT, T_BOR, T_BXOR, T_BAND, T_SHIFT, T_ADD, T_MUL, T_OTHER = range(13)

COMP_OPS = {"==", "~=", "<", ">", "<=", ">=", "<$>", "<*>", "<~"}
ORDER_OPS = ("<", ">", "<=", ">=", "==")      # the operators that chain (`~=` does not: `a ~= b ~= c` would only say neighbors differ)
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


CAST_STYLE = {}


class ExprParser(PBase):
    stop_bol = 0

    def note_cast_style(self, kind, line):
        """A file spells its conversions one way: `cast[T](x)` everywhere, or `[T](x)` everywhere (Spec 3)."""
        seen = CAST_STYLE.setdefault(self.file, {})
        seen.setdefault(kind, line)
        if len(seen) > 1:
            other = "cast" if kind == "sugar" else "sugar"
            what = {"cast": "`cast[T](x)`", "sugar": "`[T](x)`"}
            self.err_at(line, f"this file already converts with {what[other]} (line {seen[other]}), so use {what[other]} here too: one spelling of a conversion per file")

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
                t = self.peek()
                if self._tier_of(t) is not None and not (self.stop_bol and t.bol):
                    left = self._climb(T_OR, left)       # `a |> f() == 2` compares the pipe's result: (a |> f()) == 2
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

    def build_chain(self, ops, operands, line):
        """`a < b <= c` is `a < b and b <= c`. A plain name, literal or field is written twice; any other middle operand (a call,
        say) is bound to a hidden name at the moment its link is reached, so it runs once and a false link stops the chain."""
        import copy

        def simple(e):
            if e.__class__ in (Name, IntLit, FloatLit):
                return True
            return e.__class__ is Field and isinstance(e.name, str) and simple(e.obj)
        if len(ops) == 1:
            return Binary(ops[0], operands[0], operands[1], line=line)

        def link(k, left):
            nxt = operands[k + 1]
            if k == len(ops) - 1:
                return Binary(ops[k], left, nxt, line=line)
            if simple(nxt):
                return AndE(Binary(ops[k], left, nxt, line=line), link(k + 1, copy.deepcopy(nxt)), line=line)
            tmp = f"$c{k + 1}"
            bind = Assign(PBind(tmp, line=line), nxt, None, "=", None, line=line)
            test = AndE(Binary(ops[k], left, Name(tmp, line=line), line=line), link(k + 1, Name(tmp, line=line)), line=line)
            return DoE(Block([bind, ExprStmt(test, line=line)], line=line), None, line=line)
        first = operands[0]
        if simple(first):
            return link(0, first)
        bind = Assign(PBind("$c0", line=line), first, None, "=", None, line=line)
        return DoE(Block([bind, ExprStmt(link(0, Name("$c0", line=line)), line=line)], line=line), None, line=line)

    def _climb(self, minp, left=None):
        if left is None:
            left = self.parse_unary()
        chain = None
        while True:
            prev_chain, chain = chain, None
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
                neg = False
                if self.peek().kind == "NAME" and self.peek().val == "not":
                    self.next()
                    neg = True
                alts = self.parse_pattern_alts()
                pat = alts[0]
                if len(alts) > 1:                                    # `x is A | B`: true when any alternative matches
                    if any(self._pat_binds(a) for a in alts):
                        self.err("the alternatives of an `is` test cannot bind names: use `when` for alternatives that do", t)
                    if left.__class__ not in (Name, Field, IntLit, StrLit, CharLit):
                        self.err("`is` with alternatives needs a name to test: bind the value to a name first", t)
                    test = IsOp(left, alts[0], line=line)
                    for a in alts[1:]:
                        test = OrE(test, IsOp(left, a, line=line), line=line)
                    left = test
                else:
                    left = IsOp(left, pat, line=line)
                if neg:
                    left = Unary("not", left, line=line)
            elif t.kind == "NAME" and (t.val == "in" or t.val == "not"):
                neg = False
                if t.val == "not":
                    self.next()
                    neg = True
                self.next()
                if not neg and t.val == "in" and self.peek().kind == "NAME" and self.peek().val in self.units:
                    text = self.unit_text()                       # `d in km`: the number of kilometers in a quantity
                    left = QtyIn(left, text, units_mod.scale_of(units_mod.parse_text(text) or [], self.units), line=line)
                    continue
                right = self._climb(tier + 1)
                left = InOp(left, right, neg, line=line)
            elif t.kind == "BTICK":
                self.next()
                right = self._climb(tier + 1)
                left = Tick(left, t.val, right, line=line)
            elif t.val in ("..", "..="):
                self.next()
                left = self.range_rest(left, t.val, tier + 1, line)
            elif t.val in ("+%", "-%"):
                self.next()
                right = self._climb(tier + 1)
                left = self.listener_op(t.val, left, right, line)
            else:
                self.next()
                right = self._climb(tier + 1)
                if t.val in ORDER_OPS and prev_chain is not None and prev_chain[2] is left and prev_chain[0] != ["~="]:
                    ops, operands = prev_chain[0] + [t.val], prev_chain[1] + [right]
                    left = self.build_chain(ops, operands, line)
                    chain = (ops, operands, left)
                else:
                    if t.val in ("~=", "==") and prev_chain is not None and prev_chain[0] == ["~="] and prev_chain[2] is left:
                        self.err("`~=` doesn't chain: `a ~= b ~= c` would only say that neighbors differ. Write `a ~= b and b ~= c`", t)
                    left = Binary(t.val, left, right, line=line)
                    if t.val in ORDER_OPS or t.val == "~=":
                        chain = ([t.val], [left.l, left.r], left)
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

    def step_kw_ahead(self):
        """`step` directly after a range, with an operand following on the same line (`1..9 step 2`, `10..1 step -3`).  Anywhere else
        `step` is an ordinary name."""
        t = self.peek()
        if not (t.kind == "NAME" and t.val == "step"):
            return False
        n = self.peek(1)
        if n.kind in ("INT", "FLOAT", "NAME") and n.val not in ("then", "do", "else", "elif", "and", "or", "if", "in", "is", "not"):
            return True
        if n.kind == "OP" and n.val == "(":
            return True
        return n.kind == "OP" and n.val == "-" and not self.peek(2).sp

    def range_rest(self, left, op, hi_tier, line):
        """What follows `..` or `..=`: the limit, then an optional `step` (the only place `step` is a keyword)."""
        hi = None
        if not self.step_kw_ahead() and not self._ends_operand(self.peek()):
            hi = self._climb(hi_tier)
        st = None
        if self.step_kw_ahead():
            self.next()
            st = self._climb(hi_tier)
            if self.step_kw_ahead():
                self.err("a range takes one `step`")
        return RangeE(left, hi, op == "..=", st, line=line)

    def _ends_operand(self, t):
        if t.kind in ("NL", "DEDENT", "INDENT", "EOF"):
            return True
        if t.kind == "OP" and t.val in (")", "]", ",", ":", "->", ";", "}", "|>"):
            return True
        if t.kind == "NAME" and t.val in ("else", "elif", "and", "or", "if", "then", "do"):
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
                return self.range_rest(None, t.val, T_RANGE + 1, line)
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
            if v == "@" and not t.sp and e.__class__ is Name and self.peek(1).kind == "INT" and not self.peek(1).sp \
                    and isinstance(self.peek(1).val, int):
                self.next()                                        # `total@1`: the nearest enclosing block's `total` (Spec 2)
                e = Gimme(self.next().val, e.name, line=t.line)
            elif v == "@" and not t.sp and e.__class__ is Name and self.peek(1).kind == "NAME" and not self.peek(1).sp \
                    and (self.peek(1).val[:1].islower()) and not self.at_op("(", 2):
                self.next()                                        # `total@serve`: the `total` outside the loop labeled `#serve`
                e = Gimme(self.next().val, e.name, line=t.line)
            elif v == "(" and not t.sp:
                e = self.parse_call(e)
            elif v == "[" and not t.sp and self._can_generic(e):
                groups = []
                while self.at_op("[") and not self.peek().sp:
                    groups.append(self.parse_targ_group())
                e = GenApp(e, groups, line=t.line)
                if e.base.__class__ is Name and e.base.name == "cast":
                    self.note_cast_style("cast", t.line)
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
        base = fn.base if fn.__class__ is GenApp else fn
        saved_dc = getattr(self, "dict_call", False)
        self.dict_call = base.__class__ is Name and base.name == "Dict"      # inside `Dict(...)` a `(k) -> v` is a key, not a lambda
        try:
            args = self.parse_args()
        finally:
            self.dict_call = saved_dc
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
        if call.__class__ is Call and not self.no_trailing and call.trailing is None and self.at_block() and not self.trailing_if_block():
            call.block = self.parse_collect_block()          # `ul(class: "menu")` and an indented block of children
        return call

    def trailing_if_block(self):
        """`stmt` then an indented `if cond` line with no body of its own is the trailing-`if` form, not a block of children."""
        i = self.p + 2
        if not (self.toks[i].kind == "NAME" and self.toks[i].val == "if"):
            return False
        while self.toks[i].kind not in ("NL", "EOF"):
            i += 1
        return self.toks[i + 1].kind != "INDENT" if self.toks[i].kind == "NL" else True

    def parse_collect_block(self):
        """An indented block after a call: each line is a child, a binding, an `if` / `for` of children, or `...list`.  It becomes one
        expression, the list of the children, which the checker passes to the callee's `block` parameter."""
        line = self.peek().line
        self.expect_nl_indent()
        self.collecting = getattr(self, "collecting", 0) + 1
        try:
            stmts = self.parse_stmts_until_dedent()
        finally:
            self.collecting -= 1
        self.expect_dedent()
        return self.collect_list(stmts, line)

    def collect_list(self, stmts, line):
        """The statements of a collecting block as a block that ends in the concatenation of its pieces."""
        if stmts.__class__ is Block:
            stmts = stmts.stmts
        out, names = [], []
        for s in stmts:
            c = s.__class__
            if c is Assign or c is ElseLet or c is Refine:
                out.append(s)
                continue
            if c is not ExprStmt:
                self.err("a block of children holds children, bindings, `if`, `for` and `...list`; this line is something else", None)
            x = s.e
            xl = getattr(x, "line", line) or line
            if x.__class__ is Splat:
                piece = Pipe(x.e, Call(Name("collect", line=xl), [], None, None, None, line=xl), line=xl)
            elif x.__class__ is IfE:
                br = [(cond, self.collect_list(body, xl)) for cond, body in x.branches]
                els = self.collect_list(x.else_, xl) if x.else_ is not None else Call(Name("List", line=xl), [], None, None, None, line=xl)
                piece = IfE(br, els, line=xl)
            elif x.__class__ is ForE:
                if x.else_ is not None or x.label is not None:
                    self.err("a `for` in a block of children takes no `else` or label", None)
                lam = Lambda([Param(None if x.pat.__class__ is not PBind else None, x.pat.name if x.pat.__class__ is PBind else None, None, None, None, False, None, None, line=xl)]
                             if x.pat.__class__ is PBind else
                             [Param(x.pat, None, None, None, None, False, None, None, line=xl)],
                             ExprStmt(self.collect_list(x.body, xl), line=xl), None, None, None, line=xl)
                piece = Pipe(Pipe(x.iter, Call(Name("flat_map", line=xl), [Arg(None, lam, None)], None, None, None, line=xl), line=xl),
                             Call(Name("collect", line=xl), [], None, None, None, line=xl), line=xl)
            elif x.__class__ in (WhileE, DaemonE):
                self.err("a block of children holds children, bindings, `if`, `for` and `...list`; a loop other than `for` is not one of them", None)
            elif x.__class__ is WhenE:
                self.err("a `when` is not allowed in a block of children: use `if` / `elif` / `else`", None)
            else:
                piece = Call(Name("List", line=xl), [Arg(None, x, None)], None, None, None, line=xl)
            self._kid_n = getattr(self, "_kid_n", 0) + 1
            nm = f"kids__{self._kid_n}"
            out.append(Assign(PBind(nm, line=xl), piece, None, "=", None, None, line=xl))
            names.append(nm)
        total = None
        for nm in names:
            n = Name(nm, line=line)
            total = n if total is None else Binary("+", total, n, line=line)
        if total is None:
            total = Call(Name("List", line=line), [], None, None, None, line=line)
        out.append(ExprStmt(total, line=line))
        return Block(out, line=line)

    def parse_lambda_body(self):
        if self.peek().kind == "NL" and self.peek(1).kind == "INDENT":
            return self.parse_block()
        save = self.stop_bol
        self.stop_bol += 1
        save_nt = self.no_trailing
        self.no_trailing = False
        e = self.parse_inline_seq()
        self.no_trailing = save_nt
        self.stop_bol = save
        if self.at_op(";"):
            self.err("unexpected ';': a lambda body is one expression; write an indented block for more")
        return e

    def parse_args(self):
        self.expect_op("(")
        save = (self.no_trailing, self.stop_bol)
        self.no_trailing = False
        self.stop_bol = 0
        args = []
        self.skip_nl()
        while not self.at_op(")"):
            if self.at_op("{") and getattr(self, "dict_call", False):
                args.extend(self.parse_multi_entry())
                self.skip_nl()
                if not self.eat_op(","):
                    break
                self.skip_nl()
                continue
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

    def parse_multi_entry(self):
        """`{alice, bob} -> (31, 26)` inside a `Dict(...)`: several entries at once, the keys and the values paired by position."""
        line = self.next().line                  # {
        keys = []
        self.skip_nl()
        while not self.at_op("}"):
            t = self.peek()
            nt = self.peek(1)
            if t.kind == "INT" and nt.kind == "OP" and nt.val in (",", "}"):
                self.next()
                keys.append((t.val, None))
            elif t.kind == "STR" and nt.kind == "OP" and nt.val in (",", "}"):
                self.next()
                keys.append((("str", "".join(p for p in t.val if isinstance(p, str))), None))
            else:
                keys.append((None, self.parse_expr()))
            self.skip_nl()
            if not self.eat_op(","):
                break
            self.skip_nl()
        self.expect_op("}", "to close the list of keys")
        if not keys:
            self.err("`{}` needs at least one key before `->`")
        self.expect_op("->", "after the keys: `{a, b} -> (1, 2)`")
        val = self.parse_expr()
        if len(keys) == 1:
            vals = [val.items[0][1]] if False else [val]
        elif val.__class__ is TupleE and len(val.items) == len(keys) and not any(it[2] or it[0] is not None for it in val.items):
            vals = [it[1] for it in val.items]
        else:
            n = len(val.items) if val.__class__ is TupleE else 1
            self.err_at(line, f"`{{...}} -> (...)` pairs keys and values by position: {len(keys)} keys need a tuple of {len(keys)} values, found {n}")
        out = []
        for (lab, kexpr), v in zip(keys, vals):
            if lab is not None:
                a = Arg(lab, v, None, line=line)
            else:
                a = Arg(None, TupleE([(None, kexpr, False), (None, v, False)], line=line), None, line=line)
            out.append(a)
            if not hasattr(self, "_arrow_args"):
                self._arrow_args = {}
            self._arrow_args[id(a)] = a
        return out

    def parse_comprehension(self, first):
        """Container comprehension: List(x * x for x in xs if x > 1) / Dict(k -> v for k in ks)."""
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

    def paren_arrow_ahead(self):
        """A `(` that opens a key: its matching `)` is followed by `->`."""
        depth, k = 0, 0
        while True:
            t = self.peek(k)
            if t.kind == "EOF":
                return False
            if t.kind == "OP" and t.val in ("(", "[", "{"):
                depth += 1
            elif t.kind == "OP" and t.val in (")", "]", "}"):
                depth -= 1
                if depth == 0:
                    n = self.peek(k + 1)
                    return n.kind == "OP" and n.val == "->"
            k += 1

    def parse_arg(self):
        t = self.peek()
        arrow = t.kind in ("NAME", "INT", "STR") and self.at_op("->", 1)
        colon = self.peek(1) if (t.kind in ("NAME", "INT", "STR") and self.at_op(":", 1)) else None
        a = self.parse_arg0()
        if colon is not None:
            if not hasattr(self, "_colon_of"):
                self._colon_of = {}
            self._colon_of[id(a)] = colon
            if not hasattr(self, "_colon_keep"):
                self._colon_keep = []
            self._colon_keep.append(a)
        if arrow:
            if not hasattr(self, "_arrow_args"):
                self._arrow_args = {}
            self._arrow_args[id(a)] = a          # the node is kept, so its id is not reused by a later one
        return a

    def unit_suffix(self, lit, line):
        """`5.0 m`, `9.8 m/s^2`: a number, a space, then a declared unit (with `*`, `/`, `^n` and more declared units)."""
        t = self.peek()
        if not (t.kind == "NAME" and t.sp and t.line == line and t.val in self.units):
            return lit
        text = self.unit_text()
        pairs = units_mod.parse_text(text) or []
        return QtyLit(lit, text, units_mod.scale_of(pairs, self.units), line=line)

    def unit_text(self):
        """The unit expression at the cursor (`km`, `m/s^2`, `kg*m`), which starts with a declared unit."""
        text = self.next().val
        while True:
            t = self.peek()
            if t.kind == "OP" and t.val == "^" and self.peek(1).kind == "INT" and not t.sp:
                self.next()
                text += "^" + str(self.next().val)
            elif t.kind == "OP" and t.val in ("*", "/") and self.peek(1).kind == "NAME" and self.peek(1).val in self.units:
                text += self.next().val + self.next().val
            else:
                break
        return text

    def parse_arg0(self):
        t = self.peek()
        line = t.line
        label = None
        if t.kind == "OP" and t.val == "(" and getattr(self, "dict_call", False) and self.paren_arrow_ahead():
            key = self.parse_paren()                      # `(1, 2) -> "a"`: a tuple key, written like any other key
            self.expect_op("->")
            val = self.parse_expr()
            return Arg(None, TupleE([(None, key, False), (None, val, False)], line=line), None, line=line)
        if t.kind in ("NAME", "INT") and self.at_op("->", 1) and not (t.kind == "NAME" and getattr(self, "dict_call", False)):   # in a Dict a name is the variable, not a word
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
        if label is None and getattr(self, "dict_call", False):
            # inside `Dict(...)` an expression followed by `->` is a computed key: `abs(-3) -> 1`, `Color.Red -> 1`, `Key.ById(7) -> 1`
            # (read as a call with a trailing lambda it would lose the entry)
            save_nt = self.no_trailing
            self.no_trailing = True
            try:
                e = self.parse_expr()
            finally:
                self.no_trailing = save_nt
            if self.at_op("->"):
                self.next()
                val = self.parse_expr()
                return Arg(None, TupleE([(None, e, False), (None, val, False)], line=line), None, line=line)
            return Arg(label, e, None, line=line)
        e = self.parse_expr()
        return Arg(label, e, None, line=line)

    def finish_call(self, fn, args, line):
        base = fn.base if fn.__class__ is GenApp else fn
        is_dict = base.__class__ is Name and base.name == "Dict"
        arrows = getattr(self, "_arrow_args", {})
        for a in args:
            if id(a) in arrows and not is_dict:
                self.err("`key -> value` is how a `Dict` entry is written; a named argument is `name: value`", None)
            ct = getattr(self, "_colon_of", {}).get(id(a))
            if is_dict and ct is not None:
                if PBase.RECORD is not None:
                    PBase.RECORD.append(("dict", ct))
                else:
                    self.err("a `Dict` entry is written `key -> value`, not `key: value`", ct)
        seen_named = False
        for a in args:                      # a bare name after a named argument, or anywhere in a Dict, names itself: `User(name: who, age)`
            if a.label is not None:
                seen_named = True
            elif a.mod is None and a.expr.__class__ is Name and is_dict:
                self.err_at(line, f"a `Dict` entry is written `key -> value`; to use `{a.expr.name}` as a key write `\"{a.expr.name}\" -> {a.expr.name}`")
            elif a.mod is None and a.expr.__class__ is Name and seen_named:
                a.label = a.expr.name
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
        if k == "OP" and t.val == "[":                   # `[Int](x)` is `cast[Int](x)` (Spec 3)
            self.next()
            tys = [self.parse_type()]
            while self.eat_op(":"):                        # `[A : B : C](x)`: first C, then B, then A
                tys.append(self.parse_type())
            self.expect_op("]", "to close the conversion type")
            if not (self.at_op("(") and not self.peek().sp):
                self.err("a type in brackets converts a value: write `[Int](x)`, or `cast[Int](x)`", t)
            self.note_cast_style("sugar", line)
            args = self.parse_args()
            e = Call(GenApp(Name("cast", line=line), [[tys[-1]]], line=line), args, None, line=line)
            for ty in reversed(tys[:-1]):
                e = Call(GenApp(Name("cast", line=line), [[ty]], line=line), [Arg(None, e, None, line=line)], None, line=line)
            return e
        if k == "INT":
            self.next()
            return self.unit_suffix(IntLit(t.val, t.extra, line=line), line)
        if k == "FLOAT":
            self.next()
            return self.unit_suffix(FloatLit(t.val, t.extra, line=line), line)
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
        if v == "mutable" and self.nl_indent_at(1):
            self.next()
            blk = self.parse_block()
            self.mutable_rewrite(blk)
            return DoE(blk, None, line=line)
        if v == "eval" and self.nl_indent_at(1):
            self.next()
            return self.parse_eval(line)
        if v == "eval" and self.peek(1).kind == "NAME" and self.peek(1).val == "impure" and self.nl_indent_at(2):
            self.next()
            self.next()
            return self.parse_eval(line, free=True)
        if v == "eval" and self.peek(1).kind == "NAME" and self.peek(1).val == "pure" and self.nl_indent_at(2):
            self.next()
            self.next()
            return self.parse_eval(line)                 # `eval pure` says out loud what a plain `eval` already means
        if v == "scope" and (self.nl_indent_at(1) or (self.peek(1).kind == "NAME" and self.nl_indent_at(2))):
            self.err("`scope` is now `wait`: write `wait` (or `wait token`) before the block")
        if v == "wait" and (self.nl_indent_at(1) or (self.peek(1).kind == "NAME" and self.nl_indent_at(2))):
            self.next()
            name = self.next().val if self.peek().kind == "NAME" else None
            return WaitE(name, self.parse_block(), line=line)
        if v == "select" and self.nl_indent_at(1):
            return self.parse_select()
        if v == "daemon" and self.nl_indent_at(1):
            self.next()
            return DaemonE(self.parse_block(), line=line)
        if v == "go" or v == "try_go":
            return self.parse_run(v == "try_go")
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
        if v == "gimme" and self.at_op(".", 1) and self.peek(2).kind == "INT":
            nm = self.peek(4).val if self.peek(4).kind == "NAME" else "name"
            self.err(f"`gimme.N.name` is now written `name@N`: write `{nm}@{self.peek(2).val}`")
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

    SECT_OPS = frozenset(o for o in BINTIER if o not in ("..", "..=", "+%", "-%"))

    def section_op(self, t, nt):
        """Is token `t` (followed by `nt`) an operator that can name a section?  `(- 4)` with a space is the section, `(-4)` and `(-x)`
        are negation, and `(/dir)` is a path."""
        if t.kind == "BTICK":
            return True
        if t.kind != "OP" or t.val not in self.SECT_OPS:
            return False
        if nt.kind == "OP" and nt.val == ")":
            return False
        if t.val == "-":
            return nt.sp
        if t.val == "/" and nt.kind == "NAME" and not nt.sp:
            return False
        return True

    WORD_SECT = ("and", "or", "in")

    def sect_body(self, t, left, right):
        if t.kind == "BTICK":
            return Tick(left, t.val, right, line=t.line)
        if t.kind == "NAME" and t.val in self.WORD_SECT:                # `(and ok)`, `(or x)`, `(in xs)`
            if t.val == "in":
                return InOp(left, right, False, line=t.line)
            return (AndE if t.val == "and" else OrE)(left, right, line=t.line)
        return Binary(t.val, left, right, line=t.line)

    def left_section_end(self):
        """At the `(` already consumed: the index of the `)` that closes it when the last thing before it is a binary operator, as in
        `(10 -)`, else None."""
        depth, i = 0, 0
        while True:
            k = self.peek(i)
            if k.kind == "EOF":
                return None
            if k.kind == "OP" and k.val in ("(", "[", "{"):
                depth += 1
            elif k.kind == "OP" and k.val in (")", "]", "}"):
                if depth == 0:
                    if k.val != ")" or i == 0:
                        return None
                    p = self.peek(i - 1)
                    pp = self.peek(i - 2) if i >= 2 else None
                    ok = (p.kind == "BTICK" or (p.kind == "OP" and p.val in self.SECT_OPS) or (p.kind == "NAME" and p.val in self.WORD_SECT)) and i >= 2 \
                        and not (pp.kind == "OP" and pp.val in ("(", "[", "{", ",", ":", "->", "=")) and pp.kind != "NL"
                    return i if ok else None
                depth -= 1
            elif k.kind == "OP" and k.val in (",", ";") and depth == 0:
                return None
            i += 1

    def parse_paren(self):
        t = self.next()
        line = t.line
        save = (self.no_trailing, self.stop_bol)
        self.no_trailing = False
        self.stop_bol = 0
        self.skip_nl()
        o, nt = self.peek(), self.peek(1)
        word = o.kind == "NAME" and o.val in self.WORD_SECT and not (nt.kind == "OP" and nt.val == ")")
        if word or self.section_op(o, nt):                                   # `(+ 1)`, `(`div` 2)`, `(and ok)`, `(in xs)`
            self.next()
            right = self._climb((self._tier_of(o) if word else BINTIER.get(o.val) if o.kind == "OP" else T_BT) + 1)
            self.skip_nl()
            self.expect_op(")", "to close the section")
            self.no_trailing, self.stop_bol = save
            if contains_ph(right):
                self.err("a section already has its hole: write `(+ 1)`, not `(+ _)`", o)
            return ph_lambda(self.sect_body(o, PH(1, line=o.line), right), line)
        end = self.left_section_end()
        if end is not None:                                                   # `(10 -)`
            op = self.peek(end - 1)
            fake = (op.kind, op.val)
            op.kind, op.val = "OP", ")"
            left = self.parse_expr()
            self.skip_nl()
            self.expect_op(")")
            op.kind, op.val = fake
            self.next()
            self.no_trailing, self.stop_bol = save
            if contains_ph(left):
                self.err("a section already has its hole: write `(10 -)`, not `(_ -)`", op)
            return ph_lambda(self.sect_body(op, left, PH(1, line=op.line)), line)
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
            elif tt.kind == "OP" and tt.val == ":" and not cur:
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
            self.err("`(:` marks a one-item tuple: write `(:40)`", t)
        if multi:
            rows.append((cur, 0))
            return MArr(rows, line=line)
        if len(cur) == 1 and cur[0][0] is None and not cur[0][2] and not trailing_comma:
            e = cur[0][1]
            return e if not isinstance(e, (Pipe,)) else e
        return TupleE(cur, line=line)

    # ------------------------------------------------------------ lambda
    ARROW_MSG = ("an anonymous `fn` has no `->`: declare it like a named function without the name, `fn (params) Ret`, "
                 "with the body indented below (a lambda, `(params) -> body`, is the one-line form)")

    def fn_block_body(self):
        """The indented body of an anonymous `fn` or an inline fiber."""
        if self.at_op("->"):
            self.err(self.ARROW_MSG, self.peek())
        if not (self.peek().kind == "NL" and self.peek(1).kind == "INDENT"):
            self.err("an anonymous `fn` takes an indented body on the lines below, so bind it on its own line first (`f = fn (params) Ret`, body indented) and pass `f`", self.peek())
        return self.parse_block()

    def parse_anon_fn(self):
        """`fn (params) [Ret]` and an indented body: an anonymous function that may have effects (a lambda, `(params) -> body`, is pure)."""
        t = self.next()   # fn
        if not self.at_op("("):
            self.err("'fn' here begins an anonymous function, `fn (params) Ret` with an indented body; a named function is a declaration", t)
        params = self.parse_params()
        ret = None
        if not (self.at_op("->") or self.peek().kind == "NL"):
            ret = self.parse_ret_type()
        body = self.fn_block_body()
        lam = Lambda(params, body, None, None, ret, line=t.line)
        lam.fiber = True        # effects allowed (the flag also marks an inline fiber)
        return lam

    def parse_lambda(self, run=True):
        """The inline fiber `go fn (args)(params)` and an indented body (the arguments come first, like `go name(args)`).
        An anonymous function elsewhere is written `(params) -> body` (parse_bare_lambda)."""
        t = self.next()   # fn
        line = t.line
        if self.at_op("("):
            m = self.matching(0)
            t2 = self.toks[m + 1] if m is not None else None
            if t2 is not None and t2.kind == "OP" and t2.val == "(" and not t2.sp:
                m2 = self.matching(m + 1 - self.p)
                t3 = self.toks[m2 + 1] if m2 is not None else None
                if t3 is not None and (t3.kind == "NL" or (t3.kind == "OP" and t3.val == "->")):
                    args = self.parse_args()
                    params = self.parse_params()
                    body = self.fn_block_body()
                    lam = Lambda(params, body, None, None, None, line=line)
                    lam.fiber = True
                    return Call(lam, args, None, line=line)
        params = self.parse_params()
        body = self.fn_block_body()
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
        is_block = False
        if t.kind == "NAME" and t.val in ("ref", "lazy", "using", "move", "block") and self.peek(1).kind == "NAME" \
                and (self.at_op(",", 2) or self.at_op(")", 2) or self.at_op("=", 2) or self.at_op(":", 2) or self.type_follows(2)):
            mod = t.val
            self.next()
            if mod == "block":            # `block items List[Li]`: the parameter an indented block of children fills
                is_block, mod = True, None
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
        where = None
        wtext = None
        if typ is not None and self.at_name("where"):
            self.next()
            wstart = self.p
            where = self.parse_expr()                 # a refinement: a condition the compiler proves at each call (Spec 9c)
            wtext = ""
            for tk in self.toks[wstart:self.p]:
                wtext += (" " if tk.sp and wtext else "") + str(tk.val)
        if self.at_op("="):
            self.next()
            default = self.parse_expr()
        if mod == "using" and (name is None or name == "_"):
            self.err("a `using` parameter needs a name and a type: write `using ctx Context`", t)
        if is_block:
            if default is None:
                default = Call(Name("List", line=line), [], None, None, None, line=line)       # no block given: no children
            p = Param(pat, name, typ, default, mod, variadic, where, wtext, True, line=line)
            return p
        return Param(pat, name, typ, default, mod, variadic, where, wtext, line=line)

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

    def pattern_bind_ahead(self):
        """A line of an `eval` block that starts with a pattern and then `<-` (a `<` and a `-` with no space between them): `(a, b) <- e`."""
        depth = 0
        k = 0
        while True:
            t = self.peek(k)
            if t.kind in ("NL", "EOF", "INDENT", "DEDENT"):
                return False
            if t.kind == "OP":
                if t.val in ("(", "[", "{"):
                    depth += 1
                elif t.val in (")", "]", "}"):
                    depth -= 1
                elif depth == 0 and t.val == "=":
                    return False
                elif depth == 0 and t.val == "<" and k > 0:
                    t2 = self.peek(k + 1)
                    return t2.kind == "OP" and t2.val == "-" and not t2.sp
            k += 1

    def mutable_rewrite(self, blk):
        """A `mutable` block assigns instead of rebinding: a name declared in the block (or on its `in` line) is changed by any
        later `x = e`, `x += e`, `x(i) = e` or `x.f = e`, at any depth, so inside a nested block the target is rewritten to the
        declaring block's name (`x@1`).  A name first assigned in a nested block is that block's own local."""
        if not hasattr(self, "_mut_done"):
            self._mut_done = set()
        stack = [set()]
        bound = set()

        def names_of_pattern(pt):
            out = []

            def go(x):
                if isinstance(x, (list, tuple)):
                    for y in x:
                        go(y)
                elif hasattr(x, "_fields"):
                    if x.__class__ is PBind:
                        out.append(x.name)
                    for f in x._fields:
                        go(getattr(x, f))
            go(pt)
            return out

        def root_swap(e):
            """Replace the `Name` at the root of a place (`x`, `x(i)`, `x.f`) with `x@1`; True when it was one of ours."""
            k = e.__class__
            if k is Name:
                return None if e.name not in outer_names() else Gimme(1, e.name, line=e.line)
            for f in ("fn", "obj", "e", "target"):
                sub = getattr(e, f, None) if f in e._fields else None
                if sub is not None and hasattr(sub, "_fields"):
                    r = root_swap(sub)
                    if r is not None:
                        setattr(e, f, r)
                        return e
                    return None
            return None

        def outer_names():
            return set().union(*stack[:-1]) - stack[-1] if len(stack) > 1 else set()

        def walk(n):
            if isinstance(n, (list, tuple)):
                for x in n:
                    walk(x)
                return
            if not hasattr(n, "_fields"):
                return
            k = n.__class__
            if k in (Lambda, FnDecl) or (k is DoE and id(n.body) in self._mut_done):
                return
            if k is Carry:
                for it in n.items:
                    stack[-1].add(it.name)
                return
            if k is Block:
                stack.append(set())
                walk(n.stmts)
                stack.pop()
                return
            if k is Assign:
                walk(n.value)
                if n.op == "=" and n.targets.__class__ is PBind and n.targets.name in stack[-1]:
                    MUT_RE.add(id(n))                  # an assignment to a mutable name: its type is already fixed
                for t in (n.targets if isinstance(n.targets, list) else [n.targets]):
                    if t.__class__ is PBind:
                        if t.name in outer_names():
                            if n.op == "=":
                                MUT_RE.add(id(n))
                            n.targets = PPlace(Gimme(1, t.name, line=n.line), line=n.line) if not isinstance(n.targets, list) else n.targets
                            if isinstance(n.targets, list):
                                n.targets[n.targets.index(t)] = PPlace(Gimme(1, t.name, line=n.line), line=n.line)
                        else:
                            stack[-1].add(t.name)
                    elif t.__class__ is PPlace:
                        r = root_swap(t.expr)
                        if r is not None:
                            t.expr = r
                        else:
                            rt = t.expr
                            while rt.__class__ in (Call, Field) and not isinstance(getattr(rt, "fn" if rt.__class__ is Call else "obj", None), str):
                                rt = rt.fn if rt.__class__ is Call else rt.obj
                            if rt.__class__ is Name and rt.name not in bound and not any(rt.name in st for st in stack):
                                self.err(f"`{rt.name}` is not a variable of this `mutable` block, so it can't be assigned here: "
                                         f"copy it in with `in {rt.name}` as the block's first line (or declare it in the block)",
                                         type("T", (), {"line": n.line, "col": 0})())
                    else:
                        for nm in names_of_pattern(t):
                            stack[-1].add(nm)
                return
            for f in n._fields:
                walk(getattr(n, f))
        bound.update(names_of_pattern(blk.stmts))
        walk(blk.stmts)
        self._mut_done.add(id(blk))

    def parse_eval(self, line, free=False):
        """`eval` block: `name <- e` binds the answer of `e`, a bare expression runs for its effect, a binding line is
        an ordinary local, and the last line is the value. Each step becomes `e.flat_map((name) -> rest)`."""
        self.expect_nl_indent()
        items = []                                                       # (name, line, expr) or (None, line, stmt)
        toks = []
        while True:
            self.skip_nl()
            t = self.peek()
            if t.kind in ("DEDENT", "EOF"):
                break
            t1, t2 = self.peek(1), self.peek(2)
            if (t.kind == "NAME" and t1.kind == "OP" and t1.val == "<" and t2.kind == "OP" and t2.val == "-" and not t2.sp):
                self.next(); self.next(); self.next()
                e = self.parse_expr()
                self.end_line()
                items.append((t.val, t.line, e)); toks.append(t)
            elif self.pattern_bind_ahead():
                pat = self.parse_pattern()
                self.next(); self.next()                                 # `<` `-`
                e = self.parse_expr()
                self.end_line()
                items.append((("pat", pat), t.line, e)); toks.append(t)
            else:
                st = self.parse_stmt()
                items.append((None, st.line, st)); toks.append(t)
        self.expect_dedent()
        if not items:
            self.err("a `eval` block is empty")
        name, ln, last = items[-1]
        if name is not None or last.__class__ in (Assign, ElseLet):
            self.err("a `eval` block ends with the value it gives: write an expression on the last line, not a binding", toks[-1])
        acc = last.e if last.__class__ is ExprStmt else last
        for name, ln, e in reversed(items[:-1]):
            if name is None and e.__class__ in (Assign, ElseLet):
                acc = Block([e, acc], line=ln)                           # an ordinary local line
                continue
            val = e.e if (name is None and e.__class__ is ExprStmt) else e
            if name.__class__ is tuple:
                prm = Param(name[1], None, None, None, None, False, line=ln)            # `(a, b) <- e`: a pattern parameter
            else:
                prm = Param(None, name if name is not None else "_", None, None, None, False, line=ln)
            lam = Lambda([prm], acc, None, None, None, line=ln)
            lam.free = True if free else "eval"          # True: `eval impure`; "eval": a pure `eval`, whose error names `eval impure`
            acc = Call(Field(val, "flat_map", line=ln), [Arg(None, lam, None, line=ln)], None, line=ln)
            acc.chain = True
        return acc

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

    def parse_block_or_inline(self, seq=False):
        """The body after a header: an indented block, or a one-line statement (a `when` arm may have several, joined by `;`)."""
        if self.at_block():
            return self.parse_block()
        save = (self.no_trailing,)
        self.no_trailing = False
        e = self.parse_inline_seq() if seq else self.parse_stmt_inline()
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
        nscr = 1
        if self.peek().kind != "NL":
            scrut = self.parse_header_expr()
            if self.at_op(","):                                          # `when a, b, c`: several values matched at once, as one tuple
                items = [(None, scrut, False)]
                while self.eat_op(","):
                    items.append((None, self.parse_header_expr(), False))
                nscr = len(items)
                scrut = TupleE(items, line=line)
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
                body = self.parse_block_or_inline(seq=True)
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
                body = self.parse_block_or_inline(seq=True)
                arms.append(Arm(None, cond, body, line=aline))
                self.end_line()
                continue
            slots = [self.parse_alts()]
            if nscr == 1 and self.at_op(","):
                self.err("a comma does not separate alternatives: write `A | B` (a comma separates the values only in `when a, b`)")
            while nscr > 1 and self.eat_op(","):
                slots.append(self.parse_alts())
            whole = len(slots) == 1 and nscr > 1 and all(a.__class__ in (PWild, PTuple) for a in slots[0])      # `_`, or `(a, b) | (c, d)`: the whole tuple
            if whole and all(a.__class__ is PWild for a in slots[0]):
                slots = [slots[0]] * nscr                                 # a lone `_` takes whatever the values are
                whole = False
            if len(slots) != nscr and not whole:
                self.err(f"this arm has {len(slots)} pattern{'s' if len(slots) != 1 else ''}, but the `when` matches {nscr} values: write one pattern for each, separated by commas")
            if nscr == 1 or whole:
                pats = slots[0]
            else:                                                       # `A | B, true` is the alternatives (A, true) and (B, true)
                combos = [[]]
                for alts in slots:
                    if len(combos) * len(alts) > self.MAX_ALTS:
                        self.err(f"this arm's alternatives multiply into more than {self.MAX_ALTS} combinations: split it into separate arms")
                    combos = [c + [a] for c in combos for a in alts]
                pats = [PTuple([(None, a) for a in c], line=aline) for c in combos]
            guard = None
            if self.at_name("if"):
                self.next()
                save = self.no_trailing
                self.no_trailing = True
                guard = self.parse_expr()
                self.no_trailing = save
            self.expect_op("->")
            body = self.parse_block_or_inline(seq=True)
            arms.append(Arm(pats, guard, body, line=aline))
            self.end_line()
        self.expect_dedent()
        return WhenE(scrut, arms, line=line)

    def _pat_binds(self, p):
        """True when the pattern binds a name (a lowercase name, an `@`, a rest with a name)."""
        c = p.__class__
        if c is PBind:
            return p.name[:1].islower()
        if c is PAs:
            return True
        if c is PRest:
            return bool(p.name)
        if c is PTuple:
            return any(self._pat_binds(q) for _, q in p.items or [])
        if c is PCon:
            return any(self._pat_binds(q) for _, q in p.args or [])
        if c is PTyped:
            return self._pat_binds(p.pat)
        return False

    def parse_alts(self):
        """One pattern, or several joined by `|` (alternatives that bind the same names)."""
        return self.parse_pattern_alts()

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
            used_else = self.at_name("else")                            # `else body` is `_ -> body`
            if self.at_name("case") and not self.at_op("=", 1):
                self.err("`case` is gone from `select` arms, which are written like `when` arms: `v = read(ch) -> body`, "
                         "`closed(ch) -> body`, `cancelled(c) -> body`, `_ -> body` (drop the word `case`)")
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
            body = self.parse_block_or_inline(seq=True)
            arms.append(SelArm(kind, bind, ex, body, line=aline))
            self.end_line()
            if used_else:
                self.after_else_arm()
        self.expect_dedent()
        return SelectE(arms, line=line)

    def parse_run(self, try_=False):
        line = self.next().line
        if self.at_name("fn"):
            lam = self.parse_lambda(run=True)
            return RunE(lam, None, try_, line=line)
        target = self.parse_postfix()
        return RunE(target, None, try_, line=line)

    def parse_recv_block(self, recv, kind, line):
        if kind == "do":
            if self.at_op("->"):
                self.err("`do` takes its block on the lines below, with no `->` (`->` is for lambdas, Dict entries, and arms)", self.peek())
            self.expect_nl_indent_block()
            body = self.parse_block()
            return DoRecv(recv, "do", body, line=line)
        lines = self.parse_upd_lines()
        return DoRecv(recv, "update", lines, line=line)

    def parse_upd_lines(self):
        if self.peek().kind == "NL" and self.peek(1).kind == "INDENT":
            self.expect_nl_indent()
            out = []
            had = False
            while True:
                self.skip_nl()
                if self.peek().kind in ("DEDENT", "EOF"):
                    break
                ln = self.parse_upd_line()
                out.append(ln)
                had = self.upd_comma
                self.skip_nl()
                if self.peek().kind in ("DEDENT", "EOF"):
                    break
                if not had:
                    self.err(f"an update line ends with a comma unless it is the last one: write `,` after `{ln.name}`", self.peek())
            self.expect_dedent()
            self.upd_comma = had            # a comma after the last line of a nested block also ends the nested entry itself
            return out
        # single inline: field: value
        self.upd_comma = False
        return [self.parse_upd_line(inline=True)]

    def parse_upd_line(self, inline=False):
        t = self.next()
        if t.kind != "NAME":
            self.err("expected a field name", t)
        self.expect_op(":")
        if self.peek().kind == "NL" and self.peek(1).kind == "INDENT":
            nested = self.parse_upd_lines()
            return UpdLine(t.val, None, nested, line=t.line)
        e = self.cur_value(self.parse_expr(), t.val)
        self.upd_comma = False
        if not inline and self.at_op(","):
            self.next()
            self.upd_comma = True
        if not inline and (not self.upd_comma or self.peek().kind == "NL"):
            self.end_line()
        return UpdLine(t.val, e, None, line=t.line)

    def cur_value(self, x, name, keep=False):
        """In an update line `field: ...`, a `&` that is not the slot of a pipe stage is the field's current value."""
        if x.__class__ is Slot:
            return x if keep else UpdCur(name, line=getattr(x, "line", 0))
        if isinstance(x, list):
            return [self.cur_value(y, name) for y in x]
        if isinstance(x, tuple):
            return tuple(self.cur_value(y, name) for y in x)
        if not hasattr(x, "_fields"):
            return x
        if x.__class__ is Pipe:
            x.l = self.cur_value(x.l, name)
            st = x.stage
            if st.__class__ is Call:
                st.fn = self.cur_value(st.fn, name)
                for a in st.args or []:
                    if a.expr.__class__ is not Slot:
                        a.expr = self.cur_value(a.expr, name)
            else:
                x.stage = self.cur_value(st, name)
            return x
        for f in x._fields:
            setattr(x, f, self.cur_value(getattr(x, f), name))
        return x
