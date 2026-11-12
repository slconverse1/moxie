"""par_map and par_traverse: bounded parallel map, results in input order, the earliest error, the fiber count.
Each program runs in both dialects with the same output.  Run: python3 tests/run_parallel.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLOW = 'fn slow_double(n Int) Int\n  sleep((6 - n) * 10ms)\n  n * 2\n'
CHECK = 'fn check(n Int) Result[Int, String]\n  sleep((6 - n) * 10ms)\n  when n % 2 == 0\n    true -> Err("even ${n}")\n    false -> Ok(n)\n'
PMA = 'fn ok_n(n Int) Result[Int, String]\n  sleep((6 - n) * 10ms)\n  Ok(n)\nfn bad(m String) Result[Int, String]\n  sleep(10ms)\n  Err(m)\nfn add3(a Int, b Int, c Int) Int\n  a + b + c\n'
CASES = [
 ("par_map keeps input order", SLOW + 'println(List(1, 2, 3, 4, 5) |> par_map(slow_double, limit: 3))\n', "List(2, 4, 6, 8, 10)"),
 ("par_map of nothing", SLOW + 'println(par_map(slow_double, List(), limit: 2))\n', "List()"),
 ("par_map runs at most limit at once", 'lanes = 3\nlive = Atom[Int](0)\npeak = Atom[Int](0)\nfn work(n Int) Int\n  now = swap(live, _ + 1)\n  _ = swap(peak, max(_, now))\n  sleep(10ms)\n  _ = swap(live, _ - 1)\n  n\nr = List(1, 2, 3, 4, 5, 6, 7, 8) |> par_map(work, limit: lanes)\nprintln("${r} peak ${@peak}")\n', "List(1, 2, 3, 4, 5, 6, 7, 8) peak 3"),
 ("par_map really overlaps", 'peak = Atom[Int](0)\nlive = Atom[Int](0)\nfn work(n Int) Int\n  now = swap(live, _ + 1)\n  _ = swap(peak, max(_, now))\n  sleep(10ms)\n  _ = swap(live, _ - 1)\n  n\n_ = par_map(work, List(1, 2, 3, 4), limit: 4)\nprintln(@peak)\n', "4"),
 ("par_traverse gives Ok in order", CHECK + 'println(par_traverse(check, List(1, 3, 5), limit: 2))\n', "Ok(List(1, 3, 5))"),
 ("par_traverse gives the earliest error", CHECK + 'println(par_traverse(check, List(1, 2, 3, 4, 5), limit: 5))\nprintln(par_traverse(check, List(1, 2, 3, 4, 5), limit: 1))\n', 'Err("even 2")\nErr("even 2")'),
 ("par_traverse stops starting items after an error", 'ran = Atom[Int](0)\nfn work(n Int) Result[Int, String]\n  _ = swap(ran, _ + 1)\n  when n == 1\n    true -> Err("one")\n    false -> Ok(n)\nprintln(par_traverse(work, List(1, 2, 3, 4, 5, 6), limit: 1))\nprintln(@ran)\n', 'Err("one")\n1'),
 ("par_map_all combines three checks", PMA + 'println(par_map_all(add3, fn () -> ok_n(1), fn () -> ok_n(2), fn () -> ok_n(3), limit: 3))\n', "Ok(6)"),
 ("par_map_all gives every error in argument order", PMA + 'println(par_map_all(add3, fn () -> bad("first"), fn () -> ok_n(2), fn () -> bad("third"), limit: 3))\n', 'Err(List("first", "third"))'),
 ("par_map_all with a limit of one runs them one by one", PMA + 'println(par_map_all(add3, fn () -> ok_n(1), fn () -> bad("two"), fn () -> ok_n(3), limit: 1))\n', 'Err(List("two"))'),
 ("par_map_all really overlaps", 'peak = Atom[Int](0)\nlive = Atom[Int](0)\nfn work(n Int) Result[Int, String]\n  now = swap(live, _ + 1)\n  _ = swap(peak, max(_, now))\n  sleep(10ms)\n  _ = swap(live, _ - 1)\n  Ok(n)\nfn pair(a Int, b Int) Int\n  a + b\n_ = par_map_all(pair, fn () -> work(1), fn () -> work(2), limit: 2)\nprintln(@peak > 1)\n', "true"),
 ("par_map inside a loop", SLOW + 'for i in 1..=2\n  println(par_map(slow_double, List(i, i + 1), limit: 2))\n', "List(2, 4)\nList(4, 6)"),
 ("retry around par_traverse", 'n = Atom[Int](0)\nfn work(x Int) Result[Int, Error]\n  k = swap(n, _ + 1)\n  when k < 3\n    true -> Err(Error(TIMED_OUT, "slow"))\n    false -> Ok(x)\nfn once() Result[List[Int], Error]\n  par_traverse(work, List(1), limit: 1)\nprintln(retry(5, 1ms, once))\n', "Ok(List(1))"),
]
BAD = [
 ("par_map needs a limit", 'x = par_map((n) -> n, List(1))\n', "`par_map` needs `limit:`"),
 ("par_map limit must be constant", 'fn f(k Int) List[Int]\n  par_map((n) -> n, List(1), limit: k)\n', "needs `limit:` with a constant"),
 ("par_traverse needs a limit", 'x = par_traverse((n) -> Ok(n), List(1))\n', "`par_traverse` needs `limit:`"),
 ("par_map limit of zero", 'x = par_map((n) -> n, List(1), limit: 0)\n', "needs `limit:` with a constant number of 1 or more"),
 ("par_map_all needs a limit", PMA + 'x = par_map_all(add3, fn () -> ok_n(1), fn () -> ok_n(2), fn () -> ok_n(3))\n', "`par_map_all` needs `limit:`"),
 ("par_map_all takes functions, not results", PMA + 'x = par_map_all(add3, ok_n(1), ok_n(2), ok_n(3), limit: 3)\n', "`par_map_all` can't take"),
 ("par_map_all checks must give a Result", PMA + 'fn plain() Int\n  1\nx = par_map_all(add3, fn () -> ok_n(1), fn () -> ok_n(2), fn () -> plain(), limit: 3)\n', "`par_map_all` can't take"),
 ("par_map_all function arity", PMA + 'x = par_map_all((a, b) -> a + b, fn () -> ok_n(1), fn () -> ok_n(2), fn () -> ok_n(3), limit: 3)\n', "takes 2 parameters"),
 ("par_map takes a function", 'x = par_map(5, List(1), limit: 2)\n', "`par_map` can't take"),
]
POOLS = [("par_map counts its limit as fibers", SLOW + 'r = par_map(slow_double, List(1, 2), limit: 3)\nprintln(r)\n', ["par_map@", "(limit 3)", "largest possible fiber count: 4"])]
POOLS.append(("par_map_all counts its limit as fibers", PMA + 'println(par_map_all(add3, fn () -> ok_n(1), fn () -> ok_n(2), fn () -> ok_n(3), limit: 3))\n', ["par_map_all@", "(limit 3)"]))
POOLS.append(("limit from constants and arithmetic is counted", 'base = 2\nlanes = base * 2 + 1\nfn dbl(n Int) Int\n  n * 2\nprintln(par_map(dbl, List(1, 2, 3), limit: lanes))\nprintln(par_map(dbl, List(1, 2, 3), limit: 2 + 2))\n', ["(limit 5)", "(limit 4)", "largest possible fiber count: 10"]))
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
for name, src, wants in POOLS:
    rc, o = run("pools", src)
    ok = rc == 0 and all(w in o for w in wants)
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  {o[:300]!r}"))
    if not ok:
        fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
