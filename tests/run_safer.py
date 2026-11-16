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
