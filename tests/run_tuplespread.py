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
T = 'tuple Item(id Int, tags List[String], owner String) deriving show\nit = Item(id: 1, tags: List("a"), owner: "ada")\n'
CASES = [
 ("labeled fields leave the others in rest", T + "when it\n  Item(id: i, ...rest) -> println(rest)\n", '(tags: List("a"), owner: "ada")'),
 ("a field of the rest is readable", T + "when it\n  Item(id: i, ...rest) -> println(rest.owner)\n", "ada"),
 ("positional fields are taken first", T + "when it\n  Item(i, ...rest) -> println(rest)\n", '(tags: List("a"), owner: "ada")'),
 ("rest alone is every field", T + "when it\n  Item(...all) -> println(all)\n", '(id: 1, tags: List("a"), owner: "ada")'),
 ("nothing left is an empty tuple", T + "when it\n  Item(id: i, tags: t, owner: o, ...none) -> println(none)\n", "()"),
 ("a bare ... still skips", T + "when it\n  Item(id: i, ...) -> println(i)\n", "1"),
 ("a tuple with no declaration", '(id: j, ...more) = (id: 7, name: "x", age: 3)\nprintln(more)\n', '(name: "x", age: 3)'),
 ("an enum case with names", 'enum Shape deriving show\n  Circle(radius Double, label String)\n  Dot\ns = Shape.Circle(radius: 2.0, label: "c")\nwhen s\n  Circle(radius: r, ...more) -> println(more.label)\n  _ -> println("dot")\n', "c"),
 ("destructuring with a declared tuple", T + "Item(id: k, ...others) = it\nprintln(others)\n", '(tags: List("a"), owner: "ada")'),
 ("a list spread is still a list", "when List(1, 2, 3)\n  List(a, ...r) -> println(r)\n  _ -> println(0)\n", "List(2, 3)"),
 ("a dict spread is still a dict", "when Dict(\"a\" -> 1, \"b\" -> 2)\n  Dict(\"a\" -> x, ...r) -> println(r)\n  _ -> println(0)\n", 'Dict("b" -> 2)'),
 ("a bound field has its type", T + "when it\n  Item(id: i, ...rest) -> println(i + \"x\")\n", "cannot apply `+` to `Int` and `String`"),
 ("rest has the type of what is left", T + "when it\n  Item(id: i, ...rest) -> println(rest.nme)\n", "has no field `nme` (it has `tags`, `owner`)"),
 ("rest does not have a field the pattern took", T + "when it\n  Item(id: i, ...rest) -> println(rest.id)\n", "has no field `id`"),
 ("a field of rest has its type", T + "when it\n  Item(id: i, ...rest) -> println(rest.owner + 1)\n", "cannot apply `+`"),
 ("a label the declared tuple lacks", T + "when it\n  Item(idd: i, ...rest) -> println(1)\n", "has no field `idd`"),
 ("a label an anonymous tuple lacks", 'when (a: 1, b: 2)\n  (c: x, ...r) -> println(1)\n', "has no field `c`"),
 ("anonymous destructuring is typed", '(id: j, ...others) = (id: 7, name: "x", age: 3)\nprintln(others.age + "x")\n', "cannot apply `+`"),
 ("anonymous destructuring reads rest", '(id: j, ...others) = (id: 7, name: "x", age: 3)\nprintln(others.age + 1)\n', "4"),
 ("* is a short spelling of ... on a list", "when List(1, 2, 3)\n  List(a, *r) -> println(r)\n  _ -> println(0)\n", "List(2, 3)"),
 ("a bare * skips the rest", "when List(1, 2, 3)\n  List(a, *) -> println(a)\n  _ -> println(0)\n", "1"),
 ("* on a dict", "when Dict(\"a\" -> 1, \"b\" -> 2)\n  Dict(\"a\" -> x, *r) -> println(r)\n  _ -> println(0)\n", 'Dict("b" -> 2)'),
 ("* on a tuple", T + "when it\n  Item(id: i, *rest) -> println(rest)\n", '(tags: List("a"), owner: "ada")'),
 ("* in destructuring", '(id: j, *more) = (id: 7, name: "x", age: 3)\nprintln(more)\n', '(name: "x", age: 3)'),
 ("* is typed like ...", T + "when it\n  Item(id: i, *rest) -> println(rest.nme)\n", "has no field `nme`"),
 ("* nested in one pattern", 'p = (status: "ok", items: List((id: 1, tags: List("u", "b"), owner: "ada"), (id: 2, tags: List("l"), owner: "g")))\nwhen p\n  (status: "ok", items: List((id: f, tags: List(a, *o), *e), *rem), *top) -> println("${f} ${a} ${o} ${e} ${rem.len()} ${top}")\n  _ -> println("no")\n', '1 u List("b") (owner: "ada") 1 ()'),
 ("a pattern over several lines", 'p = (status: "ok", n: 3)\nwhen p\n  (\n    status: "ok"\n    *rest\n  ) -> println(rest)\n  _ -> println("no")\n', "(n: 3)"),
 ("a spread in an enum case is typed", "enum Shape deriving show\n  Circle(radius Double, label String)\n  Square(side Double, label String)\ns = Circle(radius: 1.5, label: \"c\")\nwhen s\n  Circle(radius: r, *more) -> println(r + more.label)\n  _ -> println(0)\n", "cannot apply `+` to `Double` and `String`"),
 ("a spread in an enum case still runs", "enum Shape deriving show\n  Circle(radius Double, label String)\n  Square(side Double, label String)\ns = Circle(radius: 1.5, label: \"c\")\nwhen s\n  Circle(radius: r, *more) -> println(\"${r} ${more.label}\")\n  _ -> println(0)\n", "1.5 c"),
 ("the rest of an enum case is the other fields", "enum Shape deriving show\n  Circle(radius Double, label String)\n  Square(side Double, label String)\ns = Square(side: 2.0, label: \"q\")\nwhen s\n  Square(side: x, *more) -> println(more)\n  _ -> println(0)\n", "(label: \"q\")"),
 ("an enum case spread names a field the case lacks", "enum Shape deriving show\n  Circle(radius Double, label String)\n  Square(side Double, label String)\ns = Square(side: 2.0, label: \"q\")\nwhen s\n  Square(radius: x, *more) -> println(more)\n  _ -> println(0)\n", "can never match"),
 ("* is still multiplication", "println(2 * 3)\n", "6"),
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
