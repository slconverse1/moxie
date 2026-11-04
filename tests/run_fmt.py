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
      "x = 1\n\n\ny = 2\n\nfn f() Int:\n  a = 1\n\n  a\n")
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
check("spaces around binary operators and after commas", format_source("x=a+b*2\ny = f(a,b ,c)\nz = g(-1, x-1)\n"), "x = a + b * 2\ny = f(a, b, c)\nz = g(-1, x - 1)\n")
check("arrows, comparisons and pipes", format_source("fn f(x: Int) Int:\n  when x:\n    1->2\n    _->3\nok = 1==1\nv = 2|>f\n"),
      "fn f(x: Int) Int:\n  when x:\n    1 -> 2\n    _ -> 3\nok = 1 == 1\nv = 2 |> f\n")
check("strings and comments are not touched", format_source('s = "a,b+c==d"  // x,y=1\n'), 's = "a,b+c==d"  // x,y=1\n')
check("a blank line before a declaration after a block", format_source("fn a() Int:\n  1\nfn b() Int:\n  2\n"), "fn a() Int:\n  1\n\nfn b() Int:\n  2\n")
check("no blank line is added after a comment", format_source("fn a() Int:\n  1\n/// doc\nfn b() Int:\n  2\n"), "fn a() Int:\n  1\n/// doc\nfn b() Int:\n  2\n")
check("a fragment that does not parse still gets layout only", format_source("x=(\n"), "x=(\n")
check("a block under a continuation line stays deeper than it", format_source("x = 5\n    |> seq:\n      a -> b\n      c -> d\ny = 1\n"), "x = 5\n    |> seq:\n      a -> b\n      c -> d\ny = 1\n")
check("an operator method name keeps its form", format_source("impl Money:\n  fn +(other: Money) Money:\n    other\n"), "impl Money:\n  fn +(other: Money) Money:\n    other\n")
check("a fragment that changes meaning when spaced is left with layout only", format_source("x = 1\ny = 2\n"), "x = 1\ny = 2\n")
LONG = "fn main() Unit:\n  result = compute_something_long(first_argument_name, second_argument_name, third_argument_name, fourth_arg)\n  println(result)\n"
check("a long call breaks one argument to a line", format_source(LONG),
      "fn main() Unit:\n  result = compute_something_long(\n    first_argument_name,\n    second_argument_name,\n    third_argument_name,\n    fourth_arg\n  )\n  println(result)\n")
check("a line that fits is left alone", format_source("x = foo(a, b)\n"), "x = foo(a, b)\n")
check("breaking is stable", format_source(format_source(LONG)), format_source(LONG))
check("a long parameter list breaks and the body stays put",
      format_source("fn very_long_function_name(first_parameter: Int, second_parameter: String, third_parameter: List[Int]) Int:\n  first_parameter\n"),
      "fn very_long_function_name(\n  first_parameter: Int,\n  second_parameter: String,\n  third_parameter: List[Int]\n) Int:\n  first_parameter\n")
check("nested groups break from the outside in", format_source("total = alpha(beta(gamma(delta_value_with_long_name, epsilon_value_with_long_name), zeta_value_with_long_name), eta_value_xx)\n"),
      "total = alpha(\n  beta(\n    gamma(delta_value_with_long_name, epsilon_value_with_long_name),\n    zeta_value_with_long_name\n  ),\n  eta_value_xx\n)\n")
LS = 's = "' + "a very long string that cannot be broken because it is one token " * 2 + '"\n'
check("a long string alone is left", format_source(LS), LS)
check("a line with a comment is left", format_source("x = compute_something_long(first_argument_name, second_argument_name, third_argument_name, fourth_arg_)  // c\n"),
      "x = compute_something_long(first_argument_name, second_argument_name, third_argument_name, fourth_arg_)  // c\n")
check("commas inside strings do not split", format_source('x = compute_something_long("a, b, c, d, e, f, g, h, i", second_argument_name, third_argument_name, fourth_arg_xx)\n'),
      'x = compute_something_long(\n  "a, b, c, d, e, f, g, h, i",\n  second_argument_name,\n  third_argument_name,\n  fourth_arg_xx\n)\n')
check("a trailing comma stays", format_source("x = compute_something_long(first_argument_name, second_argument_name, third_argument_name, fourth_a,)\n"),
      "x = compute_something_long(\n  first_argument_name,\n  second_argument_name,\n  third_argument_name,\n  fourth_a,\n)\n")
check("an inline fiber is written run fn (", format_source("run fn(tx)(out): write(out, 1)\nrun fn   (tx)(out): write(out, 2)\n"), "run fn (tx)(out): write(out, 1)\nrun fn (tx)(out): write(out, 2)\n")
check("a lambda keeps its colon form", format_source("x = map(xs,(a):a+1)\ny: (Int) -> Int = (a) :a\n"), "x = map(xs, (a): a + 1)\ny: (Int) -> Int = (a): a\n")
from moxie.fmt import _comments
msg = "// a  b\nfn f() Int:\n    /* x\n         y */\n    1  // t,u=1\n// end\n"
check("every comment survives, in order", _comments(format_source(msg), "x"), _comments(msg, "x"))
check("comments are listed", _comments(msg, "x"), ["// a  b", "/* x\ny */", "// t,u=1", "// end"])
print(f"fmt: {total - fails} / {total}" if fails else "fmt: all passed")
sys.exit(1 if fails else 0)
