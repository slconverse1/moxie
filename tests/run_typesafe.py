"""Compile-time type safety: programs that must be rejected by `check`, and programs that must pass and run.  Run: python3 tests/run_typesafe.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(src, cmd):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    try:
        r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, capture_output=True, timeout=60)
        rc, out = r.returncode, (r.stdout + r.stderr).decode()
    except subprocess.TimeoutExpired:
        rc, out = -9, "TIMEOUT"
    os.unlink(f.name)
    return rc, out

# (name, "R" = must be rejected / "A" = must be accepted and run without aborting, source)
CASES = [
    ('iface-missing-method', 'R', 'interface Shape\n  fn area(self) Float\ntuple Sq\n  s Float\nimpl Shape for Sq\n  fn perimeter(self) Float = 4.0\n'),
    ('generic-wrong-bound', 'R', 'fn big[T Ordered](a T, b T) T = if a > b then a else b\ntuple P\n  x Int\nprintln(big(P(1), P(2)))\n'),
    ('generic-mixed', 'R', 'fn same[T](a T, b T) T = a\nprintln(same(1, "a"))\n'),
    ('generic-ok', 'A', 'fn same[T](a T, b T) T = a\nprintln(same(1, 2))\n'),
    ('return-type-mismatch', 'R', 'fn f() Int = "s"\nprintln(f())\n'),
    ('missing-return-branch', 'R', 'fn f(x Int) String\n  if x > 0 then "p"\n'),
    ('wrong-arg-label', 'R', 'fn f(a Int, b Int) Int = a + b\nprintln(f(a: 1, c: 2))\n'),
    ('named-ok', 'A', 'fn f(a Int, b Int) Int = a - b\nprintln(f(b: 1, a: 5))\n'),
    ('dup-arm', 'A', 'x = 3\nwhen x\n  1 -> println("a")\n  _ -> println("b")\n'),
    ('non-exhaustive-enum', 'R', 'enum C\n  R\n  G\n  B\nfn f(c C) Int\n  when c\n    R -> 1\n    G -> 2\n'),
    ('exhaustive-enum', 'A', 'enum C\n  R\n  G\nfn f(c C) Int\n  when c\n    R -> 1\n    G -> 2\nprintln(f(C.R))\n'),
    ('arm-type-mismatch', 'R', 'x = 1\ny = when x\n  1 -> "a"\n  _ -> 2\nprintln(y)\n'),
    ('option-unwrap-misuse', 'R', 'o Option[Int] = Some(1)\nprintln(o * 2)\n'),
    ('result-unwrap-misuse', 'R', 'r Result[Int, Error] = Ok(1)\nprintln(r + 1)\n'),
    ('question-in-nonresult', 'R', 'fn f() Int\n  x = Some(1)?\n  x\n'),
    ('string-index-int', 'R', 's = "abc"\nprintln(s("a"))\n'),
    ('list-index-string', 'R', 'xs = List(1,2)\nprintln(xs("a"))\n'),
    ('dict-key-type', 'R', 'd = Dict("a" -> 1)\nprintln(d(1))\n'),
    ('set-add-type', 'R', 's = Set(1, 2)\nt = s + "a"\nprintln(t)\n'),
    ('list-plus-wrong', 'R', 'xs = List(1, 2)\nys = xs + "a"\nprintln(ys)\n'),
    ('tuple-field-type', 'R', 'tuple P\n  x Int\np = P(x: "a")\nprintln(p)\n'),
    ('tuple-update-type', 'R', 'tuple P\n  x Int\np = P(x: 1)\nq = p.update\n  x: "s"\nprintln(q)\n'),
    ('tuple-update-ok', 'A', 'tuple P\n  x Int\np = P(x: 1)\nq = p.update\n  x: & + 1\nprintln(q)\n'),
    ('lambda-return-type', 'R', 'f (Int) -> Int = (x) -> "s"\nprintln(f(1))\n'),
    ('lambda-param-count', 'R', 'f (Int, Int) -> Int = (x) -> x\nprintln(f(1, 2))\n'),
    ('hof-wrong-fn', 'R', 'fn app(f (Int) -> Int, x Int) Int = f(x)\nprintln(app((s String) -> 1, 2))\n'),
    ('map-fn-type', 'R', 'xs = List(1,2)\nprintln(xs |> map((s String) -> s) |> collect())\n'),
    ('filter-non-bool', 'R', 'xs = List(1,2)\nprintln(xs |> filter(_ + 1) |> collect())\n'),
    ('reduce-type', 'R', 'xs = List(1,2)\nprintln(xs |> reduce("", _1 + _2))\n'),
    ('sum-strings', 'A', 'xs = List("a","b")\nprintln(xs |> sum())\n'),
    ('sort-nonordered', 'R', 'tuple P\n  x Int\nxs = List(P(2), P(1))\nprintln(xs |> sort() |> collect())\n'),
    ('undefined-var', 'R', 'println(y)\n'),
    ('undefined-fn', 'R', 'println(nope(1))\n'),
    ('undefined-type', 'R', 'x Foo = 1\n'),
    ('unit-value-use', 'R', 'fn f() Unit = println("a")\nx Int = f()\n'),
    ('bool-int', 'R', 'x Bool = 1\n'),
    ('float-int-implicit', 'R', 'x Int = 1.5\n'),
    ('int-float-widen', 'A', 'x Float = 1\nprintln(x)\n'),
    ('int-overflow-literal', 'R', 'x Int8 = 300\nprintln(x)\n'),
    ('char-string', 'R', 'c Char = "a"\n'),
    ('channel-wrong-send', 'R', 'c = Chan[Int](1)\nsend(c, "s")\n'),
    ('break-outside', 'R', 'break\n'),
    ('enum-case-wrong-payload', 'R', 'enum E\n  A(Int)\nx = E.A("s")\nprintln(x)\n'),
    ('tuple-pattern-arity', 'R', 't = (1, 2)\n(a, b, c) = t\n'),
    ('tuple-pattern-ok', 'A', 't = (1, 2)\n(a, b) = t\nprintln(a + b)\n'),
    ('list-pattern-type', 'R', 'xs = List(1, 2)\nwhen xs\n  List("a", ...) -> 1\n  _ -> 2\n'),
    ('shadow-ok', 'A', 'x = 1\nx = x + 1\nprintln(x)\n'),
    ('equality-diff-types', 'R', 'println(1 == "a")\n'),
    ('compare-tuples-no-ord', 'R', 'tuple P\n  x Int\nprintln(P(1) < P(2))\n'),
    ('string-mul', 'R', 'println("a" - "b")\n'),
    ('method-not-found', 'R', 'tuple P\n  x Int\nprintln(P(1).nope())\n'),
    ('method-wrong-arg', 'R', 'tuple P\n  x Int\nimpl P\n  fn add(self, n Int) Int = self.x + n\nprintln(P(1).add("s"))\n'),
    ('opt-get_or-type', 'R', 'o Option[Int] = None\nprintln(o |> get_or("s"))\n'),
    ('dict-values-type', 'R', 'd Dict[String, Int] = Dict("a" -> "b")\n'),
    ('array-size', 'R', 'a Array[Int][2] = Array(1, 2, 3)\n'),
    ('nested-generic', 'R', 'xs List[List[Int]] = List(List(1), List("a"))\n'),
    ('continue-outside', 'R', 'continue\n'),
    ('labels-needed-value', 'R', 'fn f(a Int, b Int) Int = a + b\nprintln(f(a: 1))\n'),
    ('loops-with-break-ok', 'A', 'for i in 1..5\n  if i == 2 then continue\n  if i == 4 then break\n  println(i)\n'),
    ('option-field', 'R', 'o Option[Int] = None\nprintln(o.value)\n'),
    ('result-field', 'R', 'r Result[Int, String] = Ok(1)\nprintln(r.value)\n'),
    ('option-eq-scalar', 'R', 'println(Some(1) == 1)\n'),
    ('option-eq-option-ok', 'A', 'println(Some(1) == Some(1))\n'),
    ('tuple-index-range', 'R', 'x = (1, 2)\nprintln(x.2)\n'),
    ('tuple-index-ok', 'A', 'x = (1, 2)\nprintln(x.1)\n'),
    ('range-mixed-ends', 'R', 'println(1 .. "a")\n'),
    ('type-called-as-fn', 'R', 'println(Int("3") + 1)\n'),
    ('local-lambda-arg-type', 'R', 'f = (a Int) -> a\nprintln(f("x"))\n'),
    ('local-lambda-arg-ok', 'A', 'f = (a Int) -> a\nprintln(f(2))\n'),
    ('top-bound-below-fn', 'R', 'fn f() Int = z\nz = 5\nprintln(f())\n'),
    ('top-rebound-after-fn-read', 'R', 'y = 1\nfn f() Int = y\ny = 2\nprintln(f())\n'),
    ('top-rebind-unread-ok', 'A', 'x = 5\nx += 1\na, b = 1, 2\na, b = b, a\nprintln("$x $a $b")\n'),
    ('top-fn-reads-above-ok', 'A', 'rate = 3\nfn price(n Int) Int = n * rate\nprintln(price(5))\n'),
    ('top-fn-local-same-name-ok', 'A', 'fn f() Int\n  t = 1\n  t\nt = 5\nprintln(f() + t)\n'),
]

fails = []
for name, want, src in CASES:
    rc, out = run(src, "check")
    if want == "R":
        ok = rc != 0 and "error" in out
    else:
        r2, o2 = run(src, "run")
        ok = rc == 0 and r2 == 0 and "abort" not in o2
        out = out + o2
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  {out.strip()[:200]!r}"))
    if not ok:
        fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
