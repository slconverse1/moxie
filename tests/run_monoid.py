"""Semigroup, Monoid, the wrapper tuples, fold_all and fold_map.  Each program runs in both dialects with the same output.
Run: python3 tests/run_monoid.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATS = 'tuple Stats deriving show\n  count Int\n  total Int\nimpl Semigroup for Stats\n  fn combine(self, other Stats) Stats\n    Stats(count: self.count + other.count, total: self.total + other.total)\nimpl Monoid for Stats\n  static fn empty() Stats = Stats(count: 0, total: 0)\n'
CASES = [
 ("strings", 'println(fold_all(List("a", "b", "c")))\nprintln("x".combine("y"))\n', "abc\nxy"),
 ("lists", 'println(fold_all(List(List(1), List(2, 3))))\n', "List(1, 2, 3)"),
 ("Sum and Product", 'println(fold_all(List(Sum(1), Sum(2), Sum(3))))\nprintln(fold_all(List(Product(2), Product(3), Product(4))))\n', "Sum(value: 6)\nProduct(value: 24)"),
 ("Sum of doubles", 'println(fold_all(List(Sum(1.5), Sum(2.5))))\n', "Sum(value: 4.0)"),
 ("All and Any", 'println(fold_all(List(All(true), All(false))))\nprintln(fold_all(List(Any(false), Any(true))))\n', "All(value: false)\nAny(value: true)"),
 ("Min and Max are semigroups", 'println(Min(3).combine(Min(2)))\nprintln(Max(3).combine(Max(9)))\nprintln(fold_map(fn (n) -> Min(n), List(4, 2, 8)))\n', "Min(value: 2)\nMax(value: 9)\nMin(value: 2)"),
 ("fold_map", 'println(fold_map(fn (w) -> List(len(w)), List("a", "bb", "ccc")))\n', "List(1, 2, 3)"),
 ("your own type", STATS + 'println(fold_map(fn (n) -> Stats(count: 1, total: n), List(4, 6, 8)))\n', "Stats(count: 3, total: 18)"),
 ("an empty input gives empty", STATS + 'println(fold_all[Stats](List()))\nprintln(fold_all[String](List()) == "")\n', "Stats(count: 0, total: 0)\ntrue"),
 ("a generic function over Monoid", STATS + 'fn twice[T Monoid](x T) T\n  x.combine(x)\nprintln(twice(Stats(count: 1, total: 5)))\nprintln(twice("ab"))\n', "Stats(count: 2, total: 10)\nabab"),
 ("a program may declare its own Sum", 'tuple Sum\n  n Int\nprintln(Sum(n: 1))\n', "Sum(n: 1)"),
]
BAD = [
 ("a bound is checked", 'fn g[T Monoid](x T) T\n  x\nprintln(g(5))\n', "`Int` doesn't implement `Monoid`"),
 ("fold_all gives the item type", 'n Int = fold_all(List("a", "b"))\n', "expected `Int`, found `String`"),
]
fails = []


def run(cmd, src, gc=False):
    f = os.path.join(tempfile.mkdtemp(), "main.mxi")
    open(f, "w").write(src)
    r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + [cmd, f], cwd=ROOT, capture_output=True, timeout=60)
    return r.returncode, r.stdout.decode() + r.stderr.decode()


for name, src, want in CASES:
    a, b = run("run", src), run("run", src, True)
    ok = a[0] == 0 and a == b and a[1].strip() == want
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  {a[1][:300]!r} / {b[1][:200]!r}"))
    if not ok:
        fails.append(name)
for name, src, want in BAD:
    rc, o = run("check", src)
    ok = rc != 0 and want in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  {o[:300]!r}"))
    if not ok:
        fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
