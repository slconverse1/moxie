"""A size parameter used twice stands for one size: `pair[N](a: Array[Int][N], b: Array[Int][N])`.  Run: python3 tests/run_sizes.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAIR = '''fn pair[N](a: Array[Int][N], b: Array[Int][N]) Int
  len(a) + len(b)
'''

# (name, source, how, text): how is "run" (exit 0 and text in output) or "fail" (nonzero exit and text in output)
CASES = [
 ("an unknown size is a warning that says how to check it at compile time",
  'fn big[N where N > 2](e: Array[Int][N]) Int\n  e(0)\nfn make(n: Int) Array[Int]\n  List(1, 2, 3, 4) |> to_stream() |> take(n) |> collect()\nx = make(2)\nprintln(big(x))\n', "fail", "to check this at compile time instead of runtime"),
 ("and the constraint is checked at run time, not silently",
  'fn big[N where N > 2](e: Array[Int][N]) Int\n  e(0)\nfn make(n: Int) Array[Int]\n  List(1, 2, 3, 4) |> to_stream() |> take(n) |> collect()\nx = make(2)\nprintln(big(x))\n', "fail", "fails the `where` constraint"),
 ("a where constraint on a size is checked at the call",
  'fn big[N where N > 2](e: Array[Int][N]) Int\n  e(0)\nx: Array[Int] = (1, 2)\nprintln(big(x))\n', "fail", "gives `N` the size 2, which fails its `where` constraint"),
 ("a where constraint on a literal array is checked",
  'fn big[N where N > 2](e: Array[Int][N]) Int\n  e(0)\nprintln(big((1, 2)))\n', "fail", "gives `N` the size 2"),
 ("a where constraint that holds is accepted",
  'fn big[N where N > 2](e: Array[Int][N]) Int\n  e(0)\nprintln(big((5, 2, 3)))\n', "run", "5"),
 ("arrays of different sizes, annotated without a size, are an error",
  PAIR + 'x: Array[Int] = (1, 2, 3)\ny: Array[Int] = (1, 2)\nprintln(pair(x, y))\n', "fail", "where `Array[Int][3]` was fixed by another argument"),
 ("arrays of different sizes, annotated with sizes, are an error",
  PAIR + 'x: Array[Int][3] = (1, 2, 3)\ny: Array[Int][2] = (1, 2)\nprintln(pair(x, y))\n', "fail", "needs one type for its type parameters"),
 ("arrays built with Array(...) of different sizes are an error",
  PAIR + 'x = Array(1, 2, 3)\ny = Array(1, 2)\nprintln(pair(x, y))\n', "fail", "fixed by another argument"),
 ("arrays of the same size are fine",
  PAIR + 'x: Array[Int] = (1, 2, 3)\ny: Array[Int] = (4, 5, 6)\nprintln(pair(x, y))\n', "run", "6"),
 ("a size used once may differ between calls",
  'fn count[N](a: Array[Int][N]) Int\n  len(a)\nx: Array[Int] = (1, 2, 3)\ny: Array[Int] = (1, 2)\nprintln("${count(x)} ${count(y)}")\n', "run", "3 2"),
 ("a variadic call is unaffected",
  'fn total(base: Int, numbers: ...Int) Int\n  base + len(numbers)\nprintln("${total(10, 1, 2, 3)} ${total(10, 1)}")\n', "run", "13 11"),
]

fails = []
for name, src, how, word in CASES:
    for gc in (False, True):
        if how == "nogc-fail" and gc:
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        want_fail = how in ("fail", "nogc-fail")
        ok = ((r.returncode != 0) if want_fail else (r.returncode == 0)) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:300]}"))
        if not ok:
            fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
