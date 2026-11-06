"""`\\expr` discards a value at statement start."""
import sys, io, contextlib, subprocess
sys.path.insert(0, ".")
GOOD = r'''
fn f(x: Int) Int:
  x + 1
\f(1)
\f(2) if true
rx, tx = Chan[Int][2]()
\write(tx, 1)
fiber fn w(t: ChanW[Int]) Unit:
  \write(t, 5)
\run w(tx)
println("ok ${read(rx).get_or(0)}")
'''
BAD = [
  ("fn main() Unit:\n  y = \\f(1)\n", "can only start a statement"),
  ("x = 1 + \\2\n", "can only start a statement"),
]
fails = 0
def run(src, *flags):
    open("/tmp/_discard.mx", "w").write(src)
    return subprocess.run([sys.executable, "-m", "moxie", *flags, "run", "/tmp/_discard.mx"],
                          capture_output=True, text=True)
for flags in ((), ("--gc",)):
    r = run(GOOD, *flags)
    if r.stdout.strip() != "ok 1" or r.returncode:
        fails += 1; print("FAIL good", flags, r.stdout, r.stderr)
    for src, msg in BAD:
        r = run(src, *flags)
        if msg not in r.stdout + r.stderr:
            fails += 1; print("FAIL bad", flags, src, r.stdout, r.stderr)
print("discard: FAIL" if fails else "discard: ok")

# Err(fail(...)) double wrap is a compile error
bad = "fn a(x: Int) Result[Int, Error]:\n  Err(fail(1, \"x\"))\n"
good = "fn a(x: Int) Result[Int, Error]:\n  fail(1, \"x\")\nfn b(x: Int) Result[Int, Error]:\n  Err(Error(1, \"x\"))\nprintln(a(1).is_err())\n"
for flags in ((), ("--gc",)):
    r = run(bad, *flags)
    if "wraps an `Err` in an `Err`" not in r.stdout + r.stderr:
        print("FAIL double wrap", flags, r.stdout, r.stderr); fails += 1
    r = run(good, *flags)
    if r.stdout.strip() != "true":
        print("FAIL fail ok", flags, r.stdout, r.stderr); fails += 1
print("double wrap: FAIL" if fails else "double wrap: ok")
