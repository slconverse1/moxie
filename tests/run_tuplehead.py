"""One-line tuple declarations: `tuple Point(x Int, y Int)`.  Run: python3 tests/run_tuplehead.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()
CASES = [
 ("fields on the header line", 'tuple Point(x Int, y Int) deriving show\np = Point(x: 1, y: 2)\nprintln(p)\nprintln(p.x + p.y)\n', 0, "Point(x: 1, y: 2)"),
 ("the same as the block form", 'tuple A(x Int, y Int) deriving eq, show\ntuple B deriving show\n  x Int,\n  y Int\nprintln(A(1, 2) == A(1, 2))\nprintln(B(x: 1, y: 2))\n', 0, "true"),
 ("deriving after the header", 'tuple P(x Int, y Int) deriving show, eq\nprintln(P(1, 2) == P(1, 3))\nprintln(P(1, 2))\n', 0, "false"),
 ("a default value", 'tuple Box(xs List[Int], n Int = 3) deriving show\nprintln(Box(xs: List(1)))\n', 0, "Box(xs: List(1), n: 3)"),
 ("a generic tuple", 'tuple Pair[A, B](first A, second B) deriving show\nprintln(Pair(1, "a").second)\n', 0, "a"),
 ("a function-typed field", 'tuple Op(name String, f (Int) -> Int)\no = Op("inc", (n) -> n + 1)\nprintln(o.f(1))\n', 0, "2"),
 ("a one-field tuple", 'tuple Q(a Int) deriving show\nprintln(Q(1))\n', 0, "Q(a: 1)"),
 ("export", 'export tuple Q(a Int) deriving show\nprintln(Q(1))\n', 0, "Q(a: 1)"),
 ("an invariant in the body", 'tuple Pos(x Int, y Int) deriving show\n  invariant x >= 0\nprintln(Pos(1, 2).x)\nprintln(Pos(-1, 2))\n', 1, "invariant"),
 ("a pattern over it", 'tuple P(x Int, y Int) deriving show\nP(a, b) = P(3, 4)\nprintln(a * b)\n', 0, "12"),
 ("fields in both places is an error", 'tuple P(x Int) deriving show\n  y Int\n', 2, "write the fields in one place"),
 ("a missing type is an error", 'tuple P(x Int, y) deriving show\n', 2, ""),
 ("a duplicate field is an error", 'tuple P(x Int, x Int) deriving show\n', 2, "x"),
 ("a colon is still not allowed", 'tuple P(x: Int) deriving show\n', 2, ""),
]
fails = []
for name, src, rc_want, word in CASES:
    for gc in (False, True):
        p = os.path.join(D, "t.mxi")
        open(p, "w").write(src)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check" if rc_want == 2 else "run", p], cwd=ROOT, capture_output=True, text=True)
        o = r.stdout + r.stderr
        good = ((r.returncode != 0) if rc_want in (1, 2) else (r.returncode == 0)) and word in o
        print(("ok    " if good else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if good else f"  -> rc={r.returncode} {o.strip()[:300]!r}"))
        if not good: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
