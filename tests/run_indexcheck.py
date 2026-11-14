"""A constant index that can't be in range is a compile error: past the end of a List or Array whose length the text gives, or negative.  Run: python3 tests/run_indexcheck.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()
CASES = [
 ("past the end of a List literal", 'xs = List(1, 2, 3)\nprintln(xs(3))\n', 2, "index 3 is past the end of `xs`, which has 3 elements"),
 ("the last element is fine", 'xs = List(1, 2, 3)\nprintln(xs(2) + 1)\n', 0, "4"),
 ("inside a function", 'fn f() Int\n  q = List(1, 2)\n  q(2)\n', 2, "past the end of `q`"),
 ("a negative literal into a List", 'xs = List(1, 2)\nprintln(xs(-1))\n', 2, "before the start of `xs`"),
 ("a negative literal into a List parameter", 'fn f(ys List[Int]) Int\n  ys(-1)\n', 2, "before the start of `ys`"),
 ("a parameter has no known length", 'fn f(ys List[Int]) Int\n  ys(5)\nprintln(f(List(1)))\n', 1, "out of range"),
 ("an Array still checks", 'a = Array(1, 2)\nprintln(a(2))\n', 2, "past the end of `a`"),
 ("rebinding the name makes the length unknown", 'ys = List(1)\nys = ys + List(2)\nprintln(ys(1))\n', 0, "2"),
 ("a ref argument makes the length unknown", 'zs = List(1)\nfn grow(ref l List[Int]) Unit\n  l = l + List(1)\ngrow(ref zs)\nprintln(zs(1))\n', 0, "1"),
 ("+= makes the length unknown", 'ws = List(1, 2)\nws += 3\nprintln(ws(2))\n', 0, "3"),
 ("another function's list of the same name does not matter", 'fn a() Int\n  q = List(1, 2, 3)\n  q(2)\nfn b() Int\n  q = List(1)\n  q(0)\nprintln(a() + b())\n', 0, "4"),
 ("a variable index is not checked here", 'xs = List(1, 2)\ni = 5\nprintln(xs(i))\n', 1, "out of range"),
 ("a comprehension has no known length", 'xs = List(x * 2 for x in 0..3)\nprintln(xs(2))\n', 0, "4"),
]
fails = []
for name, src, rc_want, word in CASES:
    for gc in (False, True):
        p = os.path.join(D, "t.mxi")
        open(p, "w").write(src)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check" if rc_want == 2 else "run", p], cwd=ROOT, capture_output=True, text=True)
        o = r.stdout + r.stderr
        good = ((r.returncode != 0) if rc_want == 2 else (r.returncode == rc_want)) and word in o
        print(("ok    " if good else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if good else f"  -> rc={r.returncode} {o.strip()[:300]!r}"))
        if not good: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
