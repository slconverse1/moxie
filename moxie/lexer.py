"""Moxie lexer: turns source text into a token stream with NEWLINE / INDENT / DEDENT.

The rules implemented here come from Spec section 1:
  * a line ending in ':' or '->' (outside brackets) opens a block,
  * a statement continues after a dangling operator or comma, inside brackets,
    when the next line starts with '|>', '|>>', another operator or '.name',
    or after a trailing backslash,
  * comments are // and /* */.
"""
import re
import unicodedata


class MoxieSyntaxError(Exception):
    def __init__(self, msg, line=0, col=0, file="<input>"):
        super().__init__(msg)
        self.msg = msg
        self.line = line
        self.col = col
        self.file = file

    def __str__(self):
        return f"{self.file}:{self.line}:{self.col}: syntax error: {self.msg}"


class Tok:
    __slots__ = ("kind", "val", "line", "col", "bol", "sp", "extra")

    def __init__(self, kind, val, line, col, sp=False):
        self.kind = kind      # NAME INT FLOAT DEC STR CHAR BYTES BCHAR HASH DUR OP BTICK NL INDENT DEDENT EOF SQL
        self.val = val
        self.line = line
        self.col = col
        self.bol = False      # first token of a physical line that continues the previous statement
        self.sp = sp          # whitespace before the token
        self.extra = None

    def __repr__(self):
        return f"Tok({self.kind},{self.val!r}@{self.line})"


OPS = [
    "...", "..=", "|>>", "<$>", "<*>", ">>=", "<<=",
    "<~", "~>", "|>", "->", "==", "~=", "<=", ">=", "+=", "-=", "*=", "/=", "%=", "+%", "-%",
    "&=", "|=", "^=", "<<", ">>", "++", "--", "..",
    "+", "-", "*", "/", "%", "<", ">", "=", "&", "|", "^", "~", "(", ")", "[", "]",
    "{", "}", ",", ":", ".", "?", "@", ";", "!", "$", "\\",
]
OPS_BY_FIRST = {}
for _o in OPS:
    OPS_BY_FIRST.setdefault(_o[0], []).append(_o)
for _k in OPS_BY_FIRST:
    OPS_BY_FIRST[_k].sort(key=lambda s: -len(s))

DANGLING = {"+", "-", "*", "/", "%", "==", "~=", "<", ">", "<=", ">=", "=", "&", "|", "^",
            "<<", ">>", "|>", "|>>", "~>", "<~", "<$>", "<*>", "+=", "-=", "*=", "/=", "%=",
            ",", "and", "or", "not", "in", "is", "&=", "|=", "^="}
CONT_STARTERS = {"|>", "|>>", "~>", "<~", "<$>", "<*>"}

ESC_STR = {"n": "\n", "t": "\t", "\\": "\\", '"': '"', "$": "$"}
ESC_CHR = {"n": "\n", "t": "\t", "\\": "\\", "'": "'"}

SQL_HEAD = re.compile(r"\bsql\s*\(.*\)\s*:\s*(//.*)?$")


def is_id_start(c):
    return c == "_" or c.isalpha()


def is_id_char(c):
    return c == "_" or c.isalnum()


NUM_SUFFIX = re.compile(r"(i8|i16|i32|i64|u8|u16|u32|u64|f|d|ns|us|ms|s|m|h)(?![A-Za-z0-9_])")


class Lexer:
    def __init__(self, src, file="<input>"):
        self.src = src.replace("\r\n", "\n").replace("\r", "\n")
        self.file = file
        self.n = len(self.src)
        self.i = 0
        self.line = 1
        self.col0 = 0           # index of the start of the current line
        self.raw = []           # raw tokens including NL tokens
        self.comments = []      # the text of each comment in order, for the formatter's check
        self.spans = []         # (first, last) physical lines inside a multi-line token, for the formatter
        self.info = {}          # first physical line of a code line -> layout facts, for the formatter
        self.depth = 0

    def err(self, msg, line=None, col=None):
        raise MoxieSyntaxError(msg, line or self.line, col if col is not None else self.i - self.col0 + 1, self.file)

    # ------------------------------------------------------------------
    def tokenize(self):
        src, n = self.src, self.n
        line_tokens_start = 0
        at_bol = True
        indent = 0
        while self.i < n:
            c = src[self.i]
            if at_bol:
                # measure indentation
                j = self.i
                while j < n and src[j] == " ":
                    j += 1
                if j < n and src[j] == "\t":
                    self.err("tabs are not allowed in indentation")
                indent = j - self.i
                self.i = j
                at_bol = False
                # blank or comment-only line
                if self.i >= n:
                    break
                c = src[self.i]
                if c == "\n":
                    self.i += 1
                    self.line += 1
                    self.col0 = self.i
                    at_bol = True
                    continue
                if src.startswith("//", self.i):
                    self._skip_line_comment()
                    self.i += 1
                    self.line += 1
                    self.col0 = self.i
                    at_bol = True
                    continue
                if src.startswith("/*", self.i):
                    # block comment starting a line
                    save = (self.i, self.line, self.col0)
                    self._skip_block_comment()
                    # if only whitespace remains on the line, treat as blank
                    k = self.i
                    while k < n and src[k] in " ":
                        k += 1
                    if k >= n or src[k] == "\n":
                        self.i = k + 1 if k < n else k
                        self.line += 1
                        self.col0 = self.i
                        at_bol = True
                        continue
                    # code follows the comment; re-measure as same indent
                    indent_now = indent
                    # fall through to tokenizing the rest of the line
                    c = src[self.i]
                self.raw.append(Tok("BOL", indent, self.line, 1))
                if self._maybe_sql_line():
                    at_bol = True
                    continue
                c = src[self.i]
            if c == "\n":
                self.i += 1
                self.raw.append(Tok("NL", None, self.line, self.i - self.col0))
                self.line += 1
                self.col0 = self.i
                at_bol = True
                continue
            if c == " ":
                self.i += 1
                continue
            if c == "\\" and self.i + 1 < n and src[self.i + 1] == "\n":
                self.i += 2
                self.line += 1
                self.col0 = self.i
                # continuation: the next physical line is not a new logical line
                while self.i < n and src[self.i] == " ":
                    self.i += 1
                continue
            if src.startswith("//", self.i):
                self._skip_line_comment()
                continue
            if src.startswith("/*", self.i):
                self._skip_block_comment()
                continue
            self._token()
            if self.raw and self.raw[-1].kind in ("STR", "CHAR") and False:
                pass
        self.raw.append(Tok("NL", None, self.line, 1))
        return self._structure()

    # ------------------------------------------------------------------
    def _skip_line_comment(self):
        s = self.i
        while self.i < self.n and self.src[self.i] != "\n":
            self.i += 1
        self.comments.append(self.src[s:self.i].rstrip())

    def _skip_block_comment(self):
        start_line = self.line
        first = self.i
        self.i += 2
        depth = 1
        while self.i < self.n and depth:
            if self.src.startswith("/*", self.i):
                depth += 1
                self.i += 2
            elif self.src.startswith("*/", self.i):
                depth -= 1
                self.i += 2
            else:
                if self.src[self.i] == "\n":
                    self.line += 1
                    self.col0 = self.i + 1
                self.i += 1
        if depth:
            self.err("unterminated /* comment", start_line)
        self.comments.append("\n".join(x.strip() for x in self.src[first:self.i].split("\n")))
        if self.line > start_line:
            self.spans.append((start_line + 1, self.line))

    def _maybe_sql_line(self):
        """If this physical line is `... sql(conn):` capture the indented lines that follow as raw text."""
        src = self.src
        eol = src.find("\n", self.i)
        if eol < 0:
            eol = self.n
        text = src[self.i:eol]
        if "sql" not in text or not SQL_HEAD.search(text):
            return False
        # tokenize the head line normally, then add a SQL token
        head_indent = self.raw[-1].val
        self._tokenize_until(eol)
        # now at eol; gather raw lines deeper than head_indent
        pos = eol + 1 if eol < self.n else self.n
        lines = []
        line_no = self.line + 1
        first_line = line_no
        while pos < self.n:
            e = src.find("\n", pos)
            if e < 0:
                e = self.n
            ln = src[pos:e]
            if ln.strip() == "":
                lines.append("")
                pos = e + 1
                line_no += 1
                continue
            k = len(ln) - len(ln.lstrip(" "))
            if k <= head_indent:
                break
            lines.append(ln)
            pos = e + 1
            line_no += 1
        # trim trailing blank lines
        while lines and lines[-1] == "":
            lines.pop()
            pos_back = True
        # recompute pos to just after the last kept line
        consumed = len(lines)
        p = eol + 1 if eol < self.n else self.n
        for _ in range(consumed):
            e = src.find("\n", p)
            if e < 0:
                e = self.n
            p = e + 1
        self.i = min(p, self.n)
        if consumed:
            self.spans.append((first_line, first_line + consumed - 1))
        self.line = first_line + consumed
        self.col0 = self.i
        tk = Tok("SQL", "\n".join(lines), first_line, 1)
        self.raw.append(tk)
        self.raw.append(Tok("NL", None, self.line, 1))
        return True

    def _tokenize_until(self, stop):
        src = self.src
        while self.i < stop:
            c = src[self.i]
            if c == " ":
                self.i += 1
                continue
            if src.startswith("//", self.i):
                self.comments.append(src[self.i:stop].rstrip())
                self.i = stop
                break
            self._token()
        self.i = stop

    # ------------------------------------------------------------------
    def _token(self):
        src = self.src
        i = self.i
        c = src[i]
        sp = i > 0 and src[i - 1] in " \n"
        line = self.line
        col = i - self.col0 + 1
        def add(kind, val, extra=None):
            t = Tok(kind, val, line, col, sp)
            t.extra = extra
            self.raw.append(t)
            return t

        if c in "‘’“”":
            self.err("curly quote found; use a straight quote")
        if c.isdigit():
            return self._number(add)
        if is_id_start(c):
            # raw string / byte string prefixes
            if c == "r" and i + 1 < self.n and src[i + 1] in "\"#":
                if self._raw_string(add):
                    return
            if c == "b" and i + 1 < self.n and src[i + 1] in "\"'":
                return self._byte_literal(add)
            j = i + 1
            while j < self.n and is_id_char(src[j]):
                j += 1
            name = unicodedata.normalize("NFKC", src[i:j])
            self.i = j
            add("NAME", name)
            return
        if c == '"':
            return self._string(add)
        if c == "'":
            return self._char(add)
        if c == "#":
            j = i + 1
            while j < self.n and is_id_char(src[j]):
                j += 1
            if j == i + 1:
                self.err("stray '#'")
            self.i = j
            add("HASH", src[i + 1:j])
            return
        if c == "`":
            j = src.find("`", i + 1)
            if j < 0:
                self.err("unterminated backtick")
            self.i = j + 1
            add("BTICK", src[i + 1:j])
            return
        # operators
        for op in OPS_BY_FIRST.get(c, ()):
            if src.startswith(op, i):
                # '..' after an int literal is handled in _number
                self.i = i + len(op)
                if op in "([{":
                    self.depth += 1
                elif op in ")]}":
                    self.depth -= 1
                add("OP", op)
                return
        self.err(f"unexpected character {c!r}")

    # ------------------------------------------------------------------
    def _number(self, add):
        src = self.src
        i = self.i
        m = None
        if src[i] == "0" and i + 1 < self.n and src[i + 1] in "xXoObB":
            base = {"x": 16, "o": 8, "b": 2}[src[i + 1].lower()]
            j = i + 2
            digs = "0123456789abcdefABCDEF" if base == 16 else ("01234567" if base == 8 else "01")
            k = j
            while k < self.n and (src[k] in digs or src[k] == "_"):
                k += 1
            body = src[j:k]
            if not body or body.startswith("_") or body.endswith("_") or "__" in body:
                self.err("bad number literal")
            val = int(body.replace("_", ""), base)
            self.i = k
            suf = NUM_SUFFIX.match(src, k) if base != 16 else None
            if base == 16 and k < self.n and src[k] in "iu":
                suf = NUM_SUFFIX.match(src, k)
            if suf:
                self.i = suf.end()
                return add("INT", val, suf.group(1))
            return add("INT", val, None)
        j = i
        while j < self.n and (src[j].isdigit() or (src[j] == "_" and j + 1 < self.n and src[j + 1].isdigit() and src[j - 1].isdigit())):
            j += 1
        text = src[i:j]
        is_float = False
        if j + 1 < self.n and src[j] == "." and src[j + 1].isdigit():
            is_float = True
            j += 1
            while j < self.n and (src[j].isdigit() or (src[j] == "_" and j + 1 < self.n and src[j + 1].isdigit())):
                j += 1
            text = src[i:j]
        # exponent
        if j < self.n and src[j] in "eE":
            k = j + 1
            if k < self.n and src[k] in "+-":
                k += 1
            if k < self.n and src[k].isdigit():
                while k < self.n and src[k].isdigit():
                    k += 1
                is_float = True
                j = k
                text = src[i:j]
        self.i = j
        suf = NUM_SUFFIX.match(src, j)
        suffix = None
        if suf:
            suffix = suf.group(1)
            self.i = suf.end()
        clean = text.replace("_", "")
        if suffix in ("ns", "us", "ms", "s", "m", "h"):
            val = float(clean) if is_float else int(clean)
            return add("DUR", val, suffix)
        if suffix == "d":
            return add("DEC", clean, None)
        if suffix == "f":
            return add("FLOAT", float(clean), "f")
        if is_float:
            return add("FLOAT", float(clean), None)
        return add("INT", int(clean), suffix)

    # ------------------------------------------------------------------
    def _find_string_end(self, start):
        """start is just after the opening quote. Returns index of the closing quote."""
        src = self.src
        i = start
        while i < self.n:
            c = src[i]
            if c == "\\":
                i += 2
                continue
            if c == "$" and i + 1 < self.n and src[i + 1] == "{":
                i = self._skip_interp(i + 2)
                continue
            if c == '"':
                return i
            if c == "\n":
                self.err("unterminated string", self.line)
            i += 1
        self.err("unterminated string")

    def _skip_interp(self, i):
        """i is just after '${'. Returns index just after the matching '}'."""
        src = self.src
        depth = 1
        while i < self.n:
            c = src[i]
            if c == '"':
                i = self._find_string_end(i + 1) + 1
                continue
            if c == "'":
                # char literal: 'x' or '\n'
                j = i + 1
                if j < self.n and src[j] == "\\":
                    j += 2
                    if j - 1 < self.n and src[j - 1] == "u":
                        j = src.find("}", j) + 1
                else:
                    j += 1
                if j < self.n and src[j] == "'":
                    i = j + 1
                    continue
                i += 1
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return i + 1
            elif c == "\n":
                self.err("unterminated interpolation")
            i += 1
        self.err("unterminated interpolation")

    def _string(self, add):
        src = self.src
        i = self.i
        if src.startswith('"""', i):
            return self._triple(add)
        end = self._find_string_end(i + 1)
        body = src[i + 1:end]
        line = self.line
        self.i = end + 1
        parts = self._parse_body(body, ESC_STR, True, line)
        add("STR", parts)

    def _triple(self, add):
        src = self.src
        i = self.i + 3
        eol = src.find("\n", i)
        if eol < 0 or src[i:eol].strip() != "":
            self.err('a triple-quoted string must end its opening line')
        start_line = self.line
        pos = eol + 1
        lines = []
        while True:
            if pos > self.n:
                self.err("unterminated triple-quoted string", start_line)
            e = src.find("\n", pos)
            if e < 0:
                e = self.n
            ln = src[pos:e]
            stripped = ln.lstrip(" ")
            if stripped.startswith('"""') and not stripped.startswith('\\"""'):
                margin = len(ln) - len(stripped)
                after = pos + margin + 3
                break
            lines.append(ln)
            if e >= self.n:
                self.err("unterminated triple-quoted string", start_line)
            pos = e + 1
        out = []
        for ln in lines:
            if ln.strip() == "":
                out.append("")
                continue
            lead = len(ln) - len(ln.lstrip(" "))
            if "\t" in ln[:lead] or ln[:1] == "\t":
                self.err("tabs in leading whitespace of a triple-quoted string")
            if lead < margin:
                self.err("a line is indented less than the closing \"\"\" of the string")
            out.append(ln[margin:])
        body = "\n".join(out)
        # count lines consumed
        consumed = body.count("\n") + len(lines) - body.count("\n")  # = len(lines)
        self.spans.append((start_line + 1, start_line + len(lines) + 1))
        self.line = start_line + len(lines) + 1
        self.i = after
        self.col0 = pos + margin + 3 - (margin + 3)
        parts = self._parse_body(body, ESC_STR, True, start_line, triple=True)
        add("STR", parts)

    def _raw_string(self, add):
        src = self.src
        i = self.i + 1
        hashes = 0
        while i < self.n and src[i] == "#":
            hashes += 1
            i += 1
        if i >= self.n or src[i] != '"':
            return False
        if src.startswith('"""', i):
            # raw triple
            self.i = i
            save = len(self.raw)
            self._triple_raw(add)
            return True
        close = '"' + "#" * hashes
        j = src.find(close, i + 1)
        if j < 0:
            self.err("unterminated raw string")
        text = src[i + 1:j]
        if "\n" in text:
            self.spans.append((self.line + 1, self.line + text.count("\n")))
        self.line += text.count("\n")
        self.i = j + len(close)
        add("STR", [text])
        return True

    def _triple_raw(self, add):
        src = self.src
        i = self.i + 3
        eol = src.find("\n", i)
        pos = eol + 1
        lines = []
        start_line = self.line
        while True:
            e = src.find("\n", pos)
            if e < 0:
                e = self.n
            ln = src[pos:e]
            stripped = ln.lstrip(" ")
            if stripped.startswith('"""'):
                margin = len(ln) - len(stripped)
                after = pos + margin + 3
                break
            lines.append(ln)
            if e >= self.n:
                self.err("unterminated raw string")
            pos = e + 1
        out = [ln[margin:] if ln.strip() else "" for ln in lines]
        self.spans.append((start_line + 1, start_line + len(lines) + 1))
        self.line = start_line + len(lines) + 1
        self.i = after
        add("STR", ["\n".join(out)])

    def _byte_literal(self, add):
        src = self.src
        i = self.i + 1
        q = src[i]
        j = i + 1
        buf = []
        while j < self.n and src[j] != q:
            ch = src[j]
            if ch == "\\":
                nx = src[j + 1]
                if nx == "x":
                    buf.append(int(src[j + 2:j + 4], 16))
                    j += 4
                    continue
                m = {"n": 10, "t": 9, "\\": 92, '"': 34, "'": 39}
                if nx not in m:
                    self.err(f"bad byte escape \\{nx}")
                buf.append(m[nx])
                j += 2
                continue
            if ord(ch) > 127:
                self.err("a non-ASCII character in a byte literal")
            if ch == "\n":
                self.err("unterminated byte literal")
            buf.append(ord(ch))
            j += 1
        if j >= self.n:
            self.err("unterminated byte literal")
        self.i = j + 1
        if q == "'":
            if len(buf) != 1:
                self.err("a byte literal holds exactly one byte")
            add("BCHAR", buf[0])
        else:
            add("BYTES", bytes(buf))

    def _char(self, add):
        src = self.src
        i = self.i + 1
        if i >= self.n:
            self.err("unterminated char literal")
        if src[i] == "\\":
            nx = src[i + 1]
            if nx == "u" and src[i + 2] == "{":
                e = src.find("}", i)
                ch = chr(int(src[i + 3:e], 16))
                j = e + 1
            elif nx in ESC_CHR:
                ch = ESC_CHR[nx]
                j = i + 2
            else:
                self.err(f"bad escape \\{nx}")
        else:
            ch = src[i]
            j = i + 1
        if j >= self.n or src[j] != "'":
            self.err("a Char holds exactly one Unicode scalar")
        self.i = j + 1
        add("CHAR", ch)

    def _parse_body(self, body, esc, interp, line, triple=False):
        """Split a string body into literal text and interpolation parts."""
        parts = []
        buf = []
        i = 0
        n = len(body)
        while i < n:
            c = body[i]
            if c == "\\":
                if i + 1 >= n:
                    self.err("bad escape at end of string", line)
                nx = body[i + 1]
                if nx == "u" and i + 2 < n and body[i + 2] == "{":
                    e = body.find("}", i)
                    buf.append(chr(int(body[i + 3:e], 16)))
                    i = e + 1
                    continue
                if nx in esc:
                    buf.append(esc[nx])
                    i += 2
                    continue
                if triple and nx == '"':
                    buf.append('"')
                    i += 2
                    continue
                self.err(f"unknown escape \\{nx}", line)
            if c == "$" and interp:
                if i + 1 < n and body[i + 1] == "{":
                    # find matching brace honoring nested strings
                    j = self._match_interp(body, i + 2, line)
                    inner = body[i + 2:j]
                    expr, spec = self._split_spec(inner)
                    if buf:
                        parts.append("".join(buf))
                        buf = []
                    parts.append(("e", expr, spec, line))
                    i = j + 1
                    continue
                if i + 1 < n and is_id_start(body[i + 1]):
                    j = i + 1
                    while j < n and is_id_char(body[j]):
                        j += 1
                    while j + 1 < n and body[j] == "." and is_id_start(body[j + 1]):
                        j += 1
                        while j < n and is_id_char(body[j]):
                            j += 1
                    if buf:
                        parts.append("".join(buf))
                        buf = []
                    parts.append(("e", body[i + 1:j], None, line))
                    i = j
                    continue
            buf.append(c)
            i += 1
        if buf or not parts:
            parts.append("".join(buf))
        return parts

    def _match_interp(self, body, i, line):
        depth = 1
        n = len(body)
        while i < n:
            c = body[i]
            if c == '"':
                # skip nested string
                i += 1
                while i < n and body[i] != '"':
                    if body[i] == "\\":
                        i += 1
                    elif body[i] == "$" and i + 1 < n and body[i + 1] == "{":
                        i = self._match_interp(body, i + 2, line)
                    i += 1
                i += 1
                continue
            if c == "'":
                j = i + 1
                if j < n and body[j] == "\\":
                    j += 2
                else:
                    j += 1
                if j < n and body[j] == "'":
                    i = j + 1
                    continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        self.err("unterminated interpolation", line)

    def _split_spec(self, inner):
        """Split '${expr:spec}' at the first top-level colon."""
        depth = 0
        i = 0
        n = len(inner)
        if re.match(r"\s*(if|when|fn|for|while|do)\b", inner):
            return inner, None
        while i < n:
            c = inner[i]
            if c == '"':
                i += 1
                while i < n and inner[i] != '"':
                    if inner[i] == "\\":
                        i += 1
                    i += 1
            elif c == "'":
                j = i + 1
                if j < n and inner[j] == "\\":
                    j += 2
                else:
                    j += 1
                if j < n and inner[j] == "'":
                    i = j
            elif c in "([{":
                depth += 1
            elif c in ")]}":
                depth -= 1
            elif c == ":" and depth == 0:
                return inner[:i], inner[i + 1:]
            i += 1
        return inner, None

    # ------------------------------------------------------------------
    # second pass: logical lines, NEWLINE / INDENT / DEDENT
    # ------------------------------------------------------------------
    def _structure(self):
        raw = self.raw
        out = []
        stack = [0]
        depth = 0
        stmt_indent = 0
        prev_last = None       # last token of the current logical line
        prev_toks = None       # all tokens of the previous physical line (a `property` header may be followed by accessors)
        prev_opens_block = False
        have_line = False
        # split raw into physical lines
        lines = []
        cur = None
        pending_join = False
        for t in raw:
            if t.kind == "BOL":
                cur = {"indent": t.val, "toks": [], "join": pending_join, "line": t.line}
                pending_join = False
                lines.append(cur)
            elif t.kind == "NL":
                cur = None
            else:
                if cur is None:
                    cur = lines[-1]
                cur["toks"].append(t)
        for L in lines:
            toks = L["toks"]
            if not toks:
                continue
            first = toks[0]
            was_open_depth = depth
            snap = (list(stack), depth)
            # compute continuation
            is_cont = False
            if have_line:
                if depth > 0:
                    is_cont = True
                elif prev_last is not None and (
                        (prev_last.kind == "OP" and prev_last.val in DANGLING)
                        or (prev_last.kind == "NAME" and prev_last.val in ("and", "or", "not", "in", "is"))):
                    is_cont = True
                elif first.kind == "OP" and first.val in CONT_STARTERS:
                    is_cont = True
                elif first.kind == "OP" and first.val == "." and len(toks) > 1 and toks[1].kind == "NAME" and not toks[1].sp:
                    is_cont = True
            if is_cont:
                first.bol = True
                if depth == 0 and first.kind == "OP" and (first.val in CONT_STARTERS or first.val == "."):
                    while len(stack) > 1 and stack[-1] > stmt_indent:
                        stack.pop()
                        out.append(Tok("DEDENT", None, first.line, 1))
            else:
                if have_line:
                    out.append(Tok("NL", None, first.line, 1))
                ind = L["indent"]
                top = stack[-1]
                if ind > top:
                    if not prev_opens_block and not (first.kind == "NAME" and first.val in ("requires", "ensures")
                                                     and len(toks) > 1) \
                            and not (first.kind == "NAME" and first.val in ("get", "set", "priv", "did_set")
                                     and prev_toks is not None
                                     and any(t.kind == "NAME" and t.val == "property" for t in prev_toks[:3])):
                        raise MoxieSyntaxError("unexpected indent", first.line, ind + 1, self.file)
                    stack.append(ind)
                    out.append(Tok("INDENT", None, first.line, 1))
                elif ind < top:
                    while stack[-1] > ind:
                        stack.pop()
                        out.append(Tok("DEDENT", None, first.line, 1))
                    if stack[-1] != ind:
                        raise MoxieSyntaxError("a dedent must match an indentation already on the stack",
                                               first.line, ind + 1, self.file)
                stmt_indent = ind
            self.info[L["line"]] = {"cont": is_cont, "canon": None if is_cont else 2 * (len(stack) - 1),
                                    "indent": L["indent"], "before": snap, "after": list(stack)}
            for t in toks:
                if t.kind == "OP":
                    if t.val in ("(", "[", "{"):
                        depth += 1
                    elif t.val in (")", "]", "}"):
                        depth -= 1
                out.append(t)
            have_line = True
            last = toks[-1]
            prev_last = last
            prev_toks = toks
            # does the logical line (so far) end with a block opener?
            prev_opens_block = (depth == 0 and (
                (last.kind == "OP" and last.val in (":", "->")) or last.kind == "SQL"))
            if last.kind == "SQL":
                prev_opens_block = False
        if have_line:
            out.append(Tok("NL", None, self.line, 1))
        while len(stack) > 1:
            stack.pop()
            out.append(Tok("DEDENT", None, self.line, 1))
        out.append(Tok("EOF", None, self.line, 1))
        return out


def tokenize(src, file="<input>"):
    return Lexer(src, file).tokenize()


if __name__ == "__main__":
    import sys
    for t in tokenize(open(sys.argv[1]).read()):
        print(t)
