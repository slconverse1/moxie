"""A keyword cannot name a function (a method may be called `run`).  Run: python3 tests/run_keyname.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
CASES = [
 ("fn run is rejected", "fn run(n Int) Int = n + 1\nprintln(run(2))\n", 2, "`run` is a keyword"),
 ("fn daemon is rejected", "fn daemon(n Int) Int = n + 1\n", 2, "`daemon` is a keyword"),
 ("fn move is rejected", "fn move(n Int) Int = n\n", 2, "`move` is a keyword"),
 ("a method may be called run", "tuple T()\nimpl T\n  fn run(self) Int = 1\nprintln(T().run())\n", 0, "1"),
 ("an interface method may be called do_it and run", "interface Job\n  fn run(self) Int\ntuple J()\nimpl Job for J\n  fn run(self) Int = 7\nprintln(J().run())\n", 0, "7"),
]
fails = []
for name, src, rc_want, word in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check" if rc_want == 2 else "run", f.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        ok = ((r.returncode != 0) if rc_want else r.returncode == 0) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:240]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
