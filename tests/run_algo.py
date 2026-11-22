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
 ("merge_sort, counting_sort, prefix_sums, rotate, shuffle, search, permutations, knapsack", 'import algo\nprintln(algo.merge_sort((5, 2, 9, 1, 5, 6)))\nprintln(algo.counting_sort((3, 1, 2, 3, 0), 4))\nprintln(algo.binary_search((1, 3, 5, 7), 5))\nprintln(algo.binary_search((1, 3, 5, 7), 4))\nprintln(algo.prefix_sums((1, 2, 3, 4)))\nprintln(algo.rotate((1, 2, 3, 4, 5), 2))\nprintln(algo.rotate((1, 2, 3, 4, 5), -1))\nprintln(algo.shuffle((1, 2, 3, 4, 5), 42))\nprintln(algo.next_permutation((1, 2, 3)))\nprintln(algo.next_permutation((3, 2, 1)))\nprintln(algo.knapsack(List(1, 3, 4, 5), List(1, 4, 5, 7), 7))\n', 0, "Array(1, 2, 5, 5, 6, 9)\nArray(0, 1, 2, 3, 3)\nOk(2)\nErr(Error(code: 4, message: \"not found\"))\nArray(1, 3, 6, 10)\nArray(3, 4, 5, 1, 2)\nArray(5, 1, 2, 3, 4)\nArray(1, 4, 3, 5, 2)\nOk(Array(1, 3, 2))\nErr(Error(code: 4, message: \"last permutation\"))\n9"),
 ("the new algorithms agree with plain code on 40 pseudo-random arrays", 'import algo\nfn next(s Int) Int = (s * 1103515245 + 12345) % 2147483648\nfn make(seed Int) Array[Int][12]\n  mutable\n    out Array[Int][12] = fill(0)\n    s = seed\n    for i in 0..<12\n      s = next(s)\n      out(i) = s % 20\n    out\nbad = 0\nfor seed in 1..40\n  a = make(seed)\n  want = a |> sort() |> collect()\n  if algo.merge_sort(a) |> collect() ~= want\n    bad@1 += 1\n  if algo.counting_sort(a, 20) |> collect() ~= want\n    bad@1 += 1\n  if algo.shuffle(a, seed) |> sort() |> collect() ~= want\n    bad@1 += 1\n  if algo.shuffle(a, seed) ~= algo.shuffle(a, seed)\n    bad@1 += 1\n  sums = algo.prefix_sums(a) |> collect()\n  by_scan = a |> scan(0, _1 + _2) |> collect()\n  if sums ~= by_scan\n    bad@1 += 1\n  r = algo.rotate(a, seed)\n  back = algo.rotate(r, 0 - seed)\n  if back ~= a\n    bad@1 += 1\n  sorted_a = algo.merge_sort(a)\n  for x in a\n    if algo.binary_search(sorted_a, x) |> is_err()\n      bad@1 += 1\nprintln("bad ${bad}")\n', 0, "bad 0"),
 ("next_permutation walks all 24 arrangements of four items", 'import algo\nfn walk(start Array[Int][4]) Int\n  mutable\n    cur = start\n    seen = 1\n    for true\n      when algo.next_permutation(cur)\n        Ok(nx) ->\n          cur = nx\n          seen += 1\n        Err(_) -> break\n    seen\nprintln("${walk((1, 2, 3, 4))}")\n', 0, "24"),
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
