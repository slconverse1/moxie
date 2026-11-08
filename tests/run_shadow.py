"""Shadow warnings: a binding in a deeper block hides the outer name (Spec section 1).  Run: python3 tests/run_shadow.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def check(src):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "check", f.name], cwd=ROOT, capture_output=True, timeout=120)
    os.unlink(f.name)
    return r.stdout.decode() + r.stderr.decode()

WARN = [
 ("+= in a loop", "total = 0\nfor i in List(1, 2):\n  total += i\nprintln(total)\n"),
 ("= in a loop", "total = 0\nfor i in List(1, 2):\n  total = total + i\nprintln(total)\n"),
 ("= in an if", "j = 0\nif true:\n  j = 9\nprintln(j)\n"),
 ("= in a when arm", "i = 0\nwhen 1:\n  1 -> i = 2\n  _ -> i = 5\nprintln(i)\n"),
 ("shadowing a parameter", "fn f(n: Int) Int:\n  if n > 0:\n    n = 1\n  n\n"),
]
QUIET = [
 ("rebinding in the same block", "x = 1\nx = x + 1\nprintln(x)\n"),
 ("gimme reaches the outer name", "total = 0\nfor i in List(1, 2):\n  gimme.1.total += i\nprintln(total)\n"),
 ("a function local named like a global", "n = 1\nfn f() Int:\n  n = 2\n  n\nprintln(f() + n)\n"),
 ("a lambda local named like an outer name", "n = 1\nf = (a): a + 1\nprintln(f(n))\n"),
 ("an underscore name", "_t = 0\nfor i in List(1):\n  _t = i\nprintln(1)\n"),
]
fails = []
for name, src in WARN:
    out = check(src)
    ok = "warning" in out and "hides the outer one" in out and "error" not in out
    print(("ok    " if ok else "FAIL  ") + "warns: " + name + ("" if ok else f"  {out.strip()[:160]!r}"))
    if not ok: fails.append(name)
for name, src in QUIET:
    out = check(src)
    ok = "hides the outer one" not in out
    print(("ok    " if ok else "FAIL  ") + "quiet: " + name + ("" if ok else f"  {out.strip()[:160]!r}"))
    if not ok: fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
