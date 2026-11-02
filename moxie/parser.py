"""Statement and declaration parser."""
from .pexpr import ExprParser, ph_lambda
from .pbase import HARD, ASSIGN_OPS
from .lexer import MoxieSyntaxError, tokenize
from .ast import *   # noqa

MODS = {"export", "internal", "inline", "forward", "fiber", "static", "pure", "tailrec"}
DECL_START = {"fn", "tuple", "enum", "interface", "impl"}


class Parser(ExprParser):

    # ------------------------------------------------------------ module
    def parse_module(self):
        self.skip_nl()
        stmts = self.parse_stmts_until_dedent(top=True)
        if self.peek().kind != "EOF":
            self.err(f"unexpected {self.describe(self.peek())}")
        return Block(group_fns(stmts), line=1)

    def parse_stmts_until_dedent(self, top=False):
        out = []
        while True:
            self.skip_nl()
            t = self.peek()
            if t.kind in ("DEDENT", "EOF"):
                break
            if t.kind == "INDENT":
                self.err("unexpected indent")
            out.append(self.parse_stmt())
        return group_fns(out)

    def parse_stmt(self):
        s = self.parse_stmt_core(allow_decl=True)
        self.end_line()
        return s

    def parse_stmt_inline(self):
        return self.parse_stmt_core(allow_decl=False)

    # ------------------------------------------------------------ dispatch
    def parse_stmt_core(self, allow_decl):
        t = self.peek()
        line = t.line
        if t.kind == "NAME":
            v = t.val
            if v in MODS or v in DECL_START:
                pass
            if (v in MODS and v not in ("pure", "tailrec")) or v in DECL_START or (v in ("pure", "tailrec") and self.at_name("fn", 1)):
                d = self.try_decl()
                if d is not None:
                    return d
            if v == "import":
                return self.parse_import()
            if v == "type" and self.peek(1).kind == "NAME" and self.peek(1).val in ("alias", "opaque", "union"):
                return self.parse_type_decl([])
            if v == "test" and self.peek(1).kind == "STR":
                return self.parse_test()
            if v == "init" and self.at_op(":", 1) and self.peek(2).kind == "NL":
                self.next()
                self.next()
                return InitDecl(self.parse_block(), line=line)
            if v == "using" and self.peek(1).kind == "NAME" and (self.at_op("=", 2) or self.at_op(":", 2)):
                return self.parse_using()
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
            if self.at_op(":") :
                self.next()
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
        if self.at_name("else") and self.at_op(":", 1) and op == "=":
            self.next()
            self.next()
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
        if self.eat_op(":"):
            self.parse_type()
        self.expect_op("=")
        e = self.parse_expr()
        return UsingDecl(name, e, line=line)

    def parse_test(self):
        line = self.next().line
        name = "".join(p for p in self.next().val if isinstance(p, str))
        self.expect_op(":")
        return TestDecl(name, self.parse_block_or_inline(), line=line)

    def parse_type_decl(self, mods):
        line = self.next().line  # type
        kind = self.next().val
        name = self.expect_ident("a type name").val
        tparams = []
        if self.at_op("["):
            tparams = self.parse_tparams_v2()
        self.expect_op("=")
        typ = self.parse_type()
        return AliasDecl(kind, name, tparams, typ, mods[0] if mods else None, line=line)

    # ------------------------------------------------------------ declarations
    def try_decl(self):
        i = 0
        mods = []
        while self.peek(i).kind == "NAME" and self.peek(i).val in MODS and not (self.peek(i).val in ("pure", "tailrec") and not (self.peek(i + 1).kind == "NAME" and self.peek(i + 1).val in MODS | {"fn"})):
            mods.append(self.peek(i).val)
            i += 1
        t = self.peek(i)
        if t.kind != "NAME":
            return None
        if t.val == "fn":
            nt = self.peek(i + 1)
            # lambda used as expression statement: fn (x): ...  /  fn Type.(..)
            if nt.kind == "OP" and nt.val == "(":
                # receiver declaration: fn (ref Self) name(...)
                m = self.matching(i + 1)
                after = self.toks[m + 1] if m is not None else None
                if after is not None and not (after.kind == "OP" and after.val in (":", "(")) and after.kind != "NL":
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
        if not self.at_op(":") and self.peek().kind != "NL" and not self.at_op("=") and not self.at_name("if"):
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
        if self.at_op(":"):
            self.next()
            if self.peek().kind == "NL" and self.peek(1).kind == "INDENT":
                bline = self.peek().line
                self.expect_nl_indent()
                contracts = self.parse_contract_lines(("requires", "ensures"))
                stmts = self.parse_stmts_until_dedent()
                self.expect_dedent()
                body = Block(stmts, line=bline)
            else:
                body = self.parse_block_or_inline_body()
        elif self.peek().kind == "NL" and self.peek(1).kind == "INDENT" and self.peek(2).kind == "NAME" \
                and self.peek(2).val in ("requires", "ensures"):
            self.expect_nl_indent()          # contracts on a bodyless member (interface)
            contracts = self.parse_contract_lines(("requires", "ensures"))
            self.expect_dedent()
        return FnDecl(name, tparams, params, ret, locals_, body, flags, None, None, guard, contracts, line=line)

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
        if self.at_op(":"):
            self.next()
            self._invariants = invariants
            fields = self.parse_field_decls()
        vis = None
        for m in mods:
            if m in ("export", "internal"):
                vis = m
        return TupleDecl(name, tparams, fields, derivs, positional, vis, invariants, line=line)

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
            t = self.peek()
            if t.kind == "NAME" and t.val == "invariant" and self.peek(1).kind not in ("NL", "EOF") \
                    and not (self.peek(1).kind == "OP" and self.peek(1).val == ":"):
                got = self.parse_contract_lines(("invariant",))
                self._invariants.extend(got)
                continue
            t = self.next()
            if t.kind != "NAME":
                self.err("expected a field name", t)
            self.expect_op(":")
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
        self.expect_op(":")
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
                        if ft.kind == "NAME" and self.at_op(":", 1):
                            self.next()
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
        self.expect_op(":")
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
        if self.peek().kind in ("NL", "EOF", "DEDENT"):
            return ImplDecl(iface, target, tparams, [], True, line=line)
        self.expect_op(":")
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
            if t.kind == "NAME" and t.val in ("fn", "static", "inline", "export", "internal", "fiber"):
                d = self.try_decl()
                if d is None:
                    self.err("expected a method declaration")
                members.append(d)
                if self.eat_op(","):
                    continue
                self.end_line()
                continue
            if iface and t.kind == "NAME":
                # embedded interface or property
                if self.at_op(":", 1):
                    nm = self.next().val
                    self.next()
                    ty = self.parse_type()
                    members.append(FieldDecl(nm, ty, None, None, line=t.line))
                else:
                    embeds.append(self.parse_type())
                if self.eat_op(","):
                    continue
                self.end_line()
                continue
            # property inside an impl:  name: Type = expr  /  name = expr
            if t.kind == "NAME":
                a = self.try_assign()
                if a is not None:
                    members.append(a)
                    self.end_line()
                    continue
            self.err(f"unexpected {self.describe(t)} in a declaration block")
        self.expect_dedent()
        return group_fns(members), embeds


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
