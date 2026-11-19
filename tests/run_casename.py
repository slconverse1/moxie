"""A program's own enum case that shares a name with a prelude type (`Key`).  Run: python3 tests/run_casename.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(src, flags=()):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    try:
        r = subprocess.run([sys.executable, "-m", "moxie", *flags, "run", f.name], cwd=ROOT, capture_output=True, timeout=60)
        rc, out = r.returncode, r.stdout.decode() + r.stderr.decode()
    except subprocess.TimeoutExpired:
        rc, out = -9, "TIMEOUT"
    os.unlink(f.name)
    return rc, out

fails = []
def chk(name, src, rc_want, *wants):
    for flags in ((), ("--gc",)):
        rc, out = run(src, flags)
        ok = rc == rc_want and all(w in out for w in wants)
        label = name + (" (gc)" if flags else "")
        print(("ok    " if ok else "FAIL  ") + label + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
        if not ok: fails.append(label)

chk("a case named Key is built and matched", '''enum Event
  Click(x Int),
  Key(c String),
  Quit
fn show(e Event) String
  when e
    Click(x) -> "click ${x}"
    Key(c) -> "key ${c}"
    Quit -> "quit"
println(show(Key("a")))
println(show(Click(3)))
println(Key("b"))
''', 0, "key a\nclick 3\nEvent.Key(\"b\")")
chk("the prelude's own Key cases still work", 'k = Key.Enter\nprintln(k)\n', 0, "Key.Enter")
chk("a bare case named Option is the program's own case", '''enum Mode deriving eq
  Option
  Plain
x Mode = Option
println(x == Mode.Option)
println(x)
when x
  Option -> println("opt")
  Plain -> println("plain")
''', 0, "true\nMode.Option\nopt")
chk("a mistyped prelude case is a compile error", 'e = Option.Som(3)\n', 2, "`Option` has no case `Som`")
chk("a prelude case with the wrong number of values", 'q Option[Int] = Some()\n', 2, "`Some` has 1 field, but 0 values are given")
chk("a prelude case with too many values", 'q Option[Int] = Option.Some(1, 2)\n', 2, "`Some` has 1 field, but 2 values are given")
chk("a nullary case written with parentheses", 'o Option[Int] = None()\n', 2, "`None` has no fields, so write `None`, not `None()`")
chk("a placeholder alone after a pipe", 'x = 3\ny = x |> _ + 1\n', 2, "can't stand alone after `|>`")
chk("a pipe into a written-out function", 'x = 3\nprintln(x |> ((v) -> v + 1)())\n', 0, "4")
chk("a lambda called with too many arguments", 'f = (x) -> x + 1\nprintln(f(1, 2))\n', 2, "`f` takes 1 argument, but 2 given")
chk("a lambda called with too few arguments", 'g = (a, b) -> a + b\nprintln(g(1))\n', 2, "`g` takes 2 arguments, but 1 given")
chk("lambdas called correctly", 'f = (x) -> x + 1\ng = (a, b) -> a + b\nh = () -> 5\nprintln("${f(1)} ${g(1, 2)} ${h()}")\n', 0, "2 3 5")
chk("a tuple built with one plain number too few", 'tuple P\n  x Int,\n  y Int\np = P(1)\n', 2, "`P` needs a value for `y`")
chk("a one-field tuple built with one value", 'tuple W\n  n Int\nw = W(3)\nprintln(w)\n', 0, "W(n: 3)")
chk("arithmetic on an Option", 'o Option[Int] = Some(1)\nprintln(o + 1)\n', 2, "cannot apply `+` to `Option[Int]`")
chk("a field on a number", 'x = 5\nprintln(x.foo)\n', 2, "a `Int` has no field `foo`")
chk("a field on a List", 'xs = List(1, 2)\nprintln(xs.len)\n', 2, "a `List` has no field `len`", "`.len()`")
chk("for taking apart numbers", 'xs = List(1, 2)\nfor (a, b) in xs\n  println(a)\n', 2, "the elements are `Int`, not tuples")
chk("for taking apart tuples of the wrong size", 'd = Dict("a" -> 1)\nfor (a, b, c) in d\n  println(a)\n', 2, "tuples of 2")
chk("for taking apart pairs is fine", 'd = Dict("a" -> 1)\nfor (k, v) in d\n  println("$k $v")\nfor (i, x) in List(5, 6) |> enumerate()\n  println("$i $x")\n', 0, "a 1", "0 5", "1 6")
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
