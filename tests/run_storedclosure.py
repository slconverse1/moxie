"""A capturing closure in a collection literal: an error in moxie, fine in moxie/gc; module-level names aren't captures.  Run: python3 tests/run_storedclosure.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP = 'fn go(k Int) Unit\n  t = Dict("a" -> (x Int) -> x * k)\n  println(t("a").unwrap()(5))\ngo(3)\n'
LST = 'fn go(k Int) Unit\n  t = List((x Int) -> x + k)\n  println(len(t))\ngo(3)\n'
MOD = 'rate = 3\nt = Dict("a" -> (x Int) -> x * rate)\nprintln(t("a").unwrap()(5))\n'
LOCALC = 'fn go(n Int) Unit\n  k = 3\n  m = k * 2\n  t = Dict("a" -> (x Int) -> x * m)\n  println(t("a").unwrap()(5))\ngo(1)\n'
REBOUND = 'fn go(n Int) Unit\n  k = 3\n  k = k + n\n  t = Dict("a" -> (x Int) -> x * k)\n  println(t("a").unwrap()(5))\ngo(1)\n'
PARAM = 'fn go(n Int) Unit\n  t = Dict("a" -> (x Int) -> x * n)\n  println(t("a").unwrap()(5))\ngo(1)\n'
ENTRY_REBOUND = 'rate = 3\nrate += 1\nt = Dict("a" -> (x Int) -> x * rate)\nprintln(t("a").unwrap()(5))\n'
LOOPED = 'fn go() Unit\n  k = 3\n  for i in List(1, 2)\n    k = k + i\n  t = Dict("a" -> (x Int) -> x * k)\n  println(t("a").unwrap()(5))\ngo()\n'
CASES = [
 ('a local bound once to a constant is not a capture', LOCALC, False, 0, '30'),
 ('a local bound to a constant but rebound is a capture', REBOUND, False, 2, 'closure captures `k`'),
 ('a parameter is a capture', PARAM, False, 2, 'closure captures `n`'),
 ('an entry-file name that is rebound is a capture', ENTRY_REBOUND, False, 2, 'closure captures `rate`'),
 ('a name rebound in a loop is a capture', LOOPED, False, 2, 'closure captures `k`'),
 ('Dict literal captures a local', CAP, False, 2, 'only plain functions can be stored'),
 ('List literal captures a local', LST, False, 2, 'only plain functions can be stored'),
 ('moxie/gc stores it', CAP, True, 0, '15'),
 ('module-level name is not a capture', MOD, False, 0, '15'),
]
fails = []
for name, src, gc, rc_want, word in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name], cwd=ROOT, capture_output=True, text=True)
    os.unlink(f.name)
    o = r.stdout + r.stderr
    ok = ((r.returncode == 0) == (rc_want == 0)) and word in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:200]}"))
    if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
