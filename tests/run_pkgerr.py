"""A syntax error in an imported package gives a clean message (file, line, column), not a Python traceback.  Run: python3 tests/run_pkgerr.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = tempfile.mkdtemp()
os.mkdir(os.path.join(d, "lib"))
open(os.path.join(d, "lib", "lib.mxi"), "w").write("fn broken(x: Int) Int:\n  x +\n")
main = os.path.join(d, "main.mxi")
open(main, "w").write("import lib\nprintln(lib.broken(1))\n")
fails = []
for name, args, want_rc in (("check", ["check", main], 1), ("run", ["run", main], 2), ("run, check skipped", ["run", main, "--no-check"], 2)):
    r = subprocess.run([sys.executable, "-m", "moxie"] + args, cwd=ROOT, capture_output=True, timeout=60)
    o = r.stdout.decode() + r.stderr.decode()
    ok = r.returncode == want_rc and "syntax error" in o and "lib.mxi:3:1" in o and "Traceback" not in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {r.returncode}) {o[:300]!r}"))
    if not ok:
        fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
