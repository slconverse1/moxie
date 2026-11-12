"""Calls into an imported package are checked at compile time from the package's signatures.  Run: python3 tests/run_pkgcalls.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

A = 'import stats\na: Array[Double] = (1.0, 2.0, 3.0)\nb: Array[Double] = (2.0, 4.0, 7.0)\nc: Array[Double] = (1.0, 2.0)\n'
LIB = 'export fn twice(n Int) Int\n  n * 2\n\nexport fn name_of(s String, k Int = 1) String\n  s\n\nexport tuple Box\n  v Int\n\nexport fn unbox(b Box) Int\n  b.v\n\nexport fn mk(n Int) Box\n  Box(v: n)\n'
LIB2 = LIB + 'impl Box\n  export fn plus(self Box, n Int) Int\n    self.v + n\n'

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
 ("a package type is not a String", 'import lib\nprintln(lib.unbox("x"))\n', "fail", "expected `lib.Box`, found `String`", LIB),
 ("this file's own Box is not the package's Box", 'import lib\ntuple Box\n  v Int\nprintln(lib.unbox(Box(v: 1)))\n', "fail", "expected `lib.Box`, found `Box`", LIB),
 ("a field of a package type is read with its type", 'import lib\nn: Int = lib.mk(2).v\nprintln(n)\ns: String = lib.mk(2).v\n', "fail", "expected `String`, found `Int`", LIB),
 ("a missing field of a package type", 'import lib\nprintln(lib.mk(2).nope)\n', "fail", "has no field `nope`", LIB),
 ("a package type in an annotation", 'import lib\nb: lib.Box = lib.mk(5)\nprintln(lib.unbox(b))\nc: lib.Box = 3\n', "fail", "expected `lib.Box`, found `Int`", LIB),
 ("a result holding a package type", 'import stats\na: Array[Double] = (1.0, 2.0, 3.0)\nb: Array[Double] = (2.0, 4.0, 7.0)\nwhen stats.fit_line(a, b)\n  Ok(l) -> println(stats.predict(l, 4.0))\n  Err(e) -> println(e)\n', "run", "9", None),
 ("a package type where a number is wanted", 'import stats\na: Array[Double] = (1.0, 2.0, 3.0)\nb: Array[Double] = (2.0, 4.0, 7.0)\nwhen stats.fit_line(a, b)\n  Ok(l) -> println(stats.predict(3.0, 4.0))\n  Err(e) -> println(e)\n', "fail", "expected `stats.Line`, found `Double`", None),
 ("a package function used as a value is checked", 'import lib\nxs = List("a", "b")\nprintln(xs |> map(lib.twice) |> collect())\n', "fail", "can't take", LIB),
 ("a package function used as a value runs", 'import lib\nxs = List(1, 2)\nprintln(xs |> map(lib.twice) |> collect())\n', "run", "List(2, 4)", LIB),
 ("a method of a package type is checked", 'import lib\nprintln(lib.mk(1).plus("x"))\n', "fail", "expected `Int`, found `String`", LIB2),
 ("a method of a package type runs", 'import lib\nprintln(lib.mk(1).plus(2))\n', "run", "3", LIB2),
 ("a delegate from another module gets its set function", 'import lib (Pct)\ntuple Gauge\n  level Int delegate(Pct)\nfn bump(g Gauge) Result[Gauge, Error]\n  g.set_level(9)\nwhen Gauge(level: 5)\n  Ok(g) -> println(bump(g))\n  Err(e) -> println(e)\n', "run", "Ok(Gauge(level: 5))", 'export tuple Pct\n  value Int\nimpl Pct\n  export fn get_value(self Pct) Int\n    self.value\n  export fn set_value(self Pct, v Int) Result[Unit, Error]\n    Ok(())\n'),
 ("a higher-kinded parameter is checked against a plain value", 'fn lift[F[_] Functor, A, B](x F[A], f (A) -> B) F[B]\n  x.map(f)\nprintln(lift("abc", (a) -> a + 1))\n', "fail", "takes a type argument", None),
 ("a nested generic parameter is checked", 'fn flat[T](xs List[List[T]]) Int\n  len(xs)\nprintln(flat(List(1, 2)))\n', "fail", "expected `List[T]`, found `Int`", None),
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
