"""moxie fmt: canonical layout for Moxie source (Spec section 1, indentation).

The formatter changes layout only: every block is indented 2 spaces per level, continuation lines keep their
offset from the statement they continue, multi-line strings, SQL bodies, and block comments move as a unit,
trailing spaces are removed, blank lines are collapsed (two at the top level, one inside a block), and the file
ends with one newline. Spacing inside a line is left alone. Before it returns, the result is lexed again and must
give the same tokens, and formatting it a second time must change nothing; otherwise `FmtError` is raised and
nothing is written."""
import os
import sys

from .lexer import Lexer, MoxieSyntaxError


class FmtError(Exception):
    pass


def _tokens(src, file):
    return [(t.kind, repr(t.val)) for t in Lexer(src, file).tokenize()]


def _once(src, file):
    src = src.replace("\r\n", "\n").replace("\r", "\n")
    lx = Lexer(src, file)
    lx.tokenize()
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
        if info is not None:
            if info["cont"]:
                new = lead + stmt_delta
            else:
                new = info["canon"]
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
                elif lead in stack:
                    new = 2 * stack.index(lead)
                else:
                    new = ni["canon"]
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
        res.append(text)
        k += 1
    return "\n".join(res) + "\n" if res else ""


def format_source(src, file="<input>"):
    try:
        a = _once(src, file)
        if _tokens(a, file) != _tokens(src, file):
            raise FmtError("the formatted text does not lex to the same tokens")
        if _once(a, file) != a:
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
