"""moxie fmt: canonical layout for Moxie source (Spec section 1, indentation).

The formatter changes layout only: every block is indented 2 spaces per level, continuation lines keep their
offset from the statement they continue, multi-line strings, SQL bodies, and block comments move as a unit,
trailing spaces are removed, blank lines are collapsed (two at the top level, one inside a block), and the file
ends with one newline. Spacing inside a line is left alone. Before it returns, the result is lexed again and must
give the same tokens, and formatting it a second time must change nothing; otherwise `FmtError` is raised and
nothing is written."""
import os
import re
import sys

from .lexer import Lexer, MoxieSyntaxError
from .parser import parse_program


class FmtError(Exception):
    pass


_LINE_IN_PART = re.compile(r"(\('e', '(?:[^'\\]|\\.)*', (?:None|'[^']*')), \d+\)")


def _comments(src, file):
    lx = Lexer(src, file)
    lx.tokenize()
    return lx.comments


def _tokens(src, file):
    """Token kinds and values; the line numbers inside string interpolations are not part of the comparison."""
    return [(t.kind, _LINE_IN_PART.sub(r"\1)", repr(t.val)) if t.kind == "STR" else repr(t.val))
            for t in Lexer(src, file).tokenize()]


SPACED = {"==", "~=", "<=", ">=", "->", "|>", "|>>", "<$>", "<*>", "~>", "<~", "=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^="}
ARITH = {"+", "-", "*", "/", "%"}
KEYWORDS = {"return", "and", "or", "not", "in", "is", "if", "elif", "else", "when", "while", "for", "yield", "break",
            "continue", "move", "ref", "using", "assert", "match", "do", "then", "where", "as", "lazy", "run"}
DECL_WORDS = {"fn", "type", "impl", "interface", "enum", "test", "export", "internal", "pure", "parks", "prints", "impure",
              "foreign", "fiber"}


def _space_line(text, toks):
    """One space around binary operators and after commas; none before a comma. Only whitespace changes."""
    edits = {}

    def gap_before(p):
        j = p
        while j > 0 and text[j - 1] == " ":
            j -= 1
        if j == 0 or (j > 0 and text[j - 1] == "\t") or (p < len(text) and text[p] == "\t"):
            return None
        return j, p

    def gap_after(e):
        k = e
        while k < len(text) and text[k] == " ":
            k += 1
        if k >= len(text) or text[k] == "\t":
            return None
        return e, k

    def want(g, s):
        if g is not None and g[0] not in edits and text[g[0]:g[1]] != s:
            edits[g[0]] = (g[1], s)
    for i, t in enumerate(toks):
        if t.kind != "OP":
            continue
        p = t.col - 1
        e = p + len(t.val)
        if text[p:e] != t.val:
            return text                     # columns do not line up with the text; leave the line alone
        v = t.val
        if i > 0 and toks[i - 1].kind == "NAME" and toks[i - 1].val == "fn":
            if v == "(":
                want(gap_before(p), " ")    # an inline fiber is always written `run fn (`
            continue                        # fn +(other: Money) names an operator; leave it as written
        if False:
            pass
        elif v == ",":
            want(gap_before(p), "")
            g = gap_after(e)
            if g is not None:
                want(g, "" if text[g[1]] in ")]}" else " ")
        elif v in SPACED:
            want(gap_before(p), " ")
            want(gap_after(e), " ")
        elif v in ARITH and 0 < i < len(toks) - 1:
            pv = toks[i - 1]
            value_end = (pv.kind in ("INT", "FLOAT", "DEC", "STR", "CHAR", "DUR", "BYTES", "BCHAR")
                         or (pv.kind == "NAME" and pv.val not in KEYWORDS)
                         or (pv.kind == "OP" and pv.val in (")", "]", "}")))
            if value_end:
                want(gap_before(p), " ")
                want(gap_after(e), " ")
    for s in sorted(edits, reverse=True):
        e, r = edits[s]
        text = text[:s] + r + text[e:]
    return text


def _once(src, file, spacing=True):
    src = src.replace("\r\n", "\n").replace("\r", "\n")
    lx = Lexer(src, file)
    lx.tokenize()
    by_line = {}
    for t in lx.raw:
        if t.kind not in ("BOL", "NL", "SQL"):
            by_line.setdefault(t.line, []).append(t)
    lines = src.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    interior = set()
    for a, b in lx.spans:
        interior.update(range(a, b + 1))
    codes = sorted(lx.info)
    nxt = {}
    j = 0
    for ln in range(1, len(lines) + 2):
        while j < len(codes) and codes[j] < ln:
            j += 1
        nxt[ln] = codes[j] if j < len(codes) else None
    # phase 1: the new indentation of every code line, following the lexer's indent stack
    new_of, nm_before = {}, {}
    nm = {0: 0}
    d0 = 0
    prev_new = 0
    for ln in codes:
        info = lx.info[ln]
        lead = len(lines[ln - 1]) - len(lines[ln - 1].lstrip(" "))
        nm_before[ln] = dict(nm)
        if info["cont"]:
            new = lead + d0
        else:
            ind = info["indent"]
            new = nm[ind] if ind in nm else prev_new + 2
            d0 = new - lead
            nm = {o: (nm[o] if o in nm else new) for o in info["after"]}
        new_of[ln] = new
        prev_new = new
    out = []                      # (text, protected)
    stmt_delta = span_delta = 0
    for ln, text in enumerate(lines, 1):
        lead = len(text) - len(text.lstrip(" "))
        body = text.lstrip(" ")
        if ln in interior:
            n = lead + span_delta
            if body == "" :
                out.append((text, True))
                continue
            if n < 0:
                raise FmtError(f"line {ln}: cannot move this text without changing it")
            out.append((" " * n + body, True))
            continue
        if body.strip() == "":
            out.append(("", False))
            continue
        info = lx.info.get(ln)
        if info is not None and spacing and ln in by_line:
            text = _space_line(text, by_line[ln])
            body = text.lstrip(" ")
        if info is not None:
            new = new_of[ln]
            if not info["cont"]:
                stmt_delta = new - lead
            if new < 0:
                raise FmtError(f"line {ln}: cannot move this text without changing it")
            span_delta = new - lead
            out.append((" " * new + body.rstrip(), False))
            continue
        # a comment-only line, or a backslash continuation
        if body.startswith("//") or body.startswith("/*"):
            nx = nxt.get(ln)
            if nx is None:
                new = 0 if lead == 0 else lead
            else:
                ni = lx.info[nx]
                stack, depth = ni["before"]
                if depth > 0 or ni["cont"]:
                    new = lead + stmt_delta
                elif lead in nm_before[nx]:
                    new = nm_before[nx][lead]
                else:
                    new = new_of[nx]
            new = max(new, 0)
            span_delta = new - lead
            out.append((" " * new + body.rstrip(), False))
        else:
            new = lead + stmt_delta
            if new < 0:
                raise FmtError(f"line {ln}: cannot move this text without changing it")
            span_delta = new - lead
            out.append((" " * new + body.rstrip(), False))
    # blank lines: none at the start or end, at most two before a top-level line, one before an indented one
    res = []
    prot_idx = set()
    k = 0
    m = len(out)
    while k < m:
        text, prot = out[k]
        if text == "" and not prot:
            e = k
            while e < m and out[e][0] == "" and not out[e][1]:
                e += 1
            if res and e < m:
                nxt_text = out[e][0]
                limit = 2 if not nxt_text.startswith(" ") else 1
                res.extend([""] * min(e - k, limit))
            k = e
            continue
        if prot:
            prot_idx.add(len(res))
        res.append(text)
        k += 1
    if spacing:
        fin = []
        for k, text in enumerate(res):
            word = text.split(" ", 1)[0].split("(", 1)[0] if text else ""
            if (word in DECL_WORDS and not text.startswith(" ") and fin and fin[-1] != ""
                    and not fin[-1].lstrip().startswith(("//", "/*", "#")) and (fin[-1].startswith(" ") or (k + 1 < len(res) and res[k + 1].startswith(" ")))
                    and k not in prot_idx):
                fin.append("")
            fin.append(text)
        res = fin
    return "\n".join(res) + "\n" if res else ""


WIDTH = 80
_DECL = re.compile(r"\s*((export|internal|pure|parks|prints|impure|inline|static|tailrec)\s+)*fn\b")
OPENS, CLOSES = "([{", ")]}"


def _break(text, marks, indent):
    """Lines for `text` (whose brackets and commas are `marks`, (index, char) pairs): the text itself when it fits
    or cannot be made shorter, else the outermost bracket group that reaches past the width opened with one item
    to a line, each item and the closing line broken again if they are still too long."""
    if len(text) <= WIDTH:
        return [text]
    stack, groups = [], []
    for i, ch in marks:
        if ch in OPENS:
            stack.append(i)
        elif ch in CLOSES and stack:
            o = stack.pop()
            if not stack:
                groups.append((o, i))
    groups = [(o, c) for o, c in groups if text[o + 1:c].strip()]
    if not groups:
        return [text]
    hit = [g for g in groups if g[0] < WIDTH <= g[1]]
    before = [g for g in groups if g[0] < WIDTH]
    if _DECL.match(text):
        o, c = groups[0]                        # a declaration breaks its parameter list first
    else:
        o, c = (hit or before or groups)[-1 if not hit else 0]
    depth, cuts = 0, [o]
    for i, ch in marks:
        if i <= o or i >= c:
            continue
        if ch in OPENS:
            depth += 1
        elif ch in CLOSES:
            depth -= 1
        elif ch == "," and depth == 0:
            cuts.append(i)
    cuts.append(c)
    pieces = []                                     # (start, end, trailing comma) in the original text
    for a, b in zip(cuts, cuts[1:]):
        pieces.append((a + 1, b, b < c))
    last = pieces[-1]
    if text[last[0]:last[1]].strip() == "" and len(pieces) > 1:       # an existing trailing comma stays
        pieces.pop()
        pieces[-1] = (pieces[-1][0], pieces[-1][1], True)
    head = text[:o + 1].rstrip()
    lines = _break(head, [(i, ch) for i, ch in marks if i <= o], indent)
    pad = " " * (indent + 2)
    for a, b, comma in pieces:
        raw = text[a:b]
        lead = len(raw) - len(raw.lstrip())
        item = pad + raw.strip() + ("," if comma else "")
        sub = [(i - a - lead + len(pad), ch) for i, ch in marks if a + lead <= i < b]
        lines.extend(_break(item, sub, indent + 2))
    tail = " " * indent + text[c:]
    sub = [(i - c + indent, ch) for i, ch in marks if i >= c]
    lines.extend(_break(tail, sub, indent))
    if max(len(x) for x in lines) >= len(text):
        return [text]
    return lines


def _wrap(src, file):
    """Break the lines that are longer than WIDTH (one bracket group at a time, one item to a line)."""
    lx = Lexer(src, file)
    lx.tokenize()
    marks = {}
    for t in lx.raw:
        if t.kind == "OP" and t.val in ("(", ")", "[", "]", "{", "}", ","):
            marks.setdefault(t.line, []).append((t.col - 1, t.val))
    interior = set()
    for a, b in lx.spans:
        interior.update(range(a, b + 1))
    out = []
    for ln, text in enumerate(src.split("\n"), 1):
        if (len(text) <= WIDTH or ln in interior or ln not in lx.info or ln not in marks or "//" in text or "/*" in text
                or text.rstrip().endswith("\\")):
            out.append(text)
            continue
        indent = len(text) - len(text.lstrip(" "))
        out.extend(_break(text.rstrip(), marks[ln], indent))
    return "\n".join(out)


def _ast(src, file):
    try:
        return repr(parse_program(src, file))
    except Exception:
        return None


def format_source(src, file="<input>"):
    try:
        use = True
        a = _once(src, file)
        before = _ast(src, file)
        if before is None or _ast(a, file) != before:
            use = False                      # spacing is applied only when the program is shown to be unchanged
            a = _once(src, file, spacing=False)
        a = _wrap(a, file)
        if before is not None and _ast(a, file) != before:
            raise FmtError("breaking long lines changed the program")
        if _tokens(a, file) != _tokens(src, file):
            raise FmtError("the formatted text does not lex to the same tokens")
        if _comments(a, file) != _comments(src, file):
            raise FmtError("the formatted text does not keep every comment")
        if _once(a, file, spacing=use) != a or _wrap(a, file) != a:
            raise FmtError("formatting is not stable on this file")
    except MoxieSyntaxError as e:
        raise FmtError(str(e))
    return a


def _files(args):
    for a in args:
        if os.path.isdir(a):
            for root, dirs, names in os.walk(a):
                dirs[:] = sorted(d for d in dirs if not d.startswith("."))
                for n in sorted(names):
                    if n.endswith((".mxi", ".mx")):
                        yield os.path.join(root, n)
        else:
            yield a


def fmt_main(argv, out=sys.stdout, err=sys.stderr):
    check = "--check" in argv
    to_stdout = "--stdout" in argv
    paths = [a for a in argv if not a.startswith("--")]
    if not paths:
        err.write("usage: moxie fmt [--check] [--stdout] FILE-or-DIR...\n")
        return 2
    changed, failed = [], 0
    for path in _files(paths):
        try:
            src = open(path, encoding="utf-8").read()
        except OSError as e:
            err.write(f"moxie: cannot read {path}: {e.strerror}\n")
            failed += 1
            continue
        try:
            new = format_source(src, os.path.basename(path))
        except FmtError as e:
            err.write(f"{path}: not formatted: {e}\n")
            failed += 1
            continue
        if to_stdout:
            out.write(new)
            continue
        if new != src.replace("\r\n", "\n").replace("\r", "\n"):
            changed.append(path)
            if not check:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new)
    if not to_stdout:
        for p in changed:
            out.write(("would change " if check else "formatted ") + p + "\n")
    if failed:
        return 2
    return 1 if (check and changed) else 0
