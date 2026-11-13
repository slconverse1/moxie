"""Statement and declaration parser."""
from .pexpr import ExprParser, ph_lambda
from .pbase import HARD, ASSIGN_OPS, PBase
from .lexer import MoxieSyntaxError, tokenize
from .ast import *   # noqa

EFFMODS = ("pure", "tailrec", "prints", "parks", "impure")
MODS = {"export", "internal", "inline", "forward", "fiber", "static", "pure", "tailrec", "prints", "parks", "impure"}
DECL_START = {"fn", "tuple", "enum", "interface", "impl"}


class Parser(ExprParser):

    # ------------------------------------------------------------ module
    def parse_module(self):
        self.skip_nl()
        stmts = self.parse_stmts_until_dedent(top=True)
        if self.peek().kind != "EOF":
            self.err(f"unexpected {self.describe(self.peek())}")
        stmts = expand_delegates(stmts, self.file)
        from .withs import expand_withs
        stmts = expand_withs(group_fns(stmts), self.file)
        return Block(stmts, line=1)

    def parse_stmts_until_dedent(self, top=False):
        out = []
        while True:
            self.skip_nl()
            t = self.peek()
            if t.kind in ("DEDENT", "EOF"):
                break
            if t.kind == "INDENT":
                self.err("unexpected indent")
            s = self.parse_stmt()
            out.append(s)
            if s.__class__ is TupleDecl and s.props:
                im = expand_props(s)
                if im is not None:
                    out.append(im)           # the methods behind the tuple's properties, as an impl right after it
        return group_fns(out)

    def parse_stmt(self):
        s = self.parse_stmt_core(allow_decl=True)
        if s.__class__ is TrailIf and self.at_name("else"):
            s = self.parse_guard_else(s.stmt, s.cond, s.line)
        elif s.__class__ in (ExprStmt, Return, Break, Continue) and self.wrapped_if_ahead():
            s = self.parse_wrapped_if(s)
        self.end_line()
        return s

    def wrapped_if_ahead(self):
        """An action line followed by an indented `if` line: a guard whose condition is on its own line."""
        t = self.peek(2)
        return self.nl_indent_at(0) and t.kind == "NAME" and t.val == "if"

    def parse_wrapped_if(self, action):
        """`action` then, indented under it, `if cond` (and optionally `else value`): the same as `action if cond`, for a
        condition too long for the line."""
        self.next()                                   # NL
        self.next()                                   # INDENT
        line = self.next().line                       # `if`
        cond = self.parse_expr()
        if self.at_block() or self.nl_then_word(("elif",)):
            self.err_at(line, "a condition under an action holds one `if cond` line (and an optional `else value`): no body and no `elif`")
        guard = None
        if self.at_name("else"):
            guard = self.parse_guard_else(action, cond, line)
            self.skip_nl()
        elif self.nl_then_word(("else",)):
            self.skip_nl()
            guard = self.parse_guard_else(action, cond, line)
            self.skip_nl()
        else:
            self.skip_nl()
        if self.at_block():
            self.err_at(line, "the `else` of a guard is a value on the same line, not a block")
        self.expect_dedent()
        return guard if guard is not None else TrailIf(action, cond, line=line)

    def parse_guard_else(self, action, cond, line):
        """`action if cond else value`: when the condition fails the action is skipped and the function returns the value,
        so it means `if cond` with the action in the branch and `return value` in the `else`."""
        self.next()                                   # else
        self.no_block_colon()
        if self.at_block() or self.peek().kind in ("NL", "DEDENT", "EOF"):
            self.err_at(line, "the `else` of a guard is a value on the same line: `action if cond else value`")
        value = self.parse_expr()
        return ExprStmt(IfE([(cond, Block([action], line=line))], Block([Return(value, line=line)], line=line), line=line), line=line)

    def nl_then_word(self, words):
        k = 0
        while self.peek(k).kind == "NL":
            k += 1
        t = self.peek(k)
        return t.kind == "NAME" and t.val in words

    def parse_stmt_inline(self):
        return self.parse_stmt_core(allow_decl=False)

    # ------------------------------------------------------------ dispatch
    def parse_stmt_core(self, allow_decl):
        t = self.peek()
        line = t.line
        if t.kind == "OP" and t.val == "\\":
            self.next()
            if self._ends_stmt(self.peek()):
                self.err("`\\` discards a value, so an expression must follow it on the same line")
            value = self.parse_expr()
            return self.trail_if(Assign(PWild(line=line), value, None, "=", None, line=line))
        if t.kind == "NAME" and t.val == "lazy" and self.peek(1).kind == "NAME" and (self.at_op("=", 2) or self.at_op(":", 2) or self.type_follows(2)):
            self.next()
            s = self.parse_stmt_core(allow_decl)
            if s.__class__ is not Assign or s.targets.__class__ is not PBind or s.op != "=":
                self.err("`lazy` goes in front of a plain binding: `lazy total = sum(data)`", t)
            s.lazy = True
            return s
        if t.kind == "NAME":
            v = t.val
            if v in MODS or v in DECL_START:
                pass
            if (v in MODS and v not in EFFMODS) or v in DECL_START or (v in EFFMODS and self.peek(1).kind == "NAME" and self.peek(1).val in MODS | {"fn"}):
                d = self.try_decl()
                if d is not None:
                    return d
            if v == "foreign" and self.peek(1).kind == "STR" and self.nl_indent_at(2):
                return self.parse_foreign()
            if v == "import":
                return self.parse_import()
            if v == "type" and self.peek(1).kind == "NAME" and self.peek(1).val in ("alias", "opaque", "union"):
                return self.parse_type_decl([])
            if v == "test" and self.peek(1).kind == "STR":
                return self.parse_test()
            if v == "init" and self.nl_indent_at(1):
                self.next()
                return InitDecl(self.parse_block(), line=line)
            if v == "using" and self.peek(1).kind == "NAME" and (self.at_op("=", 2) or self.at_op(":", 2) or self.type_follows(2)):
                return self.parse_using()
            if v == "forall" and self.peek(1).kind == "NAME" and (self.at_op(":", 2) or self.type_follows(2)):
                return self.parse_forall()
            if v == "return":
                self.next()
                e = None
                if not self._ends_stmt(self.peek()):
                    e = self.parse_expr()
                return self.trail_if(Return(e, line=line))
            if v == "break":
                return self.trail_if(self.parse_break())
            if v == "continue":
                self.next()
                lab = None
                if self.peek().kind == "HASH":
                    lab = self.next().val
                return self.trail_if(Continue(lab, line=line))
            if v == "end" and self.peek(1).kind == "NL" and self.p > 0 and self.toks[self.p - 1].kind == "DEDENT":
                self.next()
                return UnitLit(line=line)
        if t.kind == "HASH" and self.peek(1).kind == "NAME" and self.peek(1).val in ("for", "while", "do"):
            pass
        # assignment?
        a = self.try_assign()
        if a is not None:
            return a
        e = self.parse_expr()
        if self.at_op("++") or self.at_op("--"):
            op = self.next().val
            return Incr(e, 1 if op == "++" else -1, line=line)
        return self.trail_if(ExprStmt(e, line=line))

    def _ends_stmt(self, t):
        if t.kind in ("NL", "DEDENT", "EOF"):
            return True
        if t.kind == "NAME" and t.val in ("if", "else", "elif"):
            return True
        if t.kind == "OP" and t.val in (")", ","):
            return True
        return False

    def trail_if(self, s):
        if self.at_name("if") and not (self.p > 0 and self.toks[self.p - 1].kind in ("DEDENT", "NL")):
            line = self.next().line
            c = self.parse_expr()
            return TrailIf(s, c, line=line)
        return s

    def parse_break(self):
        line = self.next().line
        label = None
        daemon = False
        if self.peek().kind == "HASH":
            label = self.next().val
        elif self.at_name("daemon"):
            self.next()
            daemon = True
        e = None
        if self.at_op("(") and not self.peek().sp:
            args = self.parse_args()
            if len(args) == 1:
                e = args[0].expr
            elif args:
                e = TupleE([(a.label, a.expr, False) for a in args], line=line)
        return Break(label, e, daemon, line=line)

    # ------------------------------------------------------------ assignment
    def try_assign(self):
        """Detect `lhs = rhs`, `lhs op= rhs`, `name: T = rhs`; returns node or None."""
        t = self.peek()
        if not (t.kind == "NAME" or (t.kind == "OP" and t.val in ("(", "^"))):
            return None
        if t.kind == "NAME" and t.val in ("if", "when", "for", "while", "fn", "do", "select", "daemon",
                                           "run", "not", "todo", "true", "false", "return"):
            return None
        # scan to find a top-level assignment operator
        depth = 0
        i = self.p
        if t.kind == "NAME" and t.val in ("export", "internal") and self.peek(1).kind == "NAME":
            i += 1
        ann_at = i + 1
        found = None
        seen_ann = False
        at = self.toks[ann_at]
        if at.sp and ((at.kind == "NAME" and at.val not in ("if", "else", "and", "or", "in", "is", "fn", "when", "not"))
                      or (at.kind == "OP" and at.val in ("(", "["))):
            seen_ann = True                   # `total Int = 0`: a name and then its type
        n = len(self.toks)
        while i < n:
            k = self.toks[i]
            if k.kind in ("NL", "EOF", "INDENT", "DEDENT", "SQL"):
                break
            if k.kind == "OP":
                v = k.val
                if v in ("(", "["):
                    depth += 1
                elif v in (")", "]"):
                    depth -= 1
                    if depth < 0:
                        break
                elif depth == 0:
                    if v in ASSIGN_OPS:
                        found = i
                        break
                    if v == ":" and i == ann_at:
                        seen_ann = True
                        i += 1
                        continue
                    if v == "->" and seen_ann:
                        i += 1
                        continue
                    if v in ("->", "|>", "?", ":"):
                        break
            elif k.kind == "NAME" and depth == 0 and k.val in ("if", "else", "and", "or", "in", "is", "fn", "when"):
                break
            i += 1
        if found is None:
            return None
        return self.parse_assign(found)

    def _is_ann_colon(self, i):
        return False

    def parse_assign(self, op_idx):
        t = self.peek()
        line = t.line
        vis = None
        if t.kind == "NAME" and t.val in ("export", "internal"):
            vis = t.val
            self.next()
        # LHS
        pats = []
        ann = None
        while True:
            pats.append(self.parse_lhs_item())
            if self.at_op(":"):
                if PBase.RECORD is not None:
                    PBase.RECORD.append(("decl", self.next()))
                else:
                    self.err("a binding has no colon before its type: write `total Int = 0`")
                ann = self.parse_type()
            elif self.type_follows() and not self.at_op("=") and not self.at_op(","):
                ann = self.parse_type()
            if self.eat_op(","):
                continue
            break
        pat = pats[0] if len(pats) == 1 else PTuple([(None, p) for p in pats], line=line)
        opt = self.peek()
        if not (opt.kind == "OP" and opt.val in ASSIGN_OPS):
            self.err(f"expected '=' but found {self.describe(opt)}")
        self.next()
        op = opt.val
        value = self.parse_expr()
        if self.at_op(",") and op == "=":
            items = [(None, value, False)]
            while self.eat_op(","):
                items.append((None, self.parse_expr(), False))
            value = TupleE(items, line=line)
        if self.at_name("else") and op == "=":
            self.next()
            self.no_block_colon()
            el = self.parse_block_or_inline()
            return ElseLet(pat, value, el, line=line)
        return Assign(pat, value, ann, op, vis, line=line)

    def parse_lhs_item(self):
        t = self.peek()
        if t.kind == "NAME" and t.val not in HARD or (t.kind == "NAME" and t.val == "self"):
            nt = self.peek(1)
            lower = t.val[:1].islower() or t.val[:1] == "_"
            if lower and ((nt.kind == "OP" and nt.val == "." ) or (nt.kind == "OP" and nt.val == "(" and not nt.sp)):
                e = self.parse_postfix_place()
                return PPlace(e, line=t.line)
        return self.parse_pattern()

    def parse_postfix_place(self):
        save = self.no_trailing
        self.no_trailing = True
        e = self.parse_postfix()
        self.no_trailing = save
        return e

    # ------------------------------------------------------------ import etc
    def parse_import(self):
        line = self.next().line
        parts = [self.next().val]
        while self.at_op("."):
            self.next()
            parts.append(self.next().val)
        alias = None
        names = None
        if self.at_name("as"):
            self.next()
            alias = self.next().val
        if self.at_op("("):
            names = [a.expr.name if isinstance(a.expr, Name) else a.expr for a in self.parse_args()]
        return ImportDecl(parts, alias, names, line=line)

    def parse_using(self):
        line = self.next().line
        name = self.next().val
        self.no_decl_colon("a `using` binding")
        if self.type_follows():
            self.parse_type()
        self.expect_op("=")
        e = self.parse_expr()
        return UsingDecl(name, e, line=line)

    def parse_forall(self):
        line = self.next().line
        binds = []
        while True:
            name = self.expect_ident("a name").val
            self.no_decl_colon("a `forall` name")
            binds.append((name, self.parse_type()))
            if not self.eat_op(","):
                break
        self.expect_nl_indent_block()
        return ForAll(binds, self.parse_block(), line=line)

    def parse_test(self):
        line = self.next().line
        name = "".join(p for p in self.next().val if isinstance(p, str))
        self.expect_nl_indent_block()
        return TestDecl(name, self.parse_block(), line=line)

    def parse_type_decl(self, mods):
        line = self.next().line  # type
        kind = self.next().val
        name = self.expect_ident("a type name").val
        tparams = []
        if self.at_op("["):
            tparams = self.parse_tparams_v2()
        self.expect_op("=")
        if self.at_name("when"):
            typ = self.parse_type_match()
        else:
            typ = self.parse_type()
        return AliasDecl(kind, name, tparams, typ, mods[0] if mods else None, line=line)

    def parse_arm_result(self):
        """The result of an arm of a type function: a type, or arithmetic on types and numbers (`1 + Length[Rest]`)."""
        save = self.p
        try:
            t = self.parse_type()
            if self.peek().kind in ("NL", "DEDENT", "EOF"):
                return t
        except MoxieSyntaxError:
            pass
        self.p = save
        e = self.parse_expr()
        return TExpr(e, line=e.line)

    def parse_type_match(self):
        """`when T:` and then, indented, `pattern -> type` arms: a type function that looks at the shape of a type."""
        line = self.next().line
        scrut = self.parse_type()
        self.no_block_colon()
        self.expect_nl_indent()
        arms = []
        while True:
            self.skip_nl()
            if self.peek().kind in ("DEDENT", "EOF"):
                break
            if self.peek().kind == "INT":                # a number is a type too: `() -> 0`
                tk = self.next()
                pat = TExpr(IntLit(tk.val, tk.extra, line=tk.line), line=tk.line)
            elif self.peek().kind == "STR":              # and so is a string: `"id" -> Int`
                e = self.parse_atom()
                pat = TExpr(e, line=e.line)
            elif self.peek().kind == "NAME" and self.peek().val not in ("any", "static") and self.peek(1).kind == "NAME" \
                    and self.peek(1).val not in ("if",) \
                    or (self.peek().kind == "NAME" and self.peek(1).kind == "OP" and self.peek(1).val == ":" and self.peek(2).kind == "NAME"):
                tk = self.next()                         # `X Show` or `X Show + Eq`, written like a bound `[T Show + Eq]`
                self.no_decl_colon("a bound")
                first = self.next().val
                also = []
                while self.at_op("+") and self.peek(1).kind == "NAME":
                    self.next()
                    also.append(self.next().val)
                pat = TBound(tk.val, first, also, line=tk.line)
            else:
                pat = self.parse_type_prim()             # no `->` inside: a function type here is written in parentheses
            guard = None
            if self.at_name("if"):
                self.next()
                save = self.no_trailing
                self.no_trailing = True
                guard = self.parse_expr()
                self.no_trailing = save
            self.expect_op("->")
            arms.append((pat, self.parse_arm_result(), guard))
            self.end_line()
        self.expect_dedent()
        return TMatch(scrut, arms, line=line)

    # ------------------------------------------------------------ declarations
    def try_decl(self):
        i = 0
        mods = []
        while self.peek(i).kind == "NAME" and self.peek(i).val in MODS and not (self.peek(i).val in EFFMODS and not (self.peek(i + 1).kind == "NAME" and self.peek(i + 1).val in MODS | {"fn"})):
            mods.append(self.peek(i).val)
            if self.peek(i).val == "fiber" and self.peek(i + 1).kind == "OP" and self.peek(i + 1).val == "[" \
                    and self.peek(i + 2).kind == "INT" and self.peek(i + 3).kind == "OP" and self.peek(i + 3).val == "]":
                mods.append("fiber:" + str(self.peek(i + 2).val))        # fiber[3] fn: at most 3 alive at once
                i += 3
            i += 1
        t = self.peek(i)
        if t.kind != "NAME":
            return None
        if t.val == "fn":
            nt = self.peek(i + 1)
            # `fn (` here is a ref receiver declaration, `fn (ref Self) name(...)`; a lambda no longer starts with fn
            if nt.kind == "OP" and nt.val == "(":
                # receiver declaration: fn (ref Self) name(...)
                m = self.matching(i + 1)
                after = self.toks[m + 1] if m is not None else None
                if after is not None and not (after.kind == "OP" and after.val in ("->", "(")) and after.kind != "NL":
                    pass
                else:
                    return None
            elif nt.kind == "NAME" and self.peek(i + 2).kind == "OP" and self.peek(i + 2).val == "." and self.peek(i + 3).kind == "OP" and self.peek(i + 3).val == "(":
                return None
            for _ in range(i):
                self.next()
            return self.parse_fn_decl(mods)
        if t.val in ("tuple", "enum", "interface", "impl"):
            if t.val == "impl" and False:
                return None
            for _ in range(i):
                self.next()
            if t.val == "tuple":
                return self.parse_tuple_decl(mods)
            if t.val == "enum":
                return self.parse_enum_decl(mods)
            if t.val == "interface":
                return self.parse_iface_decl(mods)
            return self.parse_impl_decl(mods)
        if t.val == "type" and self.peek(i + 1).kind == "NAME" and self.peek(i + 1).val in ("alias", "opaque", "union"):
            for _ in range(i):
                self.next()
            return self.parse_type_decl(mods)
        return None

    # fn declaration (with optional receiver spec, operator names, aliasing)
    def parse_fn_decl(self, mods):
        line = self.next().line   # fn
        flags = set(mods)
        # receiver spec
        if self.at_op("("):
            self.next()
            if self.at_name("ref"):
                self.next()
                flags.add("ref_self")
            self.expect_name("Self")
            self.expect_op(")")
        t = self.peek()
        if t.kind == "NAME":
            name = self.next().val
        elif t.kind == "OP":
            name = self.next().val
        else:
            self.err(f"expected a function name but found {self.describe(t)}")
        tparams = []
        if self.at_op("["):
            tparams = self.parse_tparams_v2()
        if self.at_op("="):
            self.next()
            target = self.parse_expr()
            return FnDecl(name, tparams, [], None, None, None, flags, None, target, line=line)
        params = self.parse_params()
        ret = None
        if self.peek().kind != "NL" and not self.at_op("=") and not self.at_name("if"):
            ret = self.parse_type()
        locals_ = None
        if self.at_op("("):
            locals_ = [p.name for p in self.parse_params()]
        guard = None
        if self.at_name("if"):
            self.next()
            guard = self.parse_expr()
        body = None
        contracts = []
        self.no_block_colon()
        if self.at_op("="):
            self.next()
            body = self.parse_block_or_inline()
        elif self.at_block():
            bline = self.peek().line
            self.expect_nl_indent()
            contracts = self.parse_contract_lines(("requires", "ensures"))
            if self.peek().kind in ("DEDENT", "EOF"):
                self.expect_dedent()          # contracts only: a bodyless member (interface)
            else:
                stmts = self.parse_stmts_until_dedent()
                self.expect_dedent()
                body = Block(stmts, line=bline)
        return FnDecl(name, tparams, params, ret, locals_, body, flags, None, None, guard, contracts, line=line)

    def parse_foreign(self):
        """foreign "lib": a block of body-less function declarations (Spec 19a)."""
        line = self.next().line
        lib = "".join(x for x in self.next().val if isinstance(x, str))
        self.no_block_colon()
        self.expect_nl_indent()
        fns = []
        handles = []
        while True:
            self.skip_nl()
            if self.peek().kind in ("DEDENT", "EOF"):
                break
            t0 = self.peek()
            if t0.kind == "NAME" and t0.val == "handle" and self.peek(1).kind == "NAME" \
                    and self.peek(2).kind == "NAME" and self.peek(2).val == "closes":
                self.next()
                hname = self.next().val
                self.next()
                closer = self.next()
                if closer.kind != "NAME":
                    self.err("expected the name of the function that closes the handle", closer)
                handles.append((hname, closer.val, t0.line))
                self.end_line()
                continue
            d = self.try_decl()
            if d is None or d.__class__ is not FnDecl:
                self.err("expected a foreign function declaration")
            if d.body is not None:
                self.err("a foreign function has no body", self.peek())
            fns.append(d)
            self.end_line()
        self.expect_dedent()
        return ForeignDecl(lib, fns, handles, line=line)

    def parse_contract_lines(self, kws):
        """Leading `requires EXPR` / `ensures EXPR` / `invariant EXPR` lines of a block."""
        out = []
        while True:
            self.skip_nl()
            t = self.peek()
            nxt = self.peek(1)
            if t.kind == "NAME" and t.val in kws and not (nxt.kind == "OP" and nxt.val in ("=", ".", ":")) \
                    and nxt.kind not in ("NL", "EOF"):
                self.next()
                start = self.p
                e = self.parse_expr()
                text = ""
                for tk in self.toks[start:self.p]:
                    text += (" " if tk.sp and text else "") + str(tk.val)
                self.end_line()
                out.append((t.val, e, t.line, text))
            else:
                break
        return out

    def parse_block_or_inline_body(self):
        return self.parse_block_or_inline()

    def parse_derivs(self):
        derivs = []
        if self.at_name("deriving"):
            self.next()
            derivs.append(self.next().val)
            while self.eat_op(","):
                derivs.append(self.next().val)
        return derivs

    def parse_tuple_decl(self, mods):
        line = self.next().line
        name = self.expect_ident("a tuple name").val
        tparams = []
        if self.at_op("["):
            tparams = self.parse_tparams_v2()
        positional = None
        if self.at_op("(") and not self.peek().sp:
            self.next()
            positional = []
            while not self.at_op(")"):
                positional.append(self.parse_type())
                if not self.eat_op(","):
                    break
            self.expect_op(")")
        derivs = self.parse_derivs()
        fields = []
        invariants = []
        props = []
        self.no_block_colon()
        if self.at_block():
            self._invariants = invariants
            self._props = props
            fields = self.parse_field_decls()
        vis = None
        for m in mods:
            if m in ("export", "internal"):
                vis = m
        return TupleDecl(name, tparams, fields, derivs, positional, vis, invariants, props or None, line=line)

    # ------------------------------------------------------------ properties
    def property_ahead(self):
        """`property name: T`, `property[n] name: T`, `lazy property ...`, `static property ...` (a field may still be called `property`)."""
        i = 0
        while self.peek(i).kind == "NAME" and self.peek(i).val in ("static", "lazy"):
            i += 1
        t = self.peek(i)
        if not (t.kind == "NAME" and t.val == "property"):
            return False
        n = self.peek(i + 1)
        if n.kind == "OP" and n.val == "[":
            return True
        return n.kind == "NAME" and (self.type_follows(i + 2) or self.at_op(":", i + 2))

    def err_at(self, line, msg):
        raise MoxieSyntaxError(msg, line, 0, self.file)

    def parse_property(self):
        mods = set()
        while self.peek().kind == "NAME" and self.peek().val in ("static", "lazy"):
            m = self.next().val
            if m in mods:
                self.err(f"`{m}` twice")
            mods.add(m)
        line = self.next().line                      # property
        cap = None
        if self.at_op("["):
            self.next()
            ct = self.next()
            if ct.kind != "INT" or not isinstance(ct.val, int) or ct.val < 1:
                self.err("the number in `property[n]` is how many observers the property can have, a positive integer", ct)
            cap = ct.val
            self.expect_op("]")
        name = self.expect_ident("a property name").val
        self.no_decl_colon("a property")
        typ = self.parse_type()
        default = None
        if self.at_op("="):
            self.next()
            default = self.parse_expr()
        self.eat_op(",")
        get = set_ = did = will = None
        priv = False
        if self.peek().kind == "NL" and self.peek(1).kind == "INDENT" and self.peek(2).kind == "NAME" \
                and self.peek(2).val in ("get", "set", "priv", "did_set", "will_set"):
            self.expect_nl_indent()
            while True:
                self.skip_nl()
                if self.peek().kind in ("DEDENT", "EOF"):
                    break
                t = self.next()
                if t.kind != "NAME":
                    self.err("expected `get`, `set`, or `did_set` in a property", t)
                which = t.val
                if which == "priv":
                    if not self.at_name("set"):
                        self.err("`priv` goes in front of `set`: a property's getter is always public", t)
                    self.next()
                    which = "set"
                    priv = True
                if which == "get":
                    if get is not None:
                        self.err(f"`{name}` has two getters", t)
                    if self.at_block() or self.at_op("->"):
                        get = self.parse_body("->", "a getter")
                    else:
                        self.no_block_colon()
                        get = "default"
                elif which == "set":
                    if set_ is not None:
                        self.err(f"`{name}` has two setters", t)
                    pname, ptype = "value", None
                    named = False
                    if self.at_op("("):
                        self.next()
                        pname = self.expect_ident("the name of the new value").val
                        self.no_decl_colon("a setter parameter")
                        if self.type_follows():
                            ptype = self.parse_type()
                        self.expect_op(")")
                        named = True
                    rtype = None
                    if named and not (self.at_block() or self.at_op("->")):
                        rtype = self.parse_type()
                        if not (rtype.__class__ is TName and rtype.path == ["Result"]):
                            self.err(f"a setter that can fail returns a `Result`, as in `set(value) Result[Unit, Error]`", t)
                    if self.at_block() or self.at_op("->"):
                        set_ = (pname, ptype, self.parse_body("->", "a setter"), rtype)
                    elif named:
                        self.err("a setter with a parameter needs a body: `set(value)` and an indented block", t)
                    else:
                        set_ = "default"
                elif which == "will_set":
                    if will is not None:
                        self.err(f"`{name}` has two `will_set` blocks", t)
                    self.expect_op("(")
                    pname = self.expect_ident("the name of the new value").val
                    self.expect_op(")")
                    will = (pname, self.parse_body("->", "`will_set`"))
                elif which == "did_set":
                    if did is not None:
                        self.err(f"`{name}` has two `did_set` blocks", t)
                    self.expect_op("(")
                    pname = self.expect_ident("the name of the old value").val
                    self.expect_op(")")
                    did = (pname, self.parse_body("->", "`did_set`"))
                else:
                    self.err(f"expected `get`, `set`, `will_set`, or `did_set` in a property, not `{which}`", t)
                self.end_line()
            self.expect_dedent()
        bodies = [get if isinstance(get, N) else None,
                  set_[2] if isinstance(set_, tuple) else None,
                  did[1] if did is not None else None,
                  will[1] if will is not None else None]
        uses = any(b is not None and _mentions_field(b) for b in bodies)
        static, lazy = "static" in mods, "lazy" in mods
        if static and lazy:
            self.err_at(line, f"`{name}`: a static property can't also be `lazy`")
        if static:
            if set_ is not None or did is not None or will is not None or priv or cap is not None:
                self.err_at(line, f"`{name}`: a static property is read-only, so it has no `set`, `did_set`, or observer count")
            if uses:
                self.err_at(line, f"`{name}`: a static property stores nothing, so `field` has no meaning there")
            if default is not None and get is not None:
                self.err_at(line, f"`{name}`: a static property has an `= value` or a `get`, not both")
            if default is None and not isinstance(get, N):
                self.err_at(line, f"`{name}`: a static property needs a value (`= expr`) or a `get:` body")
        computed = isinstance(get, N) and not uses
        if lazy:
            if not isinstance(get, N) or uses:
                self.err_at(line, f"`{name}`: a `lazy` property is computed by its `get:` body, which stores nothing")
            if set_ is not None or did is not None or will is not None or default is not None or cap is not None:
                self.err_at(line, f"`{name}`: a `lazy` property has only a `get:` body")
        stored = not static and not lazy and not computed
        if computed and default is not None and not static:
            self.err_at(line, f"`{name}` has no storage (its `get` never uses `field`), so it can't have an `= value`")
        if isinstance(set_, tuple) and set_[3] is not None and (priv or static or lazy):
            self.err_at(line, f"`{name}`: a setter that returns a `Result` is public, so it can't be `priv set`")
        if stored and isinstance(set_, tuple) and not _mentions_field(set_[2]):
            self.err_at(line, f"the setter of `{name}` never stores into `field`, so every write would be lost")
        if (did is not None or will is not None) and not stored:
            self.err_at(line, f"`did_set` and `will_set` go on a property that stores a value, and `{name}` doesn't")
        for b in bodies:
            if b is not None:
                _subst_field(b, name)
        return PropertyDecl(name, typ, default, cap, get, set_, did, priv, stored, lazy, static, None, will, line=line)

    def parse_field_decls(self):
        fields = []
        inline = not (self.peek().kind == "NL" and self.peek(1).kind == "INDENT")
        if not inline:
            self.expect_nl_indent()
        while True:
            if not inline:
                self.skip_nl()
                if self.peek().kind in ("DEDENT", "EOF"):
                    break
            if self.property_ahead():
                if inline:
                    self.err("a property goes on its own line, inside an indented tuple body")
                p = self.parse_property()
                self._props.append(p)
                if p.stored:
                    fields.append(FieldDecl(p.name, p.type, p.default, None, p, line=p.line))
                continue
            t = self.peek()
            if t.kind == "NAME" and t.val == "invariant" and self.peek(1).kind not in ("NL", "EOF") \
                    and not (self.peek(1).kind == "OP" and self.peek(1).val == ":"):
                got = self.parse_contract_lines(("invariant",))
                self._invariants.extend(got)
                continue
            t = self.next()
            if t.kind != "NAME":
                self.err("expected a field name", t)
            self.no_decl_colon("a field")
            typ = self.parse_type()
            default = None
            delegate = None
            if self.at_op("="):
                self.next()
                default = self.parse_expr()
            if self.at_name("delegate"):
                self.next()
                self.expect_op("(")
                delegate = self.parse_type()
                self.expect_op(")")
            fields.append(FieldDecl(t.val, typ, default, delegate, line=t.line))
            self.eat_op(",")
            if inline and self.peek().kind in ("NL", "EOF"):
                break
        if not inline:
            self.expect_dedent()
        return fields

    def parse_enum_decl(self, mods):
        line = self.next().line
        name = self.expect_ident("an enum name").val
        tparams = []
        if self.at_op("["):
            tparams = self.parse_tparams_v2()
        header = None
        if self.at_op("(") and not self.peek().sp:
            header = self.parse_params()
        derivs = self.parse_derivs()
        self.no_block_colon()
        self.expect_nl_indent()
        cases = []
        while True:
            self.skip_nl()
            if self.peek().kind in ("DEDENT", "EOF"):
                break
            t = self.expect_ident("a case name")
            fields = None
            if self.at_op("(") and not self.peek().sp:
                if header is not None:
                    fields = self.parse_args()
                else:
                    fields = []
                    self.next()
                    while not self.at_op(")"):
                        ft = self.peek()
                        colon = self.colon_label_at(0, "a case field has no colon: write `Circle(radius Float)`")
                        if ft.kind == "NAME" and (colon or (ft.val not in ("any", "static") and self.type_follows(1))):
                            self.next()
                            if colon:
                                self.next()
                            fields.append(FieldDecl(ft.val, self.parse_type(), None, None, line=ft.line))
                        else:
                            fields.append(FieldDecl(None, self.parse_type(), None, None, line=ft.line))
                        if not self.eat_op(","):
                            break
                    self.expect_op(")")
            cases.append(CaseDecl(t.val, fields, line=t.line))
            self.eat_op(",")
        self.expect_dedent()
        vis = None
        for m in mods:
            if m in ("export", "internal"):
                vis = m
        return EnumDecl(name, tparams, header, cases, derivs, vis, line=line)

    def parse_iface_decl(self, mods):
        line = self.next().line
        name = self.expect_ident("an interface name").val
        tparams = []
        if self.at_op("["):
            tparams = self.parse_tparams_v2()
        self.no_block_colon()
        members, embeds = self.parse_members(iface=True)
        vis = None
        for m in mods:
            if m in ("export", "internal"):
                vis = m
        return IfaceDecl(name, tparams, members, embeds, vis, line=line)

    def parse_impl_decl(self, mods):
        line = self.next().line
        tparams = []
        if self.at_op("["):
            tparams = self.parse_tparams_v2()
        first = self.parse_type()
        iface = None
        target = first
        if self.at_name("for"):
            self.next()
            iface = first
            target = self.parse_type()
        self.no_block_colon()
        if not self.at_block():
            return ImplDecl(iface, target, tparams, [], True, line=line)
        members, _ = self.parse_members(iface=False)
        return ImplDecl(iface, target, tparams, members, False, line=line)

    def parse_members(self, iface):
        members = []
        embeds = []
        self.expect_nl_indent()
        while True:
            self.skip_nl()
            if self.peek().kind in ("DEDENT", "EOF"):
                break
            t = self.peek()
            if t.kind == "NAME" and t.val == "type" and self.peek(1).kind == "NAME":
                self.next()
                nm = self.next().val
                ty = None
                if self.eat_op("="):
                    ty = self.parse_type()
                members.append(AliasDecl("assoc", nm, [], ty, None, line=t.line))
                self.end_line()
                continue
            if t.kind == "NAME" and t.val in ("fn", "static", "inline", "export", "internal", "fiber", "pure", "prints", "parks", "impure"):
                d = self.try_decl()
                if d is None:
                    self.err("expected a method declaration")
                members.append(d)
                if self.eat_op(","):
                    continue
                self.end_line()
                continue
            if iface and t.kind == "NAME" and t.val == "property" and self.peek(1).kind == "NAME":
                self.next()
                nm = self.expect_ident("a property name").val
                self.no_decl_colon("a property")
                ty = self.parse_type()
                self.eat_op(",")
                need = set()
                if self.peek().kind == "NL" and self.peek(1).kind == "INDENT" and self.peek(2).kind == "NAME" \
                        and self.peek(2).val in ("get", "set"):
                    self.expect_nl_indent()
                    while True:
                        self.skip_nl()
                        if self.peek().kind in ("DEDENT", "EOF"):
                            break
                        w = self.next()
                        if w.kind != "NAME" or w.val not in ("get", "set"):
                            self.err("an interface lists a property's accessors bare: `get`, `set`", w)
                        need.add(w.val)
                        self.eat_op(",")
                    self.expect_dedent()
                need = need or {"get", "set"}
                pd = PropertyDecl(nm, ty, None, None, None, None, None, False, False, False, False, need, line=t.line)
                members.append(FieldDecl(nm, ty, None, None, pd, line=t.line))
                self.end_line()
                continue
            if iface and t.kind == "NAME":
                # embedded interface or property
                colon = self.colon_label_at(0, "an interface field has no colon: write the name and then its type")
                if colon or (t.val not in ("any", "static") and self.type_follows(1)):
                    nm = self.next().val
                    if colon:
                        self.next()
                    ty = self.parse_type()
                    members.append(FieldDecl(nm, ty, None, None, line=t.line))
                else:
                    embeds.append(self.parse_type())
                if self.eat_op(","):
                    continue
                self.end_line()
                continue
            # property inside an impl:  name Type = expr  /  name = expr
            if t.kind == "NAME":
                a = self.try_assign()
                if a is not None:
                    members.append(a)
                    self.end_line()
                    continue
            self.err(f"unexpected {self.describe(t)} in a declaration block")
        self.expect_dedent()
        return group_fns(members), embeds


def _walk_field(node, fn):
    if isinstance(node, N):
        fn(node)
        for f in node._fields:
            _walk_field(getattr(node, f, None), fn)
    elif isinstance(node, (list, tuple)):
        for x in node:
            _walk_field(x, fn)
    elif isinstance(node, dict):
        for x in node.values():
            _walk_field(x, fn)


def _mentions_field(body):
    hit = []
    _walk_field(body, lambda n: hit.append(1) if n.__class__ in (Name, PBind) and n.name == "field" else None)
    return bool(hit)


def _subst_field(body, new):
    """Inside an accessor, `field` is the property's own stored value: rename it to the field's name."""
    def sub(n):
        if n.__class__ in (Name, PBind) and n.name == "field":
            n.name = new
    _walk_field(body, sub)


def _as_block(b, line):
    return b if b.__class__ is Block else Block([b], line=line)


def _with_setter(td, p, ln):
    """`set_NAME(value) Result[Self, Error]`: the visible function for a property whose setter can fail. It runs the setter on
    a copy and returns the changed tuple, or the setter's `Err`; the original is untouched either way."""
    import copy
    src = (f"fn set_{p.name}(value Int) Result[Int, Error]\n"
           f"  c = self\n  c.__set_{p.name}(value)?\n  Ok(c)\n")
    fn = parse_program(src).stmts[0]
    me = TName([td.name], [[TName([tp.name], []) for tp in td.tparams]] if td.tparams else [])
    fn.flags = set(fn.flags or ()) | {"generated"}
    fn.params[0].type = copy.deepcopy(p.set[1] or p.type)
    fn.ret = TName(["Result"], [[me, TName(["Error"], [])]])
    def lines(n):
        if isinstance(n, N):
            n.line = ln
            for f in n._fields:
                lines(getattr(n, f, None))
        elif isinstance(n, (list, tuple)):
            for x in n:
                lines(x)
    lines(fn)
    return fn


_DELEGATE_BUSY = set()
SEARCH_DIR = [None]        # where imported packages are found, set by the interpreter before it parses the entry file


def failing_delegates(stmts):
    """The names of the types in `stmts` whose `set_value` returns a `Result`."""
    failing = set()
    for s in stmts:
        if s.__class__ is ImplDecl and s.target.__class__ is TName and s.target.path:
            for m in s.members or []:
                for fn in (m.clauses if m.__class__ is FnGroup else [m]):
                    if fn.__class__ is FnDecl and fn.name == "set_value" and fn.ret.__class__ is TName and fn.ret.path == ["Result"]:
                        failing.add(s.target.path[-1])
    return failing


def imported_failing_delegates(stmts, file):
    """The same for the packages this module imports, so a delegate declared elsewhere gets its `set_NAME` too."""
    import os
    from .packages import package_files, parse_package
    from .stdpkg import find_std
    out = set()
    for s in stmts:
        if s.__class__ is not ImportDecl:
            continue
        try:
            base = SEARCH_DIR[0] if SEARCH_DIR[0] is not None else (os.path.dirname(os.path.abspath(file)) if file and not file.startswith("<") else None)
            found = package_files(base, s.pkg)
            if found is not None:
                paths = found[0]
            else:
                one = find_std(s.pkg)
                paths = [one] if one else []
            if not paths or any(p in _DELEGATE_BUSY for p in paths):
                continue
            _DELEGATE_BUSY.update(paths)
            try:
                out |= failing_delegates(parse_package(paths)[1].stmts)
            finally:
                _DELEGATE_BUSY.difference_update(paths)
        except Exception:
            continue
    return out


def expand_delegates(stmts, file=None):
    """For a delegate field whose `set_value` returns a `Result` (declared in this module or in an imported package), a visible
    `set_NAME(v) Result[Self, Error]` in an implicit impl, like the one a property with a failing setter gets."""
    import copy
    failing = failing_delegates(stmts)
    if any(s.__class__ is TupleDecl and any(f.delegate is not None for f in s.fields or []) for s in stmts):
        failing |= imported_failing_delegates(stmts, file)
    out = []
    for s in stmts:
        out.append(s)
        if s.__class__ is not TupleDecl:
            continue
        members = []
        for f in s.fields or []:
            d = f.delegate
            if d is None or d.__class__ is not TName or d.path[-1] not in failing:
                continue
            ln = s.line
            src = f"fn set_{f.name}(value Int) Result[Int, Error]\n  __set_delegate(self, \"{f.name}\", value)\n"
            fn = parse_program(src).stmts[0]
            fn.flags = set(fn.flags or ()) | {"generated"}
            fn.params[0].type = copy.deepcopy(f.type)
            fn.ret = TName(["Result"], [[TName([s.name], [[TName([tp.name], []) for tp in s.tparams]] if s.tparams else []),
                                         TName(["Error"], [])]])
            members.append(fn)
        if members:
            groups = [[TName([tp.name], []) for tp in s.tparams]] if s.tparams else []
            out.append(ImplDecl(None, TName([s.name], groups), [], members, False, line=s.line))
    return out


def expand_props(td):
    """The hidden methods that make a tuple's properties work, as an inherent `impl` for the tuple:
    `__get_NAME` (a computed, lazy, or custom getter, or a static property's value), `__set_NAME` (a custom setter, with a
    `ref` receiver so that `field = ...` writes the stored value), and `__did_set_NAME`."""
    import copy
    members = []
    unit = TName(["Unit"], [])
    for p in td.props:
        ln = p.line
        if p.static:
            body = p.get if isinstance(p.get, N) else Block([ExprStmt(p.default, line=ln)], line=ln)
            members.append(FnDecl("__get_" + p.name, [], [], copy.deepcopy(p.type), None, _as_block(body, ln),
                                  {"static"}, None, None, None, [], line=ln))
            continue
        if isinstance(p.get, N):
            members.append(FnDecl("__get_" + p.name, [], [], copy.deepcopy(p.type), None, _as_block(p.get, ln),
                                  {"pure"} if p.lazy else set(), None, None, None, [], line=ln))
        if isinstance(p.set, tuple):
            pname, ptype, body, rtype = p.set
            prm = Param(None, pname, ptype or copy.deepcopy(p.type), None, None, False, line=ln)
            members.append(FnDecl("__set_" + p.name, [], [prm], copy.deepcopy(rtype or unit), None, _as_block(body, ln),
                                  {"ref_self"}, None, None, None, [], line=ln))
            if rtype is not None:
                members.append(_with_setter(td, p, ln))
        if p.will_set is not None:
            pname, body = p.will_set
            prm = Param(None, pname, copy.deepcopy(p.type), None, None, False, line=ln)
            members.append(FnDecl("__will_set_" + p.name, [], [prm], copy.deepcopy(unit), None, _as_block(body, ln),
                                  set(), None, None, None, [], line=ln))
        if p.did_set is not None:
            pname, body = p.did_set
            prm = Param(None, pname, copy.deepcopy(p.type), None, None, False, line=ln)
            members.append(FnDecl("__did_set_" + p.name, [], [prm], copy.deepcopy(unit), None, _as_block(body, ln),
                                  set(), None, None, None, [], line=ln))
    if not members:
        return None
    groups = [[TName([tp.name], []) for tp in td.tparams]] if td.tparams else []
    return ImplDecl(None, TName([td.name], groups), [], members, False, line=td.line)


def group_fns(stmts):
    """Adjacent FnDecls sharing a name become a FnGroup."""
    out = []
    for s in stmts:
        if isinstance(s, FnDecl) and out and s.body is not None and s.alias is None:
            prev = out[-1]
            if isinstance(prev, FnGroup) and prev.name == s.name:
                prev.clauses.append(s)
                continue
            if isinstance(prev, FnDecl) and prev.name == s.name and prev.body is not None:
                out[-1] = FnGroup(s.name, [prev, s], line=prev.line)
                continue
        out.append(s)
    return out


def _has_pattern_params(fn):
    for p in fn.params:
        if p.pat is not None:
            return True
    return False


def parse_program(src, file="<input>"):
    toks = tokenize(src, file)
    return Parser(toks, file).parse_module()
