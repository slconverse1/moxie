"""`[T](x)` is `cast[T](x)`.  Run: python3 tests/run_castsugar.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()
CASES = [
 ("same as cast", 'x = 70\nprintln([Int8](x))\nprintln(cast[Int8](x))\n', 0, "70"),
 ("to a bounded alias", 'type alias Pct = Int[0..=100]\nx = 70\np = [Pct](x)\nprintln([Int](p) + 1)\n', 0, "71"),
 ("in a lambda", 'println(List(1, 2).map((n) -> [Int32](n)))\n', 0, "List(1, 2)"),
 ("aborts like cast", 'x = 300\nprintln([Int8](x))\n', 1, "abort"),
 ("a constant that cannot fit is a compile error", 'println([Int8](300))\n', 2, "does not fit"),
 ("a bare type in brackets is an error", 'x = [Int]\n', 2, "converts a value"),
 ("a space before the argument is an error", 'x = [Int] (3)\n', 2, "converts a value"),
 ("generic type arguments still work", 'x = List[Int](1, 2)\nprintln(x)\n', 0, "List(1, 2)"),
]
fails = []
for name, src, want, word in CASES:
    for gc in (False, True):
        p = os.path.join(D, "t.mxi")
        open(p, "w").write(src)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check" if want == 2 else "run", p], cwd=ROOT, capture_output=True, text=True)
        o = r.stdout + r.stderr
        good = ((r.returncode != 0) if want in (1, 2) else (r.returncode == 0)) and word in o
        print(("ok    " if good else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if good else f"  -> rc={r.returncode} {o.strip()[:300]!r}"))
        if not good: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
