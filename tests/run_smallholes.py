"""Patterns that can never match, a dropped Result, a `cast` of a constant that can't fit.  Run: python3 tests/run_smallholes.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def check(src):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "check", f.name], cwd=ROOT, capture_output=True, text=True, timeout=120)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
F = 'fn f() Result[Int, Error] = Err(Error(code: 1, message: "x"))\n'
# (name, source, text that must be in the output, or None for "no error and no warning")
CASES = [
 ("Some against a Result", 'fn f(xs List[Int]) Int\n  when first(xs)\n    Some(n) -> n\n    _ -> 0\n', "`Some` matches an `Option`"),
 ("None against a Result", 'fn f(xs List[Int]) Int\n  when first(xs)\n    None -> 1\n    _ -> 0\n', "`None` matches an `Option`"),
 ("Ok against an Option", 'fn f(o Option[Int]) Int\n  when o\n    Ok(n) -> n\n    _ -> 0\n', "`Ok` matches a `Result`"),
 ("is against the wrong type", 'fn f(xs List[Int]) Bool\n  first(xs) is Some(_)\n', "can never match"),
 ("let-else against the wrong type", 'fn f(xs List[Int]) Int\n  Some(n) = first(xs) else 0\n  n\n', "can never match"),
 ("a literal inside Ok", 'fn f(xs List[Int]) Int\n  when first(xs)\n    Ok("a") -> 1\n    _ -> 0\n', "can never match"),
 ("the right cases are fine", 'fn f(xs List[Int]) Int\n  when first(xs)\n    Ok(n) -> n\n    Err(_) -> 0\nfn g(o Option[Int]) Int\n  when o\n    Some(n) -> n\n    None -> 0\n', None),
 ("a program's own Some is left alone", 'enum Box\n  Some(n Int)\n  Empty\nfn f(b Box) Int\n  when b\n    Some(n) -> n\n    Empty -> 0\n', None),
 ("a dropped Result", F + 'fn g() Int\n  f()\n  2\n', "this `Result` is dropped"),
 ("a dropped Result in a loop", F + 'for i in 0..2\n  f()\n', "this `Result` is dropped"),
 ("a dropped library Result", 'fn g() Int\n  write_file("/tmp/x", "a")\n  2\n', "this `Result` is dropped"),
 ("backslash drops on purpose", F + 'fn g() Int\n  \\ f()\n  2\n', None),
 ("a Result passed on with ?", F + 'fn g() Result[Int, Error]\n  f()?\n  Ok(2)\n', None),
 ("a Result bound to a name", F + 'fn g() Int\n  r = f()\n  2\n', None),
 ("the last line is the value", F + 'fn g() Result[Int, Error]\n  f()\n', None),
 ("a Unit call", 'fn p() Unit\n  println(1)\nfn g() Int\n  p()\n  2\n', None),
 ("cast of a constant that is too big", 'x = cast[UInt8](300)\n', "the constant 300 does not fit `UInt8`"),
 ("cast of a negative to unsigned", 'x = cast[UInt8](-1)\n', "the constant -1 does not fit `UInt8`"),
 ("cast of a constant expression", 'x = cast[Int8](100 + 100)\n', "the constant 200 does not fit `Int8`"),
 ("cast of a value that fits", 'x = cast[UInt8](200)\n', None),
 ("cast of a variable", 'n = 300\nx = cast[UInt8](n)\n', None),
]
fails = []
for name, src, want in CASES:
    rc, out = check(src)
    good = (want in out) if want is not None else (rc == 0 and "warning" not in out and "error" not in out)
    print(("ok    " if good else "FAIL  ") + name + ("" if good else f"  -> rc={rc} {out.strip()[:300]!r}"))
    if not good:
        fails.append(name)
sys.exit(1 if fails else 0)
