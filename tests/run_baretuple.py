"""A bare `a, b` as a whole statement or after `return` is the tuple `(a, b)`.  Run: python3 tests/run_baretuple.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(src, cmd="run"):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, capture_output=True, text=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
OK = [
 ("last line of a function", 'fn pair() (Int, Int)\n  1, 2\nlo, hi = pair()\nprintln("$lo $hi")\n', "1 2\n"),
 ("three values", 'fn f() (Int, Int, Int)\n  1, 2, 3\nprintln(f())\n', "(1, 2, 3)\n"),
 ("after return", 'fn f(x Int) (Int, Int)\n  return x, x + 1\nprintln(f(4))\n', "(4, 5)\n"),
 ("in both branches of an if", 'fn f(a Int, b Int) (lo Int, hi Int)\n  if a < b\n    a, b\n  else\n    b, a\nprintln(f(5, 3))\n', "(lo: 3, hi: 5)\n"),
 ("early return then bare last line", 'fn f(x Int) (Int, Int)\n  if x > 0\n    return x, 0\n  0, x\nprintln(f(1))\nprintln(f(-1))\n', "(1, 0)\n(0, -1)\n"),
 ("round trip with multiple binding", 'fn swap(a Int, b Int) (Int, Int)\n  b, a\nx, y = swap(1, 2)\nprintln("$x $y")\n', "2 1\n"),
 ("values are expressions", 'fn f(n Int) (Int, String)\n  n * 2, "n=${n}"\nprintln(f(3))\n', '(6, "n=3")\n'),
 ("call arguments are untouched", 'fn add(a Int, b Int) Int = a + b\nprintln(add(1, 2))\n', "3\n"),
 ("a lambda argument is not a tuple", 'fn ap(f (Int) -> Int, x Int) Int\n  f(x)\nprintln(ap((n) -> n + 1, 1))\n', "2\n"),
 ("a one-item return is untouched", 'fn f() Int\n  return 7\nprintln(f())\n', "7\n"),
]
fails = []
for name, src, want in OK:
    rc, out = run(src)
    good = rc == 0 and out == want
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} {out.strip()[:200]!r}"))
    if not good:
        fails.append(name)
sys.exit(1 if fails else 0)
