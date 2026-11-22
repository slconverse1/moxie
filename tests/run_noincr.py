"""`x++` and `x--` are gone: write `x += 1` and `x -= 1`.  Run: python3 tests/run_noincr.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [
 ("x++ is refused", "x = 1\nx++\nprintln(x)\n", 2, "write `x += 1`"),
 ("x-- is refused", "x = 1\nx--\nprintln(x)\n", 2, "write `x -= 1`"),
 ("a place ++ is refused", "tuple P deriving show\n  n Int\nfn f(p P) P\n  mutable\n    q = p\n    q.n++\n    q\nprintln(f(P(1)))\n", 2, "`++` is not used"),
 ("x += 1 works", "x = 1\nx += 1\nprintln(x)\n", 0, "2"),
 ("x -= 1 works", "x = 3\nx -= 1\nprintln(x)\n", 0, "2"),
]
fails = []
for name, src, rc, want in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        r = subprocess.run([sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name], cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = (r.stdout + r.stderr).strip()
        ok = r.returncode == rc and (want in o if rc else o == want)
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o[:200]!r}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
