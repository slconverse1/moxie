"""Decimal `div` returns a Result and a zero divisor is an Err, not a Python exception.  Run: python3 tests/run_decdiv.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [("div(10.00d, 3.00d, 4, #half_up)", 'Ok(3.3333)'), ("div(10.00d, 4.00d, 1, #half_even)", 'Ok(2.5)'),
         ("div(1.0d, 0.0d, 2, #half_up)", 'Err(Error(code: 6, message: "division by zero"))')]
bad = 0
for expr, want in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write("println(%s)\n" % expr)
    r = subprocess.run([sys.executable, "-m", "moxie", "run", f.name], cwd=ROOT, capture_output=True, text=True)
    os.unlink(f.name)
    ok = r.returncode == 0 and r.stdout.strip() == want
    print(("ok    " if ok else "FAIL  ") + expr + " -> " + (r.stdout.strip() or r.stderr.strip()[-80:]))
    bad += 0 if ok else 1
sys.exit(1 if bad else 0)
