"""A keyword cannot name a function (a method may be called `go`).  Run: python3 tests/run_keyname.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
CASES = [
 ("fn go is rejected", "fn go(n Int) Int = n + 1\nprintln(go(2))\n", 2, "`go` is a keyword"),
 ("fn daemon is rejected", "fn daemon(n Int) Int = n + 1\n", 2, "`daemon` is a keyword"),
 ("fn try_go is rejected", "fn try_go(n Int) Int = n\n", 2, "`try_go` is a keyword"),
 ("fn move is rejected", "fn move(n Int) Int = n\n", 2, "`move` is a keyword"),
 ("a method may be called go", "tuple T() deriving show\nimpl T\n  fn go(self) Int = 1\nprintln(T().go())\n", 0, "1"),
 ("run is an ordinary name again", "fn run(n Int) Int = n + 1\nprintln(run(2))\n", 0, "3"),
 ("an interface method may be called do_it and run", "interface Job\n  fn run(self) Int\ntuple J() deriving show\nimpl Job for J\n  fn run(self) Int = 7\nprintln(J().run())\n", 0, "7"),
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
