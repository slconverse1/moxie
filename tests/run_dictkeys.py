"""Dict literal keys: computed keys (`abs(-3) -> 1`, `Color.Red -> 1`, `Key.ById(7) -> 1`, `$k -> 1`, `(k) -> 1`), a capitalized bare name as an
enum case, named unions as keys.  Run: python3 tests/run_dictkeys.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(src, gc=False):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
COLOR = "enum Color deriving eq, hash, show\n  Red\n  Green\n  Blue\n"
KEY = "enum Key deriving eq, hash, show\n  ById(n Int)\n  ByName(s String)\n"
CASES = [
 ("a call as a key", "println(Dict(abs(-3) -> 1))\n", "Dict(3 -> 1)"),
 ("arithmetic as a key", "println(Dict(2 + 2 -> 5, 7 -> 3))\n", "Dict(4 -> 5, 7 -> 3)"),
 ("two call keys", "xs = List(1, 2)\nprintln(Dict(len(xs) -> \"two\", xs(0) -> \"one\"))\n", 'Dict(2 -> "two", 1 -> "one")'),
 ("a qualified case as a key", COLOR + "d Dict[Color, Int] = Dict(Color.Red -> 1, Color.Green -> 2)\nprintln(d.get(Color.Red))\nprintln(d.get(Color.Blue))\n", 'Ok(1)\nErr(Error(code: 4, message: "no such key"))'),
 ("a constructor call as a key", KEY + "d Dict[Key, Int] = Dict(Key.ById(7) -> 1)\nprintln(d.get(Key.ById(7)))\n", "Ok(1)"),
 ("a capitalized bare name is a case", COLOR + "d Dict[Color, Int] = Dict(Red -> 1, Green -> 2)\nprintln(d.get(Red))\n", "Ok(1)"),
 ("a capitalized bare name without a type", COLOR + "println(Dict(Red -> 1, Green -> 2))\n", "Dict(Color.Red -> 1, Color.Green -> 2)"),
 ("several keys at once with cases", COLOR + "d = Dict(Red -> 1, Green -> 2)\nprintln(Dict(...d, {Blue, Red} -> (3, 9)))\n", "Dict(Color.Red -> 9, Color.Green -> 2, Color.Blue -> 3)"),
 ("a lowercase bare name is still a string", "println(Dict(alice -> 1, bob -> 2))\n", 'Dict("alice" -> 1, "bob" -> 2)'),
 ("$name is the value of a variable", KEY + "k1 = Key.ById(1)\nk2 = Key.ByName(\"a\")\nd Dict[Key, Int] = Dict($k1 -> 10, $k2 -> 20)\nprintln(d.get(k1))\nn = 5\nprintln(Dict($n -> \"five\"))\n", "Ok(10)\nDict(5 -> \"five\")"),
 ("a parenthesized variable is a key", "n = 5\nprintln(Dict((n) -> \"five\", (n + 1) -> \"six\"))\n", 'Dict(5 -> "five", 6 -> "six")'),
 ("a computed key after a spread", "d = Dict(1 -> \"one\")\nprintln(Dict(...d, 9 - 1 -> \"eight\"))\n", 'Dict(1 -> "one", 8 -> "eight")'),
 ("a tuple key is still one key", 'println(Dict((0, 0) -> "start"))\n', 'Dict((0, 0) -> "start")'),
 ("a value that is a pipeline", "xs = List(1, 2)\nprintln(Dict(1 -> (xs |> map((x) -> x + 1) |> collect())))\n", "Dict(1 -> List(2, 3))"),
 ("an unknown capitalized name is an error", "println(Dict(Alice -> 1))\n", "undefined name `Alice`"),
 ("mixed key types are still an error", 'println(Dict(1 -> "a", "b" -> "c"))\n', "must share one type"),
 ("entries keep the order written, labels and computed keys mixed", 'println(Dict(b -> 1, ("z") -> 2, a -> 3))\n', 'Dict("b" -> 1, "z" -> 2, "a" -> 3)'),
 ("a later computed key replaces an earlier labeled one", 'println(Dict(1 -> "a", (1) -> "b"))\n', 'Dict(1 -> "b")'),
 ("a repeated constant key is a warning", 'println(Dict(1 -> "a", 2 - 1 -> "b"))\n', "is the same as an earlier key"),
 ("a repeated key after a spread is allowed", 'd = Dict(a -> 1)\nprintln(Dict(a -> 1, ...d, a -> 2))\n', 'Dict("a" -> 2)'),
 ("division by a folded built-in", 'println(6 / abs(0))\n', "division by a constant zero"),
 ("division by a folded min/max/pow/len", 'println(10 / max(0, 0))\n', "division by a constant zero"),
 ("a built-in that is not constant is not folded", 'n = 3\nprintln(6 / abs(n - 3))\n', "division by zero"),
 ("a program's own abs is not folded as the built-in", 'fn abs(x Int) Int\n  x + 1\nprintln(6 / abs(0))\n', "6"),
 ("an array size from a folded call", 'b Array[Int][abs(-3)] = Array(1, 2)\nprintln(b)\n', "mismatched types"),
 ("a named union as a key", 'type union Key = Int | String\nd Dict[Key, Int] = Dict(1 -> 10, "a" -> 20)\nprintln(d.get(1))\nprintln(d.get("a"))\n', "Ok(10)\nOk(20)"),
 ("a union with a Double member is not a key", 'type union Key = Int | Double\nd Dict[Key, Int] = Dict(1 -> 10)\nprintln(d)\n', "its member `Double` is not hashable"),
 ("an inline union as a key", 'd Dict[Int | String, Int] = Dict(1 -> 10, "a" -> 20)\nprintln(d.get("a"))\n', "Ok(20)"),
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
