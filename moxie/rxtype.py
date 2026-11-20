"""The shape of a regex's captures, read from its source text at compile time (the `regex` package's `Matches("...", (a, b))` form).

`groups(src)` gives one `(name, kind, optional)` per capturing group, in order, where `kind` is Int, Float, Bool or String and `optional`
is true when the group might not take part in a match (it is under `?`/`*`/`{0,n}` or in one branch of a `|`).  It follows the same
grammar as moxie/std/regex.mxi and raises `RxError(message)` for a pattern that library would refuse.
"""


class RxError(Exception):
    pass


KINDS = ("String", "Int", "Float", "Bool")


def _err(msg, i):
    raise RxError(f"regex: {msg} at position {i}")


class _P:
    def __init__(self, s):
        self.s, self.i, self.gs = s, 0, []

    def peek(self, c, k=0):
        return self.i + k < len(self.s) and self.s[self.i + k] == c

    def alt(self):
        branches = [self.cat()]
        while self.peek("|"):
            self.i += 1
            branches.append(self.cat())
        idxs = [g for b in branches for g in b]
        if len(branches) > 1:
            for g in idxs:
                self.gs[g][2] = True
        return idxs

    def cat(self):
        out = []
        while self.i < len(self.s) and self.s[self.i] not in "|)":
            out += self.piece()
        return out

    def piece(self):
        idxs = self.atom()
        if self.i >= len(self.s):
            return idxs
        c = self.s[self.i]
        lo = None
        if c in "*+?":
            lo = 1 if c == "+" else 0
            self.i += 1
        elif c == "{":
            j = self.i + 1
            while j < len(self.s) and self.s[j].isdigit():
                j += 1
            if j == self.i + 1:
                _err("a repeat needs a number after `{`", self.i)
            lo = int(self.s[self.i + 1:j])
            if self.s[j:j + 1] == ",":
                k = j + 1
                while k < len(self.s) and self.s[k].isdigit():
                    k += 1
                hi = int(self.s[j + 1:k]) if k > j + 1 else -1
                j = k
            elif self.s[j:j + 1] == "}":
                hi = lo
            else:
                _err("expected `,` or `}` in a repeat", j)
            if self.s[j:j + 1] != "}":
                _err("missing `}` in a repeat", j)
            if 0 <= hi < lo:
                _err("the repeat's top is below its bottom", j)
            if lo > 255 or hi > 255:
                _err("a repeat count is at most 255", j)
            self.i = j + 1
        else:
            return idxs
        if self.peek("?"):
            self.i += 1
        if lo == 0:
            for g in idxs:
                self.gs[g][2] = True
        return idxs

    def atom(self):
        c = self.s[self.i]
        if c == "(":
            return self.group()
        if c == "[":
            return self.set_()
        if c == "\\":
            self.i += 1
            if self.i >= len(self.s):
                _err("the pattern ends with `\\`", self.i)
            e = self.s[self.i]
            self.i += 1
            if e.isdigit():
                _err("back-references are not supported: they need backtracking", self.i - 2)
            if e.isalpha() and e not in "dDwWsSbBAznrtfv":
                _err(f"unknown escape `\\{e}`", self.i - 2)
            return []
        if c in "*+?":
            _err("nothing to repeat", self.i)
        self.i += 1
        return []

    def set_(self):
        self.i += 1
        if self.peek("^"):
            self.i += 1
        first = True
        while True:
            if self.i >= len(self.s):
                _err("missing `]`", self.i)
            c = self.s[self.i]
            if c == "]" and not first:
                self.i += 1
                return []
            first = False
            if c == "\\":
                self.i += 1
                if self.i >= len(self.s):
                    _err("the pattern ends with `\\`", self.i)
                e = self.s[self.i]
                if e in "DWS":
                    _err(f"`\\{e}` is not allowed inside `[...]`; write `[^...]`", self.i - 1)
                if e.isalpha() and e not in "dwsnrtfv":
                    _err(f"unknown escape `\\{e}`", self.i - 1)
            self.i += 1

    def group(self):
        self.i += 1
        name, kind, capturing = "", "String", True
        if self.peek("?"):
            if self.peek(":", 1):
                capturing, self.i = False, self.i + 2
            elif not self.peek("<", 1):
                _err("look-around and flags are not supported", self.i)
            elif self.peek("=", 2) or self.peek("!", 2):
                _err("look-behind is not supported", self.i)
            else:
                j = self.i + 2
                while j < len(self.s) and self.s[j] not in ">:":
                    j += 1
                if j >= len(self.s):
                    _err("a group name needs a closing `>`", self.i)
                name = self.s[self.i + 2:j]
                if not name or not all(ch.isalnum() and ch.isascii() or ch == "_" for ch in name):
                    _err("a group name is letters, digits and `_`", self.i + 2)
                if self.s[j] == ">":
                    self.i = j + 1
                else:
                    k = j + 1
                    while k < len(self.s) and self.s[k] != ">":
                        k += 1
                    if k >= len(self.s):
                        _err("a group name needs a closing `>`", self.i)
                    kind = self.s[j + 1:k]
                    if kind not in KINDS:
                        _err(f"a group type is Int, Float, Bool or String, not `{kind}`", j + 1)
                    self.i = k + 1
        mine = None
        if capturing and name and any(g[0] == name for g in self.gs):
            _err(f"the group name `{name}` is used twice", self.i)
        if capturing:
            self.gs.append([name, kind, False])
            mine = len(self.gs) - 1
        inner = self.alt()
        if not self.peek(")"):
            _err("missing `)`", self.i)
        self.i += 1
        return ([mine] if mine is not None else []) + inner


def groups(src):
    p = _P(src)
    p.alt()
    if p.i < len(src):
        _err("unmatched `)`", p.i)
    return [tuple(g) for g in p.gs]
