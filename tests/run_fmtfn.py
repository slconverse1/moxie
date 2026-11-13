"""`fmt` (a String, literal templates only) and `try_fmt` (a Result, any template): the output, the Err cases, and the compile-time checks.  Run: python3 tests/run_fmtfn.py"""
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

case("fmt fills fields with specs", 'println(fmt("{:>8.2f} | {:<5}|", 12.5, "Ann"))\n', 0, "   12.50 | Ann  |")
case("fmt plain field and braces", 'println(fmt("{{}} {} {}", 1, "x"))\n', 0, "{} 1 x")
case("fmt hex with prefix", 'println(fmt("{:#06x}", 255))\n', 0, "0x00ff")
case("fmt with no fields", 'println(fmt("hi"))\n', 0, "hi")
case("fmt gives a String", 's String = fmt("{}", 7)\nprintln(len(s))\n', 0, "1")
case("too many arguments is a compile error", 'println(fmt("{}", 1, 2))\n', 2, "has 1 field, but 2 arguments are given")
case("too few arguments is a compile error", 'println(fmt("{} {}", 1))\n', 2, "has 2 fields, but 1 argument is given")
case("a spec that does not fit is a compile error", 'println(fmt("{:.2f}", "s"))\n', 2, "needs a number, but this is a `String`")
case("a malformed template is a compile error", 'println(fmt("{", 1))\n', 2, "bad `fmt` template")
case("fmt needs a literal template", 't = "{}"\nprintln(fmt(t, 1))\n', 2, "needs a string-literal template", "try_fmt")
case("try_fmt takes any template", 't = "{}"\nprintln(try_fmt(t, 1))\n', 0, 'Ok("1")')
case("try_fmt with a bad spec is an Err, not a crash", 't = "{:.2f}"\nwhen try_fmt(t, "s")\n  Ok(s) -> println(s)\n  Err(e) -> println("bad: ${e.code}")\n', 0, "bad: 13")
case("try_fmt with the wrong count is an Err", 't = "{} {}"\nwhen try_fmt(t, 1)\n  Ok(s) -> println(s)\n  Err(e) -> println(e.message)\n', 0, "more fields than arguments")
case("try_fmt with a literal is still checked", 'println(try_fmt("{}", 1, 2))\n', 2, "has 1 field, but 2 arguments are given")
case("try_fmt gives a Result", 'r Result[String, Error] = try_fmt("{}", 7)\nprintln(is_ok(r))\n', 0, "true")
case("a user function named fmt wins", 'fn fmt(a Int) Int\n  a + 1\nprintln(fmt(1))\n', 0, "2")

print()
print("FAILURES: " + ", ".join(fails) if fails else "all fmt function tests passed")
sys.exit(1 if fails else 0)
