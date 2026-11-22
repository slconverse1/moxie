"""Statement and declaration parser."""
from .pexpr import ExprParser, ph_lambda
from .pbase import HARD, ASSIGN_OPS, PBase
from .lexer import MoxieSyntaxError, tokenize
from .ast import *   # noqa
from . import units as units_mod

EFFMODS = ("union", "opaque", "pure", "tailrec", "prints", "parks", "impure", "unsafe", "dynamic", "pattern")        # soft: only modifiers when a declaration follows
MODS = {"opaque", "union", "unsafe", "dynamic", "export", "internal", "inline", "forward", "fiber", "static", "pure", "tailrec", "prints", "parks", "impure", "pattern"}
DECL_START = {"fn", "tuple", "enum", "interface", "impl"}


class StmtList(list):
    """The statements of a parsed file; `fwd` lists its `forward tuple` / `forward enum` signatures as (kind, name, tparam count, line, position)."""
    fwd = ()


class FwdType:
    __slots__ = ("kind", "name", "ntp", "line")

    def __init__(self, kind, name, ntp, line):
        self.kind, self.name, self.ntp, self.line = kind, name, ntp, line


SEARCH_DIR = [None]    # where local packages are found (set by the interpreter)
UNIT_SCAN = set()      # package files being read for their units, so a cycle of imports ends


class Parser(ExprParser):

    # ------------------------------------------------------------ module
    def parse_module(self):
        self.skip_nl()
        self.fwd_types = []
        stmts = self.parse_stmts_until_dedent(top=True)
        if self.peek().kind != "EOF":
            self.err(f"unexpected {self.describe(self.peek())}")
        stmts = expand_delegates(stmts, self.file)
        stmts = expand_proxies(stmts, self.file)
        stmts = expand_dyn(stmts, self.file)
        from .withs import expand_withs
        stmts = expand_withs(group_fns(stmts), self.file)
        stmts = StmtList(stmts)
        stmts.fwd = tuple(self.fwd_types)
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
            if t.kind == "NAME" and t.val == "in":
                if out or top:
                    self.err("an `in` line (local copies of outer names) belongs on the first line of a block", t)
                cd = self.try_carry_decl()
                if cd is not None:
                    out.append(cd)
                    continue
            s = self.parse_stmt()
            if s.__class__ is FwdType:
                if not top:
                    self.err(f"`forward {s.kind} {s.name}` belongs at the top level of the file")
                self.fwd_types.append((s.kind, s.name, s.ntp, s.line, len(out)))
                continue
            out.append(s)
            if getattr(self, "_chain_rest", None):
                out.extend(self._chain_rest)         # x = y = z: the later bindings follow the first
                self._chain_rest = []
            if s.__class__ is TupleDecl and s.props:
                im = expand_props(s)
                if im is not None:
                    out.append(im)           # the methods behind the tuple's properties, as an impl right after it
        return group_fns(out)

    def try_carry_decl(self):
        """The first line of a block, `in total, count@1, x@lap`: each name starts as a copy of an outer binding."""
        t0 = self.peek()
        if not (t0.kind in ("NAME", "KW", "OP") and t0.val == "in"):
            return None
        self.next()
        items = []
        while True:
            t = self.peek()
            if t.kind != "NAME" or t.val in HARD or not (t.val[:1].islower() or t.val[:1] == "_"):
                self.err("`in` is followed by the outer names to start from: `in total, count`", t)
            self.next()
            name, n = t.val, None
            a = self.peek()
            if a.kind == "OP" and a.val == "@" and not a.sp:
                b = self.peek(1)
                if b.sp or not ((b.kind == "INT" and isinstance(b.val, int)) or (b.kind == "NAME" and b.val[:1].islower())):
                    self.err("`@` in an `in` line is followed by a layer number or a loop label: `in total@2`, `in total@serve`", b)
                self.next()
                n = self.next().val
            if any(i.name == name for i in items):
                self.err(f"`{name}` is listed twice on the `in` line")
            items.append(Gimme(n, name, line=t.line))
            if self.at_op(","):
                self.next()
                continue
            break
        line = t0.line
        self.end_line()
        return Carry(items, line=line)

    def parse_stmt(self):
        s = self.parse_stmt_core(allow_decl=True)
        if s.__class__ is TrailIf and self.at_name("else"):
            s = self.parse_guard_else(s.stmt, s.cond, s.line)
        elif s.__class__ in (ExprStmt, Return, Break, Continue) and self.wrapped_if_ahead():
            s = self.parse_wrapped_if(s)
        if self.at_op(";") and s.__class__ is ExprStmt and s.e.__class__.__name__ in ("IfE", "WhileE", "ForE"):
            self.err("unexpected ';': not accepted after a `then`, `do` or `else` body; write a block")
        if self.at_op(";"):                               # `a = 1; b = 2`: several statements on one line, in order
            rest = list(getattr(self, "_chain_rest", None) or [])
            while self.eat_op(";"):
                if self.peek().kind in ("NL", "DEDENT", "EOF"):
                    break                                 # a trailing `;` is allowed
                rest.append(self.parse_stmt_core(allow_decl=True))
            self._chain_rest = rest
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

    def parse_inline_seq(self):
        """A one-line body: a single statement (`;` joins statements only at the start of a line)."""
        return self.parse_stmt_inline()

    def parse_stmt_inline(self):
        s = self.parse_stmt_core(allow_decl=False)
        if getattr(self, "_chain_rest", None):
            self._chain_rest = []
            self.err("a chain of bindings (`x = y = z`) goes on a line of its own, not after `then`, `do` or `->`")
        return s

    # ------------------------------------------------------------ dispatch
    def parse_stmt_core(self, allow_decl):
        t = self.peek()
        line = t.line
        if getattr(self, "collecting", 0) and t.kind == "OP" and t.val == "...":       # `...items` in a block of children
            self.next()
            return ExprStmt(Splat(self.parse_expr(), line=line), line=line)
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
            if (v in MODS and v not in EFFMODS) or v in DECL_START or (v in EFFMODS and self.peek(1).kind == "NAME" and self.peek(1).val in MODS | {"fn", "type"}):
                d = self.try_decl()
                if d is not None:
                    return d
            if v == "foreign" and self.peek(1).kind == "STR" and self.nl_indent_at(2):
                return self.parse_foreign()
            if v == "import":
                return self.parse_import()
            if v == "type" and self.is_type_decl(0):
                return self.parse_type_decl([])
            if v == "unit" and self.peek(1).kind == "NAME" and self.is_unit_decl():
                return self.parse_unit_decl([])
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
                    if allow_decl:
                        e = self.parse_bare_tuple(e, line)
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
        if allow_decl:
            e = self.parse_bare_tuple(e, line)
        if self.at_op("++") or self.at_op("--"):
            op = self.next().val
            self.err(f"`{op}` is not used: write `x {'+=' if op == '++' else '-='} 1`")
        return self.trail_if(ExprStmt(e, line=line))

    def parse_bare_tuple(self, first, line):
        """`a, b` as a whole statement or after `return` is the tuple `(a, b)`, the mirror of `lo, hi = f()`."""
        if not self.at_op(","):
            return first
        items = [(None, first, False)]
        while self.eat_op(","):
            items.append((None, self.parse_expr(), False))
        return TupleE(items, line=line)

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
                                           "go", "not", "todo", "true", "false", "return"):
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
                    if v in ("->", "|>", "?", ":", ";"):
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
        chain = []
        while op == "=" and pat.__class__ is PBind and not vis and self.chain_link_ahead():
            self.skip_nl()
            chain.append(self.next())
            self.next()                                # the `=`
        value = self.parse_expr()
        if self.at_op(",") and op == "=":
            items = [(None, value, False)]
            while self.eat_op(","):
                items.append((None, self.parse_expr(), False))
            value = TupleE(items, line=line)
        if chain and self.at_name("else"):
            self.err("a chain of bindings (`x = y = z`) can't have an `else`")
        if self.at_name("else") and op == "=":
            self.next()
            self.no_block_colon()
            pat2 = None
            save = self.p
            try:                      # `else Err(e) -> body`: the failure's own pattern, so its parts are in scope
                cand = self.parse_pattern()
                if self.at_op("->"):
                    self.next()
                    pat2 = cand
            except MoxieSyntaxError:
                pass
            if pat2 is None:
                self.p = save
            el = self.parse_block_or_inline()
            return ElseLet(pat, value, el, pat2, line=line)
        if chain:
            # x = y = z: z is evaluated once, bound to y, and then y to x
            names = [pat.name] + [t.val for t in chain]
            first = Assign(PBind(names[-1], line=line), value, None, "=", None, line=line)
            rest = []
            for i in range(len(names) - 2, -1, -1):
                rest.append(Assign(PBind(names[i], line=line), Name(names[i + 1], line=line), ann if i == 0 else None, "=", None, line=line))
            self._chain_rest = rest
            return first
        return Assign(pat, value, ann, op, vis, line=line)

    def chain_link_ahead(self):
        """`name =` next, possibly on the next line: another link of `x = y = z`."""
        k = 0
        while self.peek(k).kind == "NL":
            k += 1
        t = self.peek(k)
        return (t.kind == "NAME" and t.val not in HARD and t.val not in ("else", "if", "then", "do", "in", "is", "and", "or", "not")
                and self.at_op("=", k + 1))

    def parse_lhs_item(self):
        t = self.peek()
        if t.kind == "NAME" and t.val not in HARD or (t.kind == "NAME" and t.val == "self"):
            nt = self.peek(1)
            lower = t.val[:1].islower() or t.val[:1] == "_"
            if lower and nt.kind == "OP" and nt.val == "@" and not nt.sp and not self.peek(2).sp and (self.peek(2).kind == "INT"
                    or (self.peek(2).kind == "NAME" and self.peek(2).val[:1].islower() and not (self.peek(3).kind == "OP" and self.peek(3).val == "("))):
                e = self.parse_postfix_place()                         # `total@1 = ...`: write the outer binding
                return PPlace(e, line=t.line)
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
        self.import_units(parts)
        return ImportDecl(parts, alias, names, line=line)

    def import_units(self, parts):
        """The units a local package exports (`export unit m`) are in scope here, so `5.0 m` and `d in km` parse.  The scale of each
        comes from the package's own declarations, in order."""
        import os
        from .packages import package_files, unit_preset
        if self.file is None or self.file.startswith("<"):
            base = "."
        else:
            base = os.path.dirname(os.path.abspath(self.file))
        found = None
        for b in (SEARCH_DIR[0], base):
            if b is None:
                continue
            try:
                found = package_files(b, parts)
            except Exception:
                found = None
            if found:
                break
        if not found:
            return
        local = {}
        for path in found[0]:
            if path in UNIT_SCAN:
                continue
            UNIT_SCAN.add(path)
            try:
                with unit_preset(found[0]):
                    prog = parse_program(open(path, encoding="utf-8").read(), path)
            except Exception:
                continue
            finally:
                UNIT_SCAN.discard(path)
            for st in prog.stmts:
                if st.__class__ is UnitDecl:
                    local[st.name] = units_mod.decl_scale(st.text, local)
                    if st.vis == "export":
                        self.units[st.name] = local[st.name]

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

    def is_unit_decl(self):
        """`unit m`, or `unit N = kg * m / s^2` (only names, `*`, `/`, `^` and whole numbers after the `=`), so a variable that is
        itself called `unit` (`unit Shape = Circle(radius: 1.0)`) still parses as a variable."""
        if self.peek(2).kind in ("NL", "EOF"):
            return True
        if not (self.peek(2).kind == "OP" and self.peek(2).val == "="):
            return False
        i = 3
        while self.peek(i).kind not in ("NL", "EOF"):
            t = self.peek(i)
            if not (t.kind in ("NAME", "INT", "FLOAT") or t.kind == "OP" and t.val in ("*", "/", "^")):
                return False
            i += 1
        return i > 3

    def parse_unit_decl(self, mods):
        """`unit m` declares a base unit; `unit N = kg * m / s^2` a unit derived from others."""
        line = self.next().line
        name = self.expect_ident("a unit name").val
        text = None
        if self.at_op("="):
            self.next()
            text = ""
            while self.peek().kind not in ("NL", "EOF"):
                tk = self.next()
                text += str(tk.val) + (" " if tk.kind in ("INT", "FLOAT") and not (self.peek().kind == "OP" and self.peek().val == "^") else "")
            text = text.strip()
            if not text:
                self.err("a unit needs its definition after `=`, such as `unit N = kg * m / s^2` or `unit km = 1000 m`")
        self.units[name] = units_mod.decl_scale(text, self.units)
        return UnitDecl(name, text, mods[0] if mods else None, line=line)

    def is_type_decl(self, i):
        """`type Name = ...` or `type Name[T] = ...` at token `i`.  The old forms (`type alias Name`, `type opaque Name`,
        `type union Name`) are an error that says what to write."""
        a, b = self.peek(i + 1), self.peek(i + 2)
        if a.kind != "NAME":
            return False
        if a.val in ("alias", "opaque", "union") and b.kind == "NAME":
            self.err(f"`type {a.val} {b.val}` is no longer a form: write " + {
                "alias": f"`type {b.val} = ...`", "opaque": f"`opaque type {b.val} = ...`",
                "union": f"`union type {b.val} = A | B`"}[a.val])
        return b.kind == "OP" and b.val in ("=", "[")

    def parse_type_decl(self, mods):
        line = self.next().line  # type
        name = self.expect_ident("a type name").val
        tparams = []
        if self.at_op("["):
            tparams = self.parse_tparams_v2()
        self.expect_op("=")
        if self.at_name("when"):
            typ = self.parse_type_match()
        else:
            typ = self.parse_type()
        if "opaque" in mods and "union" in mods:
            self.err("a type is either `opaque` or a `union`, not both")
        if typ.__class__ is TUnion and "union" not in mods and "opaque" not in mods:
            self.err(f"a union is declared with the word `union` before `type`: write `union type {name} = ...`")
        if "union" in mods and typ.__class__ is not TUnion and typ.__class__ is not TMatch:
            typ = TUnion([typ], line=line)               # `union type One[A] = Say[A]`: a union of one member
        kind = "opaque" if "opaque" in mods else "union" if "union" in mods else "alias"
        mods = [m for m in mods if m not in ("opaque", "union")]
        where = wtext = None
        if kind == "alias" and self.at_name("where"):
            self.next()
            wstart = self.p
            where = self.parse_expr()                  # a refined alias: `type Pos = Int where self > 0` (Spec 9c)
            wtext = ""
            for tk in self.toks[wstart:self.p]:
                wtext += (" " if tk.sp and wtext else "") + str(tk.val)
        return AliasDecl(kind, name, tparams, typ, mods[0] if mods else None, where, wtext, line=line)

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
            elif self.peek().kind == "NAME" and self.peek().val not in ("any", "static", "readonly") and self.peek(1).kind == "NAME" \
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
        while self.peek(i).kind == "NAME" and self.peek(i).val in MODS and not (self.peek(i).val in EFFMODS and not (self.peek(i + 1).kind == "NAME" and self.peek(i + 1).val in MODS | {"fn", "type"})):
            mods.append(self.peek(i).val)
            if self.peek(i).val == "fiber" and self.peek(i + 1).kind == "OP" and self.peek(i + 1).val == "[" \
                    and self.peek(i + 2).kind == "INT" and self.peek(i + 3).kind == "OP" and self.peek(i + 3).val == "]":
                mods.append("fiber:" + str(self.peek(i + 2).val))        # fiber[3] fn: at most 3 alive at once
                i += 3
            i += 1
        t = self.peek(i)
        if t.kind != "NAME":
            return None
        if t.val == "unit" and mods and self.peek(i + 1).kind == "NAME":
            for _ in range(i):
                self.next()
            if self.is_unit_decl():
                return self.parse_unit_decl(mods)
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
        if "forward" in mods and t.val in ("tuple", "enum"):
            for _ in range(i):
                self.next()
            line = self.next().line
            name = self.expect_ident(f"a {t.val} name").val
            ntp = len(self.parse_tparams_v2()) if self.at_op("[") else 0
            return FwdType(t.val, name, ntp, line)
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
        if t.val == "type" and self.is_type_decl(i):
            for _ in range(i):
                self.next()
            return self.parse_type_decl(mods)
        if "opaque" in mods or "union" in mods:
            self.err("`opaque` and `union` go before a `type` declaration: `opaque type Id = Int`, `union type Key = Int | String`")
        return None

    # fn declaration (with optional receiver spec, operator names, aliasing)
    def parse_fn_decl(self, mods):
        line = self.next().line   # fn
        flags = set(mods)
        if "pattern" in flags:
            flags.add("pure")                 # a recognizer runs inside a match, so it may not have effects
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
            if t.val in HARD and not getattr(self, "member_depth", 0):
                self.err(f"`{t.val}` is a keyword, so it cannot name a function (a method may be called `go`, but a function may not): pick another name (`{t.val}_it`, `start`, ...)")
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
        rwhere = None
        if self.peek().kind != "NL" and not self.at_op("=") and not self.at_name("if"):
            ret = self.parse_type()
            if self.at_name("where"):
                wline = self.peek().line
                wcond, wtext = self.parse_where_clause()
                rwhere = ("ensures", wcond, wline, wtext)          # `Int where result >= 0` is an `ensures`
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
        for prm in params:
            if getattr(prm, "where", None) is not None and prm.name and (body is not None or getattr(self, "in_iface", False)):
                contracts = [("requires", prm.where, prm.line, prm.wtext)] + list(contracts)      # also checked on entry, for a function used as a value
        if rwhere is not None:
            contracts = list(contracts) + [rwhere]
        return FnDecl(name, tparams, params, ret, locals_, body, flags, None, None, guard, contracts, line=line)

    def parse_where_clause(self):
        """`where COND` after a result type or a field: the condition and its text as written."""
        self.next()
        wstart = self.p
        cond = self.parse_expr()
        text = ""
        for tk in self.toks[wstart:self.p]:
            text += (" " if tk.sp and text else "") + str(tk.val)
        return cond, text

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
                if t.val in ("requires", "ensures"):
                    self.err("`requires` and `ensures` are not used: write `where` after a parameter (`n Int where n > 0`) "
                             "or after the result type (`Int where result >= 0`)")
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
        head_invariants = []
        head_fields = None
        if self.at_op("(") and not self.peek().sp:
            self.next()
            if self.peek().kind == "NAME" and self.type_follows(1):
                head_fields = []              # `tuple Point(x Int, y Int)`: the fields written on the header line
                while not self.at_op(")"):
                    ft = self.next()
                    if ft.kind != "NAME":
                        self.err("expected a field name", ft)
                    self.no_decl_colon("a field")
                    fty = self.parse_type()
                    if self.at_name("where"):
                        fcond, ftext = self.parse_where_clause()
                        head_invariants.append(("invariant", fcond, ft.line, ftext))
                    fdef = self.parse_expr() if self.eat_op("=") else None
                    head_fields.append(FieldDecl(ft.val, fty, fdef, None, line=ft.line))
                    if not self.eat_op(","):
                        break
                self.expect_op(")")
                if not head_fields:
                    self.err("a tuple needs at least one field")
            else:
                positional = []
                while not self.at_op(")"):
                    positional.append(self.parse_type())
                    if not self.eat_op(","):
                        break
                self.expect_op(")")
                head_fields = [FieldDecl(None, t, None, None, line=line) for t in positional]
        derivs = self.parse_derivs()
        fields = []
        invariants = head_invariants
        props = []
        self.no_block_colon()
        if self.at_block():
            self._invariants = invariants
            self._props = props
            fields = self.parse_field_decls()
        if fields and any(f.name is None for f in fields) and any(f.name is not None for f in fields):
            self.err(f"`{name}` mixes named and unnamed fields: all of a tuple's fields are named or all are unnamed")
        if head_fields is not None:
            if fields:
                self.err(f"`{name}` has its fields in the parentheses, so its indented body can hold only `invariant` lines and properties that have no stored value: write the fields in one place")
            fields = head_fields
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
            t0 = self.peek()
            if (t0.kind == "NAME" and not self.type_follows(1) and not self.at_op(":", 1)) or (t0.kind == "OP" and t0.val == "("):
                typ = self.parse_type()                    # `Int,` on a line of its own: a positional field
                fields.append(FieldDecl(None, typ, None, None, line=t0.line))
                self.eat_op(",")
                if inline and self.peek().kind in ("NL", "EOF"):
                    break
                continue
            t = self.next()
            if t.kind != "NAME":
                self.err("expected a field name", t)
            self.no_decl_colon("a field")
            typ = self.parse_type()
            default = None
            delegate = None
            if self.at_name("where"):
                fline = self.peek().line
                fcond, ftext = self.parse_where_clause()          # `balance Int where balance >= 0` is an `invariant`
                self._invariants.append(("invariant", fcond, fline, ftext))
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

    def parse_case_fields(self):
        fields = []
        self.next()
        while not self.at_op(")"):
            ft = self.peek()
            colon = self.colon_label_at(0, "a case field has no colon: write `Circle(radius Float)`")
            if ft.kind == "NAME" and (colon or (ft.val not in ("any", "static", "readonly") and self.type_follows(1))):
                self.next()
                if colon:
                    self.next()
                fields.append(FieldDecl(ft.val, self.parse_type(), None, None, line=ft.line))
            else:
                fields.append(FieldDecl(None, self.parse_type(), None, None, line=ft.line))
            if not self.eat_op(","):
                break
        self.expect_op(")")
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
            ctps = []
            if self.at_op("[") and not self.peek().sp:
                ctps = self.parse_tparams_v2()                 # a case's own type variables, with bounds: `Shown[A Show](v A) Item[String]`
            fields = None
            payload = None
            if self.at_op("(") and not self.peek().sp:
                if header is not None:
                    fields = self.parse_args()                       # the values of the header's fields
                    if self.at_op("(") and not self.peek().sp:
                        payload, fields = fields, self.parse_case_fields()      # then the case's own payload: `Num(line: 0)(n Int) Value[Int]`
                                                                                # (`fields` is the payload; `payload` holds the header values)
                else:
                    fields = self.parse_case_fields()
            ret = None
            if tparams and self.peek().kind == "NAME" and self.peek().line == t.line:
                ret = self.parse_type()                       # a GADT case states its own result type: `Num(n Int) Value[Int]`
            if ret is not None and header is not None:
                self.err("a case of an enum with a header can't state its own result type: a header and a GADT don't mix (put the shared field in each case's payload instead)", t)
            cases.append(CaseDecl(t.val, fields, ret, ctps, payload, line=t.line))
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
        proxy = None
        if self.at_name("proxy") and self.at_op("(", 1):
            if iface is None:
                self.err("`proxy` hands an interface to a field, so it goes in an `impl Interface for Type` header: `impl Printer for Logger proxy(printer)`")
            self.next()
            self.next()
            proxy = self.expect_ident("the name of the field that takes the interface").val
            if not self.eat_op(")"):
                self.err("expected ')' after the field name in `proxy(...)`")
        self.no_block_colon()
        if not self.at_block():
            return ImplDecl(iface, target, tparams, [], proxy is None, proxy, line=line)
        members, _ = self.parse_members(iface=False)
        return ImplDecl(iface, target, tparams, members, False, proxy, line=line)

    def parse_members(self, iface):
        self.member_depth = getattr(self, "member_depth", 0) + 1
        prev_iface, self.in_iface = getattr(self, "in_iface", False), iface
        try:
            return self._parse_members(iface)
        finally:
            self.member_depth -= 1
            self.in_iface = prev_iface

    def _parse_members(self, iface):
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
            if t.kind == "NAME" and t.val in ("fn", "static", "inline", "export", "internal", "fiber", "pure", "prints", "parks", "impure", "unsafe", "dynamic", "forward"):
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
                if colon or (t.val not in ("any", "static", "readonly") and self.type_follows(1)):
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


def expand_dyn(stmts, file=None):
    """`type P(name String, age Int) deriving dyn`: an inherent `impl` with `to_dyn(self) json.Dyn` and
    `static dynamic fn from_dyn(d json.Dyn) Result[P, Error]`, written out at compile time from the field types (no reflection).
    Fields may be `Int`, `Float`, `Bool`, `String`, a `List` of those, or another tuple or enum that also derives `dyn`.
    An enum is a map with the case name under `"case"` and the case's named fields beside it: `{"case": "Rect", "w": 2.0, "h": 3.0}`."""
    out = []
    for s in stmts:
        out.append(s)
        if s.__class__ not in (TupleDecl, EnumDecl) or "dyn" not in (s.derivs or []):
            continue
        ln = s.line
        is_enum = s.__class__ is EnumDecl

        def fail(msg, s=s, ln=ln):
            raise MoxieSyntaxError(f"`deriving dyn` on `{s.name}`: {msg}", ln, 0, file)
        tps = [tp.name for tp in getattr(s, "tparams", None) or []]
        if any(tp.holes for tp in getattr(s, "tparams", None) or []):
            fail("a type parameter that takes type arguments has no `Dyn` form")
        if not is_enum and not s.fields:
            fail("it needs named fields")

        def to_(t, e, depth, fname):
            if t.__class__ is not TName or not t.path:
                fail(f"field `{fname}` has a type that has no `Dyn` form (a function, tuple type, or other unnamed type)")
            n = t.path[-1]
            if len(t.path) == 1 and n in tps and not t.groups:
                return f"{e}.to_dyn()"
            if n in ("Int", "Float", "Bool"):
                return f"json.Dyn.D{n}({e})"
            if n == "String":
                return f"json.Dyn.DText({e})"
            if n == "List" and t.groups and len(t.groups[0]) == 1:
                v = f"x{depth}"
                return f"json.Dyn.DList({e} |> map(({v}) -> {to_(t.groups[0][0], v, depth + 1, fname)}) |> collect())"
            if n in ("Dict", "Set", "Array", "Option", "Result", "Char", "Byte", "Any"):
                fail(f"field `{fname}` is a `{n}`, which has no `Dyn` form yet (use Int, Float, Bool, String, List, a type parameter, or a tuple or enum that derives `dyn`)")
            return f"{e}.to_dyn()"

        def ttext(t):
            if t.__class__ is not TName:
                fail("a field type with no name has no `Dyn` form")
            return ".".join(t.path) + ("[" + ", ".join(ttext(x) for x in t.groups[0]) + "]" if t.groups else "")

        def from_(t, e, depth, fname):
            n = t.path[-1]
            conv = {"Int": "as_int", "Float": "as_float", "Bool": "as_bool", "String": "as_text"}
            if len(t.path) == 1 and n in tps and not t.groups:
                return f"{n}.from_dyn({e})"
            if n in conv:
                return f"{e}.{conv[n]}()"
            if n == "List":
                v = f"x{depth}"
                return f"json.list_of({e}, ({v}) -> {from_(t.groups[0][0], v, depth + 1, fname)})"
            return f"{ttext(t)}.from_dyn({e})"

        def entry(key, value):
            return f'json.Entry(key: "{key}", value: {value})'
        head = (f"impl[{', '.join(t + ' json.Dynable' for t in tps)}] json.Dynable for {s.name}[{', '.join(tps)}]" if tps
                else f"impl json.Dynable for {s.name}")
        self_t = f"{s.name}[{', '.join(tps)}]" if tps else s.name
        if not is_enum:
            entries, reads = [], []
            for f in s.fields:
                entries.append(entry(f.name, to_(f.type, "self." + f.name, 0, f.name)))
                reads.append(f'{f.name}: {from_(f.type, f"d.field(\"{f.name}\")?", 0, f.name)}?')
            src = (f"{head}\n"
                   f"  fn to_dyn(self) json.Dyn\n    json.Dyn.DMap(List({', '.join(entries)}))\n"
                   f"  static dynamic fn from_dyn(d json.Dyn) Result[{self_t}, Error]\n    Ok({s.name}({', '.join(reads)}))\n")
        else:
            if not s.cases:
                fail("it needs at least one case")
            to_arms, from_arms = [], []
            for c in s.cases:
                flds = c.fields or []
                if any(not getattr(f, "name", None) for f in flds):
                    fail(f"case `{c.name}` has unnamed fields; name them (`{c.name}(w Float, h Float)`) so the map has a key for each")
                pat = f"{c.name}({', '.join(f.name for f in flds)})" if flds else c.name
                ents = [entry("case", f'json.Dyn.DText("{c.name}")')] + [entry(f.name, to_(f.type, f.name, 0, f.name)) for f in flds]
                to_arms.append(f"      {pat} -> json.Dyn.DMap(List({', '.join(ents)}))")
                if flds:
                    args = ", ".join(f'{f.name}: {from_(f.type, f"d.field(\"{f.name}\")?", 0, f.name)}?' for f in flds)
                    from_arms.append(f'      "{c.name}" -> Ok({s.name}.{c.name}({args}))')
                else:
                    from_arms.append(f'      "{c.name}" -> Ok({s.name}.{c.name})')
            src = (f"{head}\n"
                   f"  fn to_dyn(self) json.Dyn\n    when self\n" + "\n".join(to_arms) + "\n"
                   f"  static dynamic fn from_dyn(d json.Dyn) Result[{self_t}, Error]\n"
                   f"    tag = d.field(\"case\")?.as_text()?\n    when tag\n" + "\n".join(from_arms) + "\n"
                   f"      _ -> Err(Error(code: 1, message: \"unknown case \\\"${{tag}}\\\" for {s.name}\"))\n")
        impl = parse_program(src).stmts[0]
        impl.line = ln
        out.append(impl)
    return out


def imported_interfaces(stmts, file):
    """The interfaces declared by the packages this module imports, for `proxy`: {name as written in the impl header: declaration}.
    `import pkg` gives `pkg.Iface` (and the package's own types in its signatures become `pkg.T`); `from pkg import Iface` gives `Iface`."""
    import copy, os
    from .packages import package_files, parse_package
    from .stdpkg import find_std
    out = {}
    for s in stmts:
        if s.__class__ is not ImportDecl:
            continue
        try:
            base = SEARCH_DIR[0] if SEARCH_DIR[0] is not None else (os.path.dirname(os.path.abspath(file)) if file and not file.startswith("<") else None)
            found = package_files(base, s.pkg)
            paths = found[0] if found is not None else ([find_std(s.pkg)] if find_std(s.pkg) else [])
            if not paths or any(p in _DELEGATE_BUSY for p in paths):
                continue
            _DELEGATE_BUSY.update(paths)
            try:
                pk = parse_package(paths)[1].stmts
            finally:
                _DELEGATE_BUSY.difference_update(paths)
        except Exception:
            continue
        alias = s.alias or s.pkg[-1]
        own = {x.name for x in pk if x.__class__ in (TupleDecl, EnumDecl, AliasDecl)}

        def qual(t):
            if isinstance(t, list):
                return [qual(x) for x in t]
            if isinstance(t, tuple):
                return tuple(qual(x) for x in t)
            if not hasattr(t, "_fields"):
                return t
            c = copy.copy(t)
            for f in t._fields:
                setattr(c, f, qual(getattr(t, f, None)))
            if c.__class__ is TName and c.path and len(c.path) == 1 and c.path[0] in own:
                c.path = [alias, c.path[0]]
            return c
        for x in pk:
            if x.__class__ is not IfaceDecl:
                continue
            if s.names is None:
                out[f"{alias}.{x.name}"] = qual(x)
            elif x.name in s.names:
                out[x.name] = x
    return out


def expand_proxies(stmts, file=None):
    """`impl Printer for Logger proxy(printer)`: every method of the interface that the impl does not write forwards to the field,
    as `fn name(params) Ret` with the body `self.printer.name(params)`.  The interface must be declared in this module, with plain
    methods: a `static` member, a `ref` method, a `Self` in a signature, a property or an associated type can't be forwarded, and
    the impl says which."""
    import copy
    ifaces = {s.name: s for s in stmts if s.__class__ is IfaceDecl}
    for s in stmts:
        if s.__class__ is not ImplDecl or s.proxy is None:
            continue
        ln = s.line
        if s.iface.__class__ is TName and s.iface.path[-1] not in ifaces:       # a built-in interface (`Show`, ...) has its declaration in the checker
            from .check import Checker
            if s.iface.path[-1] in Checker.builtin_ifaces(Checker(())):
                ifaces[s.iface.path[-1]] = Checker.builtin_ifaces(Checker(()))[s.iface.path[-1]]

        def fail(msg):
            raise MoxieSyntaxError(msg, ln, 0, file)
        iname = s.iface.path[-1] if s.iface.__class__ is TName else None
        decl = ifaces.get(iname)
        if decl is None and s.iface.__class__ is TName:
            decl = imported_interfaces(stmts, file).get(".".join(s.iface.path))
        if decl is None:
            fail(f"`proxy` needs the declaration of `{iname}` in this file to know which methods to forward; "
                 "write the forwarding methods by hand if it is not declared in an imported package")
        sub = {}
        args = s.iface.groups[0] if s.iface.groups else []
        if len(args) != len(decl.tparams or []):
            fail(f"`{iname}` takes {len(decl.tparams or [])} type argument(s), but this `proxy` names {len(args)}")
        for tp, a in zip(decl.tparams or [], args):
            sub[tp.name] = a

        def subst(t):
            if t is None:
                return None
            if t.__class__ is TName:
                if len(t.path) == 1 and not t.groups and t.path[0] in sub:
                    return copy.deepcopy(sub[t.path[0]])
                return TName(list(t.path), [[subst(x) for x in g] for g in (t.groups or [])])
            return copy.deepcopy(t)

        def mentions_self(t):
            if t is None:
                return False
            if t.__class__ is TName:
                return t.path == ["Self"] or any(mentions_self(x) for g in (t.groups or []) for x in g)
            return "Self" in repr(t)
        tdecl = next((x for x in stmts if x.__class__ is TupleDecl and s.target.__class__ is TName and x.name == s.target.path[-1]), None)
        if tdecl is not None:
            fld = next((f for f in tdecl.fields or [] if f.name == s.proxy), None)
            if fld is None:
                fail(f"`proxy({s.proxy})`: `{tdecl.name}` has no field `{s.proxy}`"
                     + (f"; its fields are {', '.join('`' + f.name + '`' for f in tdecl.fields or [])}" if tdecl.fields else ""))
            ft = fld.type
            fname = ft.path[-1] if ft.__class__ is TName and len(ft.path) == 1 else None
            local = fname is not None and any(x.__class__ in (TupleDecl, EnumDecl) and x.name == fname for x in stmts)
            if local and fname != iname and not any(x.__class__ is ImplDecl and x.iface.__class__ is TName and x.iface.path[-1] == iname
                                                    and x.target.__class__ is TName and x.target.path[-1] == fname for x in stmts):
                fail(f"`proxy({s.proxy})`: the field is a `{fname}`, which has no `impl {iname} for {fname}` in this file, so there is nothing to forward to")
        have = {m.name for m in s.members if m.__class__ is FnDecl}
        if decl.embeds:
            fail(f"`proxy` can't forward `{iname}`: it embeds other interfaces ({', '.join(str(getattr(e, 'path', e)) for e in decl.embeds)}); proxy each one in its own impl")
        for m in decl.members:
            if m.__class__ is not FnDecl:
                fail(f"`proxy` can't forward `{iname}`: it has a property or an associated type, which is not a method; write the impl by hand")
            if m.name in have:
                continue
            flags = m.flags or set()
            if "static" in flags:
                fail(f"`proxy` can't forward `{iname}.{m.name}`: it is a `static` member and there is no value to forward it to; write it in the impl")
            if "ref_self" in flags:
                fail(f"`proxy` can't forward `{iname}.{m.name}`: a method that changes its receiver can't be forwarded; write it in the impl")
            if m.tparams:
                fail(f"`proxy` can't forward `{iname}.{m.name}`: it is generic; write it in the impl")
            if any(p.name is None or p.mod or p.variadic or p.default is not None for p in m.params or []):
                fail(f"`proxy` can't forward `{iname}.{m.name}`: its parameters are not all plain names; write it in the impl")
            if mentions_self(m.ret) or any(mentions_self(p.type) for p in m.params or []):
                fail(f"`proxy` can't forward `{iname}.{m.name}`: `Self` in its signature would be the held value's type, not this type; write it in the impl")
            names = ", ".join(p.name for p in m.params or [] if p.name != "self")      # an explicit `self` is the receiver, not an argument
            src = f"fn {m.name}()\n  self.{s.proxy}.{m.name}({names})\n"
            fn = parse_program(src).stmts[0]
            fn.params = copy.deepcopy(m.params)
            for p in fn.params:
                p.type = subst(p.type)
            fn.ret = subst(m.ret)
            fn.flags = set(fn.flags or ()) | (set(flags) - {"static"}) | {"generated"}
            fn.line = ln
            s.members.append(fn)
        s.bodyless = False
    return stmts


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


def apply_refined_aliases(prog, file=None):
    """A parameter declared with a refined alias (`type Pos = Int where self > 0`) gets the alias's condition as its own
    `where`, `self` replaced by the parameter's name, so the call-site proof and the run-time `requires` treat it like a written one."""
    import copy
    import re
    ref = {}

    def find(n):
        if isinstance(n, AliasDecl) and n.where is not None and not n.tparams:
            ref[n.name] = n
        elif isinstance(n, list):
            for x in n:
                find(x)
        elif hasattr(n, "_fields"):
            for f in n._fields:
                find(getattr(n, f, None))

    def subst(e, nm):
        if isinstance(e, Name) and e.name == "self":
            return Name(nm, line=e.line)
        if isinstance(e, list):
            return [subst(x, nm) for x in e]
        if isinstance(e, tuple):
            return tuple(subst(x, nm) for x in e)
        if hasattr(e, "_fields"):
            c = copy.copy(e)
            for f in e._fields:
                setattr(c, f, subst(getattr(e, f), nm))
            return c
        return e

    def elem_alias(t):
        """`List[Pos]`, `Array[Pos][N]`, `Set[Pos]`, `Dict[K, Pos]`: the refined alias of the elements (or values), else None."""
        if t.__class__ is not TName or len(t.path) != 1 or t.path[0] not in ("List", "Array", "Set", "Dict") or not t.groups:
            return None
        g = t.groups[0]
        if not isinstance(g, list) or not g:
            return None
        e = g[-1] if t.path[0] == "Dict" else g[0]
        if e.__class__ is TName and not e.groups and ".".join(e.path) in ref:
            return ref[".".join(e.path)], t.path[0]
        return None

    def all_cond(a, kind, nm, line):
        """`every element of nm satisfies the alias's condition`, as a call of `all`, checked when the program runs (nothing about a
        whole collection can be proved at compile time)."""
        item = "item"
        lam = Lambda([Param(None, item, None, None, None, False, None, None, line=line)], subst(a.where, item), None, None, None, line=line)
        src = nm if kind != "Dict" else f"{nm}.values()"
        target = Name(nm, line=line) if kind != "Dict" else Call(Field(Name(nm, line=line), "values", line=line), [], None, line=line)
        cond = Call(Name("all", line=line), [Arg(None, lam, None, line=line), Arg(None, target, None, line=line)], None, line=line)
        text = f"all(({item}) -> {re.sub(r'self', item, a.wtext or '')}, {src})"
        return cond, text

    def walk(n):
        if isinstance(n, FnDecl):
            extra = []
            for prm in n.params or []:
                t = prm.type
                if prm.name and prm.name != "self" and t.__class__ is TName and not t.groups and ".".join(t.path) in ref:
                    a = ref[".".join(t.path)]
                    cond = acond = subst(a.where, prm.name)
                    text = atext = re.sub(r"\bself\b", prm.name, a.wtext or "")
                    if prm.where is not None:
                        cond = AndE(prm.where, cond, line=prm.line)
                        text = f"{prm.wtext} and {text}"
                    prm.where, prm.wtext = cond, text
                    if n.body is not None:
                        extra.append(("requires", acond, prm.line, atext))
            for prm in n.params or []:
                ea = elem_alias(prm.type) if prm.name and prm.name != "self" else None
                if ea is not None and n.body is not None:
                    cond, text = all_cond(ea[0], ea[1], prm.name, prm.line)      # a run-time `requires`: no `where`, so no compile-time proof is asked for
                    extra.append(("requires", cond, prm.line, text))
            if extra:
                n.contracts = extra + list(n.contracts or [])
            ea = elem_alias(n.ret)
            if ea is not None and n.body is not None:
                cond, text = all_cond(ea[0], ea[1], "result", n.line)
                n.contracts = list(n.contracts or []) + [("ensures", cond, n.line, text)]
            rt = n.ret
            if rt.__class__ is TName and not rt.groups and ".".join(rt.path) in ref and n.body is not None:
                a = ref[".".join(rt.path)]                       # a refined result: checked on the way out, as an `ensures` on `result`
                n.contracts = list(n.contracts or []) + [("ensures", subst(a.where, "result"), n.line, re.sub(r"\bself\b", "result", a.wtext or ""))]
        if isinstance(n, TupleDecl):
            more = []
            for f in n.fields or []:
                t = f.type
                if f.name and t.__class__ is TName and not t.groups and ".".join(t.path) in ref:
                    a = ref[".".join(t.path)]             # a refined field: an `invariant` on the field, checked at every construction
                    more.append(("invariant", subst(a.where, f.name), f.line if hasattr(f, "line") else n.line, re.sub(r"\bself\b", f.name, a.wtext or "")))
            for f in n.fields or []:
                ea = elem_alias(f.type) if f.name else None
                if ea is not None:
                    cond, text = all_cond(ea[0], ea[1], f.name, f.line if hasattr(f, "line") else n.line)
                    more.append(("invariant", cond, f.line if hasattr(f, "line") else n.line, text))
            if more:
                n.invariants = list(n.invariants or []) + more
        if isinstance(n, list):
            out = []
            for x in n:
                out.append(x)
                if x.__class__ is Assign and x.op == "=" and x.targets.__class__ is PBind and x.ann.__class__ is TName \
                        and not x.ann.groups and ".".join(x.ann.path) in ref:
                    a = ref[".".join(x.ann.path)]                # `x Pos = v`: the value entering a refined alias is checked right after the binding
                    nm = x.targets.name
                    out.append(Refine(nm, subst(a.where, nm), re.sub(r"\bself\b", nm, a.wtext or ""), a.name, line=x.line))
                elif x.__class__ is Assign and x.op == "=" and x.targets.__class__ is PBind and elem_alias(x.ann) is not None:
                    ea = elem_alias(x.ann)                # `xs List[Pos] = ...`: every element is checked right after the binding, when the program runs
                    cond, text = all_cond(ea[0], ea[1], x.targets.name, x.line)
                    out.append(Refine(x.targets.name, cond, text, "", line=x.line))
            n[:] = out
            for x in list(n):
                walk(x)
        elif isinstance(n, tuple):
            for x in n:
                walk(x)
        elif hasattr(n, "_fields"):
            for f in n._fields:
                walk(getattr(n, f, None))
    find(prog)
    ref.update(imported_refined(getattr(prog, "stmts", None) or [], file))
    if ref:
        walk(prog)
    return prog


def imported_refined(stmts, file):
    """The refined aliases of the packages this module imports: `import pkg` gives `pkg.Pos`, `from pkg import Pos` gives `Pos`.  Only an
    alias whose condition uses `self` and literals is taken, since a name from the other package would not mean the same here."""
    import os
    from .packages import package_files, parse_package
    from .stdpkg import find_std
    out = {}
    for s in stmts:
        if s.__class__ is not ImportDecl:
            continue
        try:
            base = SEARCH_DIR[0] if SEARCH_DIR[0] is not None else (os.path.dirname(os.path.abspath(file)) if file and not file.startswith("<") else None)
            found = package_files(base, s.pkg)
            paths = found[0] if found is not None else ([find_std(s.pkg)] if find_std(s.pkg) else [])
            if not paths or any(p in _DELEGATE_BUSY for p in paths):
                continue
            _DELEGATE_BUSY.update(paths)
            try:
                pk = parse_package(paths)[1].stmts
            finally:
                _DELEGATE_BUSY.difference_update(paths)
        except Exception:
            continue
        alias = s.alias or s.pkg[-1]

        def plain(e):
            if isinstance(e, Name):
                return e.name == "self"
            if isinstance(e, (list, tuple)):
                return all(plain(x) for x in e)
            if hasattr(e, "_fields"):
                return all(plain(getattr(e, f, None)) for f in e._fields)
            return True
        for x in pk:
            if x.__class__ is AliasDecl and x.where is not None and not x.tparams and x.vis == "export" and plain(x.where):
                if s.names is None:
                    out[f"{alias}.{x.name}"] = x
                elif x.name in s.names:
                    out[x.name] = x
    return out


def parse_program(src, file="<input>"):
    from . import pexpr
    pexpr.CAST_STYLE.pop(file, None)
    toks = tokenize(src, file)
    return apply_refined_aliases(Parser(toks, file).parse_module(), file)
