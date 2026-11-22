"""Typestate with a phantom type parameter (no new compiler feature).  Run: python3 tests/run_typestate.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
HEAD = """tuple Open() deriving show
tuple Closed() deriving show
tuple File[S] deriving show
  name String

fn mk(n String) File[Open] = File(name: n)
fn rd(f File[Open]) String = "read " + f.name
fn cl(f File[Open]) File[Closed] = File(name: f.name)

f = mk("a.txt")
"""
CASES = [
 ("reading while open, then closing", HEAD + "println(rd(f))\ng = cl(f)\nprintln(g.name)\n", 0, "read a.txt\na.txt"),
 ("reading after close is an error", HEAD + "g = cl(f)\nprintln(rd(g))\n", 2, "expected `File[Open]`, found `File[Closed]`"),
 ("closing twice is an error", HEAD + "g = cl(f)\nh = cl(g)\n", 2, "expected `File[Open]`, found `File[Closed]`"),
]
fails = []
for name, src, rc_want, word in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as fh:
            fh.write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check" if rc_want == 2 else "run", fh.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        os.unlink(fh.name)
        o = r.stdout + r.stderr
        ok = ((r.returncode != 0) if rc_want else r.returncode == 0) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:240]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
