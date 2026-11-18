"""`fill(value)` over a declared Array / MultiArray.  Run: python3 tests/run_fill.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(src, flags=()):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "run", *flags, f.name], cwd=ROOT, capture_output=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, (r.stdout + r.stderr).decode()

CASES = [
 ("fill an Array", 'a Array[Int][3] = fill(7)\nprintln(a)\n', 0, "Array(7, 7, 7)"),
 ("fill converts the element type", 'b Array[Double][2] = fill(1.5)\nprintln(b)\n', 0, "Array(1.5, 1.5)"),
 ("fill a MultiArray", 'm MultiArray[Int][2, 3] = fill(0)\nprintln(len(m))\n', 0, "6"),
 ("fill needs a size", 'x Array[Int] = fill(0)\nprintln(x)\n', 1, "needs a size"),
]
fails = []
for name, src, rc_want, want in CASES:
    for flags in ((), ("--gc",)):
        rc, out = run(src, flags)
        ok = rc == rc_want and want in out
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if flags else "") + ("" if ok else f"  rc={rc} {out[:200]!r}"))
        if not ok: fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
