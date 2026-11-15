"""Refined parameters: `where` conditions proved at each call.  Run: python3 tests/run_refined.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()
GET = 'fn get(xs List[Int], i Int where i >= 0 and i < len(xs)) Int\n  xs(i)\n'
POS = 'fn half(n Int where n > 0) Int\n  n / 2\n'
OK, BAD, RUN = 0, 2, 1
CASES = [
 ("a literal call that holds", GET + 'println(get(List(1, 2, 3), 1))\n', OK, "2"),
 ("checked by if", GET + 'fn f(xs List[Int], i Int) Int\n  if i >= 0 and i < len(xs) then get(xs, i) else -1\nprintln(f(List(1, 2), 1))\n', OK, "2"),
 ("checked by an early return", GET + 'fn f(xs List[Int], i Int) Int\n  return -1 if i < 0 or i >= len(xs)\n  get(xs, i)\nprintln(f(List(1, 2), 5))\n', OK, "-1"),
 ("checked by elif and else", POS + 'fn f(n Int) Int\n  if n <= 0\n    0\n  elif n > 100\n    100\n  else\n    half(n)\nprintln(f(8))\n', OK, "4"),
 ("a for range proves the index", GET + 'fn f(xs List[Int]) Int\n  for i in 0..len(xs)\n    println(get(xs, i))\n  0\nprintln(f(List(1, 2, 3)))\n', OK, "3"),
 ("the same where in the caller", GET + 'fn f(xs List[Int], i Int where i >= 0 and i < len(xs)) Int\n  get(xs, i)\nprintln(f(List(4, 5), 1))\n', OK, "5"),
 ("a name bound to a linear expression", GET + 'fn f(xs List[Int]) Int\n  n = len(xs)\n  if n > 0 then get(xs, n - 1) else 0\nprintln(f(List(1, 2, 9)))\n', OK, "9"),
 ("a bounded integer type is a fact", 'fn half(n Int where n > 0) Int\n  n / 2\nfn f(k Int[1..=10]) Int\n  half(k)\nprintln(f(8))\n', OK, "4"),
 ("a named bounded type is a fact", 'type alias Pct = Int[0..=100]\n' + POS + 'fn f(k Pct) Int\n  half(k + 1)\nprintln(f(9))\n', OK, "5"),
 ("a bound that allows zero is not enough", 'type alias Pct = Int[0..=100]\n' + POS + 'fn f(k Pct) Int\n  half(k)\n', BAD, "can\'t prove"),
 ("an unchecked call is an error", GET + 'fn f(xs List[Int], i Int) Int\n  get(xs, i)\n', BAD, "can't prove"),
 ("an index one past the end", GET + 'fn f(xs List[Int]) Int\n  get(xs, len(xs))\n', BAD, "can never be true"),
 ("half a check is not enough", GET + 'fn f(xs List[Int], i Int) Int\n  if i >= 0 then get(xs, i) else 0\n', BAD, "can't prove"),
 ("a constant that fails", GET + 'fn f() Int\n  get(List(1, 2), 2)\n', BAD, "can never be true"),
 ("a fact dies when the name is rebound", GET + 'fn f(xs List[Int], i Int) Int\n  if i >= 0 and i < len(xs)\n    i = 7\n    get(xs, i)\n  else\n    0\n', BAD, "can't prove"),
 ("a fact from a `+=` target is dropped", POS + 'fn f(n Int) Int\n  k = 5\n  k += n\n  half(k - 5)\n', BAD, "can't prove"),
 ("a function value is checked at run time", GET + 'f (List[Int], Int) -> Int = get\nprintln(f(List(1, 2), 5))\n', RUN, "requires failed"),
 ("no refinement means no cost", 'fn add(a Int, b Int) Int\n  a + b\nprintln(add(1, 2))\n', OK, "3"),
]
fails = []
for name, src, want, word in CASES:
    for gc in (False, True):
        p = os.path.join(D, "t.mxi")
        open(p, "w").write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check" if want == BAD else "run", p]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        o = r.stdout + r.stderr
        good = ((r.returncode != 0) if want in (BAD, RUN) else (r.returncode == 0)) and word in o
        print(("ok    " if good else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if good else f"  -> rc={r.returncode} {o.strip()[:300]!r}"))
        if not good: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
