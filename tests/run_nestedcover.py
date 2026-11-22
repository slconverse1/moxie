"""`when` exhaustiveness through nested patterns, tuples and literals.  Run: python3 tests/run_nestedcover.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
H = "enum Shape deriving show\n  Circle(r Int)\n  Sq(s Int)\n  Tri(a Int)\n"
CASES = [
 ("an Option of an enum missing a case", H + "fn f(o Option[Shape]) Int = when o\n  Some(Circle(r)) -> r\n  Some(Sq(s)) -> s\n  None -> 0\n", 2, "does not cover `Some(Tri(_))`"),
 ("an Option of an enum, covered", H + "fn f(o Option[Shape]) Int = when o\n  Some(Circle(r)) -> r\n  Some(Sq(s)) -> s\n  Some(Tri(a)) -> a\n  None -> 0\n", 0, ""),
 ("a nested wildcard covers the rest", H + "fn f(o Option[Shape]) Int = when o\n  Some(Circle(r)) -> r\n  Some(_) -> 1\n  None -> 0\n", 0, ""),
 ("a tuple with a literal", H + "fn f(s Shape, n Int) Int = when (s, n)\n  (Circle(r), 1) -> r\n  (Sq(x), 1) -> x\n  (_, _) -> 0\n", 0, ""),
 ("a tuple of enums missing a pair", H + "fn f(a Shape, b Bool) Int = when (a, b)\n  (Circle(r), true) -> r\n  (Circle(r), false) -> 1\n  (Sq(s), _) -> s\n", 2, "does not cover `(Tri(_), _)`"),
 ("Bool pairs covered", "fn f(a Bool, b Bool) Int = when (a, b)\n  (true, true) -> 1\n  (true, false) -> 2\n  (false, _) -> 3\n", 0, ""),
 ("a Result of an Option missing None", "fn f(r Result[Option[Int], String]) Int = when r\n  Ok(Some(n)) -> n\n  Err(e) -> 0\n", 2, "does not cover `Ok(None)`"),
 ("a guard does not cover", H + "fn f(o Option[Shape]) Int = when o\n  Some(Circle(r)) if r > 0 -> r\n  Some(_) -> 1\n  None -> 0\n", 0, ""),
]
fails = []
for name, src, rc_want, word in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check", f.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        ok = ((r.returncode != 0) if rc_want else r.returncode == 0) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:240]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
