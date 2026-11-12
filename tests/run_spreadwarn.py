"""Spreading a List into a variadic: a warning in no-GC moxie (count checked at run time), silent in moxie/gc.  Run: python3 tests/run_spreadwarn.py"""
import subprocess, sys, os, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = 'fn total(xs ...Int) Int\n  xs |> sum()\nvals = List(1, 2, 3)\nprintln(total(...vals))\n'
f = os.path.join(tempfile.mkdtemp(), "t.mx")
open(f, "w").write(SRC)
fails = []
for name, flags, warn in (("no-GC warns", [], True), ("gc is silent", ["--gc"], False)):
    r = subprocess.run([sys.executable, "-m", "moxie", *flags, "run", f], capture_output=True, text=True, cwd=ROOT, timeout=120)
    ok = "6" in r.stdout and (("spreading a `List`" in r.stderr) == warn) and "Traceback" not in r.stderr
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  -> {(r.stdout + r.stderr).strip()[-200:]!r}"))
    if not ok:
        fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
