"""A small EBNF reader and Earley recognizer, used to check docs/grammar.ebnf against moxie's own lexer (tests/run_grammar.py).

Grammar syntax (one rule per `name : alternatives ;`, `#` starts a comment):
    'text'      a token whose value is `text` (an operator, or a keyword written as a name)
    NAME INT ...  a token of that kind (NAME INT FLOAT STR CHAR DEC DUR BYTES SQL HASH BTICK NL INDENT DEDENT EOF)
    ident       a NAME token that is not a reserved word (`%reserved a b c` lists them)
    rule        another rule
    ( ... )  [ ... ]  { ... }  +      grouping, optional, zero or more, postfix one or more
    |           alternative
The recognizer answers "does this token list belong to the start rule", which is all the cross-check needs.
"""
import re


class Grammar:
    def __init__(self, text):
        self.reserved = set()
        self.rules = {}
        self.order = []
        self._parse(text)
        self._compile()

    # ------------------------------------------------------------------ reading
    def _tokens(self, text):
        out = []
        for line in text.splitlines():
            line = re.sub(r"(?<!')#.*$", "", line) if "'#'" not in line else line
            m = re.match(r"\s*%reserved\s+(.*)", line)
            if m:
                self.reserved |= set(m.group(1).split())
                continue
            for t in re.findall(r"'(?:[^'\\]|\\.)+'|[A-Za-z_][A-Za-z_0-9]*|[:;|()\[\]{}+*?]", line):
                out.append(t)
        return out

    def _parse(self, text):
        toks = self._tokens(text)
        i = 0
        while i < len(toks):
            name = toks[i]
            assert toks[i + 1] == ":", f"grammar: expected ':' after {name}"
            i += 2
            j = i
            depth = 0
            while toks[j] != ";" or depth:
                if toks[j] in "([{":
                    depth += 1
                elif toks[j] in ")]}":
                    depth -= 1
                j += 1
            self.rules[name] = self._alts(toks[i:j])
            self.order.append(name)
            i = j + 1

    def _alts(self, toks):
        alts, cur, depth = [], [], 0
        for t in toks:
            if t == "|" and depth == 0:
                alts.append(cur)
                cur = []
                continue
            if t in "([{":
                depth += 1
            elif t in ")]}":
                depth -= 1
            cur.append(t)
        alts.append(cur)
        return [self._seq(a) for a in alts]

    def _seq(self, toks):
        out, i = [], 0
        while i < len(toks):
            t = toks[i]
            if t in "([{":
                close = {"(": ")", "[": "]", "{": "}"}[t]
                depth, j = 0, i
                while True:
                    if toks[j] in "([{":
                        depth += 1
                    elif toks[j] in ")]}":
                        depth -= 1
                    if depth == 0:
                        break
                    j += 1
                assert toks[j] == close, "grammar: unbalanced brackets"
                inner = ("alt", self._alts(toks[i + 1:j]))
                el = {"(": inner, "[": ("opt", inner), "{": ("star", inner)}[t]
                i = j + 1
            else:
                el = ("sym", t)
                i += 1
            while i < len(toks) and toks[i] in ("+", "*", "?"):
                el = {"+": ("plus", el), "*": ("star", el), "?": ("opt", el)}[toks[i]]
                i += 1
            out.append(el)
        return out

    # ------------------------------------------------------------------ to BNF
    def _compile(self):
        self.bnf = {}                 # nonterminal -> list of productions (list of symbols)
        self.n = 0
        for name in self.order:
            self.bnf[name] = [self._flat(s, name) for s in self.rules[name]]
        for name, prods in list(self.bnf.items()):
            for p in prods:
                for s in p:
                    if s[0] == "nt" and s[1] not in self.bnf:
                        raise ValueError(f"grammar: rule `{s[1]}` is used but not defined")

    def _fresh(self, hint):
        self.n += 1
        return f"{hint}#{self.n}"

    def _flat(self, seq, owner):
        out = []
        for el in seq:
            out.append(self._elem(el, owner))
        return out

    def _elem(self, el, owner):
        k = el[0]
        if k == "sym":
            t = el[1]
            if t.startswith("'"):
                return ("lit", re.sub(r"\\(.)", r"\1", t[1:-1]))
            if t == "ident":
                return ("ident",)
            if t.isupper() and t.replace("_", "").isalpha():
                return ("kind", t)
            return ("nt", t)
        if k == "alt":
            nt = self._fresh(owner)
            self.bnf[nt] = [self._flat(s, owner) for s in el[1]]
            return ("nt", nt)
        if k == "opt":
            nt = self._fresh(owner)
            self.bnf[nt] = [[], [self._elem(el[1], owner)]]
            return ("nt", nt)
        if k == "star":
            nt = self._fresh(owner)
            self.bnf[nt] = [[], [("nt", nt), self._elem(el[1], owner)]]
            return ("nt", nt)
        if k == "plus":
            nt = self._fresh(owner)
            one = self._elem(el[1], owner)
            self.bnf[nt] = [[one], [("nt", nt), one]]
            return ("nt", nt)
        raise ValueError(el)

    # ------------------------------------------------------------------ recognizing
    def _nullable(self):
        nul = set()
        changed = True
        while changed:
            changed = False
            for nt, prods in self.bnf.items():
                if nt in nul:
                    continue
                for p in prods:
                    if all(s[0] == "nt" and s[1] in nul for s in p):
                        nul.add(nt)
                        changed = True
                        break
        return nul

    def matches(self, sym, tok):
        k = sym[0]
        kind, val = tok
        if k == "lit":
            return val == sym[1] and kind in ("NAME", "OP")
        if k == "kind":
            return kind == sym[1]
        if k == "ident":
            return kind == "NAME" and val not in self.reserved
        return False

    def recognize(self, tokens, start="program"):
        """tokens: list of (kind, value).  Returns (True, n) or (False, furthest token index reached)."""
        nul = self._nullable()
        n = len(tokens)
        # states: (nt, prod index, dot, origin)
        chart = [dict() for _ in range(n + 1)]       # state -> True, kept in insertion order
        pending = [[] for _ in range(n + 1)]
        furthest = 0

        def add(i, st):
            if st not in chart[i]:
                chart[i][st] = True
                pending[i].append(st)

        for pi in range(len(self.bnf[start])):
            add(0, (start, pi, 0, 0))
        for i in range(n + 1):
            k = 0
            while k < len(pending[i]):
                st = pending[i][k]
                k += 1
                nt, pi, dot, org = st
                prod = self.bnf[nt][pi]
                if dot == len(prod):
                    for (nt2, pi2, dot2, org2) in list(chart[org]):
                        p2 = self.bnf[nt2][pi2]
                        if dot2 < len(p2) and p2[dot2] == ("nt", nt):
                            add(i, (nt2, pi2, dot2 + 1, org2))
                    continue
                sym = prod[dot]
                if sym[0] == "nt":
                    for pj in range(len(self.bnf[sym[1]])):
                        add(i, (sym[1], pj, 0, i))
                    if sym[1] in nul:
                        add(i, (nt, pi, dot + 1, org))
                elif i < n and self.matches(sym, tokens[i]):
                    add(i + 1, (nt, pi, dot + 1, org))
                    if i + 1 > furthest:
                        furthest = i + 1
        ok = any(st[0] == start and st[2] == len(self.bnf[start][st[1]]) and st[3] == 0 for st in chart[n])
        return (True, n) if ok else (False, furthest)
