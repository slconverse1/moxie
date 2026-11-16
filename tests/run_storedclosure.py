"""A capturing closure in a collection literal: an error in moxie, fine in moxie/gc; module-level names aren't captures.  Run: python3 tests/run_storedclosure.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP = 'fn go(k Int) Unit\n  t = Dict("a" -> (x Int) -> x * k)\n  println(t("a").unwrap()(5))\ngo(3)\n'
LST = 'fn go(k Int) Unit\n  t = List((x Int) -> x + k)\n  println(len(t))\ngo(3)\n'
MOD = 'rate = 3\nt = Dict("a" -> (x Int) -> x * rate)\nprintln(t("a").unwrap()(5))\n'
CASES = [
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
