"""Atom validators: Atom[T](v, valid: f), swap/reset abort on a rejected value, try_swap/try_reset give Err.  Run: python3 tests/run_atomvalid.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(src, flags=(), cmd="run"):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    try:
        r = subprocess.run([sys.executable, "-m", "moxie", *flags, cmd, f.name], cwd=ROOT, capture_output=True, timeout=60)
        rc, out = r.returncode, r.stdout.decode() + r.stderr.decode()
    except subprocess.TimeoutExpired:
        rc, out = -9, "TIMEOUT"
    os.unlink(f.name)
    return rc, out

fails = []
def chk(name, src, rc_want, *wants, cmd="run"):
    for flags in ((), ("--gc",)):
        rc, out = run(src, flags, cmd)
        ok = rc == rc_want and all(w in out for w in wants)
        label = name + (" (gc)" if flags else "")
        print(("ok    " if ok else "FAIL  ") + label + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
        if not ok: fails.append(label)

PCT = "pct = Atom[Int](0, valid: (n) -> n in 0..100)\n"
chk("an accepted swap stores and returns the new value", PCT + "println(swap(pct, _ + 30))\nprintln(@pct)\n", 0, "30\n30")
chk("try_swap rejects a bad value and leaves the Atom alone", PCT + "swap(pct, _ + 30)\nprintln(try_swap(pct, _ + 90))\nprintln(@pct)\nprintln(try_swap(pct, _ + 5))\n", 0, "Err(Error(code: 6", "30\nOk(35)")
chk("try_reset", PCT + "println(try_reset(pct, 50))\nprintln(try_reset(pct, -1))\nprintln(@pct)\n", 0, "Ok(50)\nErr(", "50")
chk("swap aborts on a rejected value", PCT + "swap(pct, _ + 500)\nprintln(\"not reached\")\n", 1, "rejected by the Atom's `valid` check")
chk("reset aborts on a rejected value", PCT + "reset(pct, -5)\nprintln(\"not reached\")\n", 1, "rejected by the Atom's `valid` check")
chk("the initial value is checked", "a = Atom[Int](-1, valid: (n) -> n >= 0)\nprintln(\"not reached\")\n", 1, "initial value was rejected")
chk("watchers never see a rejected value", """tuple Account deriving show
  owner String,
  property balance Int = 0
fn note(old Int, new Int) Unit
  println("saw ${new}")
shared = Atom[Account](Account(owner: "Ann"), valid: (a) -> a.balance >= 0)
shared.on_change(balance, note)
try_swap(shared, (a) -> Account(owner: a.owner, balance: -4))
try_swap(shared, (a) -> Account(owner: a.owner, balance: 7))
""", 0, "saw 7")
chk("an Atom with no valid works as before", "a = Atom[Int](1)\nprintln(swap(a, _ + 1))\nprintln(try_swap(a, _ * 5))\n", 0, "2\nOk(10)")
chk("valid must be a function", "a = Atom[Int](1, valid: 5)\n", 1, "`valid:` must be a function", cmd="check")
chk("a valid check may not park", "c = Chan[Int](1)\nfn ok_(n Int) Bool\n  read(c) > 0\na = Atom[Int](0, valid: ok_)\n", 1, "valid check may park", cmd="check")
chk("the initial type still checks with valid", "b Atom[String] = Atom[Int](1, valid: (n) -> n > 0)\n", 1, "mismatched types", cmd="check")
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
