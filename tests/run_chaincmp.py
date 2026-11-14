"""Chained comparisons: `a < b <= c` is `a < b and b <= c`, middle operands evaluated once.  Run: python3 tests/run_chaincmp.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(src, cmd="run"):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, capture_output=True, text=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
T = 'fn t(n Int) Int\n  println("t$n")\n  n\n'
OK = [
 ("in range", 'x = 5\nprintln(0 <= x <= 100)\n', "true\n"),
 ("out of range", 'x = 500\nprintln(0 <= x <= 100)\n', "false\n"),
 ("below range", 'x = -1\nprintln(0 <= x <= 100)\n', "false\n"),
 ("four operands", 'println(1 < 2 < 3 < 4)\nprintln(1 < 2 < 3 < 3)\n', "true\nfalse\n"),
 ("mixed directions", 'println(1 <= 1 < 2 > 1)\n', "true\n"),
 ("fields", 'p = (x: 3, y: 4)\nprintln(0 < p.x < p.y)\n', "true\n"),
 ("middle call runs once", T + 'println(0 < t(3) < 10)\n', "t3\ntrue\n"),
 ("stops at first false link", T + 'println(t(5) < t(2) < t(3) < t(4))\n', "t5\nt2\nfalse\n"),
 ("all links run when true", T + 'println(t(1) < t(2) < t(3) < t(4))\n', "t1\nt2\nt3\nt4\ntrue\n"),
 ("single comparison unchanged", 'println(1 < 2)\nprintln(2 < 1)\n', "true\nfalse\n"),
 ("equality still left to right", 'println(1 == 1 == true)\nprintln(1 < 2 == true)\n', "true\ntrue\n"),
 ("in an if", 'x = 7\nif 0 < x < 10 then println("in")\n', "in\n"),
 ("with and", 'x = 7\nprintln(0 < x < 10 and x ~= 8)\n', "true\n"),
]
fails = []
for name, src, want in OK:
    rc, out = run(src)
    good = rc == 0 and out == want
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} {out.strip()[:200]!r}"))
    if not good:
        fails.append(name)
sys.exit(1 if fails else 0)
