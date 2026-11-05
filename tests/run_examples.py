"""Every program in examples/ must pass `moxie check`, and sql.mxi must run.  Run: python3 tests/run_examples.py"""
import glob, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []
for f in sorted(glob.glob(os.path.join(ROOT, "examples", "*.mxi"))):
    flags = ["--gc"] if f.endswith("_gc.mxi") else []
    r = subprocess.run([sys.executable, "-m", "moxie", *flags, "check", f], cwd=ROOT, capture_output=True, timeout=60)
    ok = r.returncode == 0
    print(("ok    " if ok else "FAIL  ") + "checks: " + os.path.basename(f) + ("" if ok else "  " + (r.stdout + r.stderr).decode()[:200]))
    if not ok: fails.append(f)
r = subprocess.run([sys.executable, "-m", "moxie", "run", "--allow-all", os.path.join(ROOT, "examples", "sql.mxi")], cwd=ROOT, capture_output=True, timeout=60)
o = r.stdout.decode()
ok = "inserted Ok(3)" in o and "1 70\n2 80" in o and "SELEKT" in o
print(("ok    " if ok else "FAIL  ") + "runs: sql.mxi" + ("" if ok else "  " + o[:200]))
if not ok: fails.append("sql run")
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
