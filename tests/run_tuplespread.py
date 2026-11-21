"""Tuple spread: `...rest` in a tuple pattern binds a labeled tuple of the fields the pattern left out.  Run: python3 tests/run_tuplespread.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(src, gc=False):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
T = 'tuple Item(id Int, tags List[String], owner String)\nit = Item(id: 1, tags: List("a"), owner: "ada")\n'
CASES = [
 ("labeled fields leave the others in rest", T + "when it\n  Item(id: i, ...rest) -> println(rest)\n", '(tags: List("a"), owner: "ada")'),
 ("a field of the rest is readable", T + "when it\n  Item(id: i, ...rest) -> println(rest.owner)\n", "ada"),
 ("positional fields are taken first", T + "when it\n  Item(i, ...rest) -> println(rest)\n", '(tags: List("a"), owner: "ada")'),
 ("rest alone is every field", T + "when it\n  Item(...all) -> println(all)\n", '(id: 1, tags: List("a"), owner: "ada")'),
 ("nothing left is an empty tuple", T + "when it\n  Item(id: i, tags: t, owner: o, ...none) -> println(none)\n", "()"),
 ("a bare ... still skips", T + "when it\n  Item(id: i, ...) -> println(i)\n", "1"),
 ("a tuple with no declaration", '(id: j, ...more) = (id: 7, name: "x", age: 3)\nprintln(more)\n', '(name: "x", age: 3)'),
 ("an enum case with names", 'enum Shape\n  Circle(radius Double, label String)\n  Dot\ns = Shape.Circle(radius: 2.0, label: "c")\nwhen s\n  Circle(radius: r, ...more) -> println(more.label)\n  _ -> println("dot")\n', "c"),
 ("destructuring with a declared tuple", T + "Item(id: k, ...others) = it\nprintln(others)\n", '(tags: List("a"), owner: "ada")'),
 ("a list spread is still a list", "when List(1, 2, 3)\n  List(a, ...r) -> println(r)\n  _ -> println(0)\n", "List(2, 3)"),
 ("a dict spread is still a dict", "when Dict(a -> 1, b -> 2)\n  Dict(a -> x, ...r) -> println(r)\n  _ -> println(0)\n", 'Dict("b" -> 2)'),
]
fails = []
for name, src, want in CASES:
    for gc in (False, True):
        rc, out = run(src, gc)
        good = want in out
        print(("ok    " if good else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if good else f"  -> rc={rc} {out.strip()[:300]!r}"))
        if not good:
            fails.append(name)
print(f"{len(CASES) * 2 - len(fails)} of {len(CASES) * 2} passed")
sys.exit(1 if fails else 0)
