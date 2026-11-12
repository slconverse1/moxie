"""Run-time backstops: what the checker can't see ends the program with a message, never silently and never as a Python crash.
The checker is switched off here so the program reaches the run time.  Run: python3 tests/run_backstops.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVER = '''
import sys
sys.path.insert(0, %r)
from moxie import check
check.check_program = lambda *a, **k: []
from moxie import __main__ as M
sys.argv = ["moxie"] + sys.argv[1:]
sys.exit(M.main())
''' % ROOT

BIG = 'fn big[N where N > 2](e: Array[Int][N]) Int\n  e(0)\n'
CASES = [
 ("a wrong argument to a package function names the parameter", 'import stats\nprintln(stats.mean("abc"))\n', "parameter `xs` is `Array[Double][N]`, but the argument is a `String`"),
 ("a wrong argument to your own function", 'fn twice(n: Int) Int\n  n * 2\nprintln(twice("x"))\n', "parameter `n` is `Int`, but the argument is a `String`"),
 ("a where constraint on a literal array", BIG + 'println(big((1, 2)))\n', "fails the `where` constraint"),
 ("a where constraint on a built array", BIG + 'xs = List(1, 2) |> to_stream() |> collect()\nprintln(big(cast[Array[Int]](xs)))\n', "fails the `where` constraint"),
 ("a builtin given the wrong type", 'println(sqrt("a"))\n', "type error at run time"),
 ("a string method on a number", 'println(upper(3))\n', "type error at run time"),
]
fails = []
for name, src, word in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        r = subprocess.run([sys.executable, "-c", DRIVER] + (["--gc"] if gc else []) + ["run", f.name], capture_output=True, text=True, cwd=ROOT)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        ok = r.returncode != 0 and word in o and "Traceback" not in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[-300:]}"))
        if not ok:
            fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
