"""Compile-time checks added 2026-11-16: a function's result is compared when it is arithmetic or a local; an `impl` must write the members
of its interface and agree on plain result types; an `if` with no `else` can't end a function that returns a value; a union with `()`
(`Int | ()`) can't be used in arithmetic until it is tested.  Run: python3 tests/run_safer.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
BAD = [
 ("arithmetic result as a String", "fn f(x Int) String\n  x + 1\n", "expected `String`, found `Int`"),
 ("float arithmetic as a String", "fn f(x Float) String\n  x * 2.0\n", "expected `String`, found `Double`"),
 ("a local of the wrong type as the result", "fn f(x Int) String\n  y = x * 2\n  y\n", "expected `String`, found `Int`"),
 ("an impl missing a required method", "interface I\n  fn a(self) Int\n  fn b(self) Int\ntuple T\n  n Int\nimpl I for T\n  fn a(self) Int\n    1\n", "is missing `b`"),
 ("an impl with the wrong result type", "interface I\n  fn a(self) Int\ntuple T\n  n Int\nimpl I for T\n  fn a(self) String\n    \"x\"\n", "returns `String`, but `I` says it returns `Int`"),
 ("an if with no else at the end of a function", "fn f(b Bool) Int\n  if b then\n    return 1\n", "has no `else`"),
 ("an update line naming an unknown field", "tuple P\n  x Int\np = P(x: 1)\nq = p.update\n  z: 2\n", "has no field `z` to update"),
 ("an update line with a value of the wrong type", "tuple P\n  x Int\np = P(x: 1)\nq = p.update\n  x: \"s\"\n", "expected `Int`, found `String`"),
 ("a nested update line with the wrong type", "tuple I\n  n Int\ntuple P\n  i I\np = P(i: I(n: 1))\nq = p.update\n  i:\n    n: \"s\"\n", "expected `Int`, found `String`"),
 ("& used as the wrong type", "tuple P\n  x Int\np = P(x: 1)\nq = p.update\n  x: & ++ \"a\"\n", ""),
 ("a bounded R.f(...) as an Int result", "interface E\n  static fn lit(n Int) Self\nfn f[R E]() Int\n  R.lit(1)\n", "expected `Int`, found `R`"),
 ("an impl with the wrong number of parameters", "interface I\n  fn add(self, a Int, b Int) Int\ntuple T\n  n Int\nimpl I for T\n  fn add(self, a Int) Int\n    a\n", "takes 1 parameter, but `I` says 2"),
 ("an impl with a parameter of the wrong type", "interface I\n  fn add(self, a Int) Int\ntuple T\n  n Int\nimpl I for T\n  fn add(self, a String) Int\n    1\n", "is a `String`, but `I` says `Int`"),
 ("a generic call that leaves out the type argument it needs", "interface E\n  static fn lit(n Int) Self\ntuple A\n  v Int\nimpl E for A\n  static fn lit(n Int) A\n    A(v: n)\nfn example[R E]() R\n  R.lit(1)\nx A = example()\n", "needs its type argument `R` named"),
 ("a function that ends in a binding", "fn f(n Int) Int\n  x = n + 1\n", "ends with a binding"),
 ("a function that ends in a loop with no value", "fn f(n Int) Int\n  for i in 1..=n do\n    println(i)\n", "loop that gives no value"),
 ("an update value that is not a member of the field's union", "type union M = Int | String\ntuple P\n  v M\np = P(v: 1)\nq = p.update v: true\n", "holds one of `Int`, `String`, not a `Bool`"),
 ("arithmetic on Int | ()", "fn f(x Int | ()) Int\n  x + 1\n", "can't take `Int | ()`"),
 ("arithmetic on a named union with ()", "type union M = Int | ()\nfn f(x M) Int\n  x + 1\n", "can't take `Int | ()`"),
 ("arithmetic on a field of Int | ()", "tuple P\n  v Int | ()\nfn f(p P) Int\n  p.v + 1\n", "can't take `Int | ()`"),
]
GOOD = [
 ("arithmetic result as an Int", "fn f(x Int) Int\n  x + 1\nprintln(f(1))\n"),
 ("a local as the result", "fn f(x Int) Int\n  y = x * 2\n  y\nprintln(f(2))\n"),
 ("a comparison as a Bool", "fn f(x Int) Bool\n  x <= 3\nprintln(f(2))\n"),
 ("an impl that leaves out a member with a default body", "interface I\n  fn a(self) Int\n  fn b(self) Int\n    self.a() + 1\ntuple T\n  n Int\nimpl I for T\n  fn a(self) Int\n    1\nprintln(T(n: 0).b())\n"),
 ("an if with an else", "fn f(b Bool) Int\n  if b then\n    1\n  else\n    2\nprintln(f(true))\n"),
 ("an early return then the value", "fn f(b Bool) Int\n  if b then\n    return 1\n  2\nprintln(f(false))\n"),
 ("an if with no else in a Unit function", "fn f(b Bool) Unit\n  if b then\n    println(1)\nf(true)\n"),
 ("update lines with & and a nested block", "tuple I\n  n Int\ntuple P deriving show\n  x Int\n  i I\np = P(x: 1, i: I(n: 2))\nq = p.update\n  x: & + 1,\n  i:\n    n: & * 10\nprintln(q)\n"),
 ("an update of a generic tuple", "tuple Box[T] deriving show\n  v T\nb = Box(v: 1)\nprintln(b.update v: 2)\n"),
 ("an update of a field with a union type", "type union M = Int | String\ntuple P deriving show\n  v M\np = P(v: 1)\nprintln(p.update v: \"s\")\n"),
 ("a generic call with its type argument named", "interface E\n  static fn lit(n Int) Self\ntuple A\n  v Int\nimpl E for A\n  static fn lit(n Int) A\n    A(v: n)\nfn example[R E]() R\n  R.lit(1)\nprintln(example[A]().v)\n"),
 ("a bounded R.f(...) as the R result", "interface E\n  static fn lit(n Int) Self\ntuple A\n  v Int\nimpl E for A\n  static fn lit(n Int) A\n    A(v: n)\nfn f[R E]() R\n  R.lit(1)\nprintln(f[A]().v)\n"),
 ("a loop with else gives a value", "fn f(n Int) Int\n  for i in 1..=n do\n    if i > 2 then\n      break(i)\n  else\n    0\nprintln(f(5))\n"),
 ("a while true loop that returns", "fn f(n Int) Int\n  while true do\n    if n > 0 then\n      return n\nprintln(f(2))\n"),
 ("Int | () tested before use", "fn f(x Int | ()) Int\n  if x is Int then\n    x + 1\n  else\n    0\nprintln(f(2))\n"),
]
fails = []
def run(src, cmd):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, capture_output=True, text=True)
    os.unlink(f.name)
    return r.returncode, (r.stdout + r.stderr).strip()
for name, src, word in BAD:
    rc, o = run(src, "check")
    ok = rc != 0 and word in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  -> rc={rc} {o[:240]}"))
    if not ok: fails.append(name)
for name, src in GOOD:
    rc, o = run(src, "run")
    ok = rc == 0
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  -> rc={rc} {o[:240]}"))
    if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
