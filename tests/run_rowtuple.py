"""Open tuple types, `(name String, ...)`: a parameter that accepts any tuple (declared or not) that has at least these named fields.
Also the exact form: `(name String, age Int)` takes exactly those fields.  Run: python3 tests/run_rowtuple.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAD = 'user = (name: "Alice", age: 30)\nadmin = (...user, role: "Admin")\ntuple Employee\n  name String\n  age Int\n  salary Int\n'
GREET = 'fn greet(u (name String, ...)) String = "hi ${u.name}"\n'
CASES = [
    ("labeled tuple", HEAD + GREET + 'println(greet(user))\n', 0, "hi Alice"),
    ("wider tuple (spread)", HEAD + GREET + 'println(greet(admin))\n', 0, "hi Alice"),
    ("declared tuple", HEAD + GREET + 'println(greet(Employee(name: "Bo", age: 1, salary: 2)))\n', 0, "hi Bo"),
    ("two fields", HEAD + 'fn tag(u (name String, age Int, ...)) String = "${u.name}/${u.age + 1}"\nprintln(tag(admin))\nprintln(tag(Employee(name: "Bo", age: 40, salary: 9)))\n', 0, "Alice/31\nBo/41"),
    ("lambda parameter", HEAD + 'f = (u (name String, ...)) -> "hi ${u.name}"\nprintln(f(admin))\n', 0, "hi Alice"),
    ("inside a List type", HEAD + 'fn names(xs List[(name String, ...)]) List[String] = xs.map((u) -> u.name) |> collect()\nprintln(names(List(user, admin)))\n', 0, 'List("Alice", "Alice")'),
    ("spread keeps later fields", 'a = (x: 1, y: 2)\nb = (...a, y: 5, z: 6)\nprintln(b)\n', 0, "(x: 1, y: 5, z: 6)"),
    ("pattern with ...", HEAD + 'when admin\n  (name: n, ...) -> println(n)\n  _ -> println("no")\n', 0, "Alice"),
    ("missing field", HEAD + GREET + 'println(greet((age: 3)))\n', 1, "has no field `name`"),
    ("wrong field type", HEAD + GREET + 'println(greet((name: 5, age: 1)))\n', 1, "needs a `String`"),
    ("not a tuple", HEAD + GREET + 'println(greet(5))\n', 1, "expected a tuple with the fields"),
    ("other field is hidden", HEAD + 'fn older(u (name String, ...)) Int = u.age\nprintln(older(user))\n', 1, "not one of the fields this parameter promises"),
    ("exact type refuses extras", HEAD + 'fn exact(u (name String, age Int)) String = u.name\nprintln(exact(admin))\n', 1, "extra field `role`"),
    ("exact type refuses missing", HEAD + 'fn exact(u (name String, age Int)) String = u.name\nprintln(exact((name: "x")))\n', 1, "no `age`"),
    ("exact type still fits", HEAD + 'fn exact(u (name String, age Int)) String = u.name\nprintln(exact(user))\n', 0, "Alice"),
    ("fields must be named", 'fn bad(u (String, ...)) Int = 1\nprintln(1)\n', 1, "names its fields and ends with `...`"),
    ("not a result type", 'fn mk() (name String, ...) = (name: "x")\nprintln(1)\n', 1, "only be the type of a parameter"),
]
bad = 0
for name, src, want_rc, want in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    for flags in ([], ["--gc"]):
        r = subprocess.run([sys.executable, "-m", "moxie"] + flags + ["run", f.name], cwd=ROOT, capture_output=True, timeout=60)
        out = (r.stdout + r.stderr).decode()
        ok = (r.returncode == 0) == (want_rc == 0) and want in out
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if flags else "") + ("" if ok else "  " + repr(out[-160:])))
        bad += not ok
    os.unlink(f.name)
print(f"{bad} failed")
sys.exit(1 if bad else 0)
