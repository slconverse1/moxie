"""Compile-time evaluation: pure functions run by the compiler on constant arguments.  Run: python3 tests/run_cteval.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FIB = 'fn fib(n: Int) Int:\n  if n < 2: n else: fib(n - 1) + fib(n - 2)\n'
PORT = 'fn port(n: Int) Int:\n  assert(n <= 65535, "port too large")\n  n\n'
DEEP = 'fn deep(n: Int) Int:\n  deep(n + 1)\n'
IMPURE = 'fn noisy(n: Int) Int:\n  println(n)\n  n\n'
BAD = [
 ("a size from a function", FIB + 'a: Array[Int][fib(5)] = Array(1, 2, 3)\n', "expected `Array[Int][5]`, found `Array[Int][3]`"),
 ("a constant binding as a size", FIB + 'N = fib(6)\nb: Array[Int][N] = Array(1, 2)\n', "expected `Array[Int][8]`, found `Array[Int][2]`"),
 ("a constant built from constants", FIB + 'N = fib(4) * 2\nb: Array[Int][N + 1] = Array(1)\n', "expected `Array[Int][7]`, found `Array[Int][1]`"),
 ("an abort is a compile error", PORT + 'p = port(99999)\n', "evaluating `port(99999)` at compile time aborts: assertion failed"),
 ("a runaway recursion", DEEP + 'x = deep(0)\n', "recursed too deeply"),
 ("a function in a type-level number", FIB + 'type alias Fixed[T] = when T:\n  X -> Array[Int][fib(4)]\nc: Fixed[Int] = Array(1)\n', "expected `Array[Int][3]`, found `Array[Int][1]`"),
]
GOOD = [
 ("a size from a function runs", FIB + 'a: Array[Int][fib(5)] = Array(1, 2, 3, 4, 5)\nprintln(a(4))\n', "5"),
 ("a good constant", PORT + 'p = port(8080)\nprintln(p)\n', "8080"),
 ("an impure function is left to run time", IMPURE + 'x = noisy(3)\nprintln("ok")\n', "3"),
 ("a call with a variable is not evaluated", PORT + 'fn f(n: Int) Int:\n  port(n)\nprintln(f(1))\n', "1"),
]
fails = []


def run(cmd, src, toml=None):
    d = tempfile.mkdtemp()
    open(os.path.join(d, "main.mxi"), "w").write(src)
    if toml:
        open(os.path.join(d, "Moxie.toml"), "w").write(toml)
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, os.path.join(d, "main.mxi")], cwd=ROOT, capture_output=True, timeout=120)
    return r.returncode, r.stdout.decode() + r.stderr.decode()


def report(name, ok, o):
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  {o[:400]!r}"))
    if not ok:
        fails.append(name)


for name, src, want in BAD:
    rc, o = run("check", src)
    report(name, want in o, o)
for name, src, want in GOOD:
    rc, o = run("run", src)
    report(name, rc == 0 and want in o, o)
rc, o = run("check", FIB + 'a: Array[Int][fib(12)] = Array(1)\n', '[program]\neval_fuel = 100\n')
report("eval_fuel stops a slow call", "did not finish in 100 steps" in o, o)
rc, o = run("check", FIB + 'a: Array[Int][fib(12)] = Array(1)\n', '[program]\neval_fuel = 0\n')
report("eval_fuel must be 1 or more", "eval_fuel must be a whole number" in o, o)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
