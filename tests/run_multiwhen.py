"""`|` joins alternatives in a pattern, and `when a, b, c` matches several values at once.  Run: python3 tests/run_multiwhen.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAD = 'enum Role\n  Admin,\n  Member,\n  Guest\n'
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
