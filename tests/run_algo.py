"""The `algo` package: in-place algorithms written as `mutable` blocks.  Run: python3 tests/run_algo.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(src, flags=()):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "run", *flags, f.name], cwd=ROOT, capture_output=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, (r.stdout + r.stderr).decode()

CASES = [
 ("quicksort", 'import algo\nprintln(algo.quicksort((5, 2, 9, 1, 5, 6)))\nprintln(algo.quicksort((9, 8, 7, 6, 5, 4, 3, 2, 1)))\nprintln(algo.quicksort((7,)))\n', 0, "Array(1, 2, 5, 5, 6, 9)\nArray(1, 2, 3, 4, 5, 6, 7, 8, 9)\nArray(7)"),
 ("heapsort", 'import algo\nprintln(algo.heapsort((5, 2, 9, 1, 5, 6)))\nprintln(algo.heapsort(("pear", "apple", "fig")))\n', 0, 'Array(1, 2, 5, 5, 6, 9)\nArray("apple", "fig", "pear")'),
 ("sieve", 'import algo\nflags Array[Bool][12] = fill(true)\nprintln(algo.sieve(flags))\nprintln(flags(0))\n', 0, "Array(false, false, true, true, false, true, false, true, false, false, false, true)\ntrue"),
 ("components", 'import algo\nprintln(algo.components((0, 1, 2, 3, 4), List((0, 1), (3, 4), (1, 0))))\n', 0, "Array(0, 0, 2, 3, 3)"),
 ("both sorts agree with sort on 40 pseudo-random arrays", 'import algo\nfn next(s Int) Int = (s * 1103515245 + 12345) % 2147483648\nfn make(seed Int) Array[Int][12]\n  mutable\n    out Array[Int][12] = fill(0)\n    s = seed\n    for i in 0..<12\n      s = next(s)\n      out(i) = s % 20\n    out\nbad = 0\nfor seed in 1..40\n  a = make(seed)\n  want = a |> sort() |> collect()\n  q = algo.quicksort(a) |> collect()\n  h = algo.heapsort(a) |> collect()\n  if q ~= want or h ~= want\n    bad@1 += 1\nprintln("bad ${bad}")\n', 0, "bad 0"),
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
