"""Atoms and timers print readably.  Run: python3 tests/run_atomshow.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROG = 'a = Atom(10)\nprintln(a)\nprintln("${a}")\nprintln(Atom(List(1, 2)))\nprintln(Timer())\nprintln(@a)\n'
with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
    f.write(PROG)
r = subprocess.run([sys.executable, "-m", "moxie", "run", f.name], cwd=ROOT, capture_output=True, text=True)
os.unlink(f.name)
ok = r.returncode == 0 and r.stdout.split("\n")[:-1] == ["Atom(10)", "Atom(10)", "Atom(List(1, 2))", "Timer()", "10"]
print(("ok    " if ok else "FAIL  ") + "atoms and timers print readably")
if not ok: print(r.stdout, r.stderr)
sys.exit(0 if ok else 1)
