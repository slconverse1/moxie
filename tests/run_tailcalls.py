"""Tail calls run in constant stack and in time proportional to the depth, in both dialects: a self-call of any function, a clause function,
a mutual tail call; and a recursion too deep for the stack is a diagnostic, not a Python crash.  Run: python3 tests/run_tailcalls.py"""
import subprocess, sys, tempfile, os, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [
 ("self tail call, no `tailrec`", "fn count(n Int, acc Int) Int\n  when n\n    0 -> acc\n    else count(n - 1, acc + 1)\nprintln(count(20000, 0))\n", "20000"),
 ("clause function", "fn count(0, acc Int) Int = acc\nfn count(n, acc) = count(n - 1, acc + 1)\nprintln(count(20000, 0))\n", "20000"),
 ("mutual recursion", "forward fn is_odd(n Int) Bool\nfn is_even(n Int) Bool\n  if n == 0 then true else is_odd(n - 1)\nfn is_odd(n Int) Bool\n  if n == 0 then false else is_even(n - 1)\nprintln(is_even(6000))\n", "true"),
 ("a non-tail call still works", "fn total(n Int) Int\n  when n\n    0 -> 0\n    else n + total(n - 1)\nprintln(total(3000))\n", "4501500"),
 ("tail call after a non-tail one", "fn f(n Int) Int\n  when n\n    0 -> 0\n    else\n      if n % 1000 == 0 then f(n - 1) + 1 else f(n - 1)\nprintln(f(5000))\n", "5"),
]
bad = 0
for gc in (False, True):
    for name, src, want in CASES:
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.mxi")
            open(p, "w").write(src)
            t = time.time()
            r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", p], cwd=ROOT, capture_output=True, text=True, timeout=120)
            dt = time.time() - t
        ok = r.stdout.strip() == want and dt < 20
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + f"  {dt:.1f}s" + ("" if ok else f"  got {r.stdout.strip()!r} {r.stderr.strip()[:200]!r}"))
        bad += not ok
src = "fn depth(n Int) Int\n  when n\n    0 -> 0\n    else 1 + depth(n - 1)\nprintln(depth(1000000))\n"
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "t.mxi")
    open(p, "w").write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "run", p], cwd=ROOT, capture_output=True, text=True, timeout=120)
ok = "stack overflow" in r.stderr and "Traceback" not in r.stderr
print(("ok    " if ok else "FAIL  ") + "a runaway recursion is a stack overflow diagnostic")
bad += not ok
print(f"{bad} failed")
sys.exit(1 if bad else 0)
