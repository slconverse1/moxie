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
