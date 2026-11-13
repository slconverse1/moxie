"""Colonless declarations (`x Int`), the `(%40)` one-item tuple, `key -> value` Dict entries, and puns.  Run: python3 tests/run_decls.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(src, flags=()):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "run", *flags, f.name], cwd=ROOT, capture_output=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, (r.stdout + r.stderr).decode()

U = 'tuple User\n  name String,\n  age Int\n'
CASES = [
 ("a parameter is a name and a type", 'fn add(a Int, b Int = 2) Int\n  a + b\nprintln(add(1))\n', 0, "3\n"),
 ("a variadic parameter", 'fn total(xs ...Int) Int\n  sum(xs)\nprintln(total(1, 2, 3))\n', 0, "6\n"),
 ("a function-typed parameter", 'fn twice(f (Int) -> Int, x Int) Int\n  f(f(x))\nprintln(twice((n Int) -> n + 1, 5))\n', 0, "7\n"),
 ("tuple fields", U + 'println(User(name: "Al", age: 3))\n', 0, 'User(name: "Al", age: 3)\n'),
 ("enum case fields", 'enum Shape\n  Circle(r Float)\n  Dot\nprintln(Circle(r: 1.5))\n', 0, "Shape.Circle(1.5)\n"),
 ("a tuple type with labels", 'p (x Int, y Int) = (x: 1, y: 2)\nprintln(p)\n', 0, "(x: 1, y: 2)\n"),
 ("a type bound", 'fn big[T Ord](a T, b T) T\n  if a > b then a else b\nprintln(big(3, 9))\n', 0, "9\n"),
 ("the old parameter colon is an error", 'fn f(x: Int) Int\n  x\n', 2, "has no colon"),
 ("the old field colon is an error", 'tuple P\n  x: Int\n', 2, "has no colon"),
 ("a binding is a name and a type", 'total Int = 1\nnames List[String] = List("a")\nf (Int) -> Int = (n) -> n + 1\nprintln(total)\nprintln(f(3))\n', 0, "1\n4\n"),
 ("a binding with a destructuring tuple still works", 'a, b = 1, 2\nprintln(a + b)\n', 0, "3\n"),
 ("the old binding colon is an error", 'total: Int = 1\n', 2, "has no colon"),
 ("the one-item tuple", 't = (%40)\nprintln(t)\nprintln(t(0))\nprintln((40))\n', 0, "(%40)\n40\n40\n"),
 ("a Dict entry is key -> value", 'println(Dict("a" -> 1, "b" -> 2))\n', 0, 'Dict("a" -> 1, "b" -> 2)\n'),
 ("a Dict comprehension", 'println(Dict(w -> len(w) for w in List("aa", "b")))\n', 0, 'Dict("aa" -> 2, "b" -> 1)\n'),
 ("the old Dict entry colon is an error", 'println(Dict("a": 1))\n', 2, "key -> value"),
 ("a bare name after a named argument is a pun", U + 'who = "Al"\nage = 7\nprintln(User(name: who, age))\n', 0, 'User(name: "Al", age: 7)\n'),
 ("a bare name in a Dict is a pun", 'age = 7\nn = 3\nprintln(Dict(age, n))\n', 0, 'Dict("age" -> 7, "n" -> 3)\n'),
 ("positional arguments stay positional", 'fn f(a Int, b Int) Int\n  a - b\na = 10\nb = 1\nprintln(f(a, b))\n', 0, "9\n"),
 ("a Dict pattern entry is key -> value", 'd = Dict("speed" -> 60, "limit" -> 100)\nwhen d\n  Dict("speed" -> s, "limit" -> 100) -> println("speed ${s}")\n  else println("other")\n', 0, "speed 60\n"),
 ("the old Dict pattern colon is an error", 'd = Dict("a" -> 1)\nwhen d\n  Dict("a": x) -> println(x)\n  else println("no")\n', 2, "key -> value"),
 ("read takes a Dict in the show form", 'println(read[Dict[String, Int]]("Dict(\\"k\\" -> 3)"))\n', 0, 'Ok(Dict("k" -> 3))\n'),
]
fails = []
for name, src, rc_want, want in CASES:
    for flags in ((), ("--gc",)):
        rc, out = run(src, flags)
        ok = rc == rc_want and want in out
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if flags else "") + ("" if ok else f"  rc={rc} {out[:200]!r}"))
        if not ok: fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
