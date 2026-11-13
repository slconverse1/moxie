"""Chained bindings: `x = y = z` binds z to y, then y to x (z is evaluated once).  Run: python3 tests/run_chain.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(src, cmd="run"):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, capture_output=True, text=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
OK = [
 ("two names", 'z = 5\nx = y = z\nprintln("$x $y $z")\n', "5 5 5\n"),
 ("three names", 'a = b = c = 7\nprintln("$a $b $c")\n', "7 7 7\n"),
 ("a value that is computed once", 'fn tick() Int\n  println("tick")\n  1\nx = y = tick()\nprintln("$x $y")\n', "tick\n1 1\n"),
 ("lined up on separate lines", 'z = 5\nlong_name_one =\nlong_name_two =\nz\nprintln("$long_name_one $long_name_two")\n', "5 5\n"),
 ("the first name has a type", 'n Int = m = 3\nprintln("$n $m")\n', "3 3\n"),
 ("inside a function", 'fn f(v Int) Int\n  a = b = v + 1\n  a + b\nprintln(f(4))\n', "10\n"),
 ("rebinding is silent", 'x = 1\ny = 2\nx = y = 9\nprintln("$x $y")\n', "9 9\n"),
 ("a literal", 'x = y = "hi"\nprintln("$x $y")\n', "hi hi\n"),
]
ERR = [
 ("not after then", 'fn f(c Bool) Int\n  if c then a = b = 1\n  2\n', "goes on a line of its own"),
 ("not with an else", 'fn f(v Int) Int\n  a = b = v else 0\n  a\n', "can't have an `else`"),
 ("not with +=", 'x = 1\ny = 2\nx += y = 3\n', "unexpected '='"),
 ("not with a tuple on the left", 'x = 1\n(a, b) = c = x\n', "unexpected '='"),
 ("not with a field", 'tuple P\n  n Int\np = P(n: 1)\nq = 2\np.n = q = 3\n', "unexpected '='"),
]
fails = []
for name, src, want in OK:
    rc, out = run(src)
    good = rc == 0 and out == want
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} {out.strip()[:200]!r}"))
    if not good:
        fails.append(name)
for name, src, word in ERR:
    rc, out = run(src, "check")
    good = rc != 0 and word in out
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} {out.strip()[:200]!r}"))
    if not good:
        fails.append(name)
sys.exit(1 if fails else 0)
