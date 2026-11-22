"""`where` after a result type is an `ensures`, and `where` after a tuple field is an `invariant`.  Run: python3 tests/run_wherepos.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ABS = "fn abs(n Int) Int where result >= 0\n  if n < 0\n    0 - n\n  else\n    n\n"
CASES = [
 ("a result where holds", ABS + "println(abs(-4))\n", 0, "4"),
 ("a result where is an ensures", "fn bad(n Int) Int where result >= 0\n  n\nprintln(bad(-1))\n", 1, "ensures failed in bad: result >= 0 (supplier bug)"),
 ("a field where holds", "tuple Account deriving show\n  balance Int where balance >= 0\nprintln(Account(balance: 5))\n", 0, "Account(balance: 5)"),
 ("a field where is an invariant", "tuple Account deriving show\n  balance Int where balance >= 0\nprintln(Account(balance: -1))\n", 1, "invariant of Account failed: balance >= 0"),
 ("a header field where is an invariant", "tuple Box(w Int where w > 0, h Int) deriving show\nprintln(Box(0, 3))\n", 1, "invariant of Box failed: w > 0"),
 ("a rebuild is checked too", "tuple Account deriving show\n  balance Int where balance >= 0\na = Account(balance: 1)\nb = Account(...a, balance: -3)\nprintln(b)\n", 1, "invariant of Account failed"),
]
fails = []
for name, src, rc, want in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name], cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = (r.stdout + r.stderr).strip()
        ok = (r.returncode == 0 and o == want) if rc == 0 else (r.returncode != 0 and want in o)
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o[:240]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
