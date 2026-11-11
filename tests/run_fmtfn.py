"""`fmt(template, args...)`: the output, the Err cases, and the compile-time checks.  Run: python3 tests/run_fmtfn.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []

def run(src, *args):
    d = tempfile.mkdtemp(prefix="mxfmt")
    p = os.path.join(d, "t.mxi")
    open(p, "w").write(src)
    r = subprocess.run([sys.executable, "-m", *("moxie",) , *args, p], cwd=ROOT, capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout + r.stderr

def case(name, src, rc_want, *wants, args=()):
    rc, out = run(src, *args)
    ok = rc == rc_want and all(w in out for w in wants)
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
    if not ok:
        fails.append(name)

case("fills fields with specs", 'when fmt("{:>8.2f} | {:<5}|", 12.5, "Ann"):\n  Ok(s) -> println(s)\n  Err(e) -> println(e.message)\n', 0, "   12.50 | Ann  |")
case("plain field and braces", 'when fmt("{{}} {} {}", 1, "x"):\n  Ok(s) -> println(s)\n  Err(e) -> println(e.message)\n', 0, "{} 1 x")
case("hex with prefix", 'when fmt("{:#06x}", 255):\n  Ok(s) -> println(s)\n  Err(e) -> println(e.message)\n', 0, "0x00ff")
case("no fields", 'when fmt("hi"):\n  Ok(s) -> println(s)\n  Err(e) -> println(e.message)\n', 0, "hi")
case("too many arguments is a compile error", 'println(fmt("{}", 1, 2))\n', 2, "has 1 field, but 2 arguments are given")
case("too few arguments is a compile error", 'println(fmt("{} {}", 1))\n', 2, "has 2 fields, but 1 argument is given")
case("a spec that does not fit is a compile error", 'println(fmt("{:.2f}", "s"))\n', 2, "needs a number, but this is a `String`")
case("a malformed template is a compile error", 'println(fmt("{", 1))\n', 2, "bad `fmt` template")
case("a template that is not a literal warns", 't = "{}"\nprintln(fmt(t, 1))\n', 0, "not a string literal", "Ok(\"1\")")
case("a bad template that is not a literal is an Err, not a crash", 't = "{:.2f}"\nwhen fmt(t, "s"):\n  Ok(s) -> println(s)\n  Err(e) -> println("bad: ${e.code}")\n', 0, "bad: 13")
case("a wrong count that is not a literal is an Err", 't = "{} {}"\nwhen fmt(t, 1):\n  Ok(s) -> println(s)\n  Err(e) -> println(e.message)\n', 0, "more fields than arguments")
case("a user function named fmt wins", 'fn fmt(a: Int) Int:\n  a + 1\nprintln(fmt(1))\n', 0, "2")

print()
print("FAILURES: " + ", ".join(fails) if fails else "all fmt function tests passed")
sys.exit(1 if fails else 0)
