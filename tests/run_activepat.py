"""Pattern functions (`pattern fn Name(.., value T) Option[U]`): a recognizer used as a pattern, F#'s partial active patterns.
Run: python3 tests/run_activepat.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUM = 'pattern fn Num(s String) Option[Int] = parse_number(s).ok()\n'
PREFIX = 'pattern fn Prefix(p String, s String) Option[String] = if starts_with(s, p) then Some(s(len(p)..)) else None\n'
DIV = 'pattern fn DivisibleBy(d Int, n Int) Option[Unit] = if n % d == 0 then Some(()) else None\n'
PAIR = 'pattern fn Pair(s String) Option[(Int, Int)] = Some((1, 2))\n'
# (name, source, want exit 0 = runs / 1 = refused, text that must be in the output)
CASES = [
    ("when arm", NUM + 'fn d(s String) String\n  when s\n    Num(n) -> "int ${n}"\n    _ -> "raw"\nprintln(d("42"))\nprintln(d("x"))\n', 0, "int 42\nraw"),
    ("blank lines between arms", NUM + 'fn d(s String) String\n  when s\n    Num(n) -> "int ${n}"\n\n    _ -> "raw"\nprintln(d("1"))\n', 0, "int 1"),
    ("argument first", DIV + 'x = 15\nwhen x\n  DivisibleBy(3) -> println("by3")\n  _ -> println("no")\n', 0, "by3"),
    ("argument and payload", PREFIX + NUM + 'fn f(s String) String\n  when s\n    Prefix("--port=", Num(p)) -> "port ${p + 1}"\n    Prefix("--", rest) -> "flag ${rest}"\n    _ -> "arg"\nprintln(f("--port=80"))\nprintln(f("--v"))\nprintln(f("x"))\n', 0, "port 81\nflag v\narg"),
    ("pin as argument", DIV + 'k = 5\nprintln(10 is DivisibleBy(^k))\nprintln(11 is DivisibleBy(^k))\n', 0, "true\nfalse"),
    ("is test", NUM + 'if "7" is Num(n)\n  println(n * 6)\n', 0, "42"),
    ("let-else", NUM + 'Num(m) = "9" else\n  println("no")\n  exit(1)\nprintln(m)\n', 0, "9"),
    ("tuple payload", PAIR + 'when "x"\n  Pair(a, b) -> println(a + b)\n  _ -> println("no")\n', 0, "3"),
    ("inside a tuple pattern", NUM + 'when ("1", "2")\n  (Num(x), Num(y)) -> println(x + y)\n  _ -> println("no")\n', 0, "3"),
    ("inside Some", NUM + 'when Some("7")\n  Some(Num(n)) -> println(n)\n  _ -> println("no")\n', 0, "7"),
    ("for comprehension skips", NUM + 'ks = for\n  Num(k) in List("1", "x", "3")\n  yield k\nprintln(ks)\n', 0, "List(1, 3)"),
    ("find_map with a pattern function", PREFIX + NUM + 'fn port(a String) Option[Int]\n  when a\n    Prefix("--port=", Num(p)) -> Some(p)\n    _ -> None\nprintln(List("--v", "--port=8080") |> find_map(port))\n', 0, "Ok(8080)"),
    ("works in moxie/gc", NUM + 'println("5" is Num(_))\n', 0, "true"),
    ("needs a _ arm", NUM + 'fn d(s String) String\n  when s\n    Num(n) -> "int"\nprintln(d("1"))\n', 1, "needs a `_` arm"),
    ("wrong value type", NUM + 'x = 5\nwhen x\n  Num(n) -> println(n)\n  _ -> println(0)\n', 1, "matches a `String`"),
    ("payload type is known", NUM + 'when "1"\n  Num(n) -> println(n + "a")\n  _ -> println(0)\n', 1, "cannot apply `+`"),
    ("too many payload patterns", NUM + 'when "1"\n  Num(a, b) -> println(a)\n  _ -> println(0)\n', 1, "finds one value"),
    ("wrong tuple size", PAIR + 'when "1"\n  Pair(a, b, c) -> println(a)\n  _ -> println(0)\n', 1, "finds 2 values"),
    ("missing argument", PREFIX + 'when "1"\n  Prefix -> println(1)\n  _ -> println(0)\n', 1, "takes 1 argument"),
    ("argument type", DIV + 'when 3\n  DivisibleBy("a") -> println(1)\n  _ -> println(0)\n', 1, "takes a `Int`"),
    ("argument is a value", DIV + 'when 3\n  DivisibleBy(d) -> println(1)\n  _ -> println(0)\n', 1, "literal or `^name`"),
    ("declared below the use", 'fn d(s String) String\n  when s\n    Num(n) -> "x"\n    _ -> "y"\n' + NUM + 'println(d("1"))\n', 1, "declared below"),
    ("must return an Option", 'pattern fn Bad(s String) Int = 1\nprintln(1)\n', 1, "must return an `Option`"),
    ("name is capitalized", 'pattern fn num(s String) Option[Int] = Some(1)\nprintln(1)\n', 1, "starts with a capital"),
    ("name is not a type", 'pattern fn Int(s String) Option[Int] = Some(1)\nprintln(1)\n', 1, "already the name of a type"),
    ("is pure", 'pattern fn Loud(s String) Option[Int]\n  println(s)\n  Some(1)\nprintln(1)\n', 1, "prints"),
    ("plain for refuses it", NUM + 'for Num(k) in List("1")\n  println(k)\n', 1, "does not fit every element"),
]
bad = 0
for name, src, want_rc, want in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    flags = ["--gc"] if "gc" in name else []
    r = subprocess.run([sys.executable, "-m", "moxie"] + flags + ["run", f.name], cwd=ROOT, capture_output=True, timeout=60)
    os.unlink(f.name)
    out = (r.stdout + r.stderr).decode()
    ok = (r.returncode == 0) == (want_rc == 0) and want in out
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else "  " + repr(out[-160:])))
    bad += not ok
print(f"{bad} failed")
sys.exit(1 if bad else 0)
