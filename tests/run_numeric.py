"""Mixed numbers: a value widens implicitly only when every value of its type fits the other side; else a `cast`.  Run: python3 tests/run_numeric.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(src, gc=False):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
CASES = [
 ("Int8 with Int16 widens", "a Int8 = 6\nb Int16 = 6\nc UInt8 = 6\nd Int64 = 6\ne UInt64 = 6\nx Double = 2.5\nprintln(a + b)\n", "12"),
 ("UInt8 with Int16 widens", "a Int8 = 6\nb Int16 = 6\nc UInt8 = 6\nd Int64 = 6\ne UInt64 = 6\nx Double = 2.5\nprintln(c + b)\n", "12"),
 ("Int16 with Int64 widens", "a Int8 = 6\nb Int16 = 6\nc UInt8 = 6\nd Int64 = 6\ne UInt64 = 6\nx Double = 2.5\nprintln(b + d)\n", "12"),
 ("a literal takes the other side's type", "a Int8 = 6\nb Int16 = 6\nc UInt8 = 6\nd Int64 = 6\ne UInt64 = 6\nx Double = 2.5\nprintln(a + 1)\nprintln(x * 2)\n", "7\n5.0"),
 ("suffix literals of different widths widen", "println(6i8 + 6i16)\n", "12"),
 ("Int8 with UInt8 needs a cast", "a Int8 = 6\nb Int16 = 6\nc UInt8 = 6\nd Int64 = 6\ne UInt64 = 6\nx Double = 2.5\nbad = a + c\n", "neither type holds every value of the other"),
 ("suffix literals Int8 and UInt8", "bad = 6i8 + 6u8\n", "cannot apply `+` to `Int8` and `UInt8`"),
 ("Int64 with UInt64 needs a cast", "a Int8 = 6\nb Int16 = 6\nc UInt8 = 6\nd Int64 = 6\ne UInt64 = 6\nx Double = 2.5\nbad = d + e\n", "cannot apply `+` to `Int64` and `UInt64`"),
 ("a comparison is checked too", "a Int8 = 6\nb Int16 = 6\nc UInt8 = 6\nd Int64 = 6\ne UInt64 = 6\nx Double = 2.5\nbad = a < c\n", "neither type holds every value of the other"),
 ("Int64 with Double needs a cast", "a Int8 = 6\nb Int16 = 6\nc UInt8 = 6\nd Int64 = 6\ne UInt64 = 6\nx Double = 2.5\nbad = d * x\n", "does not fit a `Double` exactly"),
 ("an inferred Int with Double needs a cast", "n = 5\nx = 2.5\nbad = n * x\n", "convert on purpose (`cast[Double](x)`)"),
 ("a call returning Int with Double needs a cast", "x = 2.5\nbad = len(List(1)) * x\n", "does not fit a `Double` exactly"),
 ("Int32 with Double is exact", "n Int32 = 7\nx = 2.5\nprintln(n * x)\n", "17.5"),
 ("Int16 with Double is exact", "n Int16 = 7\nx = 2.5\nprintln(x + n)\n", "9.5"),
 ("a cast makes Int with Double fine", "n = 5\nx = 2.5\nprintln(cast[Double](n) * x)\n", "12.5"),
 ("a literal expression with Double", "x = 2.5\nprintln(x * (2 + 3))\n", "12.5"),
 ("a bounded Int with Double", "n Int[1..10] = 4\nx = 2.5\nprintln(n * x)\n", "10.0"),
]
fails = []
for name, src, want in CASES:
    for gc in (False, True):
        rc, out = run(src, gc)
        good = want in out
        print(("ok    " if good else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if good else f"  -> rc={rc} {out.strip()[:300]!r}"))
        if not good:
            fails.append(name)
print(f"{len(CASES) * 2 - len(fails)} of {len(CASES) * 2} passed")
sys.exit(1 if fails else 0)
