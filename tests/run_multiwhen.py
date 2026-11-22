"""`|` joins alternatives in a pattern, and `when a, b, c` matches several values at once.  Run: python3 tests/run_multiwhen.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAD = 'enum Role deriving show\n  Admin,\n  Member,\n  Guest\n'
CASES = [
    ("alternatives with |", 'fn k(n Int) String\n  when n\n    1 | 2 | 3 -> "low"\n    else "other"\nprintln(k(2))\nprintln(k(9))\n', 0, "low\nother"),
    ("comma is not an alternative", 'fn k(n Int) String\n  when n\n    1, 2 -> "low"\n    else "other"\nprintln(k(1))\n', 1, "write `A | B`"),
    ("two values", HEAD + 'fn d(r Role, ok Bool) String\n  when r, ok\n    _, false -> "no"\n    Admin, true -> "all"\n    Member | Guest, true -> "some"\nprintln(d(Admin, true))\nprintln(d(Guest, true))\nprintln(d(Guest, false))\n', 0, "all\nsome\nno"),
    ("three values", 'fn t(a Int, b Int, c Int) String\n  when a, b, c\n    0, 0, 0 -> "zero"\n    1 | 2, _, x if x > 5 -> "big"\n    _ -> "other"\nprintln(t(0, 0, 0))\nprintln(t(2, 9, 7))\nprintln(t(2, 9, 1))\n', 0, "zero\nbig\nother"),
    ("an uncovered combination", HEAD + 'fn d(r Role, ok Bool) String\n  when r, ok\n    _, false -> "no"\n    Admin, true -> "all"\n    Member, true -> "some"\nprintln(d(Admin, true))\n', 1, "does not cover `(Guest, true)`"),
    ("else covers the rest", HEAD + 'fn d(r Role, ok Bool) String\n  when r, ok\n    Admin, true -> "all"\n    else "none"\nprintln(d(Guest, true))\n', 0, "none"),
    ("wrong number of patterns", HEAD + 'fn d(r Role, ok Bool) String\n  when r, ok\n    Admin -> "all"\n    else "none"\nprintln(d(Guest, true))\n', 1, "has 1 pattern, but the `when` matches 2 values"),
    ("bindings", 'fn s(a Int, b Int) Int\n  when a, b\n    0, y -> y\n    x, 0 -> x\n    x, y -> x + y\nprintln(s(0, 5))\nprintln(s(4, 0))\nprintln(s(2, 3))\n', 0, "5\n4\n5"),
    ("alternatives must bind the same names", 'fn s(a Option[Int]) Int\n  when a\n    Some(x) | None -> 1\n    else 0\nprintln(1)\n', 1, "same names"),
    ("Option pair", 'fn s(a Option[Int], b Option[Int]) Int\n  when a, b\n    Some(x), Some(y) -> x + y\n    (Some(x), None) | (None, Some(x)) -> x\n    None, None -> 0\nprintln(s(Some(1), Some(2)))\nprintln(s(None, Some(7)))\nprintln(s(None, None))\n', 0, "3\n7\n0"),
    ("is with alternatives", 'enum R deriving show\n  A,\n  B,\n  C\nr = C\nprintln(r is A | C)\nprintln(r is not A | B)\nif r is B | C then println("ok")\n', 0, "true\ntrue\nok"),
    ("is alternatives cannot bind", 'o = Some(1)\nprintln(o is Some(x) | None)\n', 1, "cannot bind names"),
    ("nested alternatives in a constructor", 'fn f(o Option[Int]) String\n  when o\n    Some(1 | 2) -> "low"\n    Some(x) -> "other"\n    None -> "none"\nprintln(f(Some(2)))\nprintln(f(Some(9)))\n', 0, "low\nother"),
    ("nested alternatives in a tuple pattern", 'fn g(a Int, b Int) String\n  when a, b\n    (0 | 1, 0 | 1) -> "bits"\n    _ -> "no"\nprintln(g(1, 0))\nprintln(g(2, 0))\n', 0, "bits\nno"),
    ("nested alternatives are checked for coverage", 'fn f(o Option[Int]) Int\n  when o\n    Some(1 | 2) -> 1\n    None -> 0\nprintln(f(None))\n', 1, "does not cover"),
    ("nested alternatives with binding", 'fn f(r Result[Int, Int]) Int\n  when r\n    Ok(n) | Err(n) -> n\nprintln(f(Err(4)))\n', 0, "4"),
    ("alternatives only in arms and is", 'x = Some(1)\nSome(1 | 2) = x\n', 1, "only for a `when` arm and an `is` test"),
    ("too many combinations", 'fn f(a Int) Int\n  when a, a, a, a, a, a, a\n    ' + ", ".join("0 | 1 | 2 | 3 | 4 | 5" for _ in range(7)) + ' -> 1\n    _ -> 0\nprintln(f(3))\n', 1, "split it into separate arms"),
    ("Dict pattern with a bare ...", 'fn f(d Dict[String, Int]) Int\n  when d\n    Dict("a" -> x, ...) -> x\n    _ -> 0\nprintln(f(Dict("a" -> 5, "b" -> 1)))\nprintln(f(Dict("z" -> 1)))\n', 0, "5\n0"),
    ("Dict pattern with ...rest", 'fn f(d Dict[String, Int]) String\n  when d\n    Dict("a" -> x, ...rest) -> "$x ${len(rest)}"\n    _ -> "none"\nprintln(f(Dict("a" -> 5, "b" -> 1, "c" -> 2)))\n', 0, "5 2"),
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
