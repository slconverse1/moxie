"""let-else with a pattern for the failure: `Ok(n) = f() else Err(e) -> ...`.  Run: python3 tests/run_letelse.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = tempfile.mkdtemp()
HEAD = 'tuple NotFound\n  id Int\nenum Shape\n  Circle(r Int)\n  Square(s Int)\n  Dot\n'
CASES = [
 ("the Err's contents are in scope", 'fn half(s String) Result[Int, Error]\n  Ok(n) = read[Int](s) else Err(e) -> Err(Error(code: 7, message: "bad: ${e.message}"))\n  Ok(n / 2)\nprintln(half("10"))\nprintln(half("zz"))\n', 0, 'code: 7, message: "bad: cannot read"'),
 ("a wildcard inside the failure pattern", 'fn h(xs List[Int]) Int\n  Ok(x) = first(xs) else Err(_) -> -1\n  x\nprintln(h(List(4)))\nprintln(h(List()))\n', 0, "-1"),
 ("a plain name binds the whole value", 'fn h(xs List[Int]) String\n  Ok(x) = first(xs) else r -> "none: ${r}"\n  "got ${x}"\nprintln(h(List()))\n', 0, "none: Err("),
 ("an enum split in two", 'enum Two\n  Circle(r Int)\n  Square(s Int)\nfn r(s Two) Int\n  Circle(n) = s else Square(k) -> k * 10\n  n\nprintln(r(Square(3)))\nprintln(r(Circle(4)))\n', 0, "30"),
 ("three cases need a third pattern", HEAD + 'fn r(s Shape) Int\n  Circle(n) = s else Square(k) -> k\n  n\n', 2, "does not cover `Dot`"),
 ("a name for the rest covers it", HEAD + 'fn r(s Shape) Int\n  Circle(n) = s else other -> 0\n  n\nprintln(r(Dot))\n', 0, "0"),
 ("the same case twice does not cover", 'fn r(x Result[Int, Error]) Int\n  Ok(n) = x else Ok(m) -> m\n  n\n', 2, "does not cover `Err`"),
 ("a pattern for another type is an error", 'fn r(x Result[Int, Error]) Int\n  Ok(n) = x else Some(m) -> 0\n  n\n', 2, "can never match"),
 ("the failure's names are not visible afterwards", 'fn r(x Result[Int, Error]) Int\n  Ok(n) = x else Err(e) -> 0\n  e.code\n', 2, "undefined name `e`"),
 ("the success names are not visible in the else", 'fn r(x Result[Int, Error]) Int\n  Ok(n) = x else Err(e) -> n\n  n\n', 2, "undefined name `n`"),
 ("the old form still works", 'fn r(x Result[Int, Error]) Int\n  Ok(n) = x else 0\n  n\nprintln(r(Ok(5)))\nprintln(r(fail(1, "x")))\n', 0, "0"),
 ("the old form with a block still works", 'fn r(x Result[Int, Error]) Int\n  Ok(n) = x else\n    println("no")\n    return -1\n  n\nprintln(r(fail(1, "x")))\n', 0, "-1"),
 ("a constructor call as the else value still works", 'fn r(x Result[Int, Error]) Result[Int, Error]\n  Ok(n) = x else Err(Error(code: 2, message: "m"))\n  Ok(n)\nprintln(r(fail(1, "x")))\n', 0, 'code: 2'),
 ("tail call from the else", 'fn go(n Int) Int\n  Ok(x) = first(List(n)) else Err(_) -> 0\n  if x > 3000 then x else go(x + 1)\nprintln(go(1))\n', 0, "3001"),
]
fails = []
for name, src, rc_want, word in CASES:
    for gc in (False, True):
        p = os.path.join(D, "t.mxi")
        open(p, "w").write(src)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check" if rc_want == 2 else "run", p], cwd=ROOT, capture_output=True, text=True)
        o = r.stdout + r.stderr
        good = (r.returncode != 0 if rc_want == 2 else r.returncode == 0) and word in o
        print(("ok    " if good else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if good else f"  -> rc={r.returncode} {o.strip()[:300]!r}"))
        if not good: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
