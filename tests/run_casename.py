"""A program's own enum case that shares a name with a prelude type (`Key`).  Run: python3 tests/run_casename.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(src, flags=()):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    try:
        r = subprocess.run([sys.executable, "-m", "moxie", *flags, "run", f.name], cwd=ROOT, capture_output=True, timeout=60)
        rc, out = r.returncode, r.stdout.decode() + r.stderr.decode()
    except subprocess.TimeoutExpired:
        rc, out = -9, "TIMEOUT"
    os.unlink(f.name)
    return rc, out

fails = []
def chk(name, src, rc_want, *wants):
    for flags in ((), ("--gc",)):
        rc, out = run(src, flags)
        ok = rc == rc_want and all(w in out for w in wants)
        label = name + (" (gc)" if flags else "")
        print(("ok    " if ok else "FAIL  ") + label + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
        if not ok: fails.append(label)

chk("a case named Key is built and matched", '''enum Event
  Click(x Int),
  Key(c String),
  Quit
fn show(e Event) String
  when e
    Click(x) -> "click ${x}"
    Key(c) -> "key ${c}"
    Quit -> "quit"
println(show(Key("a")))
println(show(Click(3)))
println(Key("b"))
''', 0, "key a\nclick 3\nEvent.Key(\"b\")")
chk("the prelude's own Key cases still work", 'k = Key.Enter\nprintln(k)\n', 0, "Key.Enter")
chk("a bare case named Option is the program's own case", '''enum Mode deriving eq
  Option
  Plain
x Mode = Option
println(x == Mode.Option)
println(x)
when x
  Option -> println("opt")
  Plain -> println("plain")
''', 0, "true\nMode.Option\nopt")
chk("a mistyped prelude case is a compile error", 'e = Option.Som(3)\n', 2, "`Option` has no case `Som`")
chk("a prelude case with the wrong number of values", 'q Option[Int] = Some()\n', 2, "`Some` has 1 field, but 0 values are given")
chk("a prelude case with too many values", 'q Option[Int] = Option.Some(1, 2)\n', 2, "`Some` has 1 field, but 2 values are given")
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
