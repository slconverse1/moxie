"""Row extension and removal: `Extend[R, (f T)]` as a result type, `without(r, "f")` and `Without[R, "f"]`, and the compile-time field check on
labeled tuples.  Run: python3 tests/run_rowops.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = 'fn label(r (first String, last String, ...)) String = "${r.first} ${r.last}"\nfn add_full[R (first String, last String, ...)](r R) Extend[R, (full String)] = (...r, full: label(r))\n'
STRIP = 'fn strip[R (password String, ...)](r R) Without[R, "password"] = without(r, "password")\n'
CASES = [
    ("extend: result has the new field", EXT + 'x = add_full((first: "Ada", last: "L", age: 3))\nprintln(x.full)\nprintln(x.age)\n', 0, "Ada L\n3"),
    ("extend: declared tuple comes back labeled", EXT + 'tuple P\n  first String\n  last String\n  age Int\nx = add_full(P(first: "A", last: "B", age: 1))\nprintln(x)\n', 0, '(first: "A", last: "B", age: 1, full: "A B")'),
    ("extend: unknown field is an error", EXT + 'x = add_full((first: "Ada", last: "L"))\nprintln(x.nope)\n', 1, "has no field `nope`"),
    ("extend: new field has the declared type", 'fn f[R (first String, ...)](r R) Extend[R, (full String)] = (...r, full: 5)\nprintln(1)\n', 1, "expected `String`, found `Int`"),
    ("extend: result must not be the argument", 'fn f[R (first String, ...)](r R) Extend[R, (full String)] = r\nprintln(1)\n', 1, "mismatched types"),
    ("extend: a missing field in the argument", EXT + 'println(add_full((first: "Ada")))\n', 1, "has no field `last`"),
    ("extend: in a pipeline", 'fn f[R (first String, ...)](r R) Extend[R, (full String)] = (...r, full: "x")\nfor p in List((first: "A", age: 1)) |> map(f)\n  println(p.full)\n', 0, "x"),
    ("without: a labeled tuple", 'u = (id: 1, name: "Ada", password: "pw")\nsafe = without(u, "password")\nprintln(safe)\nprintln(safe.name)\n', 0, '(id: 1, name: "Ada")\nAda'),
    ("without: a declared tuple", 'tuple Emp\n  id Int\n  name String\n  salary Int\nprintln(without(Emp(id: 1, name: "Bo", salary: 5), "salary"))\n', 0, '(id: 1, name: "Bo")'),
    ("without: the field is gone", 'u = (id: 1, password: "pw")\nprintln(without(u, "password").password)\n', 1, "has no field `password`"),
    ("without: no such field", 'u = (id: 1)\nprintln(without(u, "nope"))\n', 1, "has no field `nope`"),
    ("without: generic", STRIP + 'y = strip((name: "A", password: "p", age: 3))\nprintln(y.age)\nprintln(y)\n', 0, '3\n(name: "A", age: 3)'),
    ("without: generic, field gone", STRIP + 'y = strip((name: "A", password: "p"))\nprintln(y.password)\n', 1, "has no field `password`"),
    ("without: generic needs the field", STRIP + 'println(strip((name: "A")))\n', 1, "has no field `password`"),
    ("field of a labeled tuple", 'u = (a: 1)\nprintln(u.b)\n', 1, "has no field `b`"),
    ("field of a spread tuple", 'u = (a: 1, c: 2)\nv = (...u, d: 3)\nprintln(v.b)\n', 1, "has no field `b`"),
    ("without: the key must be a literal", 'k = "id"\nu = (id: 1, n: 2)\nprintln(without(u, k))\n', 1, "string literal"),
    ("without: a generic declared tuple", 'tuple Box[T]\n  v T\n  id Int\nb = Box(v: "x", id: 1)\nw = without(b, "id")\nprintln(w)\nprintln(w.v)\n', 0, '(v: "x")\nx'),
    ("extend: no extra fields", 'fn f[R (a Int, ...)](r R) Extend[R, (b Int)] = (...r, b: 1, c: 2)\nprintln(1)\n', 1, "does not promise `c`"),
    ("update: unknown field of a labeled tuple", 'u = (a: 1)\nprintln(u.update\n  b: 5)\n', 1, "has no field `b` to update"),
    ("update: wrong type for a labeled tuple", 'u = (a: 1)\nprintln(u.update\n  a: "x")\n', 1, "expected `Int`, found `String`"),
    ("update: after without", 'u = (a: 1, b: 2)\nv = without(u, "a")\nprintln(v.update\n  a: 5)\n', 1, "has no field `a` to update"),
    ("update: still fine", 'u = (a: 1, b: 2)\nprintln(u.update\n  a: u.a + 1)\n', 0, "(a: 2, b: 2)"),
    ("open type: a field of the wrong number type", 'fn f(r (a Int, ...)) Int = r.a\nprintln(f((a: 1.5)))\n', 1, "needs a `Int`"),
    ("open type in a List parameter", 'fn f(xs List[(a Int, ...)]) Int = len(xs)\nprintln(f(List((a: 1, b: 2))))\n', 0, "1"),
    ("open type in a List parameter: missing field", 'fn f(xs List[(a Int, ...)]) Int = len(xs)\nprintln(f(List((b: 2))))\n', 1, "mismatched types"),
    ("bound: update with the wrong type", 'fn f[R (a Int, ...)](r R) R = r.update\n  a: "no"\nprintln(1)\n', 1, "expected `Int`, found `String`"),
    ("bound: update of a field not promised", 'fn f[R (a Int, ...)](r R) R = r.update\n  z: 1\nprintln(1)\n', 1, "has no field `z` to update"),
    ("without: the field is not there (generic result)", 'fn f[R (a Int, ...)](r R) Without[R, "b"] = without(r, "b")\nprintln(f((a: 1)))\n', 1, "no field `b` to leave out"),
    ("extend: every branch is checked", 'fn f[R (a Int, ...)](r R) Extend[R, (b Int)]\n  if r.a > 0 then (...r, b: 1) else (...r, b: "no")\nprintln(f((a: 1)))\n', 1, "expected `Int`, found `String`"),
    ("a tuple is not a sequence", 'u = (a: 1, b: 2)\nfor k in u\n  println(k)\n', 1, "found the tuple"),
]
bad = 0
for name, src, want_rc, want in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    for flags in ([], ["--gc"]):
        r = subprocess.run([sys.executable, "-m", "moxie"] + flags + ["run", f.name], cwd=ROOT, capture_output=True, timeout=60)
        out = (r.stdout + r.stderr).decode()
        ok = (r.returncode == 0) == (want_rc == 0) and want in out
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if flags else "") + ("" if ok else "  " + repr(out[-200:])))
        bad += not ok
    os.unlink(f.name)
print(f"{bad} failed")
sys.exit(1 if bad else 0)
