"""Type declarations: `type Pos = Int`, `opaque type Id = Int`, `union type Key = Int | String`; the old `type alias/opaque/union` forms are errors.  Run: python3 tests/run_typedecl.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(src, gc=False):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
CASES = [
 ("two opaque types over one type do not mix", "opaque type M = Double\nopaque type F = Double\nfn d(m M) String = \"x\"\nprintln(d(F(1.0)))\n", "expected `M`, found `F`"),
 ("an opaque value is not its representation", "opaque type F = Double\nf = F(1.0)\ny Int = f\n", "expected `Int`, found `F`"),
 ("an opaque value passes where its own type is wanted", "opaque type F = Double\nfn d(f F) String = \"ok\"\nprintln(d(F(1.0)))\n", "ok"),
 ("an alias", "type Kg = Double\nx Kg = 2.5\nprintln(x)\n", "2.5"),
 ("a refined alias", "type Pos = Int where self > 0\nx Pos = 3\nprintln(x)\n", "3"),
 ("a refined alias rejects a bad value", "type Pos = Int where self > 0\nx Pos = 0 - 1\n", "must satisfy"),
 ("a generic alias", "type Pair[A] = (A, A)\nfn f(p Pair[Int]) Int = 1\nprintln(f((1, 2)))\n", "1"),
 ("a union", "union type Key = Int | String\nfn f(k Key) String\n  when k\n    Int -> \"int\"\n    String -> \"str\"\nprintln(f(1))\nprintln(f(\"a\"))\n", "int\nstr"),
 ("a union is a Dict key type", "union type Key = Int | String\nd Dict[Key, Int] = Dict(1 -> 10, \"a\" -> 20)\nprintln(d.get(1))\n", "Ok(10)"),
 ("a union of one member", "enum Say[A]\n  Print(text String) Say[Unit]\nunion type One[A] = Say[A]\nfn f(x One[Unit]) Int = 1\nprintln(1)\n", "1"),
 ("a bare union is an error that says what to write", "type Key = Int | String\n", "write `union type Key = ...`"),
 ("opaque and union together", "opaque union type K = Int | String\n", "either `opaque` or a `union`"),
 ("a union that is not a bar-list still needs one type or more", "union type Id = Int\nx Id = 3\nprintln(1)\n", "1"),
 ("a union function call still works", "println(union(Set(1), Set(2)))\n", "Set"),
 ("an opaque type", "opaque type Meters = Int\nx = Meters(5)\nprintln(x)\n", "5"),
 ("an exported opaque type", "export opaque type Meters = Int\nprintln(1)\n", "1"),
 ("a type function", "type Elem[T] = when T\n  List[X] -> X\nfn f(x Elem[List[Int]]) Int = x\nprintln(f(3))\n", "3"),
 ("an associated type is still written the same way", "interface Box\n  type Item\n  fn get(self) Item\ntuple IntBox(v Int)\nimpl Box for IntBox\n  type Item = Int\n  fn get(self) Int = self.v\nprintln(IntBox(7).get())\n", "7"),
 ("a variable called type is fine", "type = 5\nprintln(type)\n", "5"),
 ("the old alias form says what to write", "type alias Pos = Int\n", "write `type Pos = ...`"),
 ("the old opaque form says what to write", "type opaque Id = Int\n", "write `opaque type Id = ...`"),
 ("the old union form says what to write", "type union Key = Int | String\n", "write `union type Key = A | B`"),
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
