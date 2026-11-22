"""Collecting blocks: an indented block after a call fills the callee's `block` parameter.  Run: python3 tests/run_block.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(src, gc=False):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
D = """tuple Li(text String) deriving show
tuple Ul(class String, items List[Li]) deriving show
fn ul(class String, block items List[Li]) Ul = Ul(class: class, items: items)
fn li(t String) Li = Li(text: t)
fn count(block xs List[Int]) Int = len(xs)
"""
CASES = [
 ("children in order", D + "m = ul(class: \"m\")\n  li(\"a\")\n  li(\"b\")\nprintln(m)\n", 'Ul(class: "m", items: List(Li(text: "a"), Li(text: "b")))'),
 ("no block, no children", D + "println(ul(class: \"e\"))\n", 'Ul(class: "e", items: List())'),
 ("if adds a child", D + "a = true\nm = ul(class: \"m\")\n  li(\"x\")\n  if a\n    li(\"admin\")\nprintln(m.items |> map(_.text) |> collect())\n", 'List("x", "admin")'),
 ("if without else adds nothing", D + "a = false\nm = ul(class: \"m\")\n  li(\"x\")\n  if a\n    li(\"admin\")\nprintln(len(m.items))\n", "1"),
 ("if elif else", D + "n = 2\nm = ul(class: \"m\")\n  if n == 1\n    li(\"one\")\n  elif n == 2\n    li(\"two\")\n    li(\"two again\")\n  else\n    li(\"many\")\nprintln(m.items |> map(_.text) |> collect())\n", 'List("two", "two again")'),
 ("for adds a child per element", D + "m = ul(class: \"m\")\n  for p in List(\"a\", \"b\", \"c\")\n    li(p)\nprintln(len(m.items))\n", "3"),
 ("for with several children each", D + "m = ul(class: \"m\")\n  for p in List(\"a\", \"b\")\n    li(p)\n    li(p + p)\nprintln(m.items |> map(_.text) |> collect())\n", 'List("a", "aa", "b", "bb")'),
 ("a binding contributes nothing", D + "m = ul(class: \"m\")\n  t = \"x\"\n  li(t)\n  t = \"y\"\n  li(t)\nprintln(m.items |> map(_.text) |> collect())\n", 'List("x", "y")'),
 ("spread adds every element", D + "more = List(li(\"p\"), li(\"q\"))\nm = ul(class: \"m\")\n  li(\"a\")\n  ...more\nprintln(len(m.items))\n", "3"),
 ("blocks nest", D + "tuple Div(kids List[Ul]) deriving show\nfn div(block kids List[Ul]) Div = Div(kids: kids)\nd = div()\n  ul(class: \"a\")\n    li(\"1\")\n  ul(class: \"b\")\n    li(\"2\")\n    li(\"3\")\nprintln(d.kids |> map(_.items) |> map(len) |> collect())\n", "List(1, 2)"),
 ("a tuple pattern in for", D + "m = ul(class: \"m\")\n  for (a, b) in List((\"x\", 1), (\"y\", 2))\n    li(a)\nprintln(len(m.items))\n", "2"),
 ("a wrong child type is an error", D + "m = ul(class: \"m\")\n  li(\"a\")\n  5\n", "List"),
 ("a function without block", D + "fn plain(x Int) Int = x\nr = plain(1)\n  2\n", "has no `block` parameter"),
 ("the block given twice", D + "m = ul(class: \"m\", items: List())\n  li(\"a\")\n", "twice"),
 ("when is not allowed", D + "n = 1\nm = ul(class: \"m\")\n  when n\n    1 -> li(\"a\")\n    _ -> li(\"b\")\n", "not allowed in a block of children"),
 ("a statement that is not a child", D + "m = ul(class: \"m\")\n  while true\n    li(\"a\")\n", "holds children"),
 ("a count of children", D + "n = count()\n  1\n  2\n  3\nprintln(n)\nprintln(count())\n", "3\n0"),
 ("an if header call still takes its block", D + "fn ok(x Int) Bool = x > 0\nif ok(1)\n  println(\"yes\")\n", "yes"),
 ("a for header call still takes its block", D + "for x in List(1, 2).map(_ * 2)\n  println(x)\n", "2\n4"),
]
fails = []
for name, src, want in CASES:
    for gc in (False, True):
        rc, out = run(src, gc)
        good = want in out
        print(("ok    " if good else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if good else f"  -> rc={rc} {out.strip()[:300]!r}"))
        if not good:
            fails.append(name)
print(f"{len(CASES) * 2 - len(fails)} of {len(CASES) * 2} passed")
sys.exit(1 if fails else 0)
