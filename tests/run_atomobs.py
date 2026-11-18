"""Whole-Atom on_change, swap_vals, reset_vals.  Run: python3 tests/run_atomobs.py"""
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
def chk(name, src, rc_want, *wants, cmd="run", no=()):
    for flags in ((), ("--gc",)):
        rc, out = run(src, flags, cmd)
        ok = rc == rc_want and all(w in out for w in wants) and not any(w in out for w in no)
        label = name + (" (gc)" if flags else "")
        print(("ok    " if ok else "FAIL  ") + label + ("" if ok else f"  (rc {rc}) {out[:300]!r}"))
        if not ok: fails.append(label)

NOTE = "fn note(old Int, new Int) Unit\n  println(\"${old} -> ${new}\")\n"
chk("a whole-Atom observer hears each change", NOTE + "c = Atom[Int](0)\non_change(c, note)\nswap(c, _ + 1)\nreset(c, 5)\n", 0, "0 -> 1\n1 -> 5")
chk("no call when the value stays the same", NOTE + "c = Atom[Int](1)\non_change(c, note)\nreset(c, 1)\nswap(c, _ * 1)\nprintln(\"done\")\n", 0, "done", no=("->",))
chk("off_change removes it", NOTE + "c = Atom[Int](0)\ntok = on_change(c, note)\nreset(c, 1)\noff_change(c, tok)\nreset(c, 2)\n", 0, "0 -> 1", no=("1 -> 2",))
chk("a rejected value is never heard", NOTE + "c = Atom[Int](1, valid: (n) -> n > 0)\non_change(c, note)\ntry_reset(c, -3)\ntry_reset(c, 4)\n", 0, "1 -> 4", no=("-3",))
chk("a lambda handler", "c = Atom[Int](0)\non_change(c, (a Int, b Int) -> b)\nprintln(swap(c, _ + 1))\n", 0, "1")
chk("swap_vals and reset_vals return (old, new)", "c = Atom[Int](9)\nprintln(swap_vals(c, _ + 1))\nprintln(reset_vals(c, 0))\nprintln(@c)\n", 0, "(9, 10)\n(10, 0)\n0")
chk("swap_vals aborts on a rejected value", "c = Atom[Int](1, valid: (n) -> n > 0)\nswap_vals(c, _ - 5)\nprintln(\"not reached\")\n", 1, "rejected by the Atom's `valid` check")
chk("a handler with one parameter is an error", "fn one(x Int) Unit\n  println(x)\nc = Atom[Int](0)\non_change(c, one)\n", 1, "takes two parameters", cmd="check")
chk("a handler of the wrong type is an error", "fn s(a String, b String) Unit\n  println(a)\nc = Atom[Int](0)\non_change(c, s)\n", 1, "mismatched types", cmd="check")
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
