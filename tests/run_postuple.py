"""Declared tuples with unnamed fields: `tuple Pair(Int, String)` and the block form with one type per line.  Run: python3 tests/run_postuple.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()
CASES = [
 ("parenthesized", 'tuple Pair(Int, String)\nprintln(Pair(1, "a"))\n', 0, 'Pair(1, "a")'),
 ("block form", 'tuple Pair\n  Int,\n  String\nprintln(Pair(1, "a"))\n', 0, 'Pair(1, "a")'),
 ("deriving eq and show", 'tuple P(Int, Int) deriving show, eq\nprintln(P(1, 2) == P(1, 2))\nprintln(P(1, 2) == P(2, 1))\n', 0, "true"),
 ("fields by position", 'tuple Pair(Int, String)\na = Pair(4, "x")\nprintln(a.0 + 1)\nprintln(a.1)\n', 0, "5"),
 ("destructuring", 'tuple Pair(Int, String)\nPair(n, s) = Pair(7, "q")\nprintln("$n $s")\n', 0, "7 q"),
 ("a generic one", 'tuple Box[T](T, Int) deriving show\nprintln(Box("x", 3))\n', 0, 'Box("x", 3)'),
 ("as a parameter type", 'tuple Pair(Int, String)\nfn first(p Pair) Int\n  p.0\nprintln(first(Pair(9, "z")))\n', 0, "9"),
 ("an anonymous tuple converts in", 'tuple Pair(Int, String)\np Pair = (1, "a")\nprintln(p)\n', 0, 'Pair(1, "a")'),
 ("the wrong number of values", 'tuple Pair(Int, String)\nprintln(Pair(1))\n', 2, "2 fields"),
 ("the wrong type", 'tuple Pair(Int, String)\nprintln(Pair("a", 1))\n', 2, "Int"),
 ("named and unnamed fields can't mix", 'tuple Mix\n  Int,\n  y Int\n', 2, "mixes named and unnamed"),
 ("a labelled argument is an error", 'tuple Pair(Int, String)\nprintln(Pair(a: 1, b: "x"))\n', 2, ""),
 ("named header form still works", 'tuple P(x Int, y Int)\nprintln(P(x: 1, y: 2))\n', 0, "P(x: 1, y: 2)"),
]
fails = []
for name, src, rc_want, word in CASES:
    for gc in (False, True):
        p = os.path.join(D, "t.mxi")
        open(p, "w").write(src)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check" if rc_want == 2 else "run", p], cwd=ROOT, capture_output=True, text=True)
        o = r.stdout + r.stderr
        good = ((r.returncode != 0) if rc_want == 2 else (r.returncode == 0)) and word in o
        print(("ok    " if good else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if good else f"  -> rc={r.returncode} {o.strip()[:300]!r}"))
        if not good: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
