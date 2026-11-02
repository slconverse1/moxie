"""Contract tests: requires / ensures / invariant.  Run: python3 tests/run_contracts.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROG = '''fn inc(x: Int) Int:
  requires x > 0
  ensures result > x
  x + 1
fn bad(x: Int) Int:
  ensures result > x
  x - 1
tuple P:
  a: Int
  invariant a >= 0
'''

def run(body, *flags):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(PROG + body)
    r = subprocess.run([sys.executable, "-m", "moxie", *flags, "run", f.name], cwd=ROOT, capture_output=True, text=True)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr

fails = []
def chk(name, cond):
    print(("ok    " if cond else "FAIL  ") + name)
    if not cond: fails.append(name)

rc, o = run('println("${inc(1)}")\n')
chk("passing contracts", rc == 0 and o.strip() == "2")
rc, o = run('println("${inc(0)}")\n')
chk("requires failure blames caller", rc != 0 and "requires failed in inc" in o and "caller bug" in o)
rc, o = run('println("${bad(5)}")\n')
chk("ensures failure blames supplier", rc != 0 and "ensures failed in bad" in o and "supplier bug" in o)
rc, o = run('println("${P(a: -1)}")\n')
chk("invariant failure at construction", rc != 0 and "invariant of P failed" in o)
rc, o = run('println("${P(a: 3)}")\n')
chk("invariant holds", rc == 0 and "P(a: 3)" in o)
rc, o = run('println("${inc(0)}")\n', "--release")
chk("--release strips checks", rc == 0 and o.strip() == "1")
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
