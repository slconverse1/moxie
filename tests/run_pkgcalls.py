"""Calls into an imported package are checked at compile time from the package's signatures.  Run: python3 tests/run_pkgcalls.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

A = 'import stats\na: Array[Double] = (1.0, 2.0, 3.0)\nb: Array[Double] = (2.0, 4.0, 7.0)\nc: Array[Double] = (1.0, 2.0)\n'
LIB = 'export fn twice(n: Int) Int:\n  n * 2\n\nexport fn name_of(s: String, k: Int = 1) String:\n  s\n\nexport tuple Box:\n  v: Int\n\nexport fn unbox(b: Box) Int:\n  b.v\n\nexport fn mk(n: Int) Box:\n  Box(v: n)\n'

# (name, source, how, text, library source or None)
CASES = [
 ("a String where the package wants an array", A + 'println(stats.mean("abc"))\n', "fail", "mismatched types", None),
 ("two arrays of different sizes", A + 'println(stats.covariance(a, c))\n', "fail", "Array[Double][2]", None),
 ("a result used as the wrong type", A + 'x: String = stats.mean(a)\n', "fail", "expected `String`, found `Double`", None),
 ("a piped call is checked", A + 'println("abc" |> stats.mean())\n', "fail", "mismatched types", None),
 ("an import with as is checked", 'import stats as s\nprintln(s.mean(5))\n', "fail", "mismatched types", None),
 ("from-import names are checked", 'import stats (mean)\nprintln(mean("abc"))\n', "fail", "mismatched types", None),
 ("right calls still run", A + 'println(stats.mean(a))\nprintln(stats.covariance(a, b))\nprintln(a |> stats.mean())\nprintln(stats.fit_line(a, b))\n', "run", "Ok(", None),
 ("a literal tuple is accepted", 'import stats\nprintln(stats.mean((1.0, 2.0, 3.0)))\n', "run", "2", None),
 ("a local package: wrong argument", 'import lib\nprintln(lib.twice("x"))\n', "fail", "expected `Int`, found `String`", LIB),
 ("a local package: right argument", 'import lib\nprintln(lib.twice(4))\nprintln(lib.name_of("a"))\nprintln(lib.name_of("a", 2))\n', "run", "8\na\na", LIB),
 ("a local package: too many arguments", 'import lib\nprintln(lib.twice(1, 2))\n', "fail", "takes 1 argument", LIB),
 ("a package type is the package's own", 'import lib\nprintln(lib.unbox(lib.mk(3)))\n', "run", "3", LIB),
]

fails = []
for name, src, how, word, lib in CASES:
    for gc in (False, True):
        if how == "nogc-fail" and gc:
            continue
        d = tempfile.mkdtemp()
        if lib is not None:
            open(os.path.join(d, "lib.mxi"), "w").write(lib)
        main = os.path.join(d, "main.mxi")
        open(main, "w").write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", main]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        o = r.stdout + r.stderr
        want_fail = how in ("fail", "nogc-fail")
        ok = ((r.returncode != 0) if want_fail else (r.returncode == 0)) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:300]}"))
        if not ok:
            fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
