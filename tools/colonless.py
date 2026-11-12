"""Rewrite moxie source from the colon syntax to the colonless one.

    python3 tools/colonless.py FILE...          rewrite .mxi files in place
    python3 tools/colonless.py --check FILE...  show what would change

The conversion works on tokens, not on a parse, so it also handles fragments (the tests build programs from pieces).
Block colons go (`if a:` becomes `if a`); one-line bodies get a word: `if a: b else: c` becomes `if a then b else c`,
`for x in xs: f(x)` becomes `for x in xs do f(x)`, `fn f(x) Int: x + 1` becomes `fn f(x) Int = x + 1`, and a lambda
`(x): x + 1` becomes `(x) -> x + 1`.  A default arm `else:` of a `when`, a `select` or a `seq` becomes `else ->`.
Colons that are not block openers (annotations, `Dict("a": 1)` keys, labels, `sql(c):`) stay.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from moxie.lexer import tokenize, MoxieSyntaxError   # noqa: E402

BLOCK_KW = {"tuple", "enum", "impl", "interface", "type", "test", "foreign", "forall", "when", "select", "scope",
            "daemon", "init", "do", "seq", "get", "set", "will_set", "did_set", "loop", "fiber", "update"}
MODS = {"export", "internal", "pub", "static", "lazy", "priv", "pure", "private", "secure", "inline", "forward", "fiber", "tailrec", "prints", "parks", "impure"}
ARM_PARENTS = {"when", "select", "seq"}
OPEN, CLOSE = "([{", ")]}"


class Unhandled(Exception):
    pass


def fix_mixed(src):
    """An `if` is all on one line or all indented: where a chain mixes the two, write the one-line branches as blocks."""
    try:
        toks = tokenize(src, "<fix>")
    except MoxieSyntaxError:
        return src
    lines, cur = [], None
    for i, t in enumerate(toks):
        if t.kind in ("NL", "INDENT", "DEDENT", "EOF"):
            if t.kind == "NL":
                cur = None
            continue
        if cur is None:
            cur = {"indent": t.col - 1, "idx": []}
            lines.append(cur)
        cur["idx"].append(i)
    chains = {}                 # indent -> list of (line number, inline?, cut token index)
    done = []
    for n, L in enumerate(lines):
        for ind in [k for k in chains if k > L["indent"]]:
            done.append(chains.pop(ind))
        first = toks[L["idx"][0]]
        if first.kind != "NAME" or first.val not in ("if", "elif", "else"):
            if L["indent"] in chains and first.kind == "NAME" and first.val in ("for", "while"):
                done.append(chains.pop(L["indent"]))
            for ind in [k for k in chains if k >= L["indent"]]:
                if ind == L["indent"]:
                    done.append(chains.pop(ind))
            continue
        depth, cut, inline = 0, None, False
        if first.val == "else":
            if len(L["idx"]) > 1:
                cut, inline = L["idx"][1], True
        else:
            for j in L["idx"][1:]:
                t = toks[j]
                if t.kind == "OP" and t.val in OPEN:
                    depth += 1
                elif t.kind == "OP" and t.val in CLOSE:
                    depth -= 1
                elif depth == 0 and t.kind == "NAME" and t.val == "then":
                    inline = True
                    cut = j + 1
                    break
        if first.val == "if":
            if L["indent"] in chains:
                done.append(chains.pop(L["indent"]))
            chains[L["indent"]] = []
        elif L["indent"] not in chains:
            continue
        chains[L["indent"]].append((n, inline, cut, first.val))
    done.extend(chains.values())
    splits = []
    for ch in done:
        if len({c[1] for c in ch}) > 1:
            splits.extend((n, cut, kind) for n, inline, cut, kind in ch if inline and cut is not None)
    if not splits:
        return src
    src_lines = src.split("\n")
    for n, cut, kind in sorted(splits, reverse=True):
        t = toks[cut]
        ln = t.line - 1
        text = src_lines[ln]
        col = t.col - 1
        head = text[:col].rstrip()
        if kind != "else":
            head = head[:-4].rstrip() if head.endswith("then") else head
        indent = " " * (len(text) - len(text.lstrip()))
        src_lines[ln:ln + 1] = [head, indent + "  " + text[col:]]
    return "\n".join(src_lines)


def convert(src, report=None):
    return fix_mixed(_convert(src, report))


def _convert(src, report=None):
    """Return the colonless text of `src` (or `src` itself when it has no block colon)."""
    toks = tokenize(src, "<convert>")
    # logical lines: (indent, [token index...]) so an `else:` can find its parent
    lines = []
    cur = None
    for i, t in enumerate(toks):
        if t.kind in ("NL", "INDENT", "DEDENT", "EOF"):
            if t.kind == "NL":
                cur = None
            continue
        if cur is None:
            cur = {"indent": t.col - 1, "idx": []}
            lines.append(cur)
        cur["idx"].append(i)
    line_of = {}
    for n, L in enumerate(lines):
        for i in L["idx"]:
            line_of[i] = n

    def is_arm_else(i):
        n = line_of[i]
        L = lines[n]
        if L["idx"][0] != i:
            return False
        m = n - 1
        while m >= 0 and lines[m]["indent"] >= L["indent"]:
            m -= 1
        if m < 0:
            return False
        d = 0
        for j in lines[m]["idx"]:
            t = toks[j]
            if t.kind == "OP" and t.val in OPEN:
                d += 1
            elif t.kind == "OP" and t.val in CLOSE:
                d -= 1
            elif d == 0 and t.kind == "NAME" and t.val in ARM_PARENTS and not (j > 0 and toks[j - 1].kind == "OP" and toks[j - 1].val == "."):
                return True
        return False

    def match(i):
        d = 0
        for j in range(i, len(toks)):
            t = toks[j]
            if t.kind == "OP" and t.val in OPEN:
                d += 1
            elif t.kind == "OP" and t.val in CLOSE:
                d -= 1
                if d == 0:
                    return j
        return None

    def nxt(i):
        j = i + 1
        return toks[j] if j < len(toks) else None

    edits = []        # (line, col, length, replacement)
    pending = []      # open headers: dict(kind, depth, idx)
    depth = 0
    for i, t in enumerate(toks):
        if t.kind == "NL":
            pending = [p for p in pending if p["depth"] > 0]
            continue
        if t.kind == "STR" and isinstance(t.val, list):
            line_text = src.split("\n")[t.line - 1]
            at = t.col - 1
            for part in t.val:
                if isinstance(part, tuple) and part and part[0] == "e":
                    new_e = convert(part[1], report)
                    pos = line_text.find(part[1], at)
                    if pos >= 0:
                        at = pos + len(part[1])
                        if new_e != part[1]:
                            edits.append((t.line, pos + 1, len(part[1]), new_e))
        if t.kind == "OP":
            if t.val in OPEN:
                depth += 1
            elif t.val in CLOSE:
                depth -= 1
                pending = [p for p in pending if p["depth"] <= depth]
            elif t.val == ":":
                n = nxt(i)
                prev = toks[i - 1] if i else None
                block = n is None or n.kind in ("NL", "EOF", "DEDENT")
                owner = None
                for p in reversed(pending):
                    if p["depth"] == depth:
                        owner = p
                        break
                if n is not None and n.kind == "SQL":
                    continue
                if owner is None:
                    lam = False
                    if prev is not None and prev.kind == "OP" and prev.val == ")":
                        lam = True
                    elif prev is not None and prev.kind == "NAME" and i >= 2 and toks[i - 2].kind == "OP" and toks[i - 2].val == ")":
                        lam = True                                   # `(x) Int: body`
                    if lam:
                        edits.append((t.line, t.col, 1, " ->"))
                    continue
                k = owner["kind"]
                if k == "forall" and not block:
                    continue                                         # `forall x: Int, y: Int:` the colons between binds stay
                pending.remove(owner)
                if k == "if":
                    edits.append((t.line, t.col, 1, "" if block else " then"))
                elif k in ("for", "while"):
                    edits.append((t.line, t.col, 1, "" if block else " do"))
                elif k == "fn":
                    fi = owner["idx"]
                    after = toks[fi + 1]
                    anon = after.kind == "OP" and after.val == "("
                    if anon:
                        lead = all(toks[j].kind == "NAME" and toks[j].val in MODS for j in lines[line_of[fi]]["idx"] if j < fi)
                        if lead:
                            anon = False                              # `fn (ref Self) name(...)`: a receiver declaration
                    if anon:
                        edits.append((t.line, t.col, 1, " ->"))
                    else:
                        edits.append((t.line, t.col, 1, "" if block else " ="))
                elif k == "else":
                    edits.append((t.line, t.col, 1, ""))
                elif k == "recvdo":
                    edits.append((t.line, t.col, 1, "" if block else " ->"))
                elif k == "recvupdate":
                    edits.append((t.line, t.col, 1, "" if block else ""))
                elif k in ("get", "set", "will_set", "did_set") and not block:
                    edits.append((t.line, t.col, 1, " ->"))
                else:                                                # a block keyword
                    if block:
                        edits.append((t.line, t.col, 1, ""))
                    elif report is not None:
                        report.append((t.line, f"a one-line `{k}` has no colonless form"))
                    else:
                        raise Unhandled(f"line {t.line}: a one-line `{k}` has no colonless form")
            continue
        if t.kind == "NAME":
            v = t.val
            dot = i > 0 and toks[i - 1].kind == "OP" and toks[i - 1].val == "."
            if dot:
                if v == "do":
                    pending.append({"kind": "recvdo", "depth": depth, "idx": i})
                elif v == "update":
                    pending.append({"kind": "recvupdate", "depth": depth, "idx": i})
                continue
            if v in ("if", "elif"):
                guard = any(p["kind"] == "fn" and p["depth"] == depth and toks[p["idx"] + 1].kind == "NAME" for p in pending)
                if not guard:                                        # `fn f(n) String if n < 0:` the guard belongs to the fn
                    pending.append({"kind": "if", "depth": depth, "idx": i})
            elif v in ("for", "while"):
                pending.append({"kind": v, "depth": depth, "idx": i})
            elif v == "fn":
                pending.append({"kind": "fn", "depth": depth, "idx": i})
            elif v == "else":
                n = nxt(i)
                if n is not None and n.kind == "OP" and n.val == ":":
                    pending.append({"kind": "else", "depth": depth, "idx": i, "arm": is_arm_else(i)})
            elif v in BLOCK_KW:
                n = nxt(i)
                lead = all(toks[j].kind == "NAME" and toks[j].val in MODS for j in lines[line_of[i]]["idx"] if j < i)
                anywhere = v in ("do", "scope", "select", "daemon", "when", "seq")
                # a declaration or block header opens a block at depth 0 of its logical line
                if depth == 0 and (lead or anywhere) and not (n is not None and n.kind == "OP" and n.val in ("=", ".", ",", ")")):
                    pending.append({"kind": v, "depth": depth, "idx": i})
    if not edits:
        return src
    src_lines = src.split("\n")
    by_line = {}
    for ln, col, ln_len, rep in edits:
        by_line.setdefault(ln, []).append((col, ln_len, rep))
    for ln, es in by_line.items():
        s = src_lines[ln - 1]
        for col, ln_len, rep in sorted(es, reverse=True):
            s = s[:col - 1] + rep + s[col - 1 + ln_len:]
        src_lines[ln - 1] = s
    return "\n".join(src_lines)


def _encode(seg, text):
    """A Python literal for `text`, in the style of the literal `seg` it replaces."""
    i = 0
    while i < len(seg) and seg[i] in "rRbBuUfF":
        i += 1
    prefix = seg[:i]
    rest = seg[i:]
    raw = "r" in prefix.lower()
    for q in ('"""', "'''"):
        if rest.startswith(q):
            body = text
            if not raw:
                body = body.replace("\\", "\\\\")
                body = body.replace(q, q[0] + "\\" + q[0] + q[0])
                if body.endswith(q[0]):
                    body = body[:-1] + "\\" + q[0]
            if not raw:
                body = "".join(c if (c >= " " or c in "\n\t") else "\\x%02x" % ord(c) for c in body)
            return prefix + q + body + q
    if raw and "\n" not in text and rest[0] not in text and "\\" not in text[-1:]:
        return prefix + rest[0] + text + rest[0]
    r = repr(text)
    return prefix.replace("r", "").replace("R", "") + r


def convert_py(text, report=None, oneline_ok=False, fix_only=False):
    """Convert the moxie source held in the string literals of a Python file."""
    import ast
    import re
    tree = ast.parse(text)
    lines = text.split("\n")
    starts = [0]
    for ln in lines:
        starts.append(starts[-1] + len(ln.encode("utf-8")) + 1)
    b = text.encode("utf-8")

    def off(lineno, col):
        return starts[lineno - 1] + col

    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body \
                and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            docs.add(id(node.body[0].value))
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            for sub in ast.walk(node):
                docs.add(id(sub))                                    # the pieces of an f-string are not literals of their own
    reps = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and (":" in node.value or "if " in node.value) and id(node) not in docs:
            val = node.value
            if "\n" not in val and not oneline_ok:
                continue
            if re.search(r"\)\s*\{|#include", val):
                continue                                             # C source, not moxie
            try:
                new = fix_mixed(val) if fix_only else convert(val)
            except (MoxieSyntaxError, Unhandled, IndexError, KeyError, RecursionError):
                continue
            if new == val:
                continue
            a, z = off(node.lineno, node.col_offset), off(node.end_lineno, node.end_col_offset)
            seg = b[a:z].decode("utf-8")
            reps.append((a, z, _encode(seg, new)))
    reps.sort(reverse=True)
    last = None
    for a, z, new in reps:
        if last is not None and z > last:
            continue
        b = b[:a] + new.encode("utf-8") + b[z:]
        last = a
    return b.decode("utf-8")


def convert_md(text, report=None, fix_only=False):
    """Convert the fenced code blocks of a Markdown file and the one-line code spans in its prose."""
    import re
    lines = text.split("\n")
    out = []
    i = 0
    span = re.compile(r"`([^`\n]+)`")

    def fix(m):
        code = m.group(1)
        if ":" not in code or code.lstrip().startswith(":") or "${" in code:
            return m.group(0)
        try:
            new = convert(code)
        except (MoxieSyntaxError, Unhandled, IndexError, KeyError, RecursionError):
            return m.group(0)
        return "`" + new + "`"
    while i < len(lines):
        ln = lines[i]
        if ln.lstrip().startswith("```"):
            ind = ln[:len(ln) - len(ln.lstrip())]
            j = i + 1
            while j < len(lines) and not lines[j].lstrip().startswith("```"):
                j += 1
            body = lines[i + 1:j]
            block = "\n".join(b[len(ind):] if b.startswith(ind) else b for b in body)
            try:
                rep = []
                new = fix_mixed(block) if fix_only else convert(block, rep)
                for k, msg in rep:
                    if report is not None:
                        report.append((i + 1 + k, msg))
            except (MoxieSyntaxError, Unhandled, IndexError, KeyError, RecursionError) as e:
                new = block
                if report is not None:
                    report.append((i + 2, f"block not converted: {e}"))
            out.append(ln)
            if body:
                out.extend((ind + b if b.strip() else b) for b in new.split("\n"))
            if j < len(lines):
                out.append(lines[j])
            i = j + 1
        else:
            out.append(ln if fix_only else span.sub(fix, ln))
            i += 1
    return "\n".join(out)


def main(argv):
    check = "--check" in argv
    fix_only = "--fix-mixed" in argv
    files = [a for a in argv if not a.startswith("--")]
    for f in files:
        old = open(f, encoding="utf-8").read()
        rep = []
        try:
            if fix_only:
                new = convert_py(old, rep, fix_only=True) if f.endswith(".py") else convert_md(old, rep, fix_only=True) if f.endswith(".md") else fix_mixed(old)
            else:
                new = convert_py(old, rep) if f.endswith(".py") else convert_md(old, rep) if f.endswith(".md") else convert(old, rep)
        except (MoxieSyntaxError, Unhandled) as e:
            print(f"{f}: skipped ({e})")
            continue
        for ln, msg in rep:
            print(f"{f}:{ln}: {msg}")
        if new != old:
            if check:
                print(f"{f}: would change")
            else:
                open(f, "w", encoding="utf-8").write(new)


if __name__ == "__main__":
    main(sys.argv[1:])
