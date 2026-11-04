"""Tests for `moxie fmt`: layout rules, safety checks, and the command line."""
import io
import os
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from moxie.fmt import format_source, fmt_main, FmtError

fails = 0
total = 0


def check(name, got, want):
    global fails, total
    total += 1
    if got != want:
        fails += 1
        print("FAIL", name, "\n  got ", repr(got), "\n  want", repr(want))


check("four-space blocks become two", format_source("fn f() Int:\n    x = 1\n    x\n"), "fn f() Int:\n  x = 1\n  x\n")
check("trailing spaces and final newline", format_source("x = 1   \ny = 2"), "x = 1\ny = 2\n")
check("crlf", format_source("x = 1\r\ny = 2\r\n"), "x = 1\ny = 2\n")
check("blank lines: two at top level, one inside", format_source("\n\n\nx = 1\n\n\n\n\ny = 2\nfn f() Int:\n  a = 1\n\n\n\n  a\n\n\n"),
      "x = 1\n\n\ny = 2\nfn f() Int:\n  a = 1\n\n  a\n")
check("comment follows the code level",
      format_source("fn f() Int:\n    // note\n    1\n// top\nx = 2\n"), "fn f() Int:\n  // note\n  1\n// top\nx = 2\n")
check("continuation keeps its offset", format_source("fn f() Int:\n    x = foo(a,\n            b)\n    x\n"),
      "fn f() Int:\n  x = foo(a,\n          b)\n  x\n")
check("triple-quoted string moves as a unit",
      format_source('fn f() String:\n    """\n      hi  \n    """\n'), 'fn f() String:\n  """\n    hi  \n  """\n')
check("block comment moves as a unit", format_source("fn f() Int:\n    /* a\n       b */\n    1\n"), "fn f() Int:\n  /* a\n     b */\n  1\n")
check("a comment inside a triple string is not a comment",
      format_source('x = """\n  // not a comment\n  """\n'), 'x = """\n  // not a comment\n  """\n')
src = "fn f() Int:\n    when 1:\n        1 -> 2\n        _ -> 3\n"
once = format_source(src)
check("idempotent", format_source(once), once)
try:
    format_source("fn f() Int:\n\t1\n")
    check("syntax error is refused", True, False)
except FmtError:
    check("syntax error is refused", True, True)

d = tempfile.mkdtemp()
p = os.path.join(d, "a.mxi")
open(p, "w").write("fn f() Int:\n    1\n")
o, e = io.StringIO(), io.StringIO()
check("--check reports a change and exits 1", fmt_main(["--check", p], o, e), 1)
check("--check does not write", open(p).read(), "fn f() Int:\n    1\n")
check("fmt writes the file", (fmt_main([p], io.StringIO(), e), open(p).read()), (0, "fn f() Int:\n  1\n"))
check("--check passes after fmt", fmt_main(["--check", d], io.StringIO(), e), 0)
open(os.path.join(d, "b.mxi"), "w").write("fn g() Int:\n\t1\n")
check("a file that does not parse exits 2", fmt_main([d], io.StringIO(), e), 2)
print(f"fmt: {total - fails} / {total}" if fails else "fmt: all passed")
sys.exit(1 if fails else 0)
