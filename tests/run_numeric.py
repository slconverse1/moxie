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
 ("assigning Int16 to Int8 needs a cast", "d Int16 = 6\ne Int8 = d\n", "`Int16` does not convert to `Int8`"),
 ("assigning UInt8 to Int8 needs a cast", "k UInt8 = 6\nw Int8 = k\n", "`UInt8` does not convert to `Int8`"),
 ("assigning Int8 to Int16 widens", "m Int8 = 6\nd Int16 = m\nprintln(d)\n", "6"),
 ("assigning UInt8 to Int16 widens", "k UInt8 = 6\nz Int16 = k\nprintln(z)\n", "6"),
 ("a sized Int8 is accepted for a Double parameter", "fn f(x Double) Double = x * 2.0\nm Int8 = 6\nprintln(f(m))\n", "12.0"),
 ("an Int64 is not accepted for a Double parameter", "fn f(x Double) Double = x\nd Int64 = 6\nprintln(f(d))\n", "does not convert to `Double`"),
 ("an Int16 argument for an Int8 parameter", "fn f(x Int8) Int8 = x\nd Int16 = 6\nprintln(f(d))\n", "`Int16` does not convert to `Int8`"),
 ("an Int8 argument for an Int16 parameter", "fn f(x Int16) Int16 = x\nm Int8 = 6\nprintln(f(m))\n", "6"),
 ("a cast narrows on purpose", "d Int16 = 6\ne Int8 = cast[Int8](d)\nprintln(e)\n", "6"),
 ("a literal still fits a narrow type", "e Int8 = 100\nprintln(e)\n", "100"),
 ("a field widens", "tuple Hdr(len UInt8, id Int16)\nfn small() Int8 = 3\nfn wide() UInt8 = 3\nh = Hdr(len: 4, id: 5)\na Int8 = 1\nb Int16 = 2\nxs List[UInt8] = List(1, 2)\nprintln(h.id + a)\n", "6"),
 ("a field of another signedness needs a cast", "tuple Hdr(len UInt8, id Int16)\nfn small() Int8 = 3\nfn wide() UInt8 = 3\nh = Hdr(len: 4, id: 5)\na Int8 = 1\nb Int16 = 2\nxs List[UInt8] = List(1, 2)\nbad = h.len + a\n", "cannot apply `+` to `UInt8` and `Int8`"),
 ("a function result widens", "tuple Hdr(len UInt8, id Int16)\nfn small() Int8 = 3\nfn wide() UInt8 = 3\nh = Hdr(len: 4, id: 5)\na Int8 = 1\nb Int16 = 2\nxs List[UInt8] = List(1, 2)\nprintln(small() + b)\n", "5"),
 ("two function results that do not fit", "tuple Hdr(len UInt8, id Int16)\nfn small() Int8 = 3\nfn wide() UInt8 = 3\nh = Hdr(len: 4, id: 5)\na Int8 = 1\nb Int16 = 2\nxs List[UInt8] = List(1, 2)\nbad = small() + wide()\n", "cannot apply `+` to `Int8` and `UInt8`"),
 ("a list element is checked", "tuple Hdr(len UInt8, id Int16)\nfn small() Int8 = 3\nfn wide() UInt8 = 3\nh = Hdr(len: 4, id: 5)\na Int8 = 1\nb Int16 = 2\nxs List[UInt8] = List(1, 2)\nbad = xs(0) + a\n", "cannot apply `+` to `UInt8` and `Int8`"),
 ("a list element widens", "tuple Hdr(len UInt8, id Int16)\nfn small() Int8 = 3\nfn wide() UInt8 = 3\nh = Hdr(len: 4, id: 5)\na Int8 = 1\nb Int16 = 2\nxs List[UInt8] = List(1, 2)\nprintln(xs(0) + b)\n", "3"),
 ("a field assigned to a narrower type", "tuple Hdr(len UInt8, id Int16)\nfn small() Int8 = 3\nfn wide() UInt8 = 3\nh = Hdr(len: 4, id: 5)\na Int8 = 1\nb Int16 = 2\nxs List[UInt8] = List(1, 2)\ne Int8 = h.id\n", "`Int16` does not convert to `Int8`"),
 ("an inferred binding keeps its width", "tuple Hdr(len UInt8, id Int16)\nfn small() Int8 = 3\nfn wide() UInt8 = 3\nh = Hdr(len: 4, id: 5)\na Int8 = 1\nb Int16 = 2\nxs List[UInt8] = List(1, 2)\nd = wide()\nbad = d + a\n", "cannot apply `+` to `UInt8` and `Int8`"),
 ("a field passed as a narrower parameter", "tuple Hdr(len UInt8, id Int16)\nfn small() Int8 = 3\nfn wide() UInt8 = 3\nh = Hdr(len: 4, id: 5)\na Int8 = 1\nb Int16 = 2\nxs List[UInt8] = List(1, 2)\nfn f(x Int8) Int8 = x\nprintln(f(h.id))\n", "`Int16` does not convert to `Int8`"),
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
