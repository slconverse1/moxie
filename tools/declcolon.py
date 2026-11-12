"""Second colonless step: declaration colons go (`x: Int` becomes `x Int`) and Dict entries use `->`.

    python3 tools/declcolon.py FILE...          rewrite .mxi, .py (string literals) and .md (code blocks, spans) in place

Run it on text that already has colonless blocks (the output of tools/colonless.py), once.  The parser decides which
colons are declaration colons: with `PBase.RECORD` set it records an old-style colon and skips it, and this tool deletes
exactly those characters.  A `Dict("a": 1)` entry colon becomes ` ->`.  Colons of annotations on bindings, labels, named
arguments, `update` lines, `sql(c):`, and format specs are not touched.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import colonless                                        # noqa: E402
from moxie.lexer import MoxieSyntaxError                # noqa: E402
from moxie.parser import parse_program                  # noqa: E402
from moxie.pbase import PBase, edit_row                 # noqa: E402


def declconvert(src, report=None):
    import re
    rec = []
    err = None
    # a program built from pieces (`{embeds}`, `{REV}`) is parsed with each piece standing in as a name of the same length
    masked = re.sub(r"\{[^{}\n]*\}", lambda m: "x" * len(m.group(0)), src)
    spaced = re.sub(r"(?m)^\{[^{}\n]*\}", lambda m: " " * len(m.group(0)), masked if False else src)
    spaced = re.sub(r"\{[^{}\n]*\}", lambda m: "x" * len(m.group(0)), spaced)
    for attempt in (src, masked, spaced):
        rec = []
        PBase.RECORD = rec
        err = None
        try:
            parse_program(attempt, "<declcolon>")
        except MoxieSyntaxError as e:
            err = e
        finally:
            PBase.RECORD = None
        if err is None or attempt is spaced:
            break
    if not rec:
        if err is not None and report is not None:
            report.append((0, f"not parsed: {err}"))
        return src
    lines = src.split("\n")
    by_line = {}
    interps = []
    for item in rec:
        if item[0] == "interp":
            interps.append(item)
        else:
            kind, t = item
            by_line.setdefault(t.line, {})[t.col] = kind
    for ln, edits in by_line.items():
        row = lines[ln - 1]
        new = edit_row(row, edits)
        if report is not None and new == row:
            report.append((ln, "expected a colon at the recorded column"))
        lines[ln - 1] = new
    for _, ln, old_src, new_src in interps:
        row = lines[ln - 1]
        if "${" + old_src in row:
            lines[ln - 1] = row.replace("${" + old_src, "${" + new_src, 1)
        elif report is not None:
            report.append((ln, f"interpolation not found: {old_src}"))
    if err is not None and report is not None:
        report.append((0, f"partly converted, then: {err}"))
    return "\n".join(lines)


def main(argv):
    check = "--check" in argv
    colonless.convert = declconvert
    files = [a for a in argv if not a.startswith("--")]
    for f in files:
        old = open(f, encoding="utf-8").read()
        rep = []
        if f.endswith(".py"):
            new = colonless.convert_py(old, rep)
        elif f.endswith(".md"):
            new = colonless.convert_md(old, rep)
        else:
            new = declconvert(old, rep)
        for ln, msg in rep:
            print(f"{f}:{ln}: {msg}")
        if new != old:
            print(f"{f}: {'would change' if check else 'converted'}")
            if not check:
                open(f, "w", encoding="utf-8").write(new)


if __name__ == "__main__":
    main(sys.argv[1:])
